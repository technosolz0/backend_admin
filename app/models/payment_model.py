# # app/models/payment_model.py
# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.database import Base
# from app.schemas.payment_schema import PaymentStatus, PaymentMethod


# class Payment(Base):
#     __tablename__ = "payments"

#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)

#     # Razorpay fields
#     razorpay_payment_id = Column(String, nullable=True)
#     razorpay_order_id = Column(String, nullable=True)
#     razorpay_signature = Column(String, nullable=True)

#     # Payment details
#     amount = Column(Integer, nullable=False)
#     currency = Column(String, default="INR")
#     payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.RAZORPAY)
#     status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

#     notes = Column(Text, nullable=True)
#     failure_reason = Column(String, nullable=True)
#     retry_count = Column(Integer, default=0)

#     # Timestamps
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     paid_at = Column(DateTime, nullable=True)
#     failed_at = Column(DateTime, nullable=True)

#     # Relationship
#     booking = relationship("Booking", back_populates="payments")



# app/models/payment_model.py - FIXED
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.schemas.payment_schema import PaymentStatus, PaymentMethod


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)

    # Razorpay fields
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)

    # Payment details - ✅ CHANGED: Float instead of Integer
    amount = Column(Float, nullable=False)  # Store in rupees (not paise)
    currency = Column(String, default="INR")
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.RAZORPAY)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    notes = Column(Text, nullable=True)
    failure_reason = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Relationship
    booking = relationship("Booking", back_populates="payments")