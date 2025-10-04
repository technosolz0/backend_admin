from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import get_db, get_current_user, get_current_vendor
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.schemas.payment_schema import PaymentCreate, PaymentOut
from app.crud import booking_crud, payment_crud, category, subcategory
from app.models.booking_model import BookingStatus
from datetime import datetime, date
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Booking"])

# ✅ Helper to enrich booking with category/subcategory names
def enrich_booking(db: Session, booking) -> BookingOut:
    category = category.get_category_by_id(db, booking.category_id)
    subcategory = subcategory.get_subcategory_by_id(db, booking.subcategory_id)
    return BookingOut.from_orm(booking).copy(update={
        "category_name": category.name if category else None,
        "subcategory_name": subcategory.name if subcategory else None,
    })

# ================== EXISTING ENDPOINTS (UPDATED) ==================

@router.post("/", response_model=BookingOut)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized attempt to create booking for user_id {booking.user_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="You can't create booking for another user.")
    booking_result = booking_crud.create_booking(db, booking)
    logger.info(f"Booking created successfully: ID {booking_result.id}")
    return enrich_booking(db, booking_result)

@router.get("/", response_model=List[BookingOut])
def get_all_bookings(
    db: Session = Depends(get_db), 
    user=Depends(get_current_user),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if status:
        bookings = booking_crud.get_bookings_by_user_and_status(db, user.id, status, skip, limit)
    else:
        bookings = booking_crud.get_bookings_by_user_id(db, user.id, skip, limit)
    
    return [enrich_booking(db, b) for b in bookings]

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return enrich_booking(db, booking)

@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(booking_id: int, update_data: BookingStatusUpdate,
                         db: Session = Depends(get_db), vendor=Depends(get_current_vendor)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized provider")
    try:
        booking_result = booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
        return enrich_booking(db, booking_result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================== PAYMENT ENDPOINTS ==================

@router.post("/{booking_id}/payment", response_model=PaymentOut)
def create_payment(booking_id: int, payment: PaymentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if payment.booking_id != booking_id:
        raise HTTPException(status_code=400, detail="Payment booking_id does not match")
    existing_payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this booking")
    return payment_crud.create_payment(db, payment)

@router.get("/{booking_id}/payment", response_model=PaymentOut)
def get_payment(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

# ================== VENDOR ENDPOINTS ==================

@router.get("/vendor/my-bookings", response_model=List[BookingOut])
def get_vendor_bookings(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    status: Optional[BookingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if status:
        bookings = booking_crud.get_bookings_by_vendor_and_status(db, vendor.id, status, skip, limit)
    else:
        bookings = booking_crud.get_bookings_by_vendor_id(db, vendor.id, skip, limit)
    return [enrich_booking(db, b) for b in bookings]

@router.get("/vendor/stats")
def get_vendor_booking_stats(db: Session = Depends(get_db), vendor=Depends(get_current_vendor)):
    stats = booking_crud.get_booking_count_by_status(db, vendor_id=vendor.id)
    recent_bookings = booking_crud.get_recent_bookings(db, vendor_id=vendor.id, limit=5)
    return {
        "total_bookings": sum(stat.count for stat in stats),
        "status_counts": {stat.status.value: stat.count for stat in stats},
        "recent_bookings": [enrich_booking(db, b) for b in recent_bookings]
    }

# ================== USER ENDPOINTS ==================

@router.get("/user/recent", response_model=List[BookingOut])
def get_user_recent_bookings(db: Session = Depends(get_db), user=Depends(get_current_user), limit: int = 5):
    bookings = booking_crud.get_recent_bookings(db, user_id=user.id, limit=limit)
    return [enrich_booking(db, b) for b in bookings]

@router.get("/user/search")
def search_user_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    vendor_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 10
):
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

    bookings = booking_crud.search_bookings(
        db, user_id=user.id, vendor_id=vendor_id, status=status,
        start_date=start_datetime, end_date=end_datetime, skip=skip, limit=limit
    )

    return {
        "bookings": [enrich_booking(db, b) for b in bookings],
        "total": len(bookings),
        "filters_applied": {
            "vendor_id": vendor_id,
            "status": status.value if status else None,
            "start_date": start_date,
            "end_date": end_date
        }
    }

# ================== UTILITY ==================

@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if booking.status in [BookingStatus.pending, BookingStatus.accepted]:
        booking_crud.update_booking_status(db, booking, BookingStatus.cancelled)
        return {"message": "Booking cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status {booking.status}")
