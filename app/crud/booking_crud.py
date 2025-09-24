# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.core.security import get_db, get_current_user, get_current_vendor
# from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
# from app.schemas.payment_schema import PaymentCreate, PaymentOut
# from app.crud import booking_crud, payment_crud
# from app.models.booking_model import BookingStatus
# import logging
# from typing import List

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/bookings", tags=["Booking"])

# @router.post("/", response_model=BookingOut)
# def create_booking(booking: BookingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized attempt to create booking for user_id {booking.user_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="You can't create booking for another user.")
#     booking_result = booking_crud.create_booking(db, booking)
#     logger.info(f"Booking created successfully: ID {booking_result.id}")
#     return booking_result

# @router.get("/", response_model=List[BookingOut])
# def get_all_bookings(
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user),
#     page: int = 1,
#     limit: int = 10
# ):
#     offset = (page - 1) * limit
#     bookings = booking_crud.get_bookings_by_user_id(db, user.id)
#     total = len(bookings)
#     paginated_bookings = bookings[offset:offset + limit]
#     if not paginated_bookings:
#         return []
#     return {"bookings": paginated_bookings, "total": total}

# @router.post("/{booking_id}/payment", response_model=PaymentOut)
# def create_payment(booking_id: int, payment: PaymentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     if payment.booking_id != booking_id:
#         logger.error(f"Payment booking_id {payment.booking_id} does not match booking ID {booking_id}")
#         raise HTTPException(status_code=400, detail="Payment booking_id does not match")
#     existing_payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if existing_payment:
#         logger.warning(f"Payment already exists for booking ID {booking_id}")
#         raise HTTPException(status_code=400, detail="Payment already exists for this booking")
#     payment_result = payment_crud.create_payment(db, payment)
#     logger.info(f"Payment created successfully for booking ID {booking_id}, payment ID {payment_result.id}")
#     return payment_result

# @router.get("/{booking_id}", response_model=BookingOut)
# def get_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     logger.info(f"Booking retrieved successfully: ID {booking_id}")
#     return booking

# @router.get("/{booking_id}/payment", response_model=PaymentOut)
# def get_payment(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if not payment:
#         logger.info(f"No payment found for booking ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Payment not found")
#     logger.info(f"Payment retrieved successfully for booking ID {booking_id}, payment ID {payment.id}")
#     return payment

# @router.patch("/{booking_id}/status", response_model=BookingOut)
# def update_booking_status(booking_id: int, update_data: BookingStatusUpdate,
#                          db: Session = Depends(get_db), vendor=Depends(get_current_vendor)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.serviceprovider_id != vendor.id:
#         logger.warning(f"Unauthorized provider {vendor.id} attempting to update booking {booking_id}")
#         raise HTTPException(status_code=403, detail="Unauthorized provider")
#     try:
#         booking_result = booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
#         logger.info(f"Booking status updated to {update_data.status} for ID {booking_id}")
#         return booking_result
#     except ValueError as e:
#         logger.error(f"Error updating booking status for ID {booking_id}: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))

# @router.patch("/{booking_id}/payment/status", response_model=PaymentOut)
# def update_payment_status(booking_id: int, status: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if not payment:
#         logger.info(f"No payment found for booking ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Payment not found")
#     payment_result = payment_crud.update_payment_status(db, payment, status)
#     logger.info(f"Payment status updated to {status} for booking ID {booking_id}, payment ID {payment.id}")
#     return payment_result

# @router.delete("/{booking_id}")
# def delete_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         logger.error(f"Booking not found for ID {booking_id}")
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     db.delete(booking)
#     db.commit()
#     logger.info(f"Booking deleted successfully: ID {booking_id}")
#     return {"message": "Booking deleted successfully"}


# mac changes 
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.booking_model import Booking, BookingStatus
from app.schemas.booking_schema import BookingCreate, BookingUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def create_booking(db: Session, booking_data: BookingCreate):
    """Create a new booking"""
    booking = Booking(**booking_data.dict())
    booking.created_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    """Get booking by ID"""
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_bookings_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get all bookings for a specific user"""
    return db.query(Booking).filter(Booking.user_id == user_id).offset(skip).limit(limit).all()

def get_bookings_by_vendor_id(db: Session, vendor_id: int, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get all bookings for a specific vendor/service provider"""
    return db.query(Booking).filter(Booking.serviceprovider_id == vendor_id).offset(skip).limit(limit).all()

def get_bookings_by_status(db: Session, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by status"""
    return db.query(Booking).filter(Booking.status == status).offset(skip).limit(limit).all()

def get_bookings_by_user_and_status(db: Session, user_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by user ID and status"""
    return db.query(Booking).filter(
        and_(Booking.user_id == user_id, Booking.status == status)
    ).offset(skip).limit(limit).all()

def get_bookings_by_vendor_and_status(db: Session, vendor_id: int, status: BookingStatus, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings by vendor ID and status"""
    return db.query(Booking).filter(
        and_(Booking.serviceprovider_id == vendor_id, Booking.status == status)
    ).offset(skip).limit(limit).all()

def get_bookings_by_date_range(db: Session, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings within a date range"""
    return db.query(Booking).filter(
        and_(Booking.booking_date >= start_date, Booking.booking_date <= end_date)
    ).offset(skip).limit(limit).all()

def get_all_bookings(db: Session, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get all bookings (admin only)"""
    return db.query(Booking).offset(skip).limit(limit).all()

def update_booking_status(db: Session, booking: Booking, status: BookingStatus, otp: Optional[str] = None):
    """Update booking status with validation"""
    # Validate status transitions
    valid_transitions = {
        BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
        BookingStatus.CONFIRMED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED],
        BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED, BookingStatus.CANCELLED],
        BookingStatus.COMPLETED: [],
        BookingStatus.CANCELLED: []
    }
    
    if status not in valid_transitions.get(booking.status, []):
        raise ValueError(f"Invalid status transition from {booking.status} to {status}")
    
    # OTP validation for completion
    if status == BookingStatus.COMPLETED and otp:
        if booking.otp != otp:
            raise ValueError("Invalid OTP provided")
    
    booking.status = status
    booking.updated_at = datetime.utcnow()
    
    if status == BookingStatus.COMPLETED:
        booking.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(booking)
    return booking

def update_booking(db: Session, booking_id: int, booking_update: BookingUpdate):
    """Update booking details"""
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return None
    
    update_data = booking_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    return booking

def delete_booking(db: Session, booking_id: int) -> bool:
    """Delete a booking"""
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return False
    
    # Only allow deletion of pending or cancelled bookings
    if booking.status not in [BookingStatus.PENDING, BookingStatus.CANCELLED]:
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
    """Advanced search for bookings with multiple filters"""
    query = db.query(Booking)
    
    filters = []
    if user_id:
        filters.append(Booking.user_id == user_id)
    if vendor_id:
        filters.append(Booking.serviceprovider_id == vendor_id)
    if status:
        filters.append(Booking.status == status)
    if start_date:
        filters.append(Booking.booking_date >= start_date)
    if end_date:
        filters.append(Booking.booking_date <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.offset(skip).limit(limit).all()

def get_booking_count_by_status(db: Session, vendor_id: Optional[int] = None, user_id: Optional[int] = None):
    """Get booking count by status for analytics"""
    query = db.query(Booking.status, db.func.count(Booking.id).label('count'))
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.group_by(Booking.status).all()

def get_recent_bookings(db: Session, vendor_id: Optional[int] = None, user_id: Optional[int] = None, limit: int = 10):
    """Get recent bookings"""
    query = db.query(Booking).order_by(Booking.created_at.desc())
    
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    return query.limit(limit).all()