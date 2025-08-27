from sqlalchemy.orm import Session
from app.models.booking_model import Booking, BookingStatus
from app.schemas.booking_schema import BookingCreate
from datetime import datetime
from app.utils.otp_utils import generate_otp, send_email_otp


def create_booking(db: Session, booking_data: BookingCreate):
    booking = Booking(**booking_data.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
def get_bookings_by_user_id(db: Session, user_id: int):
    return db.query(Booking).filter(Booking.user_id == user_id).all()


def get_booking_by_id(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()


def update_booking_status(db: Session, booking: Booking, new_status: str, otp: str = None):
    if new_status == BookingStatus.accepted:
        otp_code = generate_otp()
        booking.otp = otp_code
        booking.otp_created_at = datetime.utcnow()
        send_email_otp(booking.user.email, otp_code)
    elif new_status == BookingStatus.completed:
        if not otp or otp != booking.otp:
            raise ValueError("Invalid or missing OTP for completion.")
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    return booking