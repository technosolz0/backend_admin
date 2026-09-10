from typing import Optional
from sqlalchemy.orm import Session
from app.models.vendor_earnings_model import VendorEarnings
from app.services.commission_service import record_vendor_booking_earnings

def create_vendor_earnings(
    db: Session,
    booking_id: int,
    vendor_id: int,
    total_paid: float,
    commission_percentage: Optional[float] = None,
    commission_amount: Optional[float] = None,
    final_amount: Optional[float] = None
):
    # If commission and final amounts are provided directly, use them; otherwise use dynamic daily tier
    if commission_amount is not None and final_amount is not None and commission_percentage is not None:
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

    return record_vendor_booking_earnings(
        db=db,
        booking_id=booking_id,
        vendor_id=vendor_id,
        total_paid=total_paid,
        custom_commission_percentage=commission_percentage
    )

def get_vendor_earnings_by_vendor(db: Session, vendor_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.vendor_id == vendor_id).order_by(VendorEarnings.earned_at.desc()).all()

def get_vendor_earnings_by_booking(db: Session, booking_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.booking_id == booking_id).all()

def get_vendor_earnings_by_id(db: Session, earnings_id: int):
    return db.query(VendorEarnings).filter(VendorEarnings.id == earnings_id).first()

def get_all_vendor_earnings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(VendorEarnings).order_by(VendorEarnings.earned_at.desc()).offset(skip).limit(limit).all()

def delete_vendor_earnings(db: Session, earnings_id: int):
    earnings = db.query(VendorEarnings).filter(VendorEarnings.id == earnings_id).first()
    if earnings:
        db.delete(earnings)
        db.commit()
        return True
    return False
