from sqlalchemy.orm import Session

from app.models.signal_comment import SignalComment
from app.models.user import User
from app.schemas.signal_schema import SignalCommentCreate
from app.services.activity_service import create_activity


def create_signal_comment(
    signal_id: int,
    comment_data: SignalCommentCreate,
    db: Session,
    current_user: User
):
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