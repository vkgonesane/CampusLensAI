from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campus_signal import CampusSignal


def get_analytics_overview(db: Session):
    total_signals = db.query(CampusSignal).count()

    open_signals = (
        db.query(CampusSignal)
        .filter(CampusSignal.status != "closed")
        .count()
    )

    closed_signals = (
        db.query(CampusSignal)
        .filter(CampusSignal.status == "closed")
        .count()
    )

    reopened_signals = (
        db.query(CampusSignal)
        .filter(CampusSignal.reopen_count > 0)
        .count()
    )

    high_priority_signals = (
        db.query(CampusSignal)
        .filter(CampusSignal.priority == "high")
        .count()
    )

    return {
        "total_signals": total_signals,
        "open_signals": open_signals,
        "closed_signals": closed_signals,
        "reopened_signals": reopened_signals,
        "high_priority_signals": high_priority_signals
    }


def get_status_breakdown(db: Session):
    rows = (
        db.query(CampusSignal.status, func.count(CampusSignal.id))
        .group_by(CampusSignal.status)
        .all()
    )

    return [
        {
            "status": row[0],
            "count": row[1]
        }
        for row in rows
    ]


def get_priority_breakdown(db: Session):
    rows = (
        db.query(CampusSignal.priority, func.count(CampusSignal.id))
        .group_by(CampusSignal.priority)
        .all()
    )

    return [
        {
            "priority": row[0],
            "count": row[1]
        }
        for row in rows
    ]


def get_category_breakdown(db: Session):
    rows = (
        db.query(CampusSignal.ai_category, func.count(CampusSignal.id))
        .group_by(CampusSignal.ai_category)
        .all()
    )

    return [
        {
            "category": row[0] or "unknown",
            "count": row[1]
        }
        for row in rows
    ]


def get_department_breakdown(db: Session):
    rows = (
        db.query(CampusSignal.department, func.count(CampusSignal.id))
        .group_by(CampusSignal.department)
        .all()
    )

    return [
        {
            "department": row[0] or "unassigned",
            "count": row[1]
        }
        for row in rows
    ]


def get_hotspots(db: Session):
    rows = (
        db.query(
            CampusSignal.location_name,
            func.count(CampusSignal.id),
            func.avg(CampusSignal.hotspot_score)
        )
        .filter(CampusSignal.location_name.isnot(None))
        .group_by(CampusSignal.location_name)
        .order_by(func.count(CampusSignal.id).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "location_name": row[0],
            "signal_count": row[1],
            "average_hotspot_score": round(row[2] or 0, 2)
        }
        for row in rows
    ]