from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import enum
from app.models.vendor_referral_model import ReferralStatus

class UserReferral(Base):
    __tablename__ = "user_referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    referral_code = Column(String, nullable=False)
    status = Column(SAEnum(ReferralStatus), default=ReferralStatus.REGISTERED, nullable=False)
    referrer_reward_amount = Column(Float, default=50.0, nullable=False)
    referred_user_reward_amount = Column(Float, default=50.0, nullable=False)
    qualified_booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    rewarded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_user_id], backref="user_referrals_sent")
    referred = relationship("User", foreign_keys=[referred_user_id], backref="user_referral_received")
    qualified_booking = relationship("Booking", backref="user_referral_qualification")
