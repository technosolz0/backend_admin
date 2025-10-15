

# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from enum import Enum


# class UserStatus(str, Enum):
#     active = "active"
#     blocked = "blocked"


# class UserBase(BaseModel):
#     name: str
#     email: EmailStr
#     mobile: str


# class UserCreate(UserBase):
#     password: Optional[str] = None


# class UserUpdate(BaseModel):
#     name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     mobile: Optional[str] = None
#     password: Optional[str] = None
#     status: Optional[UserStatus] = None


# class OTPVerify(BaseModel):
#     email: EmailStr
#     otp: str


# class OTPResend(BaseModel):
#     email: EmailStr


# class UserOut(BaseModel):
#     id: int
#     name: str
#     email: EmailStr
#     mobile: str
#     status: UserStatus
#     is_verified: bool

#     model_config = {
#         "from_attributes": True
#     }


# app/schemas/user_schema.py - Updated with PasswordResetRequest and PasswordResetConfirm
# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from enum import Enum


# class UserStatus(str, Enum):
#     active = "active"
#     blocked = "blocked"


# class UserBase(BaseModel):
#     name: str
#     email: EmailStr
#     mobile: str


# class UserCreate(UserBase):
#     password: str  # Make password required for registration


# class UserUpdate(BaseModel):
#     name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     mobile: Optional[str] = None
#     password: Optional[str] = None
#     status: Optional[UserStatus] = None
#     fcm_token: Optional[str] = None  # FCM token update


# class OTPVerify(BaseModel):
#     email: EmailStr
#     otp: str


# class OTPResend(BaseModel):
#     email: EmailStr


# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str


# # Password Reset Schemas
# class PasswordResetRequest(BaseModel):
#     email: EmailStr


# class PasswordResetConfirm(BaseModel):
#     email: EmailStr
#     otp: str
#     new_password: str


# class UserOut(BaseModel):
#     id: int
#     name: str
#     email: EmailStr
#     mobile: str
#     status: UserStatus
#     is_verified: bool
#     fcm_token: Optional[str] = None  # Include FCM token in response

#     model_config = {
#         "from_attributes": True
#     }


from pydantic import BaseModel, EmailStr, HttpUrl, validator
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
    profile_pic: Optional[HttpUrl] = None  # Validate as URL
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    status: Optional[UserStatus] = None
    is_superuser: Optional[bool] = None  # For admin updates
    profile_pic: Optional[HttpUrl] = None
    old_fcm_token: Optional[str] = None
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class OTPResend(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    status: UserStatus
    is_verified: bool
    is_superuser: bool  # Include for admin visibility
    profile_pic: Optional[HttpUrl] = None
    old_fcm_token: Optional[str] = None
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    model_config = {
        "from_attributes": True
    }