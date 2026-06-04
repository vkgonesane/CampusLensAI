from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from app.database.db import Base


class SignalComment(Base):
    __tablename__ = "signal_comments"

    id = Column(Integer, primary_key=True, index=True)

    signal_id = Column(
        Integer,
        ForeignKey("campus_signals.id"),
        nullable=False,
        index=True
    )

    author_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    comment = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )