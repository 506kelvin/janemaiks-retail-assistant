from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .config import DEBUG, CORS_ORIGINS
from .database import engine, Base
from .routers import products, pricing, chatbot, inventory, analytics
from .seed import seed_database

Base.metadata.create_all(bind=engine)

# ---- Migration: add new columns if missing ----
NEW_COLUMNS = [
    ("package_cost_price", "REAL"),
    ("package_quantity", "INTEGER"),
    ("package_unit_type", "VARCHAR(50)"),
    ("unit_cost_price", "REAL"),
    ("wholesale_selling_price", "REAL"),
    ("suggested_retail_price", "REAL"),
    ("actual_retail_price", "REAL"),
    ("profit_margin_per_unit", "REAL"),
    ("allow_manual_override", "BOOLEAN"),
    ("rounding_strategy", "VARCHAR(20)"),
    ("aliases", "TEXT"),
    ("tags", "TEXT"),
    ("search_keywords", "TEXT"),
    ("clarification_state", "TEXT"),
]

try:
    inspector = inspect(engine)
    existing_products = {c["name"] for c in inspector.get_columns("products")}
    with engine.begin() as conn:
        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing_products:
                conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"))

    existing_chat = {c["name"] for c in inspector.get_columns("chat_history")}
    if "clarification_state" not in existing_chat:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE chat_history ADD COLUMN clarification_state TEXT"))
except Exception as e:
    print(f"Migration note: {e}")
# ---- End migration ----

app = FastAPI(
    title="JaneMaiks Retail Assistant API",
    description="AI-powered retail management system for JaneMaiks — wholesale + retail pricing, inventory, and analytics for Kenyan shops",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(pricing.router)
app.include_router(chatbot.router)
app.include_router(inventory.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup():
    seed_database()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "app": "JaneMaiks Retail Assistant", "version": "2.0.0", "debug": DEBUG}
