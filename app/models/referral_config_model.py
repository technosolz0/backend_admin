from sqlalchemy import Column, Integer, Float, Boolean, DateTime
import datetime
from app.database import Base

class ReferralConfig(Base):
    __tablename__ = "referral_configs"

    id = Column(Integer, primary_key=True, index=True)
    referrer_reward_amount = Column(Float, default=100.0, nullable=False)
    referred_vendor_reward_amount = Column(Float, default=50.0, nullable=False)
    user_referrer_reward_amount = Column(Float, default=50.0, nullable=False)
    user_referred_reward_amount = Column(Float, default=50.0, nullable=False)
    min_referral_reward = Column(Float, default=5.0, nullable=False)
    max_referral_reward = Column(Float, default=40.0, nullable=False)
    is_random_referral_reward = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
