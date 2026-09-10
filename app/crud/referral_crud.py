from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.referral_model import AdminReferralCode
from app.models.user import User
from app.models.vendor_model import Vendor
from app.schemas.referral_schema import AdminReferralCodeCreate, AdminReferralCodeUpdate
from app.services.referral_service import create_admin_campaign_referral_code, clean_referral_code

def create_admin_referral_code(db: Session, referral: AdminReferralCodeCreate):
    return create_admin_campaign_referral_code(
        db=db,
        name=referral.name,
        code=referral.code,
        no_of_bookings=referral.no_of_bookings,
        commission_percentage=referral.commission_percentage
    )

def get_admin_referral_codes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AdminReferralCode).order_by(AdminReferralCode.created_at.desc()).offset(skip).limit(limit).all()

def get_admin_referral_code_by_id(db: Session, referral_id: int):
    return db.query(AdminReferralCode).filter(AdminReferralCode.id == referral_id).first()

def get_admin_referral_code_by_code(db: Session, code: str):
    code_clean = clean_referral_code(code)
    return db.query(AdminReferralCode).filter(
        (func.upper(AdminReferralCode.code) == code.upper()) |
        (func.upper(AdminReferralCode.code) == code_clean)
    ).first()

def update_admin_referral_code(db: Session, referral_id: int, referral_update: AdminReferralCodeUpdate):
    db_referral = get_admin_referral_code_by_id(db, referral_id)
    if not db_referral:
        return None
    
    update_data = referral_update.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        cleaned = clean_referral_code(update_data["code"])
        if not cleaned:
            raise ValueError("Referral code must contain alphanumeric characters (no special characters).")
        # Check collision with other admin codes
        existing = db.query(AdminReferralCode).filter(
            func.upper(AdminReferralCode.code) == cleaned,
            AdminReferralCode.id != referral_id
        ).first()
        if existing:
            raise ValueError(f"Referral code '{cleaned}' already in use.")
        if db.query(User).filter(func.upper(User.referral_code) == cleaned).first():
            raise ValueError(f"Referral code '{cleaned}' conflicts with a customer referral code.")
        if db.query(Vendor).filter(func.upper(Vendor.referral_code) == cleaned).first():
            raise ValueError(f"Referral code '{cleaned}' conflicts with a vendor referral code.")
        update_data["code"] = cleaned

    for key, value in update_data.items():
        setattr(db_referral, key, value)
    
    db.commit()
    db.refresh(db_referral)
    return db_referral

def delete_admin_referral_code(db: Session, referral_id: int):
    db_referral = get_admin_referral_code_by_id(db, referral_id)
    if not db_referral:
        return False
    
    db.delete(db_referral)
    db.commit()
    return True
