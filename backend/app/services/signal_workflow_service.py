from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.campus_signal import CampusSignal
from app.models.user import User
from app.schemas.signal_schema import (
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
    notify_signal_ready_for_review,
)
from app.services.signal_permission_service import (
    ensure_admin_or_supervisor,
    ensure_assigned_staff_or_admin,
)
from app.services.workflow_service import validate_status_transition


def _get_signal_or_404(signal_id: int, db: Session):
    signal = db.query(CampusSignal).filter(CampusSignal.id == signal_id).first()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campus Signal not found",
        )

    return signal


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

    ensure_assigned_staff_or_admin(signal, current_user)

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

    ensure_assigned_staff_or_admin(signal, current_user)

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

    ensure_assigned_staff_or_admin(signal, current_user)

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

    ensure_admin_or_supervisor(current_user)

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