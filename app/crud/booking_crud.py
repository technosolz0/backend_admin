
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.booking_model import Booking, BookingStatus
from app.models.user import User
from app.models.service_provider_model import ServiceProvider as Vendor
from app.schemas.booking_schema import BookingCreate, BookingUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def create_booking(db: Session, booking_data: BookingCreate) -> Booking:
    """Create a new booking."""
    booking = Booking(**booking_data.dict())
    booking.created_at = datetime.utcnow()
    booking.status = BookingStatus.pending
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    logger.info(f"Booking created: {booking.id} for user {booking.user_id}, vendor {booking.serviceprovider_id}")
    return booking

def update_booking_status(db: Session, booking: Booking, status: BookingStatus, otp: Optional[str] = None) -> Booking:
    """Update booking status with validation."""
    valid_transitions = {
        BookingStatus.pending: [BookingStatus.accepted, BookingStatus.cancelled],
        BookingStatus.accepted: [BookingStatus.completed, BookingStatus.cancelled],
        BookingStatus.completed: [],
        BookingStatus.cancelled: []
    }

    if status not in valid_transitions.get(booking.status, []):
        logger.error(f"Invalid status transition for booking {booking.id}: {booking.status} to {status}")
        raise ValueError(f"Invalid status transition from {booking.status} to {status}")

    if status == BookingStatus.completed and otp and booking.otp != otp:
        logger.error(f"Invalid OTP for booking {booking.id}")
        raise ValueError("Invalid OTP provided")

    old_status = booking.status
    booking.status = status
    booking.updated_at = datetime.utcnow()
    if status == BookingStatus.completed:
        booking.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)
    
    logger.info(f"Booking {booking.id} status updated to {status}")
    return booking

def update_booking(db: Session, booking_id: int, booking_update: BookingUpdate) -> Optional[Booking]:
    """Update booking details."""
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found: {booking_id}")
        return None
    
    update_data = booking_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    
    logger.info(f"Booking {booking_id} updated successfully")
    return booking

def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    """Get booking by ID."""
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_vendor_by_serviceprovider_id(db: Session, serviceprovider_id: int) -> Optional[Vendor]:
    """Get vendor by serviceprovider_id."""
    return db.query(Vendor).filter(Vendor.id == serviceprovider_id).first()

def get_bookings_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by user ID."""
    return db.query(Booking).filter(Booking.user_id == user_id).offset(skip).limit(limit).all()

def get_bookings_by_vendor_id(db: Session, vendor_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by vendor ID."""
    return db.query(Booking).filter(Booking.serviceprovider_id == vendor_id).offset(skip).limit(limit).all()

def get_bookings_by_status(db: Session, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by status."""
    return db.query(Booking).filter(Booking.status == status).offset(skip).limit(limit).all()

def get_bookings_by_user_and_status(db: Session, user_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by user ID and status."""
    return db.query(Booking).filter(
        and_(Booking.user_id == user_id, Booking.status == status)
    ).offset(skip).limit(limit).all()

def get_bookings_by_vendor_and_status(db: Session, vendor_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by vendor ID and status."""
    return db.query(Booking).filter(
        and_(Booking.serviceprovider_id == vendor_id, Booking.status == status)
    ).offset(skip).limit(limit).all()

def get_bookings_by_date_range(db: Session, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by date range."""
    return db.query(Booking).filter(
        and_(Booking.scheduled_time >= start_date, Booking.scheduled_time <= end_date)
    ).offset(skip).limit(limit).all()

def get_all_bookings(db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get all bookings with pagination."""
    return db.query(Booking).offset(skip).limit(limit).all()

def delete_booking(db: Session, booking_id: int) -> bool:
    """Delete a booking if pending or cancelled."""
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found: {booking_id}")
        return False
    
    if booking.status not in [BookingStatus.pending, BookingStatus.cancelled]:
        logger.error(f"Cannot delete booking {booking_id} with status {booking.status}")
        raise ValueError("Can only delete pending or cancelled bookings")
    
    db.delete(booking)
    db.commit()
    logger.info(f"Booking {booking_id} deleted successfully")
    return True

def search_bookings(
    db: Session,
    user_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Booking]:
    """Search bookings with optional filters."""
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
    """Get booking count grouped by status."""
    query = db.query(Booking.status, func.count(Booking.id).label('count'))
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.group_by(Booking.status).all()

def get_recent_bookings(db: Session, vendor_id: Optional[int] = None, user_id: Optional[int] = None, limit: int = 10):
    """Get recent bookings for user or vendor."""
    query = db.query(Booking).order_by(Booking.created_at.desc())
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.limit(limit).all()

def cancel_booking(db: Session, booking_id: int, user_id: int) -> tuple[bool, Optional[str]]:
    """Cancel a booking if user is authorized and booking is pending/accepted.
    
    Returns: (success: bool, error_message: Optional[str])
    """
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found: {booking_id}")
        return False, "Booking not found"
    
    if booking.user_id != user_id:
        logger.error(f"User {user_id} not authorized to cancel booking {booking_id}")
        return False, "User not authorized to cancel this booking"
    
    if booking.status not in [BookingStatus.pending, BookingStatus.accepted]:
        logger.error(f"Cannot cancel booking {booking_id} with status {booking.status}")
        return False, "Can only cancel pending or accepted bookings"
    
    booking.status = BookingStatus.cancelled
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    
    logger.info(f"Booking {booking_id} cancelled successfully")
    return True, None


