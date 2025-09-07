from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_db, get_current_user, get_current_vendor
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.schemas.payment_schema import PaymentCreate, PaymentOut
from app.crud import booking_crud, payment_crud
from app.models.booking_model import BookingStatus
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Booking"])

@router.post("/", response_model=BookingOut)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized attempt to create booking for user_id {booking.user_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="You can't create booking for another user.")
    booking_result = booking_crud.create_booking(db, booking)
    logger.info(f"Booking created successfully: ID {booking_result.id}")
    return booking_result

@router.get("/", response_model=List[BookingOut])
def get_all_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit
    bookings = booking_crud.get_bookings_by_user_id(db, user.id)
    total = len(bookings)
    paginated_bookings = bookings[offset:offset + limit]
    if not paginated_bookings:
        return []
    return {"bookings": paginated_bookings, "total": total}

@router.post("/{booking_id}/payment", response_model=PaymentOut)
def create_payment(booking_id: int, payment: PaymentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if payment.booking_id != booking_id:
        logger.error(f"Payment booking_id {payment.booking_id} does not match booking ID {booking_id}")
        raise HTTPException(status_code=400, detail="Payment booking_id does not match")
    existing_payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if existing_payment:
        logger.warning(f"Payment already exists for booking ID {booking_id}")
        raise HTTPException(status_code=400, detail="Payment already exists for this booking")
    payment_result = payment_crud.create_payment(db, payment)
    logger.info(f"Payment created successfully for booking ID {booking_id}, payment ID {payment_result.id}")
    return payment_result

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    logger.info(f"Booking retrieved successfully: ID {booking_id}")
    return booking

@router.get("/{booking_id}/payment", response_model=PaymentOut)
def get_payment(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if not payment:
        logger.info(f"No payment found for booking ID {booking_id}")
        raise HTTPException(status_code=404, detail="Payment not found")
    logger.info(f"Payment retrieved successfully for booking ID {booking_id}, payment ID {payment.id}")
    return payment

@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(booking_id: int, update_data: BookingStatusUpdate,
                         db: Session = Depends(get_db), vendor=Depends(get_current_vendor)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        logger.warning(f"Unauthorized provider {vendor.id} attempting to update booking {booking_id}")
        raise HTTPException(status_code=403, detail="Unauthorized provider")
    try:
        booking_result = booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
        logger.info(f"Booking status updated to {update_data.status} for ID {booking_id}")
        return booking_result
    except ValueError as e:
        logger.error(f"Error updating booking status for ID {booking_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{booking_id}/payment/status", response_model=PaymentOut)
def update_payment_status(booking_id: int, status: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if not payment:
        logger.info(f"No payment found for booking ID {booking_id}")
        raise HTTPException(status_code=404, detail="Payment not found")
    payment_result = payment_crud.update_payment_status(db, payment, status)
    logger.info(f"Payment status updated to {status} for booking ID {booking_id}, payment ID {payment.id}")
    return payment_result

@router.delete("/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    db.delete(booking)
    db.commit()
    logger.info(f"Booking deleted successfully: ID {booking_id}")
    return {"message": "Booking deleted successfully"}