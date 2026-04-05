# main.py
import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from db import get_db, test_db_connection
from planner import load_weekly_planning_data

app = FastAPI(title="Coaching Platform API")


@app.get("/")
def root():
    return {"message": "API läuft erfolgreich."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/env-check")
def env_check():
    database_url = os.getenv("DATABASE_URL")

    return {
        "status": "ok",
        "database_url_exists": database_url is not None,
        "database_url_not_empty": bool(database_url),
        "database_url_prefix": database_url[:20] if database_url else None
    }


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {
            "status": "ok",
            "database": "connected",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "endpoint": "db-test",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@app.get("/db-test-simple")
def db_test_simple():
    result = test_db_connection()

    if result is True:
        return {
            "status": "ok",
            "database": "connected"
        }

    return {
        "status": "error",
        "endpoint": "db-test-simple",
        "error_message": str(result)
    }


@app.get("/planning-data")
def planning_data(athlete_id: int, week_start: str, db: Session = Depends(get_db)):
    try:
        data = load_weekly_planning_data(db, athlete_id, week_start)

        if not data["athlete"]:
            return {
                "status": "error",
                "endpoint": "planning-data",
                "error_message": "Athlet nicht gefunden oder nicht aktiv."
            }

        return {
            "status": "ok",
            "athlete_id": athlete_id,
            "week_start": week_start,
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "endpoint": "planning-data",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
