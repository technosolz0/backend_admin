from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "bug", "feature", "general", "complaint"
    is_resolved = Column(Boolean, default=False)
    admin_response = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    responded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="feedbacks")
    admin = relationship("User", foreign_keys=[responded_by])

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, subject='{self.subject}')>"
