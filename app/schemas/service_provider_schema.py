from pydantic import BaseModel, Field
from typing import List, Optional

class SubCategoryCharge(BaseModel):
    subcategory_id: int
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
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None
    # No step here - set in CRUD (initial 0)

class AddressDetailsUpdate(BaseModel):
    address: str
    state: str
    city: str
    pincode: str
    address_doc_type: str
    address_doc_number: str
    # No step - CRUD handles internally

class BankDetailsUpdate(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    upi_id: str
    bank_doc_type: str
    bank_doc_number: str
    # No step - CRUD handles internally

class WorkDetailsUpdate(BaseModel):
    category_id: int
    subcategory_charges: List[SubCategoryCharge]
    # No step - CRUD handles internally

class VendorDeviceUpdate(BaseModel):
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_name: Optional[str] = None
    # No step - CRUD handles internally

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
    identity_doc_type: Optional[str] = None
    identity_doc_number: Optional[str] = None
    identity_doc_url: Optional[str] = None
    bank_doc_type: Optional[str] = None
    bank_doc_number: Optional[str] = None
    bank_doc_url: Optional[str] = None
    address_doc_type: Optional[str] = None
    address_doc_number: Optional[str] = None
    address_doc_url: Optional[str] = None
    category_id: Optional[int] = None
    profile_pic: Optional[str] = None
    step: Optional[int] = None  # Include step (0-5)
    status: str = Field(..., pattern="^(pending|approved|rejected|inactive)$")
    admin_status: str = Field(..., pattern="^(active|inactive)$")
    work_status: str = Field(..., pattern="^(work_on|work_off)$")
    subcategory_charges: List[SubCategoryCharge]

    class Config:
        from_attributes = True

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

class VendorLoginRequest(BaseModel):
    email: str
    password: str