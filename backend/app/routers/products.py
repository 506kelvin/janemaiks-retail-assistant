from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
from ..services.rag import rag_service
from ..services.pricing import calculate_unit_cost, compute_full_pricing

router = APIRouter(prefix="/api/products", tags=["Products"])


def _sync_pricing_fields(product: Product):
    """Auto-calculate and sync pricing fields for a product."""
    pkg_cost = product.package_cost_price if product.package_cost_price is not None else product.wholesale_price
    pkg_qty = product.package_quantity if product.package_quantity is not None else product.quantity_in_package
    profit = product.profit_margin_per_unit if product.profit_margin_per_unit is not None else product.profit_per_item
    actual_retail = product.actual_retail_price if product.actual_retail_price is not None else product.retail_price

    product.unit_cost_price = calculate_unit_cost(pkg_cost, pkg_qty)

    # Sync legacy and new fields
    product.package_cost_price = pkg_cost
    product.package_quantity = pkg_qty
    product.profit_margin_per_unit = profit
    product.actual_retail_price = actual_retail

    # Calculate suggested retail
    if profit is not None:
        pricing = compute_full_pricing(
            package_cost_price=pkg_cost,
            package_quantity=pkg_qty,
            profit_margin_per_unit=profit,
            wholesale_selling_price=product.wholesale_selling_price,
            actual_retail_price=actual_retail,
            rounding_strategy=product.rounding_strategy or "none",
            allow_manual_override=product.allow_manual_override or False,
        )
        product.suggested_retail_price = pricing["suggested_retail_price"]

    # Sync legacy retail_price with actual_retail_price if manual override is set
    if product.allow_manual_override and product.actual_retail_price is not None:
        product.retail_price = product.actual_retail_price


@router.get("/", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)
    if search:
        term = f"%{search}%"
        q = q.filter(Product.name.ilike(term))
    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))
    if supplier:
        q = q.filter(Product.supplier.ilike(f"%{supplier}%"))
    return q.offset(skip).limit(limit).all()


@router.get("/all", response_model=List[ProductResponse])
def list_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product_data = data.model_dump()

    # Map new fields to legacy if not provided
    if product_data.get("package_cost_price") is None:
        product_data["package_cost_price"] = product_data["wholesale_price"]
    if product_data.get("package_quantity") is None:
        product_data["package_quantity"] = product_data["quantity_in_package"]
    if product_data.get("package_unit_type") is None:
        product_data["package_unit_type"] = product_data.get("unit_type")
    if product_data.get("profit_margin_per_unit") is None and product_data.get("profit_per_item") is not None:
        product_data["profit_margin_per_unit"] = product_data["profit_per_item"]
    if product_data.get("actual_retail_price") is None and product_data.get("retail_price") is not None:
        product_data["actual_retail_price"] = product_data["retail_price"]

    product = Product(**product_data)
    db.add(product)
    db.flush()

    # Auto-calculate pricing fields
    _sync_pricing_fields(product)

    db.commit()
    db.refresh(product)
    rag_service.index_product(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    exclude_unset = data.model_dump(exclude_unset=True)

    # Map legacy ↔ new fields
    if "wholesale_price" in exclude_unset and "package_cost_price" not in exclude_unset:
        exclude_unset["package_cost_price"] = exclude_unset["wholesale_price"]
    if "package_cost_price" in exclude_unset and "wholesale_price" not in exclude_unset:
        exclude_unset["wholesale_price"] = exclude_unset["package_cost_price"]
    if "quantity_in_package" in exclude_unset and "package_quantity" not in exclude_unset:
        exclude_unset["package_quantity"] = exclude_unset["quantity_in_package"]
    if "package_quantity" in exclude_unset and "quantity_in_package" not in exclude_unset:
        exclude_unset["quantity_in_package"] = exclude_unset["package_quantity"]
    if "retail_price" in exclude_unset and "actual_retail_price" not in exclude_unset:
        exclude_unset["actual_retail_price"] = exclude_unset["retail_price"]
    if "actual_retail_price" in exclude_unset and "retail_price" not in exclude_unset:
        exclude_unset["retail_price"] = exclude_unset["actual_retail_price"]
    if "profit_per_item" in exclude_unset and "profit_margin_per_unit" not in exclude_unset:
        exclude_unset["profit_margin_per_unit"] = exclude_unset["profit_per_item"]
    if "profit_margin_per_unit" in exclude_unset and "profit_per_item" not in exclude_unset:
        exclude_unset["profit_per_item"] = exclude_unset["profit_margin_per_unit"]

    for key, val in exclude_unset.items():
        setattr(product, key, val)

    db.flush()

    # Auto-calculate pricing fields
    _sync_pricing_fields(product)

    db.commit()
    db.refresh(product)
    rag_service.index_product(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    rag_service.remove_product(product_id)


@router.get("/categories/list", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    results = (
        db.query(Product.category)
        .filter(Product.is_active == True, Product.category.isnot(None))
        .distinct()
        .all()
    )
    return sorted(set(r[0] for r in results if r[0]))


@router.get("/suppliers/list", response_model=List[str])
def list_suppliers(db: Session = Depends(get_db)):
    results = (
        db.query(Product.supplier)
        .filter(Product.is_active == True, Product.supplier.isnot(None))
        .distinct()
        .all()
    )
    return sorted(set(r[0] for r in results if r[0]))
