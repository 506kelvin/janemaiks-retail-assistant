from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional

from ..database import get_db
from ..models import Sale, SaleItem, Product, Inventory, StockTransaction
from ..services.sales_query import (
    parse_date_reference,
    get_sales_by_date,
    get_sales_summary_range,
    get_top_selling_products,
    get_sales_profit,
    format_sales_response,
    format_sales_range_response,
    format_top_products_response,
)

router = APIRouter(prefix="/api/sales", tags=["Sales"])


class SaleItemCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity: float = 1
    selling_price: float


class SaleCreate(BaseModel):
    items: List[SaleItemCreate]


class SaleItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    quantity: float
    selling_price: float
    subtotal: float

    class Config:
        from_attributes = True


class SaleResponse(BaseModel):
    id: int
    sale_date: str
    total_amount: float
    created_at: str
    items: List[SaleItemResponse] = []

    class Config:
        from_attributes = True


class TodaySummary(BaseModel):
    total_sales: float
    transaction_count: int
    item_count: int


@router.post("/")
def create_sale(payload: SaleCreate, deduct_inventory: bool = True, db: Session = Depends(get_db)):
    sale_items = []
    total = 0.0

    for item in payload.items:
        subtotal = round(item.quantity * item.selling_price, 2)
        total += subtotal
        sale_items.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "selling_price": item.selling_price,
            "subtotal": subtotal,
        })

        if deduct_inventory and item.product_id:
            inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
            if inv:
                inv.quantity_available -= item.quantity
                txn = StockTransaction(
                    product_id=item.product_id,
                    transaction_type="deduct",
                    quantity=item.quantity,
                    notes=f"Sale: {item.product_name} x{item.quantity}",
                )
                db.add(txn)

    sale = Sale(total_amount=round(total, 2))
    db.add(sale)
    db.flush()

    for si in sale_items:
        db.add(SaleItem(sale_id=sale.id, **si))

    db.commit()
    db.refresh(sale)

    items_resp = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
    return {
        "id": sale.id,
        "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
        "total_amount": sale.total_amount,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "selling_price": i.selling_price,
                "subtotal": i.subtotal,
            }
            for i in items_resp
        ],
    }


@router.get("/today")
def get_today_summary(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    sales = db.query(Sale).filter(
        Sale.sale_date >= today_start,
        Sale.sale_date < today_end,
    ).all()

    total_sales = sum(s.total_amount for s in sales)
    transaction_count = len(sales)
    item_count = db.query(func.count(SaleItem.id)).join(Sale).filter(
        Sale.sale_date >= today_start,
        Sale.sale_date < today_end,
    ).scalar() or 0

    return {
        "total_sales": round(total_sales, 2),
        "transaction_count": transaction_count,
        "item_count": item_count,
        "sales": [
            {
                "id": s.id,
                "sale_date": s.sale_date.isoformat() if s.sale_date else None,
                "total_amount": s.total_amount,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sales
        ],
    }


@router.get("/history")
def get_sales_history(page: int = 1, per_page: int = 20, db: Session = Depends(get_db)):
    total = db.query(func.count(Sale.id)).scalar() or 0
    sales = (
        db.query(Sale)
        .order_by(Sale.sale_date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    result = []
    for s in sales:
        items = db.query(SaleItem).filter(SaleItem.sale_id == s.id).all()
        result.append({
            "id": s.id,
            "sale_date": s.sale_date.isoformat() if s.sale_date else None,
            "total_amount": s.total_amount,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "items": [
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "quantity": i.quantity,
                    "selling_price": i.selling_price,
                    "subtotal": i.subtotal,
                }
                for i in items
            ],
        })

    return {
        "sales": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total else 1,
    }


@router.get("/query")
def query_sales(q: str = Query("today"), db: Session = Depends(get_db)):
    """Natural-language sales query endpoint."""
    ref = parse_date_reference(q)
    if not ref:
        return {"response": "I couldn't understand the date. Try 'today', 'yesterday', or 'this week'.", "data": None}

    start_date = ref["start_date"]
    end_date = ref["end_date"]
    label = ref["label"]

    q_lower = q.lower()

    if any(w in q_lower for w in ["best selling", "top selling", "sold most", "most popular"]):
        products = get_top_selling_products(start_date, end_date, db, limit=5)
        return {"response": format_top_products_response(products, label), "data": products}

    if "profit" in q_lower:
        profit_data = get_sales_profit(start_date, db)
        return {"response": format_sales_profit_response(profit_data, label), "data": profit_data}

    if start_date == end_date:
        sales_data = get_sales_by_date(start_date, db)
        return {"response": format_sales_response(sales_data), "data": sales_data}

    range_data = get_sales_summary_range(start_date, end_date, db)
    return {"response": format_sales_range_response(range_data), "data": range_data}


@router.get("/range")
def sales_range(
    start: str = Query(...),
    end: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get sales summary for a date range. Dates in YYYY-MM-DD format."""
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    range_data = get_sales_summary_range(start_date, end_date, db)
    return range_data


@router.get("/top")
def top_selling(
    days: int = Query(1, ge=1, le=365),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get top selling products for the last N days."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    products = get_top_selling_products(start_date, end_date, db, limit=limit)
    return {"products": products, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}


@router.get("/{sale_id}")
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
    return {
        "id": sale.id,
        "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
        "total_amount": sale.total_amount,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "selling_price": i.selling_price,
                "subtotal": i.subtotal,
            }
            for i in items
        ],
    }


@router.delete("/{sale_id}")
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
    for item in items:
        if item.product_id:
            inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
            if inv:
                inv.quantity_available += item.quantity
        db.delete(item)

    db.delete(sale)
    db.commit()
    return {"detail": "Sale cancelled successfully", "id": sale_id}
