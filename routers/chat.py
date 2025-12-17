from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth.firebase import require_firebase_token
from rag.engine import get_answer

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/api/chat", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    # 【關鍵】使用 Firebase Token 驗證，而非 API Key
    token_payload: dict = Depends(require_firebase_token) 
):
    user_question = request.message
    
    # 呼叫 RAG 引擎
    ai_reply = get_answer(user_question)
    
    return ChatResponse(reply=ai_reply)