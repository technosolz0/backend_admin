from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ...database import get_db
from ...models.notification_model import Notification, NotificationType, NotificationTarget
from ...models.user import User
from ...crud.notification_crud import NotificationCRUD
from ...utils.fcm import send_fcm_notification
from ...core.security import get_current_admin_user

router = APIRouter()

@router.post("/send")
async def send_custom_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.GENERAL,
    target_type: NotificationTarget = NotificationTarget.ALL_USERS,
    target_user_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Send custom notification to users"""
    try:
        notification_crud = NotificationCRUD(db)

        # Create notification record
        notification = notification_crud.create_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            target_type=target_type,
            target_user_ids=target_user_ids,
            sent_by=current_admin.id
        )

        # Get target users
        target_users = notification_crud.get_target_users(notification)

        if not target_users:
            raise HTTPException(status_code=400, detail="No target users found")

        # Send notifications in background
        background_tasks.add_task(
            send_notifications_to_users,
            target_users,
            title,
            message,
            notification.id,
            db
        )

        return {
            "message": f"Notification queued for {len(target_users)} users",
            "notification_id": notification.id,
            "target_count": len(target_users)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

async def send_notifications_to_users(users: List[User], title: str, message: str, notification_id: int, db: Session):
    """Background task to send notifications to users"""
    success_count = 0
    failure_count = 0

    for user in users:
        try:
            # Send FCM notification if user has FCM token
            if user.fcm_token:
                await send_fcm_notification(
                    token=user.fcm_token,
                    title=title,
                    body=message,
                    data={
                        "notification_id": str(notification_id),
                        "type": "custom_notification"
                    }
                )
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            print(f"Failed to send notification to user {user.id}: {str(e)}")
            failure_count += 1

    # Mark notification as sent
    notification_crud = NotificationCRUD(db)
    notification_crud.mark_notification_as_sent(notification_id)

    print(f"Notification {notification_id} sent: {success_count} success, {failure_count} failures")

@router.get("/")
def get_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get all notifications"""
    notification_crud = NotificationCRUD(db)
    notifications = notification_crud.get_all_notifications(skip=skip, limit=limit)

    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.notification_type.value,
                "target_type": n.target_type.value,
                "target_user_ids": json.loads(n.target_user_ids) if n.target_user_ids else None,
                "is_sent": n.is_sent,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat(),
                "sent_by": n.sent_by
            }
            for n in notifications
        ],
        "total": len(notifications)
    }

@router.get("/{notification_id}")
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get notification by ID"""
    notification_crud = NotificationCRUD(db)
    notification = notification_crud.get_notification_by_id(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type.value,
        "target_type": notification.target_type.value,
        "target_user_ids": json.loads(notification.target_user_ids) if notification.target_user_ids else None,
        "is_sent": notification.is_sent,
        "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
        "created_at": notification.created_at.isoformat(),
        "sent_by": notification.sent_by
    }

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a notification"""
    notification_crud = NotificationCRUD(db)
    success = notification_crud.delete_notification(notification_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification deleted successfully"}

@router.get("/stats/overview")
def get_notification_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get notification statistics"""
    notification_crud = NotificationCRUD(db)

    total = len(notification_crud.get_all_notifications())
    sent = len([n for n in notification_crud.get_all_notifications() if n.is_sent])
    pending = total - sent

    return {
        "total_notifications": total,
        "sent_notifications": sent,
        "pending_notifications": pending,
        "delivery_rate": (sent / total * 100) if total > 0 else 0
    }
