# db.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Holt die Variable aus Railway
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback (nur falls Railway sie nicht liefert)
if not DATABASE_URL:
    print("WARNUNG: DATABASE_URL nicht gesetzt – Fallback wird verwendet")
    DATABASE_URL = "postgresql://postgres:YgtAjnPfOQNlOmmgSsGXwmXeIqjMmxBK@postgres-icm2.railway.internal:5432/railway"

# Richtigen Treiber setzen (wichtig!)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Engine erstellen
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Session erstellen
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# DB Session für FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Testfunktion
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        return str(e)
