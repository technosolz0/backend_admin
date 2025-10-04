# # app/models/booking_model.py
# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Text
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.database import Base
# from app.schemas.booking_schema import BookingStatus  # Enum for status


# class Booking(Base):
#     __tablename__ = "bookings"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     serviceprovider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    
#     category_id = Column(Integer, ForeignKey("categories.id"))
#     subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))

#     # Booking details
#     booking_date = Column(DateTime, nullable=False)
#     booking_time = Column(String, nullable=False)
#     address = Column(String, nullable=False)
#     notes = Column(Text, nullable=True)

#     # Status and OTP
#     status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
#     otp = Column(String, nullable=True)

#     # Estimates
#     estimated_duration = Column(Integer, nullable=True)  # minutes
#     estimated_price = Column(Float, nullable=True)

#     # Timestamps
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     completed_at = Column(DateTime, nullable=True)

#     # Relationships
#     user = relationship("User", backref="bookings")
#     service_provider = relationship("ServiceProvider", backref="bookings")
#     category = relationship("Category", backref="bookings")
#     subcategory = relationship("SubCategory", backref="bookings")
#     payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class BookingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    cancelled = "cancelled"
    completed = "completed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    serviceprovider_id = Column(Integer, ForeignKey("service_providers.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))
    scheduled_time = Column(DateTime, nullable=True)
    address = Column(String, nullable=False)  # Add this field
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)

    # Relationships (keep as-is)
    user = relationship("User", backref="bookings")
    service_provider = relationship("ServiceProvider", backref="bookings")
    category = relationship("Category", backref="bookings")
    subcategory = relationship("SubCategory", backref="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")