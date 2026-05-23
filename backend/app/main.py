import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from .config import DEBUG, CORS_ORIGINS, DATABASE_URL
from .database import engine, Base, get_db
from .routers import products, pricing, chatbot, inventory, analytics, auth, sales, requested_items
from .seed import seed_database

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

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
]

CHAT_COLUMNS = [
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
    with engine.begin() as conn:
        for col_name, col_type in CHAT_COLUMNS:
            if col_name not in existing_chat:
                conn.execute(text(f"ALTER TABLE chat_history ADD COLUMN {col_name} {col_type}"))
except Exception as e:
    print(f"Schema migration note: {e}")

app = FastAPI(
    title="JaneMaiks Retail Assistant API",
    description="AI-powered retail management system for JaneMaiks",
    version="2.2.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
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
app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(requested_items.router)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if not DEBUG:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.on_event("startup")
def on_startup():
    logger.info("Starting JaneMaiks API — engine: SQLite")
    logger.info("Database URL: %s", DATABASE_URL)

    seed_database()

    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection: OK")
    except Exception as e:
        logger.error("Database connection check failed: %s", e)


@app.get("/api/health")
def health_check():
    db_status = "unknown"
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "app": "JaneMaiks Retail Assistant",
        "version": "2.2.0",
        "debug": DEBUG,
        "database": db_status,
        "database_engine": "SQLite",
        "uptime_seconds": round(time.time() - app.state.start_time, 2) if hasattr(app.state, "start_time") else 0,
    }


@app.on_event("startup")
def set_start_time():
    app.state.start_time = time.time()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )
