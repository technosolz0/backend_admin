from sqlalchemy import Column, Integer, String, Float, DateTime
import datetime
from app.database import Base

class AdminReferralCode(Base):
    __tablename__ = "admin_referral_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)  # Name of the campaign or code
    no_of_bookings = Column(Integer, default=10, nullable=False)
    commission_percentage = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
