from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PaymentCreate(BaseModel):
    booking_id: int
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    signature: Optional[str] = None
    amount: int
    currency: str = "INR"
    status: str = "pending"


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    payment_id: Optional[str]
    order_id: Optional[str]
    signature: Optional[str]
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
