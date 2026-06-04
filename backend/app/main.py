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

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


@app.get("/")
def health_check():
    return {
        "message": "CampusLensAI backend is running"
    }


@app.get("/db-health")
def db_health_check():
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