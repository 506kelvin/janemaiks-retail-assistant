import re
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from ..models import Sale, SaleItem, Product


# ============================================================
# NATURAL LANGUAGE DATE PARSING
# ============================================================

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _parse_named_month(d: date, m: re.Match) -> Tuple[date, date]:
    month_str = m.group(0).split()[0].lower()
    day = int(m.group(1))
    month = MONTH_MAP.get(month_str, d.month)
    year = d.year
    try:
        dt = date(year, month, day)
        return (dt, dt)
    except ValueError:
        return (d, d)


def _parse_named_month_rev(d: date, m: re.Match) -> Tuple[date, date]:
    day = int(m.group(1))
    month_str = m.group(2).lower()
    month = MONTH_MAP.get(month_str, d.month)
    year = d.year
    try:
        dt = date(year, month, day)
        return (dt, dt)
    except ValueError:
        return (d, d)


def _parse_short_date(d: date, m: re.Match) -> Optional[Tuple[date, date]]:
    a, b = int(m.group(1)), int(m.group(2))
    if a > 12:
        day, month = a, b
    else:
        month, day = a, b
    year = d.year
    try:
        dt = date(year, month, day)
        return (dt, dt)
    except ValueError:
        return None


DATE_PATTERNS = [
    (r"\byesterday\b", lambda d: (d - timedelta(days=1), d - timedelta(days=1))),
    (r"\bday before yesterday\b", lambda d: (d - timedelta(days=2), d - timedelta(days=2))),
    (r"\bthis week\b", lambda d: (d - timedelta(days=d.weekday()), d)),
    (r"\blast week\b", lambda d: (d - timedelta(days=d.weekday() + 7), d - timedelta(days=d.weekday() + 1))),
    (r"\bthis month\b", lambda d: (d.replace(day=1), d)),
    (r"\blast month\b", lambda d: ((d.replace(day=1) - timedelta(days=1)).replace(day=1), d.replace(day=1) - timedelta(days=1))),
    (r"\b(?:last\s+)?(\d+)\s+(?:days|day)\b", lambda d, m: (d - timedelta(days=int(m.group(1)) - 1), d)),
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", lambda d, m: (date(int(m.group(1)), int(m.group(2)), int(m.group(3))), date(int(m.group(1)), int(m.group(2)), int(m.group(3))))),
    (r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b", _parse_named_month),
    (r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", _parse_named_month_rev),
    (r"\b(\d{1,2})[\/-](\d{1,2})\b", _parse_short_date),
]


def parse_date_reference(text: str) -> Optional[dict]:
    """
    Parse a natural language date reference from text.
    Returns dict with:
      - start_date: date
      - end_date: date
      - label: str (human-readable label like "today", "yesterday", "May 20")
    Returns None if no date reference found.
    """
    today = datetime.utcnow().date()
    text_lower = text.lower().strip()

    date_keywords = ["yesterday", "week", "month", "january", "february", "march", "april", "may", "june",
                     "july", "august", "september", "october", "november", "december"]
    has_digit = any(ch.isdigit() for ch in text_lower)
    has_date_word = any(kw in text_lower for kw in date_keywords)

    if re.search(r"\btoday\b", text_lower):
        return {"start_date": today, "end_date": today, "label": "today"}

    if not has_digit and not has_date_word:
        return None

    for pattern, handler in DATE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            try:
                result = handler(today, m)
                if result:
                    start_date, end_date = result
                    label = text_lower[m.start():m.end()].strip()
                    return {"start_date": start_date, "end_date": end_date, "label": label}
            except Exception:
                continue

    # If no match, check if query looks like a sales query at all
    if _is_sales_query(text):
        return {"start_date": today, "end_date": today, "label": "today"}

    return None


def _is_sales_query(text: str) -> bool:
    """Check if text is a sales-related query."""
    sales_keywords = [
        "sale", "sell", "sold", "revenue", "income", "money came in",
        "transaction", "receipt", "total", "amount",
    ]
    t = text.lower()
    return any(kw in t for kw in sales_keywords)


# ============================================================
# HELPER: normalize to UTC day boundaries
# ============================================================

def _day_range(target_date: date) -> Tuple[datetime, datetime]:
    """Get UTC datetime range for a given date."""
    start = datetime(target_date.year, target_date.month, target_date.day)
    end = start + timedelta(days=1)
    return start, end


# ============================================================
# SALES DATA RETRIEVAL
# ============================================================

def get_sales_by_date(target_date: date, db: Session) -> dict:
    """
    Get all sales for a specific date.
    Returns dict with items grouped by product_name.
    """
    start_dt, end_dt = _day_range(target_date)
    sales = db.query(Sale).filter(
        Sale.sale_date >= start_dt,
        Sale.sale_date < end_dt,
    ).order_by(Sale.sale_date.asc()).all()

    return _build_sales_response(sales, db, target_date)


def get_sales_range(start_date: date, end_date: date, db: Session) -> list:
    """
    Get sales summary for a range of dates.
    Returns a list of per-day dicts.
    """
    results = []
    current = start_date
    while current <= end_date:
        day_data = get_sales_by_date(current, db)
        if day_data["transaction_count"] > 0:
            results.append(day_data)
        current += timedelta(days=1)
    return results


def get_sales_summary_range(start_date: date, end_date: date, db: Session) -> dict:
    """
    Get a single aggregated summary across a date range.
    """
    results = get_sales_range(start_date, end_date, db)

    total_revenue = sum(r["total_revenue"] for r in results)
    total_transactions = sum(r["transaction_count"] for r in results)
    total_items = sum(r["total_items"] for r in results)

    all_items = {}
    for r in results:
        for item in r["items"]:
            name = item["product_name"]
            if name in all_items:
                all_items[name]["quantity"] += item["quantity"]
                all_items[name]["total"] += item["total"]
                all_items[name]["transactions"] += item["transactions"]
            else:
                all_items[name] = {
                    "product_name": name,
                    "quantity": item["quantity"],
                    "selling_price": item["selling_price"],
                    "total": item["total"],
                    "transactions": item["transactions"],
                }

    sorted_items = sorted(all_items.values(), key=lambda x: x["quantity"], reverse=True)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": round(total_revenue, 2),
        "transaction_count": total_transactions,
        "total_items": total_items,
        "items": sorted_items,
        "per_day": results,
    }


def get_top_selling_products(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = None,
    limit: int = 5,
) -> list:
    """Get top selling products by total quantity sold."""
    q = (
        db.query(
            SaleItem.product_name,
            func.sum(SaleItem.quantity).label("total_qty"),
            func.sum(SaleItem.subtotal).label("total_revenue"),
            func.count(func.distinct(SaleItem.sale_id)).label("transaction_count"),
        )
        .join(Sale)
    )

    if start_date and end_date:
        start_dt, end_dt = _day_range(start_date), _day_range(end_date)
        q = q.filter(Sale.sale_date >= start_dt[0], Sale.sale_date < end_dt[1])

    q = q.group_by(SaleItem.product_name).order_by(text("total_qty DESC")).limit(limit)
    return [
        {
            "product_name": row[0],
            "total_quantity": float(row[1]),
            "total_revenue": round(float(row[2]), 2),
            "transaction_count": int(row[3]),
        }
        for row in q.all()
    ]


def get_sales_profit(target_date: date, db: Session) -> dict:
    """Estimate profit from sales on a given date."""
    start_dt, end_dt = _day_range(target_date)
    items = (
        db.query(SaleItem)
        .join(Sale)
        .filter(Sale.sale_date >= start_dt, Sale.sale_date < end_dt)
        .all()
    )

    total_cost = 0.0
    total_revenue = 0.0
    for item in items:
        total_revenue += item.subtotal
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                unit_cost = product.unit_cost_price or (product.wholesale_price / product.quantity_in_package if product.quantity_in_package else 0)
                total_cost += unit_cost * item.quantity

    return {
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "estimated_profit": round(total_revenue - total_cost, 2),
    }


# ============================================================
# RESPONSE BUILDING
# ============================================================

def _build_sales_response(sales: list, db: Session, target_date: date) -> dict:
    """Build a structured sales response dict from Sale objects."""
    total_revenue = 0.0
    total_items = 0
    items_agg = {}

    for sale in sales:
        total_revenue += sale.total_amount
        sale_items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        total_items += len(sale_items)

        for si in sale_items:
            name = si.product_name
            if name in items_agg:
                items_agg[name]["quantity"] += si.quantity
                items_agg[name]["total"] += si.subtotal
                items_agg[name]["transactions"] += 1
            else:
                items_agg[name] = {
                    "product_name": name,
                    "quantity": si.quantity,
                    "selling_price": si.selling_price,
                    "total": si.subtotal,
                    "transactions": 1,
                }

    sorted_items = sorted(items_agg.values(), key=lambda x: x["quantity"], reverse=True)

    return {
        "date": target_date.isoformat(),
        "date_label": _format_date_label(target_date),
        "total_revenue": round(total_revenue, 2),
        "transaction_count": len(sales),
        "total_items": total_items,
        "items": sorted_items,
    }


def _format_date_label(d: date) -> str:
    """Format a date as a human-readable label."""
    today = datetime.utcnow().date()
    if d == today:
        return "today"
    if d == today - timedelta(days=1):
        return "yesterday"
    if d == today - timedelta(days=2):
        return "the day before yesterday"
    return d.strftime("%A, %B %d")


# ============================================================
# FORMATTED RESPONSE GENERATION
# ============================================================

def format_sales_response(sales_data: dict) -> str:
    """Format a single-day sales data dict into a chatbot-friendly string."""
    if sales_data["transaction_count"] == 0:
        label = sales_data.get("date_label") or sales_data["date"]
        return f"No sales recorded for **{label}** at JaneMaiks."

    label = sales_data.get("date_label") or sales_data["date"]
    lines = [f"**Sales Summary — {label.capitalize()}**", ""]

    for item in sales_data["items"]:
        qty = item["quantity"]
        price = item["selling_price"]
        total = item["total"]
        lines.append(f"• **{item['product_name']}** — {qty} × KSh {price} = **KSh {total}**")

    lines.append("")
    lines.append(f"📊 **Transactions:** {sales_data['transaction_count']}")
    lines.append(f"💰 **Total Revenue:** KSh {sales_data['total_revenue']:,.2f}")
    lines.append(f"📦 **Items Sold:** {sales_data['total_items']}")

    return "\n".join(lines)


def format_sales_range_response(range_data: dict) -> str:
    """Format a multi-day range sales summary."""
    if range_data["transaction_count"] == 0:
        return f"No sales recorded in this period at JaneMaiks."

    start = range_data["start_date"]
    end = range_data["end_date"]
    lines = [f"**Sales Summary — {start} to {end}**", ""]

    for item in range_data["items"]:
        qty = item["quantity"]
        total = item["total"]
        lines.append(f"• **{item['product_name']}** — {qty} sold, **KSh {total}**")

    lines.append("")
    lines.append(f"📊 **Total Transactions:** {range_data['transaction_count']}")
    lines.append(f"💰 **Total Revenue:** KSh {range_data['total_revenue']:,.2f}")
    lines.append(f"📦 **Total Items Sold:** {range_data['total_items']}")

    if len(range_data.get("per_day", [])) > 1:
        lines.append("")
        lines.append("**Per Day Breakdown:**")
        for day in range_data["per_day"]:
            d = day.get("date_label") or day["date"]
            lines.append(f"  • {d.capitalize()}: KSh {day['total_revenue']:,.2f} ({day['transaction_count']} txns)")

    return "\n".join(lines)


def format_sales_profit_response(profit_data: dict, label: str) -> str:
    """Format profit data into a response string."""
    if profit_data["total_revenue"] == 0:
        return f"No sales recorded for **{label}**, so no profit data available."
    return (
        f"**Profit Analysis — {label.capitalize()}**\n\n"
        f"💰 **Revenue:** KSh {profit_data['total_revenue']:,.2f}\n"
        f"📊 **Cost:** KSh {profit_data['total_cost']:,.2f}\n"
        f"📈 **Estimated Profit:** KSh {profit_data['estimated_profit']:,.2f}"
    )

def format_top_products_response(products: list, label: str) -> str:
    """Format top-selling products into a response."""
    if not products:
        return f"No products sold {label}."

    lines = [f"**Best Selling Items — {label.capitalize()}**", ""]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. **{p['product_name']}** — {p['total_quantity']} sold, KSh {p['total_revenue']:,.2f}")

    return "\n".join(lines)
