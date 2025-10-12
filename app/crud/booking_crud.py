from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.booking_model import Booking, BookingStatus
from app.schemas.booking_schema import BookingCreate, BookingUpdate
from typing import List, Optional
import logging

from servex_admin.backend_admin.app.utils.fcm import send_push_notification

logger = logging.getLogger(__name__)

def create_booking(db: Session, booking_data: BookingCreate):
    """Create a new booking"""
    booking = Booking(**booking_data.dict())
    booking.created_at = datetime.utcnow()
    db.add(booking)
    db.commit()
    db.refresh(booking)
    # Send notification to vendor
    vendor_fcm_token = booking.service_provider.fcm_token if booking.service_provider else None
    if vendor_fcm_token:
        send_push_notification(
            token=vendor_fcm_token,
            title="New Booking Received",
            body=f"New booking #{booking.id} for {booking.subcategory.name} has been scheduled.",
            data={"notification_type": "booking_created", "booking_id": str(booking.id)}
        )
        logger.info(f"Notification sent to vendor for booking {booking.id}")
    return booking


# def update_booking(db: Session, booking_id: int, booking_update: BookingUpdate):
#     """Update booking details"""
#     booking = get_booking_by_id(db, booking_id)
#     if not booking:
#         return None
    
#     update_data = booking_update.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(booking, field, value)
    
#     db.commit()
#     db.refresh(booking)
    
#     return booking

def update_booking_status(db: Session, booking: Booking, status: BookingStatus, otp: Optional[str] = None):
    """Update booking status with validation and send notification to user"""
    valid_transitions = {
        BookingStatus.pending: [BookingStatus.accepted, BookingStatus.cancelled],
        BookingStatus.accepted: [BookingStatus.completed, BookingStatus.cancelled],
        BookingStatus.completed: [],
        BookingStatus.cancelled: []
    }

    if status not in valid_transitions.get(booking.status, []):
        raise ValueError(f"Invalid status transition from {booking.status} to {status}")

    if status == BookingStatus.completed and otp and booking.otp != otp:
        raise ValueError("Invalid OTP provided")

    old_status = booking.status
    booking.status = status
    booking.updated_at = datetime.utcnow()
    if status == BookingStatus.completed:
        booking.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)
    
    # Send notification to user on status change
    user_fcm_token = booking.user.fcm_token if booking.user else None  # Assume User has fcm_token
    if user_fcm_token and old_status != status:
        status_messages = {
            BookingStatus.accepted: "Booking Accepted",
            BookingStatus.completed: "Booking Completed",
            BookingStatus.cancelled: "Booking Cancelled"
        }
        message = status_messages.get(status, f"Booking Status Updated to {status.value}")
        send_push_notification(
            token=user_fcm_token,
            title=message,
            body=f"Your booking #{booking.id} has been {status.value}.",
            data={"notification_type": "status_updated", "booking_id": str(booking.id), "status": status.value}
        )
        logger.info(f"Status notification sent to user for booking {booking.id}")
    
    return booking

def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_bookings_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(Booking.user_id == user_id).offset(skip).limit(limit).all()


def get_bookings_by_vendor_id(db: Session, vendor_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(Booking.serviceprovider_id == vendor_id).offset(skip).limit(limit).all()


def get_bookings_by_status(db: Session, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(Booking.status == status).offset(skip).limit(limit).all()


def get_bookings_by_user_and_status(db: Session, user_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(
        and_(Booking.user_id == user_id, Booking.status == status)
    ).offset(skip).limit(limit).all()


def get_bookings_by_vendor_and_status(db: Session, vendor_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(
        and_(Booking.serviceprovider_id == vendor_id, Booking.status == status)
    ).offset(skip).limit(limit).all()


def get_bookings_by_date_range(db: Session, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).filter(
        and_(Booking.scheduled_time >= start_date, Booking.scheduled_time <= end_date)
    ).offset(skip).limit(limit).all()


def get_all_bookings(db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
    return db.query(Booking).offset(skip).limit(limit).all()


def update_booking_status(db: Session, booking: Booking, status: BookingStatus, otp: Optional[str] = None):
    """Update booking status with validation"""
    valid_transitions = {
        BookingStatus.pending: [BookingStatus.accepted, BookingStatus.cancelled],
        BookingStatus.accepted: [BookingStatus.completed, BookingStatus.cancelled],
        BookingStatus.completed: [],
        BookingStatus.cancelled: []
    }

    if status not in valid_transitions.get(booking.status, []):
        raise ValueError(f"Invalid status transition from {booking.status} to {status}")

    if status == BookingStatus.completed and otp and booking.otp != otp:
        raise ValueError("Invalid OTP provided")

    booking.status = status
    booking.updated_at = datetime.utcnow()
    if status == BookingStatus.completed:
        booking.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking_id: int) -> bool:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return False
    
    if booking.status not in [BookingStatus.pending, BookingStatus.cancelled]:
        raise ValueError("Can only delete pending or cancelled bookings")
    
    db.delete(booking)
    db.commit()
    return True


def search_bookings(db: Session, 
                   user_id: Optional[int] = None,
                   vendor_id: Optional[int] = None,
                   status: Optional[BookingStatus] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   skip: int = 0,
                   limit: int = 100) -> List[Booking]:
    query = db.query(Booking)
    
    filters = []
    if user_id:
        filters.append(Booking.user_id == user_id)
    if vendor_id:
        filters.append(Booking.serviceprovider_id == vendor_id)
    if status:
        filters.append(Booking.status == status)
    if start_date:
        filters.append(Booking.scheduled_time >= start_date)
    if end_date:
        filters.append(Booking.scheduled_time <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.offset(skip).limit(limit).all()


def get_booking_count_by_status(db: Session, vendor_id: Optional[int] = None, user_id: Optional[int] = None):
    query = db.query(Booking.status, func.count(Booking.id).label('count'))
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.group_by(Booking.status).all()


def get_recent_bookings(db: Session, vendor_id: Optional[int] = None, user_id: Optional[int] = None, limit: int = 10):
    query = db.query(Booking).order_by(Booking.created_at.desc())
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.limit(limit).all()
def cancel_booking(db: Session, booking_id: int, user_id: int) -> bool:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return False
    
    if booking.user_id != user_id:
        raise PermissionError("User not authorized to cancel this booking")
    
    if booking.status not in [BookingStatus.pending, BookingStatus.accepted]:
        raise ValueError("Can only cancel pending or accepted bookings")
    
    booking.status = BookingStatus.cancelled
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    return True