# db.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None

if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL ist nicht gesetzt oder Datenbank nicht initialisiert.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    if engine is None:
        raise RuntimeError("DATABASE_URL ist nicht gesetzt oder Datenbank nicht initialisiert.")

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
