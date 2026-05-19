from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity_available: float
    low_stock_threshold: Optional[float]
    is_low_stock: Optional[bool] = None
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class StockTransactionCreate(BaseModel):
    product_id: int
    transaction_type: str = Field(..., pattern="^(add|deduct|adjust)$")
    quantity: float = Field(..., gt=0)
    notes: Optional[str] = None


class StockTransactionResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: str
    quantity: float
    notes: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
