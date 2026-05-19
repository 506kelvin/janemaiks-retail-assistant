from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from ..database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity_available = Column(Float, nullable=False, default=0)
    low_stock_threshold = Column(Float, nullable=True, default=10)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, qty={self.quantity_available})>"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<StockTransaction(product_id={self.product_id}, type={self.transaction_type}, qty={self.quantity})>"
