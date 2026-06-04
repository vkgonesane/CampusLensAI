from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.user_schema import UserListResponse
from app.services.user_service import get_all_users
from app.utils.auth_dependencies import require_roles


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/", response_model=list[UserListResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin"]))
):
    return get_all_users(db)