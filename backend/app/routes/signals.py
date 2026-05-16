from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.campus_signal import CampusSignal
from app.schemas.signal_schema import CampusSignalCreate, CampusSignalResponse
from app.ai.ai_service import analyze_signal


router = APIRouter(
    prefix="/signals",
    tags=["Campus Signals"]
)


@router.post("/", response_model=CampusSignalResponse)
def create_signal(signal_data: CampusSignalCreate, db: Session = Depends(get_db)):
    previous_signal_rows = db.query(CampusSignal.description).all()

    previous_descriptions = [
        row[0] for row in previous_signal_rows
    ]

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
        location_signal_count=location_signal_count
    )

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

        created_by=signal_data.created_by,

        ai_category=ai_result["ai_category"],
        ai_sentiment=ai_result["ai_sentiment"],
        ai_priority=ai_result["ai_priority"],
        ai_summary=ai_result["ai_summary"],
        duplicate_score=ai_result["duplicate_score"],
        hotspot_score=ai_result["hotspot_score"]
    )

    db.add(new_signal)
    db.commit()
    db.refresh(new_signal)

    return new_signal