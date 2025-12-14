from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base

class NotificationType(str, enum.Enum):
    GENERAL = "general"
    PROMOTIONAL = "promotional"
    BOOKING_UPDATE = "booking_update"
    SYSTEM = "system"

class NotificationTarget(str, enum.Enum):
    ALL_USERS = "all_users"
    SPECIFIC_USERS = "specific_users"
    SERVICE_PROVIDERS = "service_providers"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.GENERAL)
    target_type = Column(Enum(NotificationTarget), default=NotificationTarget.ALL_USERS)
    target_user_ids = Column(Text, nullable=True)  # JSON string of user IDs for specific users
    sent_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    sender = relationship("User", back_populates="sent_notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type={self.notification_type})>"
