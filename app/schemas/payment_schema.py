# from pydantic import BaseModel
# from datetime import datetime
# from typing import Optional


# class PaymentCreate(BaseModel):
#     booking_id: int
#     payment_id: Optional[str] = None
#     order_id: Optional[str] = None
#     signature: Optional[str] = None
#     amount: int
#     currency: str = "INR"
#     status: str = "pending"


# class PaymentOut(BaseModel):
#     id: int
#     booking_id: int
#     payment_id: Optional[str]
#     order_id: Optional[str]
#     signature: Optional[str]
#     amount: int
#     currency: str
#     status: str
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True



# mac changes 


# payment_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    RAZORPAY = "razorpay"
    CASH = "cash"
    WALLET = "wallet"

class PaymentCreate(BaseModel):
    booking_id: int
    amount: float = Field(..., gt=0, description="Payment amount must be greater than 0")
    currency: str = Field(default="INR", description="Payment currency")
    payment_method: PaymentMethod = PaymentMethod.RAZORPAY
    razorpay_order_id: Optional[str] = None
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None
    failure_reason: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    failure_reason: Optional[str] = None

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    notes: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentSearchResponse(BaseModel):
    payments: List[PaymentOut]
    total: int
    filters_applied: Dict[str, Any]

class PaymentAnalyticsResponse(BaseModel):
    total_payments: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    success_rate: float
    total_revenue: float
    pending_revenue: float
    average_payment_amount: float
    recent_payments: List[PaymentOut]

# Razorpay specific schemas
class OrderCreate(BaseModel):
    amount: int  # Amount in rupees
    currency: str = "INR"
    booking_id: int
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    key: str
    amount: int
    currency: str
    booking_id: int

class WebhookPayment(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    status: str

# Additional response models
class MonthlyRevenueData(BaseModel):
    month: int
    revenue: float
    payment_count: int
    average_payment: float

class MonthlyRevenueResponse(BaseModel):
    year: int
    monthly_data: List[MonthlyRevenueData]
    total_annual_revenue: float
    total_payments: int

class PaymentFailureDetails(BaseModel):
    payment_id: int
    booking_id: int
    amount: float
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    failure_reason: Optional[str]
    failed_at: Optional[datetime]
    retry_count: int