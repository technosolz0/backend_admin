from pydantic import BaseModel
from datetime import datetime

class VendorEarningsCreate(BaseModel):
    booking_id: int
    vendor_id: int
    total_paid: float
    commission_percentage: float = 10.0
    commission_amount: float
    final_amount: float

class VendorEarningsOut(BaseModel):
    id: int
    booking_id: int
    vendor_id: int
    total_paid: float
    commission_percentage: float
    commission_amount: float
    final_amount: float
    earned_at: datetime

    class Config:
        from_attributes = True
