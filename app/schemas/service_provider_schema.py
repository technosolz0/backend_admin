from pydantic import BaseModel
from typing import Optional, List

class ServiceProviderBase(BaseModel):
    category: str
    service_locations: List[str]
    address: str
    road: Optional[str] = None
    landmark: Optional[str] = None
    pin_code: Optional[str] = None
    experience_years: Optional[int] = None
    about: Optional[str] = None
    bank_name: str
    account_name: str
    account_number: str
    ifsc_code: str

    model_config = {
        "from_attributes": True
    }

class ServiceProviderCreate(ServiceProviderBase):
    pass

class ServiceProviderOut(ServiceProviderBase):
    id: int
    user_id: int
    profile_pic_path: str
    address_proof_path: str
    bank_statement_path: str
