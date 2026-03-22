from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AdminReferralCodeBase(BaseModel):
    code: str
    name: str
    no_of_bookings: int = 10
    commission_percentage: float = 0.0

class AdminReferralCodeCreate(AdminReferralCodeBase):
    pass

class AdminReferralCodeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    no_of_bookings: Optional[int] = None
    commission_percentage: Optional[float] = None

class AdminReferralCodeOut(AdminReferralCodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
