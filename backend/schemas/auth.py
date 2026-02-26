from pydantic import BaseModel, EmailStr

from backend.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    role: UserRole | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: UserRole

    class Config:
        from_attributes = True
