# main.py
from fastapi import FastAPI
from planner import test_planner

app = FastAPI(title="Coaching Platform API")


@app.get("/")
def root():
    return {"message": "API läuft erfolgreich."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/planner-test")
def planner_test():
    return test_planner()
