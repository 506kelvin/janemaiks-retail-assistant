from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    supplier: Optional[str] = None
    wholesale_price: float = Field(..., gt=0)
    quantity_in_package: int = Field(default=1, gt=0)
    unit_type: Optional[str] = "piece"
    retail_price: Optional[float] = None
    profit_per_item: Optional[float] = None
    profit_margin_percent: Optional[float] = None

    # New pricing fields
    package_cost_price: Optional[float] = None
    package_quantity: Optional[int] = Field(default=None, ge=1)
    package_unit_type: Optional[str] = None
    wholesale_selling_price: Optional[float] = None
    actual_retail_price: Optional[float] = None
    profit_margin_per_unit: Optional[float] = None
    allow_manual_override: Optional[bool] = False
    rounding_strategy: Optional[str] = "none"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    wholesale_price: Optional[float] = None
    quantity_in_package: Optional[int] = None
    unit_type: Optional[str] = None
    retail_price: Optional[float] = None
    profit_per_item: Optional[float] = None
    profit_margin_percent: Optional[float] = None
    is_active: Optional[bool] = None

    # New pricing fields
    package_cost_price: Optional[float] = None
    package_quantity: Optional[int] = None
    package_unit_type: Optional[str] = None
    wholesale_selling_price: Optional[float] = None
    actual_retail_price: Optional[float] = None
    profit_margin_per_unit: Optional[float] = None
    allow_manual_override: Optional[bool] = None
    rounding_strategy: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    supplier: Optional[str]
    wholesale_price: float
    quantity_in_package: int
    unit_type: Optional[str]
    retail_price: Optional[float]
    profit_per_item: Optional[float]
    profit_margin_percent: Optional[float]

    # New pricing fields
    package_cost_price: Optional[float]
    package_quantity: Optional[int]
    package_unit_type: Optional[str]
    unit_cost_price: Optional[float]
    wholesale_selling_price: Optional[float]
    suggested_retail_price: Optional[float]
    actual_retail_price: Optional[float]
    profit_margin_per_unit: Optional[float]
    allow_manual_override: Optional[bool]
    rounding_strategy: Optional[str]

    is_active: bool
    date_added: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PriceRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    quantity: Optional[float] = 1


class PriceResponse(BaseModel):
    product_name: str
    unit_wholesale_price: float
    profit_per_item: Optional[float]
    retail_price_per_unit: float
    total_price: float
    calculation_breakdown: str
    is_calculated: bool

    # New pricing info
    unit_cost_price: Optional[float] = None
    wholesale_selling_price: Optional[float] = None
    suggested_retail_price: Optional[float] = None
    actual_retail_price: Optional[float] = None
    rounded_price: Optional[float] = None
    rounding_strategy: Optional[str] = None


class SuggestPriceRequest(BaseModel):
    product_id: int
    profit_margin_per_unit: Optional[float] = None
    rounding_strategy: Optional[str] = "none"


class SuggestPriceResponse(BaseModel):
    product_id: int
    product_name: str
    package_cost_price: float
    package_quantity: int
    unit_cost_price: float
    profit_margin_per_unit: float
    suggested_retail_price: float
    rounded_price: Optional[float] = None
    actual_retail_price: Optional[float] = None
    wholesale_selling_price: Optional[float] = None
    rounding_strategy: str


class RoundPriceRequest(BaseModel):
    price: float
    strategy: str = "none"


class RoundPriceResponse(BaseModel):
    original_price: float
    rounded_price: float
    strategy: str
