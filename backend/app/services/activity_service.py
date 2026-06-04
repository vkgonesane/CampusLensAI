from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.signal_activity import SignalActivity


def create_activity(
    db: Session,
    signal_id: int,
    actor_id: int,
    action: str,
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    note: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> SignalActivity:
    activity = SignalActivity(
        signal_id=signal_id,
        actor_id=actor_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        note=note,
        metadata_json=metadata
    )

    db.add(activity)
    return activity


def get_signal_activities(
    db: Session,
    signal_id: int
):
    return (
        db.query(SignalActivity)
        .filter(SignalActivity.signal_id == signal_id)
        .order_by(SignalActivity.created_at.asc())
        .all()
    )