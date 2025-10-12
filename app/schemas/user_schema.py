

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
    password: str  # Make password required for registration


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    status: Optional[UserStatus] = None
    fcm_token: Optional[str] = None  # FCM token update


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class OTPResend(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    status: UserStatus
    is_verified: bool
    fcm_token: Optional[str] = None  # Include FCM token in response

    model_config = {
        "from_attributes": True
    }