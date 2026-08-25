

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship, synonym
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
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    serviceprovider_id = synonym("vendor_id")
    service_provider_id = synonym("vendor_id")

    category_id = Column(Integer, ForeignKey("categories.id"))
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))
    scheduled_time = Column(DateTime, nullable=True)
    address = Column(String, nullable=False)  # Add this field
    booking_latitude = Column(Float, nullable=True)
    booking_longitude = Column(Float, nullable=True)
    tracking_status = Column(String, default="NOT_STARTED")
    tracking_started_at = Column(DateTime, nullable=True)
    vendor_arrived_at = Column(DateTime, nullable=True)
    tracking_ended_at = Column(DateTime, nullable=True)
    latest_vendor_latitude = Column(Float, nullable=True)
    latest_vendor_longitude = Column(Float, nullable=True)
    latest_vendor_location_updated_at = Column(DateTime, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookings")
    vendor = relationship("Vendor", backref="bookings")

    @property
    def service_provider(self):
        return self.vendor

    @service_provider.setter
    def service_provider(self, value):
        self.vendor = value


    category = relationship("Category", backref="bookings")
    subcategory = relationship("SubCategory", backref="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    reviews = relationship(
    "Review",
    back_populates="booking",
    cascade="all, delete-orphan"
    )
