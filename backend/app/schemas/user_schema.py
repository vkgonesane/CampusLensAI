from pydantic import BaseModel, EmailStr


class UserListResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True