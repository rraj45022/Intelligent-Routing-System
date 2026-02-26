from pydantic import BaseModel, EmailStr

from backend.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str
    role: UserRole = UserRole.agent


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
