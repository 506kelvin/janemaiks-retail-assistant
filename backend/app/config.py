import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────
# Production: postgresql://user:password@host:5432/retail_assistant
#            postgresql+psycopg2://user:password@host:5432/retail_assistant
# Local dev:  sqlite:///./retail_assistant.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retail_assistant.db")

# Connection pool settings (PostgreSQL only)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

# ── App ───────────────────────────────────────────────────────────────
DEFAULT_PROFIT_MARGIN = float(os.getenv("DEFAULT_PROFIT_MARGIN", "15"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
SECRET_KEY = os.getenv("SECRET_KEY", "retail-assistant-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "janemaiks")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "admin123")
