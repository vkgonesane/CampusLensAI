from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CampusSignalCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CampusSignalStatusUpdate(BaseModel):
    status: str
    department: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    resolution_note: Optional[str] = None
    supervisor_note: Optional[str] = None


class SignalReviewRequest(BaseModel):
    note: Optional[str] = None


class SignalAssignRequest(BaseModel):
    department: str
    assigned_staff_id: int
    supervisor_id: Optional[int] = None
    note: Optional[str] = None


class SignalStartWorkRequest(BaseModel):
    note: Optional[str] = None


class SignalMarkFixedRequest(BaseModel):
    resolution_note: str


class SignalSupervisorReviewRequest(BaseModel):
    supervisor_note: Optional[str] = None


class SignalCloseRequest(BaseModel):
    supervisor_note: str


class CampusSignalReopenRequest(BaseModel):
    reason: str


class CampusSignalResponse(BaseModel):
    id: int
    title: str
    description: str
    category: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    status: str
    priority: str
    department: Optional[str]
    suggested_department: Optional[str]

    created_by: int
    assigned_staff_id: Optional[int]
    supervisor_id: Optional[int]

    resolution_note: Optional[str]
    supervisor_note: Optional[str]

    reopen_count: int
    reopen_reason: Optional[str]

    ai_category: Optional[str]
    ai_sentiment: Optional[str]
    ai_priority: Optional[str]
    ai_summary: Optional[str]
    duplicate_score: float
    hotspot_score: float

    class Config:
        from_attributes = True


class PaginatedSignalsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: list[CampusSignalResponse]


class SignalActivityResponse(BaseModel):
    id: int
    signal_id: int
    actor_id: int
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    note: Optional[str]
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class SignalAttachmentResponse(BaseModel):
    id: int
    signal_id: int
    uploaded_by: int
    original_filename: str
    stored_filename: str
    file_path: str
    content_type: str
    file_size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class SignalCommentCreate(BaseModel):
    comment: str


class SignalCommentResponse(BaseModel):
    id: int
    signal_id: int
    author_id: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True