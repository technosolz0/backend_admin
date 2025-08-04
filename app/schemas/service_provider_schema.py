from pydantic import BaseModel
from typing import List, Optional
from app.models.service_provider_model import VendorStatus

class SubCategoryCharge(BaseModel):
    subcategory_id: int
    service_charge: float

class VendorCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    terms_accepted: bool
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class AddressDetailsUpdate(BaseModel):
    address: str
    state: str
    city: str
    pincode: str
    document_type: str
    document_number: str

class BankDetailsUpdate(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    upi_id: str

class WorkDetailsUpdate(BaseModel):
    category_id: int
    subcategory_charges: List[SubCategoryCharge]

class VendorDeviceUpdate(BaseModel):
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class VendorResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
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
    category_id: Optional[int] = None
    profile_pic_url: Optional[str] = None
    document_url: Optional[str] = None
    status: VendorStatus
    subcategory_charges: List[SubCategoryCharge]

    class Config:
        orm_mode = True

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str