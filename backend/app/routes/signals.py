from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.user import User
from app.schemas.signal_schema import (
    CampusSignalCreate,
    CampusSignalResponse,
    CampusSignalStatusUpdate,
    CampusSignalReopenRequest,
    SignalActivityResponse,
    SignalAttachmentResponse,
    SignalCommentCreate,
    SignalCommentResponse,
    PaginatedSignalsResponse,
    SignalAssignRequest,
    SignalCloseRequest,
    SignalMarkFixedRequest,
    SignalReviewRequest,
    SignalStartWorkRequest,
    SignalSupervisorReviewRequest
)
from app.services import signal_service
from app.services.activity_service import get_signal_activities
from app.services.attachment_service import (
    get_signal_attachments,
    upload_signal_attachment
)
from app.services.comment_service import (
    create_signal_comment,
    get_signal_comments
)
from app.utils.auth_dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/signals",
    tags=["Campus Signals"]
)


@router.post("/", response_model=CampusSignalResponse)
def create_signal(
    signal_data: CampusSignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["user"]))
):
    return signal_service.create_signal(
        signal_data=signal_data,
        db=db,
        current_user=current_user
    )


@router.get("/", response_model=PaginatedSignalsResponse)
def get_all_signals(
    page: int = 1,
    per_page: int = 10,
    status: str | None = None,
    priority: str | None = None,
    department: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return signal_service.get_all_signals(
        db=db,
        current_user=current_user,
        page=page,
        per_page=per_page,
        status_filter=status,
        priority_filter=priority,
        department_filter=department
    )


@router.get("/{signal_id}", response_model=CampusSignalResponse)
def get_signal_by_id(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )


@router.get("/{signal_id}/activity", response_model=list[SignalActivityResponse])
def get_signal_activity(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )

    return get_signal_activities(
        db=db,
        signal_id=signal_id
    )


@router.post("/{signal_id}/attachments", response_model=SignalAttachmentResponse)
def upload_attachment(
    signal_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )

    return upload_signal_attachment(
        signal_id=signal_id,
        file=file,
        db=db,
        current_user=current_user
    )


@router.get("/{signal_id}/attachments", response_model=list[SignalAttachmentResponse])
def list_attachments(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )

    return get_signal_attachments(
        signal_id=signal_id,
        db=db
    )


@router.post("/{signal_id}/comments", response_model=SignalCommentResponse)
def create_comment(
    signal_id: int,
    comment_data: SignalCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )

    return create_signal_comment(
        signal_id=signal_id,
        comment_data=comment_data,
        db=db,
        current_user=current_user
    )


@router.get("/{signal_id}/comments", response_model=list[SignalCommentResponse])
def list_comments(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signal_service.get_signal_by_id(
        signal_id=signal_id,
        db=db,
        current_user=current_user
    )

    return get_signal_comments(
        signal_id=signal_id,
        db=db
    )


@router.put("/{signal_id}/review", response_model=CampusSignalResponse)
def review_signal(
    signal_id: int,
    review_data: SignalReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "supervisor"]))
):
    return signal_service.review_signal(
        signal_id=signal_id,
        review_data=review_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/assign", response_model=CampusSignalResponse)
def assign_signal(
    signal_id: int,
    assign_data: SignalAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "supervisor"]))
):
    return signal_service.assign_signal(
        signal_id=signal_id,
        assign_data=assign_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/start-work", response_model=CampusSignalResponse)
def start_work(
    signal_id: int,
    start_data: SignalStartWorkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "department_staff"]))
):
    return signal_service.start_work(
        signal_id=signal_id,
        start_data=start_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/mark-fixed", response_model=CampusSignalResponse)
def mark_fixed(
    signal_id: int,
    fixed_data: SignalMarkFixedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "department_staff"]))
):
    return signal_service.mark_fixed(
        signal_id=signal_id,
        fixed_data=fixed_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/send-to-supervisor", response_model=CampusSignalResponse)
def send_to_supervisor_review(
    signal_id: int,
    review_data: SignalSupervisorReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "department_staff"]))
):
    return signal_service.send_to_supervisor_review(
        signal_id=signal_id,
        review_data=review_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/close", response_model=CampusSignalResponse)
def close_signal(
    signal_id: int,
    close_data: SignalCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "supervisor"]))
):
    return signal_service.close_signal(
        signal_id=signal_id,
        close_data=close_data,
        db=db,
        current_user=current_user
    )


@router.put("/{signal_id}/status", response_model=CampusSignalResponse)
def update_signal_status(
    signal_id: int,
    update_data: CampusSignalStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(["admin", "department_staff", "supervisor"])
    )
):
    return signal_service.update_signal_status(
        signal_id=signal_id,
        update_data=update_data,
        db=db,
        current_user=current_user
    )


@router.post("/{signal_id}/reopen", response_model=CampusSignalResponse)
def reopen_signal(
    signal_id: int,
    reopen_data: CampusSignalReopenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["user"]))
):
    return signal_service.reopen_signal(
        signal_id=signal_id,
        reopen_data=reopen_data,
        db=db,
        current_user=current_user
    )