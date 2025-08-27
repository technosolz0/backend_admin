

from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class UserStatus(str, Enum):
    active = "active"
    blocked = "blocked"


class UserBase(BaseModel):
    name: str
    email: EmailStr
    mobile: str


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    status: Optional[UserStatus] = None


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class OTPResend(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    status: UserStatus
    is_verified: bool

    model_config = {
        "from_attributes": True
    }
