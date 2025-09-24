# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.core.security import get_db, get_current_user, get_current_vendor
# from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
# from app.schemas.payment_schema import PaymentCreate, PaymentOut
# from app.crud import booking_crud, payment_crud
# from app.models.booking_model import BookingStatus

# router = APIRouter(prefix="/bookings", tags=["Booking"])


# @router.post("/", response_model=BookingOut)
# def create_booking(booking: BookingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     if booking.user_id != user.id:
#         raise HTTPException(status_code=403, detail="You can't create booking for another user.")
#     return booking_crud.create_booking(db, booking)


# @router.post("/{booking_id}/payment", response_model=PaymentOut)
# def create_payment(booking_id: int, payment: PaymentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     if payment.booking_id != booking_id:
#         raise HTTPException(status_code=400, detail="Payment booking_id does not match")
#     existing_payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if existing_payment:
#         raise HTTPException(status_code=400, detail="Payment already exists for this booking")
#     return payment_crud.create_payment(db, payment)


# @router.get("/{booking_id}", response_model=BookingOut)
# def get_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     return booking


# @router.get("/{booking_id}/payment", response_model=PaymentOut)
# def get_payment(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if not payment:
#         raise HTTPException(status_code=404, detail="Payment not found")
#     return payment


# @router.patch("/{booking_id}/status", response_model=BookingOut)
# def update_booking_status(booking_id: int, update_data: BookingStatusUpdate,
#                          db: Session = Depends(get_db), vendor=Depends(get_current_vendor)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.serviceprovider_id != vendor.id:
#         raise HTTPException(status_code=403, detail="Unauthorized provider")
#     try:
#         return booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.patch("/{booking_id}/payment/status", response_model=PaymentOut)
# def update_payment_status(booking_id: int, status: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")
#     if booking.user_id != user.id:
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#     payment = payment_crud.get_payment_by_booking_id(db, booking_id)
#     if not payment:
#         raise HTTPException(status_code=404, detail="Payment not found")
#     return payment_crud.update_payment_status(db, payment, status)


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.core.security import get_db, get_current_user, get_current_vendor
# from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
# from app.schemas.payment_schema import PaymentCreate, PaymentOut
# from app.crud import booking_crud, payment_crud
# from app.models.booking_model import BookingStatus
# import logging

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
# @router.get("/", response_model=list[BookingOut])
# def get_all_bookings(db: Session = Depends(get_db), user=Depends(get_current_user)):
#     bookings = booking_crud.get_bookings_by_user_id(db, user.id)
#     if not bookings:
#         return []
#     return bookings

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



# mac changes
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import get_db, get_current_user, get_current_vendor
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.schemas.payment_schema import PaymentCreate, PaymentOut
from app.crud import booking_crud, payment_crud
from app.models.booking_model import BookingStatus
from datetime import datetime, date
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Booking"])

# ================== EXISTING ENDPOINTS (UPDATED) ==================

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
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all bookings for the current user with optional filtering"""
    if status:
        bookings = booking_crud.get_bookings_by_user_and_status(db, user.id, status, skip, limit)
    else:
        bookings = booking_crud.get_bookings_by_user_id(db, user.id, skip, limit)
    
    if not bookings:
        return []
    return bookings

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

# ================== PAYMENT ENDPOINTS (EXISTING STRUCTURE) ==================

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

# ================== NEW VENDOR ENDPOINTS ==================

@router.get("/vendor/my-bookings", response_model=List[BookingOut])
def get_vendor_bookings(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all bookings for the current vendor"""
    try:
        if status:
            bookings = booking_crud.get_bookings_by_vendor_and_status(db, vendor.id, status, skip, limit)
        else:
            bookings = booking_crud.get_bookings_by_vendor_id(db, vendor.id, skip, limit)
        
        logger.info(f"Retrieved {len(bookings)} bookings for vendor {vendor.id}")
        return bookings
    except Exception as e:
        logger.error(f"Error retrieving vendor bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendor bookings")

@router.get("/vendor/stats")
def get_vendor_booking_stats(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Get booking statistics for the current vendor"""
    try:
        stats = booking_crud.get_booking_count_by_status(db, vendor_id=vendor.id)
        recent_bookings = booking_crud.get_recent_bookings(db, vendor_id=vendor.id, limit=5)
        
        stats_dict = {stat.status.value: stat.count for stat in stats}
        
        return {
            "total_bookings": sum(stats_dict.values()),
            "status_counts": stats_dict,
            "recent_bookings": recent_bookings
        }
    except Exception as e:
        logger.error(f"Error retrieving vendor stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve booking statistics")

# ================== NEW USER ENDPOINTS ==================

@router.get("/user/recent", response_model=List[BookingOut])
def get_user_recent_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20)
):
    """Get recent bookings for the current user"""
    try:
        bookings = booking_crud.get_recent_bookings(db, user_id=user.id, limit=limit)
        return bookings
    except Exception as e:
        logger.error(f"Error retrieving recent bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent bookings")

@router.get("/user/search")
def search_user_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Advanced search for user's bookings with multiple filters"""
    try:
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        bookings = booking_crud.search_bookings(
            db,
            user_id=user.id,
            vendor_id=vendor_id,
            status=status,
            start_date=start_datetime,
            end_date=end_datetime,
            skip=skip,
            limit=limit
        )
        
        return {
            "bookings": bookings,
            "total": len(bookings),
            "filters_applied": {
                "vendor_id": vendor_id,
                "status": status.value if status else None,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Error searching bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search bookings")

# ================== UTILITY ENDPOINTS ==================

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """Cancel/Delete booking (User must own the booking)"""
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    try:
        # Try to update status to cancelled first
        if booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            booking_crud.update_booking_status(db, booking, BookingStatus.CANCELLED)
            logger.info(f"Booking cancelled successfully: ID {booking_id}")
            return {"message": "Booking cancelled successfully"}
        else:
            logger.warning(f"Cannot cancel booking {booking_id} with status {booking.status}")
            raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status {booking.status}")
    except ValueError as e:
        logger.error(f"Error cancelling booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing booking cancellation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process booking cancellation")