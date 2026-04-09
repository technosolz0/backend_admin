"""
Vendor Notification Routes
Provides notification endpoints authenticated with the vendor JWT token.
The partner app uses these endpoints (not /notifications/my-notifications
which requires a customer user token).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import json
from datetime import datetime

from app.core.security import get_db, get_current_vendor
from app.models.service_provider_model import ServiceProvider
from app.models.notification_model import Notification, NotificationType, NotificationTarget, UserNotificationStatus

router = APIRouter(prefix="/vendor/notifications", tags=["vendor-notifications"])


def _get_vendor_notifications_query(db: Session, vendor_id: int, skip: int = 0, limit: int = 50):
    """
    Return notifications that target this vendor:
    - Sent to SERVICE_PROVIDERS (all vendors)
    - Or specifically targeted to this vendor_id
    """
    # Get all notifications sent to service providers or this specific vendor
    notifications = (
        db.query(Notification)
        .filter(
            (Notification.target_type == NotificationTarget.SERVICE_PROVIDERS) |
            (
                (Notification.target_type == NotificationTarget.SPECIFIC_USERS) &
                (Notification.target_user_ids.contains(str(vendor_id)))
            )
        )
        .filter(Notification.is_sent == True)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications


def _is_read(db: Session, vendor_id: int, notification_id: int) -> bool:
    status = db.query(UserNotificationStatus).filter(
        UserNotificationStatus.user_id == vendor_id,
        UserNotificationStatus.notification_id == notification_id,
    ).first()
    return status.is_read if status else False


def _build_notification_response(db: Session, vendor_id: int, notification: Notification) -> dict:
    is_read = _is_read(db, vendor_id, notification.id)
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type.value if notification.notification_type else "general",
        "reference_id": notification.reference_id,
        "is_read": is_read,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


@router.get("")
def get_vendor_notifications(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Get paginated notifications for the current vendor."""
    try:
        notifications = _get_vendor_notifications_query(db, current_vendor.id, skip, limit)
        result = [_build_notification_response(db, current_vendor.id, n) for n in notifications]

        # Total count (for pagination)
        total = (
            db.query(func.count(Notification.id))
            .filter(
                (Notification.target_type == NotificationTarget.SERVICE_PROVIDERS) |
                (
                    (Notification.target_type == NotificationTarget.SPECIFIC_USERS) &
                    (Notification.target_user_ids.contains(str(current_vendor.id)))
                )
            )
            .filter(Notification.is_sent == True)
            .scalar()
            or 0
        )

        return {"notifications": result, "total": total}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error fetching vendor notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")


@router.get("/unread-count")
def get_vendor_unread_count(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Get the count of unread notifications for the vendor."""
    try:
        notifications = _get_vendor_notifications_query(db, current_vendor.id, skip=0, limit=500)

        # Count those NOT marked read
        unread = 0
        for n in notifications:
            if not _is_read(db, current_vendor.id, n.id):
                unread += 1

        return {"unread_count": unread}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error fetching unread count: {str(e)}")
        return {"unread_count": 0}


@router.patch("/{notification_id}/read")
def mark_vendor_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Mark a notification as read for the current vendor."""
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Upsert read status
        status = db.query(UserNotificationStatus).filter(
            UserNotificationStatus.user_id == current_vendor.id,
            UserNotificationStatus.notification_id == notification_id,
        ).first()

        if status:
            status.is_read = True
            status.read_at = datetime.utcnow()
        else:
            status = UserNotificationStatus(
                user_id=current_vendor.id,
                notification_id=notification_id,
                is_read=True,
                read_at=datetime.utcnow(),
            )
            db.add(status)

        db.commit()
        return {"message": "Notification marked as read", "notification_id": notification_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


@router.patch("/read-all")
def mark_all_vendor_notifications_as_read(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Mark all notifications as read for the current vendor."""
    try:
        notifications = _get_vendor_notifications_query(db, current_vendor.id, skip=0, limit=500)
        for n in notifications:
            status = db.query(UserNotificationStatus).filter(
                UserNotificationStatus.user_id == current_vendor.id,
                UserNotificationStatus.notification_id == n.id,
            ).first()
            if status:
                status.is_read = True
                status.read_at = datetime.utcnow()
            else:
                db.add(UserNotificationStatus(
                    user_id=current_vendor.id,
                    notification_id=n.id,
                    is_read=True,
                    read_at=datetime.utcnow(),
                ))
        db.commit()
        return {"message": "All notifications marked as read"}
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Error marking all as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")
