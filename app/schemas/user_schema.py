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
    referral_code: Optional[str] = None
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
    email: Optional[str] = None
    mobile: Optional[str] = None
    otp: Optional[str] = None
    referral_code: Optional[str] = None


class OTPResend(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str
    new_fcm_token: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None
    otp: Optional[str] = None
    new_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    status: UserStatus
    is_verified: bool
    is_superuser: bool
    referral_code: Optional[str] = None
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


class UserReferralValidateRequest(BaseModel):
    referral_code: str


class UserReferralValidateResponse(BaseModel):
    valid: bool
    message: str
    referral_type: Optional[str] = None
    referrer_name: Optional[str] = None


class UserReferralItem(BaseModel):
    id: int
    referred_user_name: str
    status: str
    created_at: datetime
    qualification_date: Optional[datetime] = None
    reward_amount: float


class UserReferralStatsResponse(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    registered_count: int
    successful_count: int
    pending_count: int
    total_rewards: float
    referrals: list[UserReferralItem] = []

