from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    payment_id = Column(String, nullable=True)  # Razorpay payment ID
    order_id = Column(String, nullable=True)   # Razorpay order ID
    signature = Column(String, nullable=True)   # Razorpay signature
    amount = Column(Integer, nullable=False)    # Amount in smallest currency unit (e.g., paise for INR)
    currency = Column(String, default="INR")    # Currency code
    status = Column(String, default="pending")  # Payment status (e.g., pending, completed, failed)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    booking = relationship("Booking", backref="payment")
