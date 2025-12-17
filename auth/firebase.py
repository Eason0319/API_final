import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def init_firebase():
    """
    初始化 Firebase Admin SDK。
    支援從 Vercel 環境變數 (FIREBASE_CREDENTIALS) 或本地檔案 (serviceAccountKey.json) 讀取憑證。
    """
    # 1. 檢查是否已經初始化過 (避免重複初始化錯誤)
    if firebase_admin._apps:
        return

    cred = None
    
    # 2. 優先嘗試從環境變數讀取 (適用於 Vercel)
    firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS")
    
    if firebase_creds_str:
        try:
            # 解析 JSON 字串
            cred_dict = json.loads(firebase_creds_str)
            cred = credentials.Certificate(cred_dict)
            print("Firebase initialized using environment variable.")
        except json.JSONDecodeError as e:
            print(f"Error decoding FIREBASE_CREDENTIALS: {e}")
            
    # 3. 如果沒有環境變數，嘗試讀取本地檔案 (適用於本地開發)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        print("Firebase initialized using local serviceAccountKey.json.")
    
    else:
        print("Warning: No Firebase credentials found! Auth functions may fail.")

    # 4. 執行初始化
    if cred:
        firebase_admin.initialize_app(cred)


def require_firebase_token(authorization: str = Header(None)):
    """
    FastAPI Dependency: 驗證 Request Header 中的 Firebase ID Token
    """
    # 確保在使用驗證功能前，Firebase 已被初始化
    # 如果您的 app.py 忘記呼叫 init_firebase()，這裡是一個最後的補救措施 (Optional)
    if not firebase_admin._apps:
        init_firebase()

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected 'Bearer <token>'"
        )

    token = authorization.split("Bearer ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )