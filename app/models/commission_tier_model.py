from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from app.database import Base

class CommissionTier(Base):
    __tablename__ = "commission_tiers"

    id = Column(Integer, primary_key=True, index=True)
    tier_name = Column(String, nullable=False)
    min_bookings = Column(Integer, nullable=False)
    max_bookings = Column(Integer, nullable=True)  # None represents > min_bookings (no upper bound)
    commission_percentage = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
