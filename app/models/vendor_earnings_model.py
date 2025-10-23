from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class VendorEarnings(Base):
    __tablename__ = "vendor_earnings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    total_paid = Column(Float, nullable=False)  # amount paid by user
    commission_percentage = Column(Float, default=10.0)
    commission_amount = Column(Float, nullable=False)
    final_amount = Column(Float, nullable=False)  # total_paid - commission_amount
    earned_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", backref="vendor_earnings")
    vendor = relationship("ServiceProvider", backref="vendor_earnings")
