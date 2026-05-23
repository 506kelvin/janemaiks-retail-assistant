import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import (
    DATABASE_URL,
    DEBUG,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_PRE_PING,
)

logger = logging.getLogger(__name__)

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=DEBUG,
    )
    logger.info("Using SQLite engine: %s", DATABASE_URL)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=DB_POOL_PRE_PING,
        pool_recycle=DB_POOL_RECYCLE,
        echo=DEBUG,
    )
    logger.info(
        "Using PostgreSQL engine: %s (pool=%s, overflow=%s, pre_ping=%s, recycle=%ss)",
        DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        DB_POOL_SIZE,
        DB_MAX_OVERFLOW,
        DB_POOL_PRE_PING,
        DB_POOL_RECYCLE,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
