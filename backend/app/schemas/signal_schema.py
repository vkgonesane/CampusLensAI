from typing import Optional
from pydantic import BaseModel


class CampusSignalCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_by: int


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

    created_by: int
    reopen_count: int

    ai_category: Optional[str]
    ai_sentiment: Optional[str]
    ai_priority: Optional[str]
    ai_summary: Optional[str]
    duplicate_score: float
    hotspot_score: float

    class Config:
        from_attributes = True