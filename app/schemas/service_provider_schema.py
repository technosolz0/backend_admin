from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class ServiceProviderBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    category_id: int
    sub_category_id: Optional[int] = None
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
    work_status: Optional[str] = "offline"

    @validator("experience_years")
    def validate_experience_years(cls, v):
        if v is not None and v < 0:
            raise ValueError("Experience years cannot be negative")
        return v

    @validator("pin_code")
    def validate_pin_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError("Pin code must contain only digits")
        return v

    class Config:
        from_attributes = True

class ServiceProviderCreate(ServiceProviderBase):
    password: str

class ServiceProviderUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    service_ids: Optional[List[int]] = None
    service_locations: Optional[List[str]] = None
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
    work_status: Optional[str] = None

    @validator("experience_years")
    def validate_experience_years(cls, v):
        if v is not None and v < 0:
            raise ValueError("Experience years cannot be negative")
        return v

    @validator("pin_code")
    def validate_pin_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError("Pin code must contain only digits")
        return v

class ServiceProviderOut(ServiceProviderBase):
    id: int
    status: str
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime

class VendorOTPRequest(BaseModel):
    email: EmailStr

class VendorOTPVerify(BaseModel):
    email: EmailStr
    otp: str

class VendorResetPassword(BaseModel):
    email: EmailStr
    new_password: str