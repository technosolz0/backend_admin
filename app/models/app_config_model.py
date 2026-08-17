from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
