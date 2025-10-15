from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime


class UserStatus(str, Enum):
    active = "active"
    blocked = "blocked"


class UserBase(BaseModel):
    name: str
    email: EmailStr
    mobile: str


class UserCreate(UserBase):
    password: str
    profile_pic: Optional[str] = None
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    status: Optional[UserStatus] = None
    is_superuser: Optional[bool] = None
    profile_pic: Optional[str] = None
    old_fcm_token: Optional[str] = None
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class OTPVerify(BaseModel):
    email: str
    otp: str


class OTPResend(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    email: str
    otp: str
    new_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    status: UserStatus
    is_verified: bool
    is_superuser: bool
    profile_pic: Optional[str] = None
    old_fcm_token: Optional[str] = None
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    model_config = {"from_attributes": True}
