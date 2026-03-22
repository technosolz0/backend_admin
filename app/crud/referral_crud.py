from sqlalchemy.orm import Session
from app.models.referral_model import AdminReferralCode
from app.schemas.referral_schema import AdminReferralCodeCreate, AdminReferralCodeUpdate

def create_admin_referral_code(db: Session, referral: AdminReferralCodeCreate):
    db_referral = AdminReferralCode(**referral.model_dump())
    db.add(db_referral)
    db.commit()
    db.refresh(db_referral)
    return db_referral

def get_admin_referral_codes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AdminReferralCode).offset(skip).limit(limit).all()

def get_admin_referral_code_by_id(db: Session, referral_id: int):
    return db.query(AdminReferralCode).filter(AdminReferralCode.id == referral_id).first()

def get_admin_referral_code_by_code(db: Session, code: str):
    return db.query(AdminReferralCode).filter(AdminReferralCode.code == code).first()

def update_admin_referral_code(db: Session, referral_id: int, referral_update: AdminReferralCodeUpdate):
    db_referral = get_admin_referral_code_by_id(db, referral_id)
    if not db_referral:
        return None
    
    update_data = referral_update.model_dump(exclude_unset=True)
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
