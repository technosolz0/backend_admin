from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base

class HelpCenter(Base):
    __tablename__ = "help_center"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., "General", "Payments", "Bookings"
    is_for_vendor = Column(Boolean, default=True)
    is_for_user = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<HelpCenter(id={self.id}, question='{self.question[:30]}...', vendor={self.is_for_vendor}, user={self.is_for_user})>"
