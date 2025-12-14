from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.notification_model import Notification, NotificationType, NotificationTarget
from ..models.user import User
from typing import List, Optional
import json

class NotificationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, title: str, message: str, notification_type: NotificationType,
                          target_type: NotificationTarget, target_user_ids: Optional[List[int]] = None,
                          sent_by: Optional[int] = None) -> Notification:
        """Create a new notification"""

        # Convert target_user_ids to JSON string if provided
        target_user_ids_json = json.dumps(target_user_ids) if target_user_ids else None

        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            target_type=target_type,
            target_user_ids=target_user_ids_json,
            sent_by=sent_by
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def get_all_notifications(self, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Get all notifications with pagination"""
        return self.db.query(Notification).offset(skip).limit(limit).all()

    def get_notifications_by_sender(self, sender_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        """Get notifications sent by a specific user"""
        return self.db.query(Notification).filter(Notification.sent_by == sender_id).offset(skip).limit(limit).all()

    def get_unsent_notifications(self) -> List[Notification]:
        """Get notifications that haven't been sent yet"""
        return self.db.query(Notification).filter(Notification.is_sent == False).all()

    def mark_notification_as_sent(self, notification_id: int) -> bool:
        """Mark a notification as sent"""
        notification = self.get_notification_by_id(notification_id)
        if notification:
            notification.is_sent = True
            notification.sent_at = self.db.func.now()
            self.db.commit()
            return True
        return False

    def get_target_users(self, notification: Notification) -> List[User]:
        """Get the list of target users for a notification"""
        if notification.target_type == NotificationTarget.ALL_USERS:
            # Get all regular users (not admins/service providers)
            return self.db.query(User).filter(User.role == "user").all()
        elif notification.target_type == NotificationTarget.SPECIFIC_USERS:
            if notification.target_user_ids:
                user_ids = json.loads(notification.target_user_ids)
                return self.db.query(User).filter(User.id.in_(user_ids)).all()
        elif notification.target_type == NotificationTarget.SERVICE_PROVIDERS:
            # Get all service providers
            return self.db.query(User).filter(User.role == "service_provider").all()

        return []

    def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        notification = self.get_notification_by_id(notification_id)
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        return False

    def update_notification(self, notification_id: int, **kwargs) -> Optional[Notification]:
        """Update notification fields"""
        notification = self.get_notification_by_id(notification_id)
        if notification:
            for key, value in kwargs.items():
                if hasattr(notification, key):
                    setattr(notification, key, value)
            self.db.commit()
            self.db.refresh(notification)
            return notification
        return None
