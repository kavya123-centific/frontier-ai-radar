"""
database.py
-----------
SQLAlchemy engine + session factory for SQLite.

Design choices:
- SQLite: zero infrastructure, perfect for hackathon
- check_same_thread=False: required for SQLite + asyncio/threading
- SessionLocal: NEVER share across threads — create fresh per use
- get_db(): FastAPI dependency that yields + closes session safely
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./radar.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,                                   # Set True to debug SQL
)

# Session factory — import this everywhere, create sessions from it
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()
