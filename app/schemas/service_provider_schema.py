

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BankAccountBase(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None

class BankAccountCreate(BankAccountBase):
    is_primary: bool = False

class BankAccountUpdate(BaseModel):
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_primary: Optional[bool] = None

class BankAccountOut(BankAccountBase):
    id: int
    vendor_id: int
    is_primary: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubCategoryCharge(BaseModel):
    subcategory_id: int
    subcategory_name: Optional[str] = None
    service_charge: float

    class Config:
        from_attributes = True

class VendorCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    terms_accepted: bool
    identity_doc_type: str
    identity_doc_number: str
    new_fcm_token: Optional[str] = None
    old_fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None

class AddressDetailsUpdate(BaseModel):
    address: str
    state: str
    city: str
    pincode: str
    address_doc_type: str
    address_doc_number: str

class BankDetailsUpdate(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    upi_id: str
    bank_doc_type: str
    bank_doc_number: str

class WorkDetailsUpdate(BaseModel):
    category_id: int
    subcategory_charges: List[SubCategoryCharge]

class VendorDeviceUpdate(BaseModel):
    new_fcm_token: Optional[str] = None
    old_fcm_token: Optional[str] = None
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
    bank_doc_type: Optional[str] = None
    bank_doc_number: Optional[str] = None
    bank_doc_url: Optional[str] = None



    identity_doc_type: Optional[str] = None
    identity_doc_number: Optional[str] = None
    identity_doc_url: Optional[str] = None
    address_doc_type: Optional[str] = None
    address_doc_number: Optional[str] = None
    address_doc_url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    profile_pic: Optional[str] = None
    step: Optional[int] = None
    status: str = Field(..., pattern="^(pending|approved|rejected|inactive)$")
    admin_status: str = Field(..., pattern="^(active|inactive)$")
    work_status: str = Field(..., pattern="^(work_on|work_off)$")
    subcategory_charges: List[SubCategoryCharge]
    bank_accounts: List[BankAccountOut] = []

    class Config:
        from_attributes = True

class PaginatedVendorsResponse(BaseModel):
    vendors: List[VendorResponse]
    total: int

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

class VendorLoginRequest(BaseModel):
    email: str
    password: str

class VendorLogoutRequest(BaseModel):
    email: str

class VendorChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
