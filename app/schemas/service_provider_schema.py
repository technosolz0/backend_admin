from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# 🔹 Shared Base Schema
class ServiceProviderBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    category_id: int
    sub_category_id: Optional[int]
    service_ids: List[int] = Field(default_factory=list)
    service_locations: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    road: Optional[str] = None
    landmark: Optional[str] = None
    pin_code: Optional[str] = None
    experience_years: Optional[int] = None
    about: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    profile_pic_path: Optional[str] = None
    address_proof_path: Optional[str] = None
    bank_statement_path: Optional[str] = None

    class Config:
        from_attributes = True


# 🔸 Create Schema (for registration)
class ServiceProviderCreate(ServiceProviderBase):
    password: str


# 🔹 Update Schema (optional fields)
class ServiceProviderUpdate(BaseModel):
    full_name: Optional[str]
    phone: Optional[str]
    category_id: Optional[int]
    sub_category_id: Optional[int]
    service_ids: Optional[List[int]]
    service_locations: Optional[List[str]]
    address: Optional[str]
    road: Optional[str]
    landmark: Optional[str]
    pin_code: Optional[str]
    experience_years: Optional[int]
    about: Optional[str]
    bank_name: Optional[str]
    account_name: Optional[str]
    account_number: Optional[str]
    ifsc_code: Optional[str]
    profile_pic_path: Optional[str]
    address_proof_path: Optional[str]
    bank_statement_path: Optional[str]


# 🔸 Output Schema
class ServiceProviderOut(ServiceProviderBase):
    id: int
    status: str
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime


# 🔹 OTP Request Schema
class VendorOTPRequest(BaseModel):
    email: EmailStr


# 🔹 OTP Verification Schema
class VendorOTPVerify(BaseModel):
    email: EmailStr
    otp: str


# 🔹 Reset Password Schema
class VendorResetPassword(BaseModel):
    email: EmailStr
    new_password: str
