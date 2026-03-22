
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ReportStatus(str, enum.Enum):
    pending = "pending"
    investigating = "investigating"
    resolved = "resolved"
    dismissed = "dismissed"

class ReportRole(str, enum.Enum):
    user = "user"
    vendor = "vendor"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, nullable=False) # User ID or Vendor ID
    reporter_role = Column(SAEnum(ReportRole), nullable=False)
    
    reported_id = Column(Integer, nullable=False) # User ID or Vendor ID
    reported_role = Column(SAEnum(ReportRole), nullable=False)
    
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    
    reason = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    status = Column(SAEnum(ReportStatus), default=ReportStatus.pending)
    admin_comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", backref="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, reporter={self.reporter_role}:{self.reporter_id}, reported={self.reported_role}:{self.reported_id})>"
