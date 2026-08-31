from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from datetime import datetime
from app.database import Base

class AppConfig(Base):
    __tablename__ = "app_configs"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, default="android", nullable=False)  # 'android', 'ios', 'all'
    latest_version = Column(String, default="1.0.0", nullable=False)
    min_supported_version = Column(String, default="1.0.0", nullable=False)
    force_update = Column(Boolean, default=False, nullable=False)
    play_store_url = Column(String, nullable=True)
    app_store_url = Column(String, nullable=True)
    update_message = Column(String, default="A new version of Serwex is available. Please update to continue.", nullable=True)
    referrer_reward_amount = Column(Float, default=100.0, nullable=False)
    referred_vendor_reward_amount = Column(Float, default=50.0, nullable=False)
    user_referrer_reward_amount = Column(Float, default=50.0, nullable=False)
    user_referred_reward_amount = Column(Float, default=50.0, nullable=False)
    min_referral_reward = Column(Float, default=5.0, nullable=False)
    max_referral_reward = Column(Float, default=40.0, nullable=False)
    is_random_referral_reward = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

