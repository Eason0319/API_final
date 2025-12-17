from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.engine import get_db
from models import posts as post_model, comments as comment_model, likes as like_model, authors as author_model
from schemas import posts as post_schema
from auth.firebase import require_firebase_token  # <--- 【關鍵】記得匯入這個驗證器

router = APIRouter()

# --- 輔助函式 ---
def get_or_create_author(db: Session, author_name: str, profile_pic: str = None):
    db_author = db.query(author_model.Author).filter(author_model.Author.name == author_name).first()
    if not db_author:
        db_author = author_model.Author(name=author_name, profilePic=profile_pic)
        db.add(db_author)
        try:
            db.commit()
            db.refresh(db_author)
        except Exception as e:
            db.rollback()
            db_author = db.query(author_model.Author).filter(author_model.Author.name == author_name).first()
            if not db_author:
                 raise HTTPException(status_code=500, detail=f"Failed to create author: {e}")
    return db_author

# --- GET 路由 (保持公開，不需 Token) ---

@router.get("/api/posts", response_model=List[post_schema.Post])
def get_all_posts(
    db: Session = Depends(get_db),
    # 如果您希望連「看文章列表」都要登入，請把下面這行解開註解：
    # token_payload: dict = Depends(require_firebase_token) 
):
    all_posts = db.query(post_model.Post).all()
    return all_posts

@router.get("/api/posts/{slug}", response_model=post_schema.Post)
def get_post_by_slug(slug: str, db: Session = Depends(get_db)):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/api/posts/{slug}/comments", response_model=List[post_schema.Comment])
def get_comments_for_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post.comments

@router.get("/api/posts/{slug}/likes", response_model=List[post_schema.Like])
def get_likes_for_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post.likes

# --- ▼▼▼ POST / DELETE 路由 (上鎖並修正) ▼▼▼ ---

@router.post("/api/posts/{slug}/comments", response_model=post_schema.Comment, status_code=status.HTTP_201_CREATED)
def create_comment_for_post(
    slug: str, 
    comment_data: post_schema.CommentCreate, 
    db: Session = Depends(get_db),
    token_payload: dict = Depends(require_firebase_token) # <--- 【上鎖】需要登入
):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 【修正】從 Token 獲取作者名稱 (不再從 comment_data 讀取)
    author_name = token_payload.get('name') or token_payload.get('email', '匿名用戶')
    
    db_author = get_or_create_author(db, author_name=author_name)
    
    new_comment = comment_model.Comment(
        text=comment_data.text,
        post_id=post.id,
        author_id=db_author.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment

@router.post("/api/posts/{slug}/like", response_model=post_schema.Like, status_code=status.HTTP_201_CREATED)
def like_post(
    slug: str, 
    like_data: post_schema.LikeCreate, 
    db: Session = Depends(get_db),
    token_payload: dict = Depends(require_firebase_token) # <--- 【上鎖】需要登入
):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 【修正】從 Token 獲取作者名稱，解決 AttributeError
    author_name = token_payload.get('name') or token_payload.get('email', '匿名用戶')
    profile_pic = like_data.profilePic or token_payload.get('picture')

    db_author = get_or_create_author(db, author_name=author_name, profile_pic=profile_pic)

    existing_like = db.query(like_model.Like).filter(
        like_model.Like.post_id == post.id,
        like_model.Like.author_id == db_author.id
    ).first()
    
    if existing_like:
        db.refresh(existing_like)
        return existing_like

    new_like = like_model.Like(
        post_id=post.id,
        author_id=db_author.id
    )
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like

@router.delete("/api/posts/{slug}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    slug: str, 
    like_data: post_schema.LikeCreate, 
    db: Session = Depends(get_db),
    token_payload: dict = Depends(require_firebase_token) # <--- 【上鎖】需要登入
):
    post = db.query(post_model.Post).filter(post_model.Post.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 【修正】從 Token 獲取作者名稱
    author_name = token_payload.get('name') or token_payload.get('email', '匿名用戶')
    
    db_author = db.query(author_model.Author).filter(author_model.Author.name == author_name).first()
    
    if not db_author:
        return 

    existing_like = db.query(like_model.Like).filter(
        like_model.Like.post_id == post.id,
        like_model.Like.author_id == db_author.id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        db.commit()
        
    return