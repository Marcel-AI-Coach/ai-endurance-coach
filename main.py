# main.py
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
    try:
        test_db_connection()
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "endpoint": "db-test-simple",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@app.get("/planning-data")
def planning_data(athlete_id: int, week_start: str, db: Session = Depends(get_db)):
    try:
        data = load_weekly_planning_data(db, athlete_id, week_start)

        if not data["athlete"]:
            return {
                "status": "error",
                "endpoint": "planning-data",
                "error_type": "NotFound",
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
