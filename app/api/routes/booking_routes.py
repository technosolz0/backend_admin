# app/routes/booking_route.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_db, get_current_user, get_current_vendor
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.crud import booking_crud
from app.models.booking_model import BookingStatus

router = APIRouter(prefix="/bookings", tags=["Booking"])


@router.post("/", response_model=BookingOut)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can't create booking for another user.")
    return booking_crud.create_booking(db, booking)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return booking


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(booking_id: int, update_data: BookingStatusUpdate,
                          db: Session = Depends(get_db),
                          vendor=Depends(get_current_vendor)):

    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized provider")

    try:
        return booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
