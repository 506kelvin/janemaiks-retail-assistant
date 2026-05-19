from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    selected_product_id: Optional[int] = None


class ClarificationMatch(BaseModel):
    id: int
    name: str
    category: str = ""
    supplier: str = ""
    score: float = 0.0


class ChatResponse(BaseModel):
    response: str
    products_found: list[str] = []
    calculation_used: bool = False
    calculation_detail: Optional[str] = None
    session_id: Optional[str] = None
    type: str = "normal"
    clarification_matches: list[ClarificationMatch] = []


class ChatHistoryResponse(BaseModel):
    id: int
    user_query: str
    bot_response: str
    products_referenced: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
