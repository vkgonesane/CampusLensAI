from fastapi import FastAPI
from sqlalchemy import text

from app.database.db import Base, engine

from app.models.user import User
from app.models.campus_signal import CampusSignal

from app.routes import auth, signals


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CampusLensAI Backend",
    description="AI-powered campus intelligence platform",
    version="1.0.0"
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