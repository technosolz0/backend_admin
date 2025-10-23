from sqlalchemy.orm import Session
from datetime import datetime
from app.models.coupon_model import Coupon

def get_coupon_by_code(db: Session, code: str):
    return db.query(Coupon).filter(
        Coupon.code == code,
        Coupon.active == True,
        Coupon.expiry_date > datetime.utcnow()
    ).first()

def create_coupon(db: Session, code: str, discount_type: str, discount_value: float,
                  min_order_value: float = None, expiry_date: datetime = None):
    if expiry_date is None:
        expiry_date = datetime.utcnow().replace(month=datetime.utcnow().month + 1)
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_value=min_order_value,
        expiry_date=expiry_date
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def get_all_coupons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Coupon).offset(skip).limit(limit).all()

def update_coupon_status(db: Session, coupon_id: int, active: bool):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if coupon:
        coupon.active = active
        db.commit()
        db.refresh(coupon)
    return coupon
