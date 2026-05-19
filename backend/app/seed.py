import random
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Product, Inventory
from .services.rag import rag_service
from .services.pricing import calculate_unit_cost


SAMPLE_PRODUCTS = [
    {
        "name": "Arimis Petroleum Jelly 50ml", "category": "Personal Care", "supplier": "Arimis Kenya",
        "wholesale_price": 390, "quantity_in_package": 12, "unit_type": "jar",
        "package_cost_price": 390, "package_quantity": 12, "package_unit_type": "jar",
        "profit_per_item": 10, "profit_margin_per_unit": 10,
        "wholesale_selling_price": 440, "actual_retail_price": 50, "rounding_strategy": "nearest_5",
        "aliases": '["arimis", "petroleum jelly", "vaseline", "mafuta"]',
        "search_keywords": "arimis petroleum jelly body cream moisturizer mafuta",
    },
    {
        "name": "Fresh Milk (500ml)", "category": "Dairy", "supplier": "Brookside Dairy",
        "wholesale_price": 540, "quantity_in_package": 12, "unit_type": "packet",
        "package_cost_price": 540, "package_quantity": 12, "package_unit_type": "packet",
        "profit_per_item": 8, "profit_margin_per_unit": 8,
        "wholesale_selling_price": 600, "rounding_strategy": "nearest_5",
        "aliases": '["milk", "fresh milk", "maziwa", "brookside"]',
        "search_keywords": "milk fresh maziwa dairy brookside",
    },
    {
        "name": "Bread (White)", "category": "Bakery", "supplier": "Kenya Bakeries",
        "wholesale_price": 450, "quantity_in_package": 10, "unit_type": "loaf",
        "package_cost_price": 450, "package_quantity": 10, "package_unit_type": "loaf",
        "retail_price": 55, "actual_retail_price": 55,
        "allow_manual_override": True, "rounding_strategy": "none",
        "aliases": '["bread", "mkate", "white bread"]',
        "search_keywords": "bread mkate white loaf bakery",
    },
    {
        "name": "Sugar (2kg)", "category": "Foodstuff", "supplier": "Mumias Sugar",
        "wholesale_price": 1300, "quantity_in_package": 10, "unit_type": "packet",
        "package_cost_price": 1300, "package_quantity": 10, "package_unit_type": "packet",
        "profit_per_item": 15, "profit_margin_per_unit": 15,
        "wholesale_selling_price": 1450, "rounding_strategy": "nearest_10",
        "aliases": '["sugar", "sukari", "mumias"]',
        "search_keywords": "sugar sukari mumias sweetener",
    },
    {
        "name": "Cooking Oil (1L)", "category": "Foodstuff", "supplier": "Bidco Africa",
        "wholesale_price": 2200, "quantity_in_package": 6, "unit_type": "bottle",
        "package_cost_price": 2200, "package_quantity": 6, "package_unit_type": "bottle",
        "profit_per_item": 50, "profit_margin_per_unit": 50,
        "wholesale_selling_price": 2400, "rounding_strategy": "nearest_10",
        "aliases": '["cooking oil", "oil", "mafuta ya kupikia", "bidco", "salad oil"]',
        "search_keywords": "cooking oil mafuta kupikia bidco frying",
    },
    {
        "name": "Sweets (Assorted)", "category": "Foodstuff", "supplier": "Kenya Sweets Ltd",
        "wholesale_price": 200, "quantity_in_package": 50, "unit_type": "piece",
        "package_cost_price": 200, "package_quantity": 50, "package_unit_type": "piece",
        "profit_per_item": 1, "profit_margin_per_unit": 1,
        "rounding_strategy": "none",
        "aliases": '["sweets", "candy", "assorted sweets", "peremende", "pipi"]',
        "search_keywords": "sweets candy peremende pipi assorted",
    },
    {
        "name": "White Handkerchief", "category": "Textiles", "supplier": "Textile Suppliers Ltd",
        "wholesale_price": 480, "quantity_in_package": 12, "unit_type": "piece",
        "package_cost_price": 480, "package_quantity": 12, "package_unit_type": "piece",
        "profit_per_item": 10, "profit_margin_per_unit": 10,
        "wholesale_selling_price": 550, "rounding_strategy": "nearest_5",
        "aliases": '["handkerchief", "hanky", "handkerchief white", "leso", "kitambaa"]',
        "search_keywords": "handkerchief hanky white leso kitambaa textile",
    },
    {
        "name": "Wheat Flour (2kg)", "category": "Foodstuff", "supplier": "Unga Limited",
        "wholesale_price": 1250, "quantity_in_package": 10, "unit_type": "packet",
        "package_cost_price": 1250, "package_quantity": 10, "package_unit_type": "packet",
        "profit_per_item": 12, "profit_margin_per_unit": 12,
        "wholesale_selling_price": 1380, "rounding_strategy": "nearest_10",
        "aliases": '["wheat flour", "flour", "unga", "unga wa ngano"]',
        "search_keywords": "wheat flour unga ngano baking",
    },
    {
        "name": "Rice (1kg)", "category": "Foodstuff", "supplier": "Capwell Industries",
        "wholesale_price": 980, "quantity_in_package": 20, "unit_type": "packet",
        "package_cost_price": 980, "package_quantity": 20, "package_unit_type": "packet",
        "profit_per_item": 8, "profit_margin_per_unit": 8,
        "rounding_strategy": "nearest_5",
        "aliases": '["rice", "mchele", "capwell"]',
        "search_keywords": "rice mchele capwell grains",
    },
    {
        "name": "Toothpaste (100g)", "category": "Personal Care", "supplier": "Unilever Kenya",
        "wholesale_price": 720, "quantity_in_package": 24, "unit_type": "tube",
        "package_cost_price": 720, "package_quantity": 24, "package_unit_type": "tube",
        "profit_per_item": 5, "profit_margin_per_unit": 5,
        "wholesale_selling_price": 800, "rounding_strategy": "nearest_5",
        "aliases": '["toothpaste", "dawa ya meno", "unilever"]',
        "search_keywords": "toothpaste dawa meno unilever dental",
    },
    {
        "name": "Bar Soap", "category": "Personal Care", "supplier": "Bidco Africa",
        "wholesale_price": 360, "quantity_in_package": 24, "unit_type": "bar",
        "package_cost_price": 360, "package_quantity": 24, "package_unit_type": "bar",
        "profit_per_item": 3, "profit_margin_per_unit": 3,
        "rounding_strategy": "none",
        "aliases": '["soap", "bar soap", "sabuni", "bidco soap"]',
        "search_keywords": "soap bar sabuni bidco bathing",
    },
    {
        "name": "Mineral Water (1L)", "category": "Beverages", "supplier": "Coca-Cola Kenya",
        "wholesale_price": 600, "quantity_in_package": 12, "unit_type": "bottle",
        "package_cost_price": 600, "package_quantity": 12, "package_unit_type": "bottle",
        "profit_per_item": 10, "profit_margin_per_unit": 10,
        "wholesale_selling_price": 680, "rounding_strategy": "nearest_10",
        "aliases": '["mineral water", "water", "maji", "coca cola water", "drinking water"]',
        "search_keywords": "mineral water maji drinking coke beverage",
    },
    {
        "name": "Tea Leaves (500g)", "category": "Foodstuff", "supplier": "Kericho Gold",
        "wholesale_price": 840, "quantity_in_package": 12, "unit_type": "packet",
        "package_cost_price": 840, "package_quantity": 12, "package_unit_type": "packet",
        "profit_per_item": 8, "profit_margin_per_unit": 8,
        "rounding_strategy": "nearest_5",
        "aliases": '["tea", "tea leaves", "chai", "kericho gold"]',
        "search_keywords": "tea leaves chai kericho gold beverage",
    },
    {
        "name": "Diapers (Small)", "category": "Baby Care", "supplier": "Softcare Ltd",
        "wholesale_price": 1500, "quantity_in_package": 30, "unit_type": "piece",
        "package_cost_price": 1500, "package_quantity": 30, "package_unit_type": "piece",
        "profit_per_item": 5, "profit_margin_per_unit": 5,
        "wholesale_selling_price": 1650, "rounding_strategy": "nearest_10",
        "aliases": '["diapers", "nappies", "baby diapers", "softcare"]',
        "search_keywords": "diapers nappies baby softcare nepi",
    },
    {
        "name": "Maize Flour (2kg)", "category": "Foodstuff", "supplier": "Unga Limited",
        "wholesale_price": 1150, "quantity_in_package": 10, "unit_type": "packet",
        "package_cost_price": 1150, "package_quantity": 10, "package_unit_type": "packet",
        "profit_per_item": 10, "profit_margin_per_unit": 10,
        "wholesale_selling_price": 1280, "rounding_strategy": "nearest_10",
        "aliases": '["maize flour", "unga wa mahindi", "corn flour", "dona"]',
        "search_keywords": "maize flour unga mahindi corn meal dona ugali",
    },
    {
        "name": "Margarine (500g)", "category": "Foodstuff", "supplier": "Bidco Africa",
        "wholesale_price": 960, "quantity_in_package": 12, "unit_type": "tub",
        "package_cost_price": 960, "package_quantity": 12, "package_unit_type": "tub",
        "profit_per_item": 7, "profit_margin_per_unit": 7,
        "rounding_strategy": "nearest_5",
        "aliases": '["margarine", "blue band", "butter", "siagi"]',
        "search_keywords": "margarine blue band butter siagi spread",
    },
    {
        "name": "Washing Powder (1kg)", "category": "Household", "supplier": "Unilever Kenya",
        "wholesale_price": 560, "quantity_in_package": 12, "unit_type": "packet",
        "package_cost_price": 560, "package_quantity": 12, "package_unit_type": "packet",
        "profit_per_item": 6, "profit_margin_per_unit": 6,
        "wholesale_selling_price": 630, "rounding_strategy": "nearest_5",
        "aliases": '["washing powder", "detergent", "sabuni ya nguo", "omi"]',
        "search_keywords": "washing powder detergent sabuni nguo omi laundry",
    },
    {
        "name": "Sardines (Tin)", "category": "Foodstuff", "supplier": "Kensalt Ltd",
        "wholesale_price": 900, "quantity_in_package": 24, "unit_type": "tin",
        "package_cost_price": 900, "package_quantity": 24, "package_unit_type": "tin",
        "profit_per_item": 5, "profit_margin_per_unit": 5,
        "wholesale_selling_price": 1020, "rounding_strategy": "nearest_10",
        "aliases": '["sardines", "tinned fish", "samaki", "kensalt"]',
        "search_keywords": "sardines tinned fish samaki kensalt tin",
    },
    {
        "name": "Matches (Box)", "category": "Household", "supplier": "Safety Matches Ltd",
        "wholesale_price": 120, "quantity_in_package": 100, "unit_type": "box",
        "package_cost_price": 120, "package_quantity": 100, "package_unit_type": "box",
        "profit_per_item": 1, "profit_margin_per_unit": 1,
        "rounding_strategy": "none",
        "aliases": '["matches", "matchbox", "kiberiti"]',
        "search_keywords": "matches matchbox kiberiti safety",
    },
    {
        "name": "Pasta (500g)", "category": "Foodstuff", "supplier": "Pasta Foods Ltd",
        "wholesale_price": 480, "quantity_in_package": 20, "unit_type": "packet",
        "package_cost_price": 480, "package_quantity": 20, "package_unit_type": "packet",
        "profit_per_item": 4, "profit_margin_per_unit": 4,
        "rounding_strategy": "nearest_5",
        "aliases": '["pasta", "spaghetti", "macaroni", "tambi"]',
        "search_keywords": "pasta spaghetti macaroni tambi noodles",
    },
]


def seed_database():
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        if existing > 0:
            return

        for data in SAMPLE_PRODUCTS:
            # Auto-calculate unit_cost_price
            pkg_cost = data.get("package_cost_price", data["wholesale_price"])
            pkg_qty = data.get("package_quantity", data["quantity_in_package"])
            data["unit_cost_price"] = calculate_unit_cost(pkg_cost, pkg_qty)

            # Auto-calculate suggested_retail_price
            margin = data.get("profit_margin_per_unit") or data.get("profit_per_item")
            if margin is not None:
                data["suggested_retail_price"] = round(data["unit_cost_price"] + margin, 2)

            product = Product(**data)
            db.add(product)
            db.flush()

            inv = Inventory(
                product_id=product.id,
                quantity_available=random.randint(20, 200),
                low_stock_threshold=10,
            )
            db.add(inv)

        db.commit()
        for product in db.query(Product).all():
            try:
                rag_service.index_product(product)
            except Exception:
                pass
    except Exception as e:
        db.rollback()
        print(f"Seed warning: {e}")
    finally:
        db.close()
