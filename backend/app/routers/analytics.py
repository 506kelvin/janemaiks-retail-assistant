from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Product, Inventory, StockTransaction, ChatHistory
from ..services.pricing import get_product_pricing

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    total_inactive = db.query(func.count(Product.id)).filter(Product.is_active == False).scalar() or 0

    low_stock_count = 0
    total_stock_value = 0.0
    daily_profit = 0.0

    # Only include inventory for ACTIVE products — filters out soft-deleted products
    active_product_ids = [
        row[0] for row in db.query(Product.id).filter(Product.is_active == True).all()
    ]

    print(f"[JaneMaiks Analytics] Products (active): {total_products}, (inactive): {total_inactive}")

    if active_product_ids:
        inventories = (
            db.query(Inventory)
            .filter(Inventory.product_id.in_(active_product_ids))
            .all()
        )
        print(f"[JaneMaiks Analytics] Inventory rows for active products: {len(inventories)}")

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

            # Compute actual profit from product pricing
            full_pricing, _ = get_product_pricing(product)
            profit_per_unit = full_pricing.get("profit_per_unit")
            if profit_per_unit is not None:
                daily_profit += profit_per_unit * inv.quantity_available
    else:
        inventories = []
        print(f"[JaneMaiks Analytics] No active products found — returning zeros")

    print(f"[JaneMaiks Analytics] Computed stock value: {total_stock_value}")
    print(f"[JaneMaiks Analytics] Computed daily profit: {daily_profit}")
    print(f"[JaneMaiks Analytics] Low stock count: {low_stock_count}")

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
    today_transactions = (
        db.query(func.count(StockTransaction.id))
        .filter(StockTransaction.created_at >= today_start)
        .scalar()
        or 0
    )

    return {
        "total_products": total_products,
        "total_inactive": total_inactive,
        "low_stock_count": low_stock_count,
        "total_stock_value": round(total_stock_value, 2),
        "daily_profit": round(daily_profit, 2),
        "monthly_profit": round(daily_profit * 30, 2),
        "today_transactions": today_transactions,
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
    }
