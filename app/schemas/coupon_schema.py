from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CouponCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    min_order_value: Optional[float] = None
    expiry_date: datetime
    active: Optional[bool] = True

class CouponOut(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    min_order_value: Optional[float]
    expiry_date: datetime
    active: bool
    created_at: datetime
