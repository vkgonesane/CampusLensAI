from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.db import Base


class CampusSignal(Base):
    __tablename__ = "campus_signals"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(100), nullable=True)
    location_name = Column(String(200), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    status = Column(String(50), nullable=False, default="submitted")
    priority = Column(String(50), nullable=False, default="medium")

    department = Column(String(100), nullable=True)
    suggested_department = Column(String(100), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    assigned_staff_id = Column(Integer, nullable=True)
    supervisor_id = Column(Integer, nullable=True)

    resolution_note = Column(Text, nullable=True)
    supervisor_note = Column(Text, nullable=True)

    reopen_count = Column(Integer, nullable=False, default=0)
    reopen_reason = Column(Text, nullable=True)

    ai_category = Column(String(100), nullable=True)
    ai_sentiment = Column(String(50), nullable=True)
    ai_priority = Column(String(50), nullable=True)
    ai_summary = Column(Text, nullable=True)
    duplicate_score = Column(Float, nullable=False, default=0.0)
    hotspot_score = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)