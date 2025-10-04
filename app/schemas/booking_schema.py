

# from pydantic import BaseModel
# from datetime import datetime
# from typing import Optional
# from app.models.booking_model import BookingStatus
# from app.schemas.category_schema import CategoryOut
# from app.schemas.sub_category_schema import SubCategoryOut


# class BookingCreate(BaseModel):
#     user_id: int
#     serviceprovider_id: int
#     category_id: int
#     subcategory_id: int
#     scheduled_time: Optional[datetime] = None
#     status: Optional[BookingStatus] = BookingStatus.pending


# class BookingOut(BaseModel):
#     id: int
#     user_id: int
#     serviceprovider_id: int
#     category_id: int
#     subcategory_id: int
#     scheduled_time: Optional[datetime]
#     status: BookingStatus
#     created_at: datetime
#     otp: Optional[str]
#     otp_created_at: Optional[datetime]

#     category: CategoryOut
#     subcategory: SubCategoryOut
    

#     class Config:
#         from_attributes = True


# class BookingStatusUpdate(BaseModel):
#     status: BookingStatus
#     otp: Optional[str] = None  # Only required for 'completed'



# mac changes 
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# class BookingStatus(str, Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     IN_PROGRESS = "in_progress"
#     COMPLETED = "completed"
#     CANCELLED = "cancelled"

# class BookingCreate(BaseModel):
#     user_id: int
#     serviceprovider_id: int
#     service_id: int
#     booking_date: datetime
#     booking_time: str
#     address: str
#     notes: Optional[str] = None
#     estimated_duration: Optional[int] = None  # in minutes
#     estimated_price: Optional[float] = None

# class BookingUpdate(BaseModel):
#     booking_date: Optional[datetime] = None
#     booking_time: Optional[str] = None
#     address: Optional[str] = None
#     notes: Optional[str] = None
#     estimated_duration: Optional[int] = None
#     estimated_price: Optional[float] = None

# class BookingStatusUpdate(BaseModel):
#     status: BookingStatus
#     otp: Optional[str] = None
#     notes: Optional[str] = None

# class BookingOut(BaseModel):
#     id: int
#     user_id: int
#     serviceprovider_id: int
#     service_id: int
#     booking_date: datetime
#     booking_time: str
#     address: str
#     notes: Optional[str] = None
#     status: BookingStatus
#     estimated_duration: Optional[int] = None
#     estimated_price: Optional[float] = None
#     otp: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime
#     completed_at: Optional[datetime] = None



class BookingStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"  # Use consistent enum values from model
    cancelled = "cancelled"
    completed = "completed"

class BookingCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    serviceprovider_id: int = Field(..., description="Service Provider ID")
    category_id: int = Field(..., description="Category ID")  # Changed from service_id
    subcategory_id: int = Field(..., description="Subcategory ID")
    scheduled_time: datetime = Field(..., description="Scheduled datetime for booking")  # Combined date + time
    address: str = Field(..., description="Booking address")  # Add this (required)
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
    category_id: int  # Changed from service_id
    subcategory_id: int
    scheduled_time: datetime
    address: str  # Add this
    status: BookingStatus
    created_at: datetime
    otp: Optional[str] = None
    otp_created_at: Optional[datetime] = None


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