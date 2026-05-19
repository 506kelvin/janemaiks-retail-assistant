from typing import Optional
from ..config import DEFAULT_PROFIT_MARGIN


# ============================================================
# ROUNDING ENGINE
# ============================================================

def round_to_nearest_5(price: float) -> float:
    """Round to nearest 5. 42 -> 45, 42.5 -> 45, 46 -> 50"""
    return round(price / 5) * 5


def round_to_nearest_10(price: float) -> float:
    """Round to nearest 10. 42 -> 40, 42.5 -> 40, 46 -> 50"""
    return round(price / 10) * 10


def apply_rounding(price: float, strategy: Optional[str]) -> float:
    """Apply rounding strategy to a price."""
    if strategy == "nearest_5":
        return round_to_nearest_5(price)
    elif strategy == "nearest_10":
        return round_to_nearest_10(price)
    return price


# ============================================================
# UNIT COST CALCULATION
# ============================================================

def calculate_unit_cost(package_cost: float, package_qty: int) -> float:
    """unit_cost = package_cost_price / package_quantity"""
    if package_qty <= 0:
        return 0.0
    return round(package_cost / package_qty, 2)


# ============================================================
# LEGACY PRICING (backwards compatible)
# ============================================================

def calculate_unit_wholesale_price(wholesale_price: float, quantity_in_package: int) -> float:
    return round(wholesale_price / quantity_in_package, 2)


def calculate_retail_price(
    wholesale_price: float,
    quantity_in_package: int,
    profit_per_item: Optional[float] = None,
    profit_margin_percent: Optional[float] = None,
    retail_price: Optional[float] = None,
) -> dict:
    if retail_price is not None:
        return {
            "unit_wholesale_price": calculate_unit_wholesale_price(wholesale_price, quantity_in_package),
            "profit_per_item": None,
            "retail_price_per_unit": retail_price,
            "calculation_breakdown": f"Retail price manually set to {retail_price}",
            "is_calculated": False,
        }

    unit_wholesale = calculate_unit_wholesale_price(wholesale_price, quantity_in_package)

    if profit_per_item is not None:
        retail = unit_wholesale + profit_per_item
        breakdown = f"({wholesale_price} / {quantity_in_package}) + {profit_per_item} = {retail}"
        return {
            "unit_wholesale_price": unit_wholesale,
            "profit_per_item": profit_per_item,
            "retail_price_per_unit": retail,
            "calculation_breakdown": breakdown,
            "is_calculated": True,
        }

    margin = profit_margin_percent if profit_margin_percent is not None else DEFAULT_PROFIT_MARGIN
    profit_amount = round(unit_wholesale * (margin / 100), 2)
    retail = round(unit_wholesale + profit_amount, 2)
    breakdown = f"({wholesale_price} / {quantity_in_package}) + ({unit_wholesale} * {margin}%) = {unit_wholesale} + {profit_amount} = {retail}"

    return {
        "unit_wholesale_price": unit_wholesale,
        "profit_per_item": profit_amount,
        "retail_price_per_unit": retail,
        "calculation_breakdown": breakdown,
        "is_calculated": True,
    }


# ============================================================
# NEW WHOLESALE + RETAIL PRICING ENGINE
# ============================================================

def compute_full_pricing(
    package_cost_price: float,
    package_quantity: int,
    profit_margin_per_unit: Optional[float] = None,
    wholesale_selling_price: Optional[float] = None,
    actual_retail_price: Optional[float] = None,
    rounding_strategy: Optional[str] = "none",
    allow_manual_override: bool = False,
) -> dict:
    """
    Compute the full pricing structure for a product.

    Returns:
    - unit_cost_price: package_cost / package_quantity
    - suggested_retail_price: unit_cost + profit_margin (if no manual override)
    - rounded_price: suggested retail with rounding applied
    - wholesale_selling_price: price to sell whole package (if set)
    - actual_retail_price: manually overridden retail (if set and allowed)
    - profit_per_unit: the profit margin used
    - profit_per_package: profit_per_unit * package_quantity
    """
    unit_cost = calculate_unit_cost(package_cost_price, package_quantity)

    result = {
        "unit_cost_price": unit_cost,
        "suggested_retail_price": None,
        "rounded_price": None,
        "actual_retail_price": actual_retail_price,
        "wholesale_selling_price": wholesale_selling_price,
        "profit_per_unit": profit_margin_per_unit,
        "profit_per_package": None,
        "margin_warning": False,
    }

    # Calculate suggested retail price
    if profit_margin_per_unit is not None:
        suggested = unit_cost + profit_margin_per_unit
        suggested = round(suggested, 2)
        result["suggested_retail_price"] = suggested

        # Apply rounding
        if rounding_strategy and rounding_strategy != "none":
            result["rounded_price"] = apply_rounding(suggested, rounding_strategy)
        else:
            result["rounded_price"] = suggested

        # Calculate profit per package
        result["profit_per_package"] = round(profit_margin_per_unit * package_quantity, 2)

        # Margin warning
        if profit_margin_per_unit < 5:
            result["margin_warning"] = True

    # Determine which retail price to show as "effective"
    if allow_manual_override and actual_retail_price is not None:
        result["effective_retail_price"] = actual_retail_price
        result["price_source"] = "manual"
    else:
        result["effective_retail_price"] = result["rounded_price"] or result["suggested_retail_price"]
        result["price_source"] = "calculated"

    return result


def suggest_retail_price(
    unit_cost_price: float,
    profit_margin_per_unit: float,
    rounding_strategy: str = "none",
) -> dict:
    """
    Given a unit cost and desired profit, suggest a retail price.
    """
    suggested = round(unit_cost_price + profit_margin_per_unit, 2)
    rounded = apply_rounding(suggested, rounding_strategy)

    return {
        "suggested_retail_price": suggested,
        "rounded_price": rounded,
        "profit_margin_per_unit": profit_margin_per_unit,
        "unit_cost_price": unit_cost_price,
        "rounding_strategy": rounding_strategy,
    }


def get_product_pricing(product) -> dict:
    """
    Get complete pricing for a product, using new fields with fallback to legacy fields.
    """
    pkg_cost = product.package_cost_price if product.package_cost_price is not None else product.wholesale_price
    pkg_qty = product.package_quantity if product.package_quantity is not None else product.quantity_in_package
    pkg_unit = product.package_unit_type if product.package_unit_type is not None else product.unit_type
    profit = product.profit_margin_per_unit if product.profit_margin_per_unit is not None else product.profit_per_item

    unit_cost = calculate_unit_cost(pkg_cost, pkg_qty)

    # Determine manual retail: prefer actual_retail_price, fallback to retail_price
    actual_retail = product.actual_retail_price if product.actual_retail_price is not None else product.retail_price

    pricing = compute_full_pricing(
        package_cost_price=pkg_cost,
        package_quantity=pkg_qty,
        profit_margin_per_unit=profit,
        wholesale_selling_price=product.wholesale_selling_price,
        actual_retail_price=actual_retail,
        rounding_strategy=product.rounding_strategy or "none",
        allow_manual_override=product.allow_manual_override or False,
    )

    # Auto-save calculated fields to the product
    changed = False
    if product.unit_cost_price != unit_cost:
        product.unit_cost_price = unit_cost
        changed = True
    if pricing["suggested_retail_price"] is not None and product.suggested_retail_price != pricing["suggested_retail_price"]:
        product.suggested_retail_price = pricing["suggested_retail_price"]
        changed = True

    return {
        "product_id": product.id,
        "product_name": product.name,
        "package_cost_price": pkg_cost,
        "package_quantity": pkg_qty,
        "package_unit_type": pkg_unit,
        "unit_cost_price": unit_cost,
        "wholesale_selling_price": product.wholesale_selling_price,
        "suggested_retail_price": pricing["suggested_retail_price"],
        "rounded_price": pricing["rounded_price"],
        "actual_retail_price": actual_retail,
        "effective_retail_price": pricing["effective_retail_price"],
        "profit_per_unit": pricing["profit_per_unit"],
        "profit_per_package": pricing["profit_per_package"],
        "margin_warning": pricing["margin_warning"],
        "price_source": pricing["price_source"],
        "rounding_strategy": product.rounding_strategy or "none",
    }, changed
