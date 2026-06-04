import os
import shutil
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.campus_signal import CampusSignal
from app.models.signal_attachment import SignalAttachment
from app.models.user import User
from app.services.activity_service import create_activity


ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp"
]

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

UPLOAD_DIRECTORY = "uploads/signals"


def upload_signal_attachment(
    signal_id: int,
    file: UploadFile,
    db: Session,
    current_user: User
):
    signal = (
        db.query(CampusSignal)
        .filter(CampusSignal.id == signal_id)
        .first()
    )

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campus Signal not found"
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )

    file_extension = os.path.splitext(file.filename)[1]

    stored_filename = f"{uuid.uuid4()}{file_extension}"

    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        stored_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    attachment = SignalAttachment(
        signal_id=signal.id,
        uploaded_by=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        content_type=file.content_type,
        file_size_bytes=file_size
    )

    db.add(attachment)
    db.flush()

    create_activity(
        db=db,
        signal_id=signal.id,
        actor_id=current_user.id,
        action="attachment_uploaded",
        note=f"Uploaded file: {file.filename}",
        metadata={
            "attachment_id": attachment.id,
            "content_type": file.content_type,
            "file_size_bytes": file_size
        }
    )

    db.commit()
    db.refresh(attachment)

    return attachment


def get_signal_attachments(
    signal_id: int,
    db: Session
):
    return (
        db.query(SignalAttachment)
        .filter(SignalAttachment.signal_id == signal_id)
        .order_by(SignalAttachment.created_at.desc())
        .all()
    )