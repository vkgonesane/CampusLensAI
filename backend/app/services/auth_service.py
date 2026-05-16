from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth_schema import UserRegister
from app.utils.security import hash_password, verify_password, create_access_token


def register_user(user_data: UserRegister, db: Session):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }