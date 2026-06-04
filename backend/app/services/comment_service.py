from sqlalchemy.orm import Session

from app.models.campus_signal import CampusSignal
from app.models.signal_comment import SignalComment
from app.models.user import User
from app.schemas.signal_schema import SignalCommentCreate
from app.services.activity_service import create_activity
from app.services.notification_service import notify_comment_added


def create_signal_comment(
    signal_id: int,
    comment_data: SignalCommentCreate,
    db: Session,
    current_user: User
):
    signal = (
        db.query(CampusSignal)
        .filter(CampusSignal.id == signal_id)
        .first()
    )

    comment = SignalComment(
        signal_id=signal_id,
        author_id=current_user.id,
        comment=comment_data.comment
    )

    db.add(comment)
    db.flush()

    create_activity(
        db=db,
        signal_id=signal_id,
        actor_id=current_user.id,
        action="note_added",
        note=comment_data.comment,
        metadata={
            "comment_id": comment.id
        }
    )

    if signal and signal.created_by != current_user.id:
        notify_comment_added(
            db=db,
            user_id=signal.created_by,
            signal_title=signal.title,
            commenter_name=current_user.full_name
        )

    db.commit()
    db.refresh(comment)

    return comment


def get_signal_comments(
    signal_id: int,
    db: Session
):
    return (
        db.query(SignalComment)
        .filter(SignalComment.signal_id == signal_id)
        .order_by(SignalComment.created_at.asc())
        .all()
    )