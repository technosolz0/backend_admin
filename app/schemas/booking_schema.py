from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class BookingStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    cancelled = "cancelled"
    completed = "completed"

class BookingCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    serviceprovider_id: int = Field(..., description="Service Provider ID")
    category_id: int = Field(..., description="Category ID")
    subcategory_id: int = Field(..., description="Subcategory ID")
    scheduled_time: datetime = Field(..., description="Scheduled datetime for booking")
    address: str = Field(..., description="Booking address")
    status: Optional[BookingStatus] = Field(BookingStatus.pending, description="Booking status")

class BookingUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    address: Optional[str] = None

class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    otp: Optional[str] = None
    notes: Optional[str] = None

class BookingOut(BaseModel):
    id: int
    user_id: int
    serviceprovider_id: int
    category_id: int
    subcategory_id: int
    category_name: Optional[str]   # ✅ extra field
    subcategory_name: Optional[str]  # ✅ extra field
    scheduled_time: datetime
    address: str
    status: BookingStatus
    created_at: datetime
    otp: Optional[str] = None
    otp_created_at: Optional[datetime] = None
    model_config = {
        "from_attributes": True
    }

    class Config:
        from_attributes = True

class BookingSearchResponse(BaseModel):
    bookings: List[BookingOut]
    total: int
    filters_applied: Dict[str, Any]

class BookingStatsResponse(BaseModel):
    total_bookings: int
    status_counts: Dict[str, int]
    recent_bookings: List[BookingOut]
