from datetime import datetime, timedelta, timezone
from signal import signal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.ai_service import analyze_signal
from app.ai.duplicate_detector import find_best_duplicate_match
from app.models.campus_signal import CampusSignal
from app.models.signal_activity import SignalActivity
from app.models.user import User
from app.schemas.signal_schema import (
    CampusSignalCreate,
    CampusSignalReopenRequest,
    CampusSignalStatusUpdate,
    SignalAssignRequest,
    SignalCloseRequest,
    SignalMarkFixedRequest,
    SignalReviewRequest,
    SignalStartWorkRequest,
    SignalSupervisorReviewRequest,
)
from app.services.activity_service import create_activity
from app.services.notification_service import (
    notify_signal_assigned,
    notify_signal_closed,
    notify_signal_reopened,
    notify_signal_ready_for_review,
    notify_sla_breached,
)
from app.services.workflow_service import validate_status_transition


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


def create_signal(signal_data: CampusSignalCreate, db: Session, current_user: User):
    ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)

    recent_same_user_signals = (
        db.query(CampusSignal)
        .filter(CampusSignal.created_by == current_user.id)
        .filter(CampusSignal.location_name == signal_data.location_name)
        .filter(CampusSignal.created_at >= ten_minutes_ago)
        .all()
    )

    duplicate_match = find_best_duplicate_match(
        current_description=signal_data.description,
        previous_signals=recent_same_user_signals,
    )

    if duplicate_match["score"] >= 0.85 and duplicate_match["matched_signal"]:
        return duplicate_match["matched_signal"]

    previous_signal_rows = db.query(CampusSignal.description).all()
    previous_descriptions = [row[0] for row in previous_signal_rows]

    location_signal_count = 0
    if signal_data.location_name:
        location_signal_count = (
            db.query(CampusSignal)
            .filter(CampusSignal.location_name == signal_data.location_name)
            .count()
        )

    ai_result = analyze_signal(
        title=signal_data.title,
        description=signal_data.description,
        location_name=signal_data.location_name,
        reopen_count=0,
        previous_descriptions=previous_descriptions,
        location_signal_count=location_signal_count,
    )

    sla_due_at = calculate_sla_due_at(ai_result["ai_priority"])

    new_signal = CampusSignal(
        title=signal_data.title,
        description=signal_data.description,
        category=signal_data.category,
        location_name=signal_data.location_name,
        latitude=signal_data.latitude,
        longitude=signal_data.longitude,
        status="submitted",
        priority=ai_result["ai_priority"],
        department=ai_result["suggested_department"],
        suggested_department=ai_result["suggested_department"],
        created_by=current_user.id,
        ai_category=ai_result["ai_category"],
        ai_sentiment=ai_result["ai_sentiment"],
        ai_priority=ai_result["ai_priority"],
        ai_summary=ai_result["ai_summary"],
        duplicate_score=ai_result["duplicate_score"],
        hotspot_score=ai_result["hotspot_score"],
        sla_due_at=sla_due_at,
        sla_breached=False,
        escalated_at=None,
    )

    db.add(new_signal)
    db.flush()

    create_activity(
        db=db,
        signal_id=new_signal.id,
        actor_id=current_user.id,
        action="signal_created",
        from_status=None,
        to_status="submitted",
        note="Signal created",
        metadata={
            "title": new_signal.title,
            "location_name": new_signal.location_name,
            "priority": new_signal.priority,
            "sla_due_at": new_signal.sla_due_at.isoformat()
            if new_signal.sla_due_at
            else None,
            "ai_category": new_signal.ai_category,
        },
    )

    db.commit()
    db.refresh(new_signal)

    return new_signal


def get_all_signals(
    db: Session,
    current_user: User,
    page: int = 1,
    per_page: int = 10,
    status_filter: str | None = None,
    priority_filter: str | None = None,
    department_filter: str | None = None,
):
    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 10

    if per_page > 100:
        per_page = 100

    query = db.query(CampusSignal)

    if current_user.role not in ["admin", "department_staff", "supervisor"]:
        query = query.filter(CampusSignal.created_by == current_user.id)

    if status_filter:
        query = query.filter(CampusSignal.status == status_filter)

    if priority_filter:
        query = query.filter(CampusSignal.priority == priority_filter)

    if department_filter:
        query = query.filter(CampusSignal.department == department_filter)

    total = query.count()

    results = (
        query.order_by(CampusSignal.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    changed = False

    for signal in results:
        breached_now = check_and_mark_sla_breached(
            signal=signal,
            db=db,
            actor_id=current_user.id,
        )
        if breached_now:
            changed = True

    if changed:
        db.commit()

        for signal in results:
            db.refresh(signal)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "results": results,
    }


def get_signal_by_id(signal_id: int, db: Session, current_user: User):
    signal = _get_signal_or_404(signal_id, db)

    if current_user.role == "user" and signal.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own Campus Signals",
        )

    breached_now = check_and_mark_sla_breached(
        signal=signal,
        db=db,
        actor_id=current_user.id,
    )

    if breached_now:
        db.commit()
        db.refresh(signal)

    return signal


def _get_signal_or_404(signal_id: int, db: Session):
    signal = db.query(CampusSignal).filter(CampusSignal.id == signal_id).first()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campus Signal not found",
        )

    return signal

def _ensure_assigned_staff_or_admin(signal: CampusSignal, current_user: User):
    if current_user.role == "admin":
        return

    if current_user.role != "department_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned department staff or admins can perform this action",
        )

    if signal.assigned_staff_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This signal is not assigned to you",
        )


def _change_status(
    signal: CampusSignal,
    requested_status: str,
    db: Session,
    current_user: User,
    action: str,
    note: str | None = None,
    metadata: dict | None = None,
):
    current_status = signal.status

    validate_status_transition(
        current_status=current_status,
        requested_status=requested_status,
    )

    signal.status = requested_status

    if requested_status == "closed":
        signal.closed_at = datetime.now(timezone.utc)

    create_activity(
        db=db,
        signal_id=signal.id,
        actor_id=current_user.id,
        action=action,
        from_status=current_status,
        to_status=requested_status,
        note=note,
        metadata=metadata,
    )


def review_signal(
    signal_id: int,
    review_data: SignalReviewRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    _change_status(
        signal=signal,
        requested_status="under_review",
        db=db,
        current_user=current_user,
        action="signal_review_started",
        note=review_data.note,
    )

    db.commit()
    db.refresh(signal)

    return signal


def assign_signal(
    signal_id: int,
    assign_data: SignalAssignRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    assigned_staff = (
        db.query(User)
        .filter(User.id == assign_data.assigned_staff_id)
        .first()
    )

    if not assigned_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned staff user does not exist",
        )

    if assigned_staff.role != "department_staff":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user must have role department_staff",
        )

    if assign_data.supervisor_id is not None:
        supervisor = (
            db.query(User)
            .filter(User.id == assign_data.supervisor_id)
            .first()
        )

        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supervisor user does not exist",
            )

        if supervisor.role != "supervisor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supervisor user must have role supervisor",
            )

    signal.department = assign_data.department
    signal.assigned_staff_id = assign_data.assigned_staff_id

    if assign_data.supervisor_id is not None:
        signal.supervisor_id = assign_data.supervisor_id

    _change_status(
        signal=signal,
        requested_status="assigned",
        db=db,
        current_user=current_user,
        action="assigned",
        note=assign_data.note,
        metadata={
            "department": assign_data.department,
            "assigned_staff_id": assign_data.assigned_staff_id,
            "supervisor_id": assign_data.supervisor_id,
        },
    )

    notify_signal_assigned(
        db=db,
        user_id=signal.assigned_staff_id,
        signal_title=signal.title,
    )

    db.commit()
    db.refresh(signal)

    return signal


def start_work(
    signal_id: int,
    start_data: SignalStartWorkRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    _ensure_assigned_staff_or_admin(signal, current_user)

    _change_status(
        signal=signal,
        requested_status="in_progress",
        db=db,
        current_user=current_user,
        action="work_started",
        note=start_data.note,
    )

    db.commit()
    db.refresh(signal)

    return signal


def mark_fixed(
    signal_id: int,
    fixed_data: SignalMarkFixedRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    _ensure_assigned_staff_or_admin(signal, current_user)

    signal.resolution_note = fixed_data.resolution_note

    _change_status(
        signal=signal,
        requested_status="fixed_by_staff",
        db=db,
        current_user=current_user,
        action="marked_fixed",
        note=fixed_data.resolution_note,
    )

    db.commit()
    db.refresh(signal)

    return signal


def send_to_supervisor_review(
    signal_id: int,
    review_data: SignalSupervisorReviewRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    _ensure_assigned_staff_or_admin(signal, current_user)

    if review_data.supervisor_note:
        signal.supervisor_note = review_data.supervisor_note

    _change_status(
        signal=signal,
        requested_status="supervisor_review",
        db=db,
        current_user=current_user,
        action="sent_to_supervisor",
        note=review_data.supervisor_note,
    )

    if signal.supervisor_id:
        notify_signal_ready_for_review(
            db=db,
            user_id=signal.supervisor_id,
            signal_title=signal.title,
        )

    db.commit()
    db.refresh(signal)

    return signal


def close_signal(
    signal_id: int,
    close_data: SignalCloseRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    if current_user.role not in ["admin", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or supervisors can close signals",
        )

    if signal.status != "supervisor_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signal must be in supervisor_review before closure",
        )

    signal.supervisor_note = close_data.supervisor_note

    _change_status(
        signal=signal,
        requested_status="closed",
        db=db,
        current_user=current_user,
        action="closed",
        note=close_data.supervisor_note,
    )

    notify_signal_closed(
        db=db,
        user_id=signal.created_by,
        signal_title=signal.title,
    )

    db.commit()
    db.refresh(signal)

    return signal


def update_signal_status(
    signal_id: int,
    update_data: CampusSignalStatusUpdate,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    current_status = signal.status
    requested_status = update_data.status

    validate_status_transition(
        current_status=current_status,
        requested_status=requested_status,
    )

    signal.status = requested_status

    if update_data.department is not None:
        signal.department = update_data.department

    if update_data.assigned_staff_id is not None:
        signal.assigned_staff_id = update_data.assigned_staff_id

    if update_data.supervisor_id is not None:
        signal.supervisor_id = update_data.supervisor_id

    if update_data.resolution_note is not None:
        signal.resolution_note = update_data.resolution_note

    if update_data.supervisor_note is not None:
        signal.supervisor_note = update_data.supervisor_note

    if requested_status == "closed":
        signal.closed_at = datetime.now(timezone.utc)

    create_activity(
        db=db,
        signal_id=signal.id,
        actor_id=current_user.id,
        action="status_changed",
        from_status=current_status,
        to_status=requested_status,
        note=update_data.resolution_note or update_data.supervisor_note,
        metadata={
            "department": update_data.department,
            "assigned_staff_id": update_data.assigned_staff_id,
            "supervisor_id": update_data.supervisor_id,
        },
    )

    db.commit()
    db.refresh(signal)

    return signal


def reopen_signal(
    signal_id: int,
    reopen_data: CampusSignalReopenRequest,
    db: Session,
    current_user: User,
):
    signal = _get_signal_or_404(signal_id, db)

    if signal.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original reporter can reopen this Campus Signal",
        )

    if signal.status != "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only closed signals can be reopened",
        )

    previous_status = signal.status

    signal.reopen_count += 1
    signal.reopen_reason = reopen_data.reason
    signal.status = "reopened"

    previous_signal_rows = db.query(CampusSignal.description).all()
    previous_descriptions = [row[0] for row in previous_signal_rows]

    location_signal_count = 0

    if signal.location_name:
        location_signal_count = (
            db.query(CampusSignal)
            .filter(CampusSignal.location_name == signal.location_name)
            .count()
        )

    ai_result = analyze_signal(
        title=signal.title,
        description=f"{signal.description} Reopen reason: {reopen_data.reason}",
        location_name=signal.location_name,
        reopen_count=signal.reopen_count,
        previous_descriptions=previous_descriptions,
        location_signal_count=location_signal_count,
    )

    signal.priority = ai_result["ai_priority"]
    signal.department = ai_result["suggested_department"]
    signal.suggested_department = ai_result["suggested_department"]
    signal.ai_category = ai_result["ai_category"]
    signal.ai_sentiment = ai_result["ai_sentiment"]
    signal.ai_priority = ai_result["ai_priority"]
    signal.ai_summary = ai_result["ai_summary"]
    signal.duplicate_score = ai_result["duplicate_score"]
    signal.hotspot_score = ai_result["hotspot_score"]
    signal.sla_due_at = calculate_sla_due_at(ai_result["ai_priority"])
    signal.sla_breached = False
    signal.escalated_at = None

    create_activity(
        db=db,
        signal_id=signal.id,
        actor_id=current_user.id,
        action="reopened",
        from_status=previous_status,
        to_status="reopened",
        note=reopen_data.reason,
        metadata={
            "reopen_count": signal.reopen_count,
            "priority": signal.priority,
            "sla_due_at": signal.sla_due_at.isoformat()
            if signal.sla_due_at
            else None,
            "hotspot_score": signal.hotspot_score,
        },
    )

    if signal.supervisor_id:
        notify_signal_reopened(
            db=db,
            user_id=signal.supervisor_id,
            signal_title=signal.title,
        )

    db.commit()
    db.refresh(signal)

    return signal