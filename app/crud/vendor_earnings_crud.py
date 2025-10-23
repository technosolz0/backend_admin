from sqlalchemy.orm import Session
from app.models.vendor_earnings_model import VendorEarnings

def create_vendor_earnings(db: Session, booking_id: int, vendor_id: int,
                          total_paid: float, commission_percentage: float = 10.0,
                          commission_amount: float = 0.0, final_amount: float = 0.0):
    earning = VendorEarnings(
        booking_id=booking_id,
        vendor_id=vendor_id,
        total_paid=total_paid,
        commission_percentage=commission_percentage,
        commission_amount=commission_amount,
        final_amount=final_amount
    )
    db.add(earning)
    db.commit()
    db.refresh(earning)
    return earning

def get_vendor_earnings_by_vendor(db: Session, vendor_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.vendor_id == vendor_id).all()

def get_vendor_earnings_by_booking(db: Session, booking_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.booking_id == booking_id).all()

def get_vendor_earnings_by_id(db: Session, earnings_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.id == earnings_id).first()

def get_all_vendor_earnings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(VendorEarnings).offset(skip).limit(limit).all()

def delete_vendor_earnings(db: Session, earnings_id: int):
    earnings = db.query(VendorEarnings).filter(VendorEarnings.id == earnings_id).first()
    if earnings:
        db.delete(earnings)
        db.commit()
        return True
    return False
