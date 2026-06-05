from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        is_read=False
    )

    db.add(notification)
    return notification


def notify_signal_assigned(
    db: Session,
    user_id: int,
    signal_title: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="New Signal Assigned",
        message=f"'{signal_title}' has been assigned to you."
    )


def notify_signal_closed(
    db: Session,
    user_id: int,
    signal_title: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="Signal Closed",
        message=f"Your signal '{signal_title}' has been resolved and closed."
    )


def notify_signal_reopened(
    db: Session,
    user_id: int,
    signal_title: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="Signal Reopened",
        message=f"Signal '{signal_title}' has been reopened and needs review."
    )


def notify_signal_ready_for_review(
    db: Session,
    user_id: int,
    signal_title: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="Signal Ready for Supervisor Review",
        message=f"Signal '{signal_title}' is ready for supervisor review."
    )


def notify_sla_breached(
    db: Session,
    user_id: int,
    signal_title: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="SLA Breached",
        message=f"Signal '{signal_title}' has breached its SLA deadline and requires escalation."
    )


def notify_comment_added(
    db: Session,
    user_id: int,
    signal_title: str,
    commenter_name: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="New Comment Added",
        message=f"{commenter_name} commented on your signal '{signal_title}'."
    )


def notify_attachment_uploaded(
    db: Session,
    user_id: int,
    signal_title: str,
    uploader_name: str
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="New Evidence Uploaded",
        message=f"{uploader_name} uploaded evidence for '{signal_title}'."
    )


def get_my_notifications(
    db: Session,
    current_user: User
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def get_unread_count(
    db: Session,
    current_user: User
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .filter(Notification.is_read == False)
        .count()
    )


def mark_notification_as_read(
    notification_id: int,
    db: Session,
    current_user: User
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == current_user.id)
        .first()
    )

    if not notification:
        return None

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification