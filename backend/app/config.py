import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retail_assistant.db")
DEFAULT_PROFIT_MARGIN = float(os.getenv("DEFAULT_PROFIT_MARGIN", "15"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
SECRET_KEY = os.getenv("SECRET_KEY", "retail-assistant-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
