import json
import re
import uuid
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Product, Inventory, ChatHistory
from .pricing import calculate_retail_price, get_product_pricing
from .rag import rag_service
from .search import (
    rank_products, detect_ambiguity,
    build_clarification_response, build_no_match_response,
    score_product,
)


# ============================================================
# INTENT DETECTION
# ============================================================

SWAHILI_PRICE_KEYWORDS = ["bei gani", "shilingi ngapi", "ghali", "bei", "pesa"]
SWAHILI_QUANTITY_KEYWORDS = ["ngapi", "zimebaki", "imesalia", "wapi", "iko"]

WHOLESALE_KEYWORDS = ["wholesale", "dozen", "package price", "bulk", "jumla", "kwa jumla"]
UNIT_COST_KEYWORDS = ["unit cost", "cost price", "how much we buy", "tunanunua", "bei ya kununua"]
PROFIT_KEYWORDS = ["profit", "faida", "margin", "how much profit"]
PACKAGE_KEYWORDS = ["package", "dozen", "carton", "bundle", "kifurushi"]
SUGGEST_KEYWORDS = ["suggest", "recommend", "propose", "pendekeza", "suggest selling"]


def _make_pattern(words: list[str]) -> re.Pattern:
    escaped = [re.escape(w) for w in words]
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)

PAT_GREETING = _make_pattern(["hello", "hi", "hey", "habari", "jambo", "mambo"])
PAT_HELP = _make_pattern(["help", "msaada", "saidia", "unaweza"])
PAT_CALCULATOR = _make_pattern(["calculator", "calculate", "hesabu"])
PAT_PRICE = _make_pattern(["price", "how much", "cost", "bei", "ghali", "pesa", "shilingi"])
PAT_WHOLESALE = _make_pattern(WHOLESALE_KEYWORDS)
PAT_UNIT_COST = _make_pattern(UNIT_COST_KEYWORDS)
PAT_PROFIT = _make_pattern(PROFIT_KEYWORDS)
PAT_PACKAGE = _make_pattern(PACKAGE_KEYWORDS)
PAT_STOCK = _make_pattern(["remaining", "stock", "available", "left", "zimebaki", "imesalia"])
PAT_SUPPLIER = _make_pattern(["supplier", "supplier", "from", "came from", "kutoka"])
PAT_ADD_PRODUCT = _make_pattern(["add", "new product", "register", "ongeza"])
PAT_SUGGEST = _make_pattern(SUGGEST_KEYWORDS)
PAT_SWAHLI = _make_pattern(SWAHILI_PRICE_KEYWORDS + SWAHILI_QUANTITY_KEYWORDS)


def _is_swahili(query: str) -> bool:
    return bool(PAT_SWAHLI.search(query))


def _detect_intent(query: str) -> str:
    q = query.lower()
    if PAT_PRICE.search(q):
        if PAT_WHOLESALE.search(q):
            return "wholesale_query"
        if PAT_UNIT_COST.search(q):
            return "unit_cost_query"
        return "price_query"
    if PAT_PROFIT.search(q):
        return "profit_query"
    if PAT_PACKAGE.search(q):
        if PAT_PRICE.search(q):
            return "package_price_query"
        return "package_query"
    if PAT_STOCK.search(q):
        return "stock_query"
    if PAT_SUPPLIER.search(q):
        return "supplier_query"
    if PAT_ADD_PRODUCT.search(q):
        return "add_product"
    if PAT_SUGGEST.search(q):
        return "suggest_price"
    if PAT_GREETING.search(q):
        return "greeting"
    if PAT_HELP.search(q):
        return "help"
    if PAT_CALCULATOR.search(q):
        return "calculator"
    return "general_query"


# ============================================================
# PRODUCT NAME EXTRACTION
# ============================================================

STOP_WORDS = [
    "how much is", "what is the price of", "price of", "cost of",
    "how many", "remaining", "left in stock", "stock of",
    "from supplier", "supplier", "came from", "tell me about",
    "what is", "show me", "find", "search", "i need",
    "what products came from", "products from", "products supplied by",
    "show products from", "list products from",
    "bei gani", "shilingi ngapi", "ghali", "bei ya",
    "ngapi", "zimebaki", "imesalia", "wapi", "iko wapi",
    "please", "the", "a", "an",
    "wholesale price of", "wholesale price for",
    "unit cost of", "cost price of",
    "how much profit on", "profit on", "profit per",
    "package price of", "how much do we buy",
    "suggest selling price for", "suggest price for",
]


def _extract_product_name(query: str) -> str:
    q = query.lower().strip().rstrip("?.,!")
    for phrase in sorted(STOP_WORDS, key=len, reverse=True):
        if q.startswith(phrase):
            q = q[len(phrase):].strip()
            break
    return q


# ============================================================
# RESPONSE FORMATTING
# ============================================================

def _format_pricing_breakdown(product, full_pricing: dict, is_swahili: bool = False) -> str:
    pkg_cost = full_pricing["package_cost_price"]
    pkg_qty = full_pricing["package_quantity"]
    unit_cost = full_pricing["unit_cost_price"]
    suggested = full_pricing["suggested_retail_price"]
    rounded = full_pricing["rounded_price"]
    actual = full_pricing["actual_retail_price"]
    effective = full_pricing["effective_retail_price"]
    wholesale = full_pricing["wholesale_selling_price"]
    profit = full_pricing["profit_per_unit"]
    profit_pkg = full_pricing["profit_per_package"]
    source = full_pricing["price_source"]
    rounding = full_pricing["rounding_strategy"]

    pkg_unit = full_pricing.get("package_unit_type") or product.unit_type or "unit"
    pkg_label = "dozen" if pkg_qty == 12 else f"{pkg_qty} {pkg_unit}s"

    lines = [f"**{product.name}**"]
    lines.append("")

    lines.append(f"📦 **Bought:** KSh {pkg_cost} per {pkg_label}")
    lines.append(f"📊 **Unit Cost:** KSh {unit_cost}")

    if suggested is not None:
        lines.append(f"💡 **Suggested Retail:** KSh {suggested}")
        if rounding != "none" and rounded is not None and rounded != suggested:
            lines.append(f"🔄 **Rounded ({rounding}):** KSh {rounded}")

    if source == "manual" and actual is not None:
        lines.append(f"🏷️ **Actual Retail (Manual):** KSh {actual}")
    else:
        lines.append(f"🏷️ **Retail Price:** KSh {effective}")

    if wholesale is not None:
        lines.append(f"📦 **Wholesale Selling:** KSh {wholesale} per {pkg_label}")

    if profit is not None:
        lines.append(f"💰 **Profit/Unit:** KSh {profit}")
        if profit_pkg is not None:
            lines.append(f"💰 **Profit/{pkg_label}:** KSh {profit_pkg}")

    if full_pricing.get("margin_warning"):
        lines.append("")
        lines.append("⚠️ **Low margin!** Consider increasing your profit per unit.")

    return "\n".join(lines)


# ============================================================
# CLARIFICATION STATE MACHINE
# ============================================================

def _get_clarification_state(session_id: str, db: Session) -> Optional[dict]:
    """Retrieve the last clarification state for a session."""
    last = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id, ChatHistory.clarification_state.isnot(None))
        .order_by(ChatHistory.created_at.desc())
        .first()
    )
    if last and last.clarification_state:
        try:
            return json.loads(last.clarification_state)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _handle_clarification_response(
    query: str, state: dict, db: Session
) -> Tuple[Optional[Product], Optional[dict], str]:
    """
    If the user's query resolves a clarification (number, product name fragment),
    return the selected product and the original intent.
    """
    q = query.lower().strip()
    candidates = state.get("candidates", [])
    original_query = state.get("original_query", "")
    original_intent = state.get("intent", "general_query")
    is_swahili = state.get("is_swahili", False)

    if not candidates:
        return None, None, ""

    # Try numeric selection: "1", "first", "the first one"
    num_match = re.search(r"^\s*(\d+)\s*$", q)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(candidates):
            product = db.query(Product).filter(Product.id == candidates[idx]["id"]).first()
            if product:
                return product, {"intent": original_intent, "is_swahili": is_swahili}, original_query

    # Try word-based selection: "first", "second", "third"
    word_to_num = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
                   "ya kwanza": 0, "ya pili": 1, "ya tatu": 2}
    if q in word_to_num:
        idx = word_to_num[q]
        if 0 <= idx < len(candidates):
            product = db.query(Product).filter(Product.id == candidates[idx]["id"]).first()
            if product:
                return product, {"intent": original_intent, "is_swahili": is_swahili}, original_query

    # Try name matching: user types part of product name
    best_product = None
    best_score = 0
    for c in candidates:
        product = db.query(Product).filter(Product.id == c["id"]).first()
        if not product:
            continue
        score, _ = score_product(q, product)
        if score > best_score:
            best_score = score
            best_product = product

    if best_product and best_score >= 50:
        return best_product, {"intent": original_intent, "is_swahili": is_swahili}, original_query

    return None, None, ""


def _save_clarification_state(session_id: str, query: str, response: str, db: Session, state: dict):
    """Save chat with clarification state for future reference."""
    try:
        chat = ChatHistory(
            session_id=session_id,
            user_query=query,
            bot_response=response,
            clarification_state=json.dumps(state),
        )
        db.add(chat)
        db.commit()
    except Exception:
        db.rollback()


# ============================================================
# SEARCH & AMBIGUITY RESOLUTION
# ============================================================

def _smart_find_product(query: str, db: Session):
    """
    Enhanced product search with ambiguity detection.
    Returns (product, matches_list, is_ambiguous, ranked_list).
    """
    all_products = db.query(Product).filter(Product.is_active == True).all()
    if not all_products:
        return None, [], False, []

    ranked = rank_products(query, all_products)
    is_ambiguous, candidates = detect_ambiguity(ranked)

    if not ranked:
        return None, [], False, []

    if is_ambiguous:
        return None, candidates, True, ranked

    # Single best match
    top_product = candidates[0][0] if candidates else ranked[0][0]
    return top_product, [], False, ranked


# ============================================================
# PRICING & STOCK HANDLERS
# ============================================================

def _handle_price_query(product, query: str, is_swahili: bool) -> Tuple[str, bool, str]:
    qty_match = re.search(r"(\d+)\s*(units?|pieces?|items?|vipande)", query.lower())
    qty = int(qty_match.group(1)) if qty_match else 1

    price_info = calculate_retail_price(
        wholesale_price=product.wholesale_price,
        quantity_in_package=product.quantity_in_package,
        profit_per_item=product.profit_per_item,
        profit_margin_percent=product.profit_margin_percent,
        retail_price=product.retail_price,
    )
    full_pricing, _ = get_product_pricing(product)

    response = _format_pricing_breakdown(product, full_pricing, is_swahili)

    if qty > 1:
        total = price_info["retail_price_per_unit"] * qty
        response += f"\n\n**{qty} {product.unit_type or 'units'}**: KSh {total:.2f}"

    return response, price_info["is_calculated"], price_info["calculation_breakdown"]


def _handle_stock_query(product, is_swahili: bool, db: Session) -> str:
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    if inventory:
            status = "⚠️ LOW STOCK" if inventory.low_stock_threshold and inventory.quantity_available <= inventory.low_stock_threshold else "✅ In stock"
            if is_swahili:
                return f"**{product.name}** - JaneMaiks ina zimesalia: **{inventory.quantity_available}** {product.unit_type or 'vipande'}\nHali: {status}"
            return f"**{product.name}** - JaneMaiks currently has **{inventory.quantity_available}** {product.unit_type or 'units'} remaining\nThreshold: {inventory.low_stock_threshold or 'N/A'} {product.unit_type or 'units'}\nStatus: {status}"
    return f"**{product.name}**: No stock information recorded yet at JaneMaiks."


def _handle_wholesale_query(product, db: Session) -> str:
    full, _ = get_product_pricing(product)
    if full["wholesale_selling_price"] is not None:
        return (
            f"**{product.name}** - JaneMaiks Wholesale Price\n\n"
            f"📦 **Wholesale Selling Price:** KSh {full['wholesale_selling_price']} per {full['package_quantity']} {full['package_unit_type'] or 'units'}\n\n"
            f"📊 **Unit Cost:** KSh {full['unit_cost_price']}\n"
            f"📦 **Package Cost:** KSh {full['package_cost_price']} per {full['package_quantity']} units\n"
            f"💰 **Profit per Package:** KSh {(full['wholesale_selling_price'] - full['package_cost_price']):.2f}"
        )
    return (
        f"**{product.name}** - JaneMaiks Package Info\n\n"
        f"📦 **Package Cost:** KSh {full['package_cost_price']} per {full['package_quantity']} {full['package_unit_type'] or 'units'}\n"
        f"📊 **Unit Cost:** KSh {full['unit_cost_price']}\n\n"
        f"*No wholesale selling price has been set at JaneMaiks for this product yet. You can add one in the Products section.*"
    )


def _handle_unit_cost_query(product, db: Session) -> str:
    full, _ = get_product_pricing(product)
    return (
        f"**{product.name}** - JaneMaiks Cost Breakdown\n\n"
        f"📦 **Package Cost:** KSh {full['package_cost_price']} per {full['package_quantity']} {full['package_unit_type'] or 'units'}\n"
        f"📊 **Unit Cost Price:** KSh {full['unit_cost_price']}\n\n"
        f"At JaneMaiks, calculation: {full['package_cost_price']} ÷ {full['package_quantity']} = **KSh {full['unit_cost_price']}** per unit"
    )


def _handle_profit_query(product, db: Session) -> str:
    full, _ = get_product_pricing(product)
    if full["profit_per_unit"] is not None:
        pkg_unit = full.get("package_unit_type") or product.unit_type or "unit"
        resp = (
            f"**{product.name}** - Profit Analysis\n\n"
            f"💰 **Profit per Unit:** KSh {full['profit_per_unit']}\n"
            f"💰 **Profit per Package ({full['package_quantity']} {pkg_unit}s):** KSh {full['profit_per_package']}\n\n"
            f"📊 **Unit Cost:** KSh {full['unit_cost_price']}\n"
            f"🏷️ **Suggested Retail:** KSh {full['suggested_retail_price']}"
        )
        if full["actual_retail_price"] is not None:
            actual_profit = full["actual_retail_price"] - full["unit_cost_price"]
            resp += f"\n🏷️ **Actual Retail:** KSh {full['actual_retail_price']} (profit: KSh {actual_profit:.2f})"
        if full["margin_warning"]:
            resp += "\n\n⚠️ **Low margin!** Consider increasing your profit per unit."
        return resp
    return (
        f"**{product.name}** - Profit info not yet configured.\n\n"
        f"Set a profit margin per unit in the Products section to see profit calculations."
    )


def _handle_package_query(product, db: Session) -> str:
    full, _ = get_product_pricing(product)
    pkg_unit = full.get("package_unit_type") or product.unit_type or "unit"
    resp = (
        f"**{product.name}** - Package Details\n\n"
        f"📦 **Package Cost:** KSh {full['package_cost_price']}\n"
        f"🔢 **Quantity:** {full['package_quantity']} {pkg_unit}s per package\n"
        f"📊 **Unit Cost:** KSh {full['unit_cost_price']}\n"
    )
    if full["wholesale_selling_price"] is not None:
        resp += f"📦 **Wholesale Selling Price:** KSh {full['wholesale_selling_price']} per package\n"
    return resp


def _handle_suggest_price(product, is_swahili: bool, db: Session) -> str:
    full_pricing, _ = get_product_pricing(product)
    response = _format_pricing_breakdown(product, full_pricing, is_swahili)
    response += '\n\n💡 *Tip: You can set a fixed retail price or adjust the profit margin in the Products section. Enable "Manual Override" to set a custom price.*'
    return response


# ============================================================
# MAIN PROCESSOR
# ============================================================

def process_chat_query(
    query: str,
    session_id: Optional[str],
    db: Session,
    selected_product_id: Optional[int] = None,
) -> dict:
    if not session_id:
        session_id = str(uuid.uuid4())

    is_swahili = _is_swahili(query)
    intent = _detect_intent(query)

    products_found = []
    calculation_used = False
    calculation_detail = None

    # ---- GREETING / HELP ----
    if intent == "greeting":
        response = (
            "Hello! I'm your **JaneMaiks Retail Assistant**. I can help with:\n"
            "- Product prices (e.g., 'How much is milk?')\n"
            "- Stock levels ('How many sweets remaining?')\n"
            "- Supplier info ('Products from supplier X')\n"
            "- Price suggestions\n"
            "- Swahili support (e.g., 'Bei gani ya mkate?')\n\n"
            "How can I help you at JaneMaiks today?"
        )
        _save_chat(session_id, query, response, db)
        return _response(response, session_id)

    if intent == "help":
        response = (
            "Welcome to **JaneMaiks Assistant**. Here's what I can do:\n\n"
            "**Price Queries:**\n"
            "- 'How much is white handkerchief?'\n"
            "- 'What is the price of milk?'\n"
            "- 'Bei gani ya sukari?'\n\n"
            "**Wholesale Queries:**\n"
            "- 'What is the wholesale price of Arimis?'\n"
            "- 'How much per dozen?'\n\n"
            "**Unit Cost Queries:**\n"
            "- 'How much do we buy a dozen at?'\n"
            "- 'What is the unit cost?'\n\n"
            "**Profit Queries:**\n"
            "- 'How much profit per unit?'\n"
            "- 'Profit per package?'\n\n"
            "**Stock Queries:**\n"
            "- 'How many sweets are remaining?'\n"
            "- 'Stock of cooking oil'\n"
            "- 'Zimebaki ngapi?'\n\n"
            "**Supplier Queries:**\n"
            "- 'What products came from supplier X?'\n"
            "- 'Show products from Bidco'\n\n"
            "**Suggestions:**\n"
            "- 'Suggest selling price for this item'\n"
            "- 'Pendekeza bei'"
        )
        _save_chat(session_id, query, response, db)
        return _response(response, session_id)

    # ---- SUPPLIER QUERY (direct, no product search needed) ----
    if intent == "supplier_query":
        supplier_term = _extract_product_name(query)
        supplier_products = (
            db.query(Product)
            .filter(Product.is_active == True, Product.supplier.ilike(f"%{supplier_term}%"))
            .all()
        )
        if supplier_products:
            names = [f"- {p.name} (KSh {p.wholesale_price}/{p.quantity_in_package} {p.unit_type}s)" for p in supplier_products]
            products_found = [p.name for p in supplier_products]
            response = f"Products from **{supplier_term.title()}**:\n\n" + "\n".join(names)
        else:
            response = f"JaneMaiks couldn't find any products from supplier '{supplier_term}'."
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found)

    # ---- CHECK FOR CLARIFICATION FOLLOW-UP ----
    # If the user is responding to a clarification question
    clarification_state = _get_clarification_state(session_id, db)
    resolved_from_clarification = False

    if clarification_state and not selected_product_id:
        resolved_product, resolved_ctx, original_query = _handle_clarification_response(query, clarification_state, db)
        if resolved_product:
            # The user answered the clarification — process the original intent
            intent = resolved_ctx.get("intent", intent)
            is_swahili = resolved_ctx.get("is_swahili", is_swahili)
            target_product = resolved_product
            resolved_from_clarification = True

    # ---- DIRECT PRODUCT SELECTION (from frontend click) ----
    if selected_product_id and not resolved_from_clarification:
        target_product = db.query(Product).filter(Product.id == selected_product_id).first()
        if target_product:
            # Process with whatever intent we detected on the original query
            # But we need the original state
            cs = _get_clarification_state(session_id, db)
            if cs:
                intent = cs.get("intent", intent)
                is_swahili = cs.get("is_swahili", is_swahili)
            resolved_from_clarification = True

    # ---- NORMAL PRODUCT SEARCH (if not resolved from clarification) ----
    if not resolved_from_clarification:
        product_name = _extract_product_name(query)
        target_product, candidates, is_ambiguous, ranked = _smart_find_product(product_name, db)

        # ---- AMBIGUITY DETECTED ----
        if is_ambiguous and target_product is None:
            clarification = build_clarification_response(candidates)
            # Save clarification state for follow-up
            state = {
                "candidates": clarification["matches"],
                "original_query": query,
                "intent": intent,
                "is_swahili": is_swahili,
            }
            _save_clarification_state(session_id, query, clarification["response"], db, state)
            return _response(
                response=clarification["response"],
                session_id=session_id,
                resp_type="clarification_required",
                clarification_matches=clarification["matches"],
            )

        # ---- NO MATCH ----
        if not target_product:
            # Fallback: try semantic search
            semantic_results = rag_service.semantic_search(query, n_results=3)
            if semantic_results:
                sem_ids = [r["product_id"] for r in semantic_results if r.get("product_id")]
                if sem_ids:
                    target_product = db.query(Product).filter(Product.id.in_(sem_ids)).first()

        if not target_product:
            response = build_no_match_response(product_name)
            # Show alternatives from scoring
            if ranked:
                alt_names = [f"- {p.name}" for p, s, r in ranked[:3]]
                response += "\n\nDid you mean one of these?\n" + "\n".join(alt_names)
                products_found = [p.name for p, s, r in ranked[:3]]
            _save_chat(session_id, query, response, db, products_found)
            return _response(response, session_id, products_found=products_found)

    # ============================================================
    # PROCESS INTENT WITH RESOLVED PRODUCT
    # ============================================================
    products_found.append(target_product.name)

    # ---- STOCK QUERY ----
    if intent == "stock_query":
        response = _handle_stock_query(target_product, is_swahili, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found)

    # ---- WHOLESALE QUERY ----
    if intent == "wholesale_query":
        response = _handle_wholesale_query(target_product, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found, calculation_used=True)

    # ---- UNIT COST QUERY ----
    if intent == "unit_cost_query":
        response = _handle_unit_cost_query(target_product, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found, calculation_used=True)

    # ---- PROFIT QUERY ----
    if intent == "profit_query":
        response = _handle_profit_query(target_product, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found, calculation_used=True)

    # ---- PACKAGE QUERY ----
    if intent in ("package_query", "package_price_query"):
        response = _handle_package_query(target_product, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found)

    # ---- PRICE / GENERAL / CALCULATOR ----
    if intent in ("price_query", "general_query", "calculator"):
        response, calc_used, calc_detail = _handle_price_query(target_product, query, is_swahili)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found, calculation_used=calc_used, calculation_detail=calc_detail)

    # ---- SUGGEST PRICE ----
    if intent == "suggest_price":
        response = _handle_suggest_price(target_product, is_swahili, db)
        _save_chat(session_id, query, response, db, products_found)
        return _response(response, session_id, products_found=products_found, calculation_used=True, calculation_detail=response)

    # ---- FALLBACK (shouldn't reach here) ----
    response = build_no_match_response(query)
    _save_chat(session_id, query, response, db)
    return _response(response, session_id, products_found=products_found)


def _response(
    response: str,
    session_id: str,
    products_found: list = None,
    calculation_used: bool = False,
    calculation_detail: str = None,
    resp_type: str = "normal",
    clarification_matches: list = None,
) -> dict:
    return {
        "response": response,
        "products_found": products_found or [],
        "calculation_used": calculation_used,
        "calculation_detail": calculation_detail,
        "session_id": session_id,
        "type": resp_type,
        "clarification_matches": clarification_matches or [],
    }


# ============================================================
# CHAT HISTORY
# ============================================================

def _save_chat(session_id: str, query: str, response: str, db: Session, products: list = None):
    try:
        chat = ChatHistory(
            session_id=session_id,
            user_query=query,
            bot_response=response,
            products_referenced=", ".join(products) if products else None,
        )
        db.add(chat)
        db.commit()
    except Exception:
        db.rollback()


def get_chat_history(session_id: Optional[str], db: Session, limit: int = 50):
    q = db.query(ChatHistory).order_by(ChatHistory.created_at.desc())
    if session_id:
        q = q.filter(ChatHistory.session_id == session_id)
    return q.limit(limit).all()
