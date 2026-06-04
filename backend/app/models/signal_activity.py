from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database.db import Base


class SignalActivity(Base):
    __tablename__ = "signal_activities"

    id = Column(Integer, primary_key=True, index=True)

    signal_id = Column(
        Integer,
        ForeignKey("campus_signals.id"),
        nullable=False,
        index=True
    )

    actor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    action = Column(String(50), nullable=False, index=True)

    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=True)

    note = Column(Text, nullable=True)

    metadata_json = Column("metadata", JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )