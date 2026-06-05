import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.error_handlers import app_exception_handler
from app.core.exceptions import AppException
from app.database.db import engine
from app.routes import analytics, auth, notifications, signals, users


app = FastAPI(
    title="CampusLensAI Backend",
    description="AI-powered campus intelligence platform",
    version="1.0.0"
)

app.add_exception_handler(
    AppException,
    app_exception_handler
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/signals", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


@app.get("/")
def root():
    return {
        "message": "CampusLensAI backend is running",
        "status": "ok"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "campuslens-backend",
        "version": "1.0.0"
    }


@app.get("/health/db")
def db_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "status": "healthy",
        "database": "connected",
        "test_result": value
    }


@app.get("/db-health")
def legacy_db_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test_result": value
    }


app.include_router(auth.router)
app.include_router(signals.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(users.router)