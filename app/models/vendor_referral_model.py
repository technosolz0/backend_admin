from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import enum

class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    REGISTERED = "REGISTERED"
    QUALIFIED = "QUALIFIED"
    REWARDED = "REWARDED"
    CANCELLED = "CANCELLED"

class VendorReferral(Base):
    __tablename__ = "vendor_referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    referred_vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, unique=True, index=True)
    referral_code = Column(String, nullable=False)
    status = Column(SAEnum(ReferralStatus), default=ReferralStatus.REGISTERED, nullable=False)
    referrer_reward_amount = Column(Float, default=100.0, nullable=False)
    referred_vendor_reward_amount = Column(Float, default=50.0, nullable=False)
    qualified_booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    rewarded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    referrer = relationship("Vendor", foreign_keys=[referrer_vendor_id], backref="referrals_sent")
    referred = relationship("Vendor", foreign_keys=[referred_vendor_id], backref="referral_received")
    qualified_booking = relationship("Booking", backref="referral_qualification")
