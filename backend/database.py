'''backend/database.py'''
"""Database connection and session handling using SQLAlchemy.
This module sets up the engine, a session factory, and a declarative Base.
It reads the DATABASE_URL environment variable (e.g., postgresql://user:pass@host/db).
If the variable is missing, the application will raise a clear error on startup.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Validate required environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable not set. "
        "Set it to a PostgreSQL connection string, e.g., "
        "postgresql://user:password@localhost/codesense"
    )

# Render (and some other hosts) provide postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with future flag for 2.0 style
engine = create_engine(DATABASE_URL, future=True, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base class for ORM models
Base = declarative_base()

def get_db():
    """FastAPI dependency that provides a database session.
    Yields a session and ensures it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
