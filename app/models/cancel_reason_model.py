from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CancelReason(Base):
    __tablename__ = "cancel_reasons"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    reason = Column(String, nullable=False)
    cancelled_by = Column(String, nullable=False)  # 'user' or 'vendor'
    cancelled_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", backref="cancel_reasons")
