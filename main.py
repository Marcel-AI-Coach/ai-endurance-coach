# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from planner import load_weekly_planning_data

from db import get_db, test_db_connection

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
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

@app.get("/db-test-simple")
def db_test_simple():
    try:
        test_db_connection()
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

@app.get("/planning-data")
def planning_data(athlete_id: int, week_start: str, db: Session = Depends(get_db)):
    try:
        data = load_weekly_planning_data(db, athlete_id, week_start)

        if not data["athlete"]:
            raise HTTPException(status_code=404, detail="Athlet nicht gefunden oder nicht aktiv.")

        return {
            "status": "ok",
            "athlete_id": athlete_id,
            "week_start": week_start,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Planungsdaten: {str(e)}")
