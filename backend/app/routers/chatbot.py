from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from ..services.chat import process_chat_query, get_chat_history

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])


@router.post("/query", response_model=ChatResponse)
def chat_query(data: ChatRequest, db: Session = Depends(get_db)):
    result = process_chat_query(
        query=data.query,
        session_id=data.session_id,
        db=db,
        selected_product_id=data.selected_product_id,
    )
    return ChatResponse(**result)


@router.get("/history", response_model=list[ChatHistoryResponse])
def chat_history(
    session_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_chat_history(session_id, db, limit)
