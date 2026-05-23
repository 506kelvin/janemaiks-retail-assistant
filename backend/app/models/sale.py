from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    selling_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
