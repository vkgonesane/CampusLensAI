from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.auth_schema import UserRegister, UserLogin, TokenResponse
from app.services.auth_service import register_user, login_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(user_data, db)

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    return login_user(
        email=login_data.email,
        password=login_data.password,
        db=db
    )