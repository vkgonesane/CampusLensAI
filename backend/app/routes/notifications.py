from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.user import User
from app.schemas.notification_schema import NotificationResponse
from app.services.notification_service import (
    get_my_notifications,
    get_unread_count,
    mark_notification_as_read
)
from app.utils.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/", response_model=list[NotificationResponse])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_my_notifications(
        db=db,
        current_user=current_user
    )


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = get_unread_count(
        db=db,
        current_user=current_user
    )

    return {
        "unread_count": count
    }


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = mark_notification_as_read(
        notification_id=notification_id,
        db=db,
        current_user=current_user
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return notification