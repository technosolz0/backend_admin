

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
    serviceprovider_id = Column(Integer, ForeignKey("service_providers.id"))  # NEW_NAME: service_provider_id
    category_id = Column(Integer, ForeignKey("categories.id"))
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))
    scheduled_time = Column(DateTime, nullable=True)
    address = Column(String, nullable=False)  # Add this field
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)

    # Relationships (keep as-is)
    # user = relationship("User", backref="bookings")
    user = relationship("User", back_populates="bookings")

    service_provider = relationship("ServiceProvider", backref="bookings")
    category = relationship("Category", backref="bookings")
    subcategory = relationship("SubCategory", backref="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    reviews = relationship(
    "Review",
    back_populates="booking",
    cascade="all, delete-orphan"
    )
