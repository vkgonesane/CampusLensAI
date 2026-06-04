from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services import analytics_service
from app.utils.auth_dependencies import require_roles


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/overview")
def analytics_overview(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_analytics_overview(db)


@router.get("/status-breakdown")
def status_breakdown(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_status_breakdown(db)


@router.get("/priority-breakdown")
def priority_breakdown(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_priority_breakdown(db)


@router.get("/category-breakdown")
def category_breakdown(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_category_breakdown(db)


@router.get("/department-breakdown")
def department_breakdown(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_department_breakdown(db)


@router.get("/hotspots")
def hotspots(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "supervisor"]))
):
    return analytics_service.get_hotspots(db)