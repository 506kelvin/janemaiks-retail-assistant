from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base


class RequestedItem(Base):
    __tablename__ = "requested_items"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    request_count = Column(Integer, nullable=False, default=1)
    last_requested_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
