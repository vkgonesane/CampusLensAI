from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.campus_signal import CampusSignal
from app.models.signal_activity import SignalActivity
from app.services.activity_service import create_activity
from app.services.notification_service import notify_sla_breached


def calculate_sla_due_at(priority: str) -> datetime:
    now = datetime.now(timezone.utc)

    sla_hours = {
        "urgent": 4,
        "critical": 4,
        "high": 24,
        "medium": 72,
        "low": 168,
    }

    normalized_priority = (priority or "medium").lower()
    hours = sla_hours.get(normalized_priority, 72)

    return now + timedelta(hours=hours)


def check_and_mark_sla_breached(
    signal: CampusSignal,
    db: Session,
    actor_id: int,
) -> bool:
    if signal.sla_breached:
        return False

    if signal.status == "closed":
        return False

    if signal.sla_due_at is None:
        return False

    now = datetime.now(timezone.utc)
    sla_due_at = signal.sla_due_at

    if sla_due_at.tzinfo is None:
        sla_due_at = sla_due_at.replace(tzinfo=timezone.utc)

    if now <= sla_due_at:
        return False

    existing_activity = (
        db.query(SignalActivity)
        .filter(SignalActivity.signal_id == signal.id)
        .filter(SignalActivity.action == "sla_breached")
        .first()
    )

    signal.sla_breached = True

    if signal.escalated_at is None:
        signal.escalated_at = now

        if signal.supervisor_id:
            notify_sla_breached(
                db=db,
                user_id=signal.supervisor_id,
                signal_title=signal.title,
            )

    if existing_activity:
        return True

    create_activity(
        db=db,
        signal_id=signal.id,
        actor_id=actor_id,
        action="sla_breached",
        from_status=signal.status,
        to_status=signal.status,
        note="SLA deadline breached",
        metadata={
            "priority": signal.priority,
            "sla_due_at": signal.sla_due_at.isoformat()
            if signal.sla_due_at
            else None,
            "checked_at": now.isoformat(),
        },
    )

    return True