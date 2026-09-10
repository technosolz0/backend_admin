from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommissionTierBase(BaseModel):
    tier_name: str
    min_bookings: int
    max_bookings: Optional[int] = None
    commission_percentage: float
    is_active: bool = True

class CommissionTierCreate(CommissionTierBase):
    pass

class CommissionTierUpdate(BaseModel):
    tier_name: Optional[str] = None
    min_bookings: Optional[int] = None
    max_bookings: Optional[int] = None
    commission_percentage: Optional[float] = None
    is_active: Optional[bool] = None

class CommissionTierOut(CommissionTierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
