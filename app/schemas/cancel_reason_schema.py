from pydantic import BaseModel
from datetime import datetime

class CancelReasonCreate(BaseModel):
    booking_id: int
    reason: str
    cancelled_by: str

class CancelReasonOut(BaseModel):
    id: int
    booking_id: int
    reason: str
    cancelled_by: str
    cancelled_at: datetime

    class Config:
        from_attributes = True
