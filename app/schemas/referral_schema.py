from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AdminReferralCodeBase(BaseModel):
    name: str
    no_of_bookings: int = 10
    commission_percentage: float = 0.0

class AdminReferralCodeCreate(AdminReferralCodeBase):
    code: Optional[str] = None  # If not provided, a unique alphanumeric code is auto-generated without special characters

class AdminReferralCodeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    no_of_bookings: Optional[int] = None
    commission_percentage: Optional[float] = None

class AdminReferralCodeOut(AdminReferralCodeBase):
    id: int
    code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
