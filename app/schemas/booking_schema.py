# # app/schemas/booking_schema.py
# from pydantic import BaseModel, EmailStr
# from datetime import datetime
# from typing import Optional
# from enum import Enum


# class BookingStatus(str, Enum):
#     pending = "pending"
#     accepted = "accepted"
#     cancelled = "cancelled"
#     completed = "completed"


# class BookingCreate(BaseModel):
#     user_id: int
#     serviceprovider_id: int
#     category_id: int
#     subcategory_id: int
#     service_id: int
#     scheduled_time: Optional[datetime]


# class BookingOut(BaseModel):
#     id: int
#     user_id: int
#     serviceprovider_id: int
#     category_id: int
#     subcategory_id: int
#     service_id: int
#     scheduled_time: Optional[datetime]
#     status: BookingStatus
#     created_at: datetime

#     class Config:
#         orm_mode = True


from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.booking_model import BookingStatus


class BookingCreate(BaseModel):
    user_id: int
    serviceprovider_id: int
    category_id: int
    subcategory_id: int
    scheduled_time: Optional[datetime] = None
    status: Optional[BookingStatus] = BookingStatus.pending


class BookingOut(BaseModel):
    id: int
    user_id: int
    serviceprovider_id: int
    category_id: int
    subcategory_id: int
    scheduled_time: Optional[datetime]
    status: BookingStatus
    created_at: datetime
    otp: Optional[str]
    otp_created_at: Optional[datetime]

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    otp: Optional[str] = None  # Only required for 'completed'
