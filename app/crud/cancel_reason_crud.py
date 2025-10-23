from sqlalchemy.orm import Session
from app.models.cancel_reason_model import CancelReason

def create_cancel_reason(db: Session, booking_id: int, reason: str, cancelled_by: str):
    cancel_reason = CancelReason(
        booking_id=booking_id,
        reason=reason,
        cancelled_by=cancelled_by
    )
    db.add(cancel_reason)
    db.commit()
    db.refresh(cancel_reason)
    return cancel_reason

def get_cancel_reasons_by_booking(db: Session, booking_id: int):
    return db.query(CancelReason).filter(CancelReason.booking_id == booking_id).all()

def get_cancel_reason_by_id(db: Session, reason_id: int):
    return db.query(CancelReason).filter(CancelReason.id == reason_id).first()

def get_all_cancel_reasons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CancelReason).offset(skip).limit(limit).all()

def delete_cancel_reason(db: Session, reason_id: int):
    reason = db.query(CancelReason).filter(CancelReason.id == reason_id).first()
    if reason:
        db.delete(reason)
        db.commit()
        return True
    return False
