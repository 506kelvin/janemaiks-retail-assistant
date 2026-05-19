from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    supplier = Column(String(200), nullable=True)

    # Search & aliases
    aliases = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    search_keywords = Column(Text, nullable=True)

    # Legacy wholesale fields (kept for backwards compatibility)
    wholesale_price = Column(Float, nullable=False)
    quantity_in_package = Column(Integer, nullable=False, default=1)
    unit_type = Column(String(50), nullable=True, default="piece")

    # Legacy retail fields
    retail_price = Column(Float, nullable=True)
    profit_per_item = Column(Float, nullable=True)
    profit_margin_percent = Column(Float, nullable=True)

    # NEW: Wholesale + retail pricing fields
    package_cost_price = Column(Float, nullable=True)
    package_quantity = Column(Integer, nullable=True, default=1)
    package_unit_type = Column(String(50), nullable=True, default="piece")
    unit_cost_price = Column(Float, nullable=True)
    wholesale_selling_price = Column(Float, nullable=True)
    suggested_retail_price = Column(Float, nullable=True)
    actual_retail_price = Column(Float, nullable=True)
    profit_margin_per_unit = Column(Float, nullable=True)
    allow_manual_override = Column(Boolean, default=False)
    rounding_strategy = Column(String(20), nullable=True, default="none")

    is_active = Column(Boolean, default=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Product(name={self.name}, wholesale={self.wholesale_price})>"
