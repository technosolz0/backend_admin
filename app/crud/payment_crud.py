from datetime import datetime
from sqlalchemy.orm import Session
from app.models.payment_model import Payment
from app.schemas.payment_schema import PaymentCreate

def create_payment(db: Session, payment_data: PaymentCreate):
    payment = Payment(**payment_data.dict())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

def get_payment_by_booking_id(db: Session, booking_id: int):
    return db.query(Payment).filter(Payment.booking_id == booking_id).first()

def update_payment_status(db: Session, payment: Payment, status: str):
    payment.status = status
    payment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return payment