from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Product, Inventory, StockTransaction, ChatHistory, Sale, SaleItem, RequestedItem
from ..services.pricing import get_product_pricing

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard(days: int = 30, db: Session = Depends(get_db)):
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    total_inactive = db.query(func.count(Product.id)).filter(Product.is_active == False).scalar() or 0

    low_stock_count = 0
    total_stock_value = 0.0
    daily_profit = 0.0

    active_product_ids = [
        row[0] for row in db.query(Product.id).filter(Product.is_active == True).all()
    ]

    if active_product_ids:
        inventories = (
            db.query(Inventory)
            .filter(Inventory.product_id.in_(active_product_ids))
            .all()
        )

        for inv in inventories:
            product = (
                db.query(Product)
                .filter(Product.id == inv.product_id, Product.is_active == True)
                .first()
            )
            if not product:
                continue
            if inv.low_stock_threshold and inv.quantity_available <= inv.low_stock_threshold:
                low_stock_count += 1
            total_stock_value += inv.quantity_available * product.wholesale_price

            full_pricing, _ = get_product_pricing(product)
            profit_per_unit = full_pricing.get("profit_per_unit")
            if profit_per_unit is not None:
                daily_profit += profit_per_unit * inv.quantity_available
    else:
        inventories = []

    recent_transactions = (
        db.query(StockTransaction)
        .order_by(StockTransaction.created_at.desc())
        .limit(10)
        .all()
    )

    recent_chats = (
        db.query(ChatHistory)
        .order_by(ChatHistory.created_at.desc())
        .limit(5)
        .all()
    )

    category_count = (
        db.query(Product.category, func.count(Product.id))
        .filter(Product.is_active == True, Product.category.isnot(None))
        .group_by(Product.category)
        .all()
    )

    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_stock_transactions = (
        db.query(func.count(StockTransaction.id))
        .filter(StockTransaction.created_at >= today_start)
        .scalar()
        or 0
    )

    today_sales = db.query(Sale).filter(
        Sale.sale_date >= today_start,
        Sale.sale_date < today_start + timedelta(days=1),
    ).all()

    today_sales_total = round(sum(s.total_amount for s in today_sales), 2)
    today_sales_count = len(today_sales)

    today_sales_profit = 0.0
    for sale in today_sales:
        items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        for item in items:
            if item.product_id:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    fp, _ = get_product_pricing(product)
                    unit_cost = fp.get("unit_cost_price") or 0
                    today_sales_profit += (item.selling_price - unit_cost) * item.quantity

    most_requested = (
        db.query(RequestedItem)
        .order_by(RequestedItem.request_count.desc())
        .limit(5)
        .all()
    )

    return {
        "total_products": total_products,
        "total_inactive": total_inactive,
        "low_stock_count": low_stock_count,
        "total_stock_value": round(total_stock_value, 2),
        "daily_profit": round(daily_profit, 2),
        "monthly_profit": round(daily_profit * 30, 2),
        "today_transactions": today_stock_transactions,
        "today_sales_total": today_sales_total,
        "today_sales_count": today_sales_count,
        "today_sales_profit": round(today_sales_profit, 2),
        "categories": [{"name": c, "count": cnt} for c, cnt in category_count],
        "recent_transactions": [
            {
                "id": t.id,
                "product_id": t.product_id,
                "type": t.transaction_type,
                "quantity": t.quantity,
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent_transactions
        ],
        "recent_chats": [
            {
                "id": c.id,
                "query": c.user_query[:100],
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent_chats
        ],
        "most_requested_items": [
            {
                "id": r.id,
                "product_name": r.product_name,
                "request_count": r.request_count,
                "last_requested_at": r.last_requested_at.isoformat() if r.last_requested_at else None,
            }
            for r in most_requested
        ],
    }
