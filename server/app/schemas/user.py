from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=72, description="비밀번호 (4-72자)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_image: Optional[str] = None

class UserResponse(UserBase):
    id: str
    profile_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
