# app/schemas/delete_request_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeleteRequestCreate(BaseModel):
    user_id: Optional[int] = None
    vendor_id: Optional[int] = None
    reason: str
    role: str   # "user" / "vendor"

class DeleteRequestResponse(BaseModel):
    id: int
    user_id: Optional[int]
    vendor_id: Optional[int]
    name: str
    phone: str
    reason: str
    role: str
    request_date: datetime

    class Config:
        from_attributes = True
