from pydantic import BaseModel
from typing import Optional

class UserAddressBase(BaseModel):
    name: str
    phone: str
    address: str
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    address_type: Optional[str] = "Home"  # Home, Work, Other
    is_default: Optional[bool] = False

class UserAddressCreate(UserAddressBase):
    pass

class UserAddressUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    address_type: Optional[str] = None
    is_default: Optional[bool] = None

class UserAddressOut(UserAddressBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }
