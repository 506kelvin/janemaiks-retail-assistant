from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas.product import (
    PriceRequest, PriceResponse, SuggestPriceRequest, SuggestPriceResponse,
    RoundPriceRequest, RoundPriceResponse,
)
from ..services.pricing import (
    calculate_retail_price, calculate_unit_wholesale_price,
    suggest_retail_price, get_product_pricing,
    apply_rounding, calculate_unit_cost,
)
from ..services.rag import rag_service
from ..services.search import rank_products

router = APIRouter(prefix="/api/pricing", tags=["Pricing"])


# ============================================================
# LEGACY ENDPOINT (backwards compatible)
# ============================================================

@router.post("/calculate", response_model=PriceResponse)
def calculate_price(data: PriceRequest, db: Session = Depends(get_db)):
    all_products = db.query(Product).filter(Product.is_active == True).all()
    ranked = rank_products(data.product_name, all_products)
    if ranked:
        product = ranked[0][0]
    else:
        product = db.query(Product).filter(Product.name.ilike(f"%{data.product_name}%")).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product '{data.product_name}' not found")

    price_info = calculate_retail_price(
        wholesale_price=product.wholesale_price,
        quantity_in_package=product.quantity_in_package,
        profit_per_item=product.profit_per_item,
        profit_margin_percent=product.profit_margin_percent,
        retail_price=product.retail_price,
    )

    # Also compute new-style pricing
    full, _ = get_product_pricing(product)

    return PriceResponse(
        product_name=product.name,
        unit_wholesale_price=price_info["unit_wholesale_price"],
        profit_per_item=price_info.get("profit_per_item"),
        retail_price_per_unit=price_info["retail_price_per_unit"],
        total_price=price_info["retail_price_per_unit"] * data.quantity if data.quantity else price_info["retail_price_per_unit"],
        calculation_breakdown=price_info["calculation_breakdown"],
        is_calculated=price_info["is_calculated"],
        unit_cost_price=full["unit_cost_price"],
        wholesale_selling_price=full["wholesale_selling_price"],
        suggested_retail_price=full["suggested_retail_price"],
        actual_retail_price=full["actual_retail_price"],
        rounded_price=full["rounded_price"],
        rounding_strategy=product.rounding_strategy,
    )


@router.get("/batch")
def batch_pricing(product_ids: str = Query(..., description="Comma-separated product IDs"), db: Session = Depends(get_db)):
    ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
    products = db.query(Product).filter(Product.id.in_(ids)).all()
    results = []
    for p in products:
        info = calculate_retail_price(
            p.wholesale_price, p.quantity_in_package, p.profit_per_item, p.profit_margin_percent, p.retail_price
        )
        # Also get new pricing
        full, _ = get_product_pricing(p)
        results.append({
            "product_id": p.id,
            "product_name": p.name,
            "retail_price_per_unit": info["retail_price_per_unit"],
            "is_calculated": info["is_calculated"],
            "unit_cost_price": full["unit_cost_price"],
            "suggested_retail_price": full["suggested_retail_price"],
            "rounded_price": full["rounded_price"],
            "effective_retail_price": full["effective_retail_price"],
            "wholesale_selling_price": full["wholesale_selling_price"],
            "profit_per_unit": full["profit_per_unit"],
            "profit_per_package": full["profit_per_package"],
            "margin_warning": full["margin_warning"],
            "price_source": full["price_source"],
        })
    return {"products": results}


# ============================================================
# NEW ENDPOINTS
# ============================================================

@router.post("/suggest", response_model=SuggestPriceResponse)
def suggest_price(data: SuggestPriceRequest, db: Session = Depends(get_db)):
    """Suggest a retail price for a product with given profit margin and rounding."""
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    pkg_cost = product.package_cost_price if product.package_cost_price is not None else product.wholesale_price
    pkg_qty = product.package_quantity if product.package_quantity is not None else product.quantity_in_package

    unit_cost = calculate_unit_cost(pkg_cost, pkg_qty)

    margin = data.profit_margin_per_unit if data.profit_margin_per_unit is not None else (
        product.profit_margin_per_unit or product.profit_per_item or 10
    )

    result = suggest_retail_price(unit_cost, margin, data.rounding_strategy or "none")

    # Get wholesale selling price
    wholesale = product.wholesale_selling_price

    return SuggestPriceResponse(
        product_id=product.id,
        product_name=product.name,
        package_cost_price=pkg_cost,
        package_quantity=pkg_qty,
        unit_cost_price=result["unit_cost_price"],
        profit_margin_per_unit=result["profit_margin_per_unit"],
        suggested_retail_price=result["suggested_retail_price"],
        rounded_price=result["rounded_price"],
        actual_retail_price=product.actual_retail_price or product.retail_price,
        wholesale_selling_price=wholesale,
        rounding_strategy=result["rounding_strategy"],
    )


@router.get("/product/{product_id}")
def get_product_pricing_endpoint(product_id: int, db: Session = Depends(get_db)):
    """Get full pricing details for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    pricing, changed = get_product_pricing(product)
    if changed:
        db.commit()

    return pricing


@router.post("/round", response_model=RoundPriceResponse)
def round_price(data: RoundPriceRequest):
    """Round a price using the specified strategy."""
    valid_strategies = ["none", "nearest_5", "nearest_10"]
    if data.strategy not in valid_strategies:
        raise HTTPException(status_code=400, detail=f"Invalid strategy. Choose from: {valid_strategies}")

    rounded = apply_rounding(data.price, data.strategy)

    return RoundPriceResponse(
        original_price=data.price,
        rounded_price=rounded,
        strategy=data.strategy,
    )


@router.post("/calculate-full")
def calculate_full_pricing(data: dict, db: Session = Depends(get_db)):
    """Calculate complete pricing from raw inputs (used by frontend for real-time calc)."""
    pkg_cost = data.get("package_cost_price", 0)
    pkg_qty = data.get("package_quantity", 1)
    profit = data.get("profit_margin_per_unit")
    wholesale = data.get("wholesale_selling_price")
    rounding = data.get("rounding_strategy", "none")

    if pkg_cost <= 0 or pkg_qty <= 0:
        raise HTTPException(status_code=400, detail="Package cost and quantity must be positive")

    unit_cost = calculate_unit_cost(pkg_cost, pkg_qty)

    result = {
        "unit_cost_price": unit_cost,
        "suggested_retail_price": None,
        "rounded_price": None,
        "wholesale_selling_price": wholesale,
    }

    if profit is not None and profit > 0:
        suggested = round(unit_cost + profit, 2)
        result["suggested_retail_price"] = suggested
        result["rounded_price"] = apply_rounding(suggested, rounding)
        result["profit_per_unit"] = profit
        result["profit_per_package"] = round(profit * pkg_qty, 2)

    return result
