from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from typing import Optional
from enum import Enum
from datetime import datetime

from servex_admin.backend_admin.app.models.service_provider_model import VendorStatus, WorkStatus
class SubCategoryCharge(BaseModel):
    subcategory_id: int
    service_charge: float

class ServiceProviderBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str

class ServiceProviderCreate(ServiceProviderBase):
    password: str
    category_id: Optional[int] = None
    subcategory_charges: Optional[List[SubCategoryCharge]] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    terms_accepted: bool = False
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class ServiceProviderUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_charges: Optional[List[SubCategoryCharge]] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    terms_accepted: Optional[bool] = None
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class ServiceProviderDeviceUpdate(BaseModel):
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class ServiceProviderOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    profile_pic: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    status: VendorStatus
    work_status: WorkStatus
    category_id: Optional[int] = None
    subcategory_charges: Optional[List[SubCategoryCharge]] = None
    terms_accepted: bool
    fcm_token: Optional[str] = None
    last_login: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None
    last_device_update: Optional[datetime] = None

    class Config:
        orm_mode = True

class ServiceProviderLogin(BaseModel):
    email: EmailStr
    password: str

class ServiceProviderLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vendor: ServiceProviderOut

class VendorOTPRequest(BaseModel):
    email: EmailStr

class VendorOTPVerify(BaseModel):
    email: EmailStr
    otp: str

class VendorResetPassword(BaseModel):
    email: EmailStr
    password: str