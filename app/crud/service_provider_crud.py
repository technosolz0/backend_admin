from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.models.service_provider_model import ServiceProvider, VendorStatus, WorkStatus  # Added WorkStatus
from app.models.service import Service

from app.schemas.service_provider_schema import ServiceProviderCreate, ServiceProviderUpdate
from app.utils.otp_utils import generate_otp, send_email_otp
from app.core.security import get_password_hash

def get_vendor_by_email(db: Session, email: str) -> Optional[ServiceProvider]:
    return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

def get_vendor_by_id(db: Session, vendor_id: int) -> Optional[ServiceProvider]:
    return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()

def get_all_providers(db: Session) -> list[ServiceProvider]:
    return db.query(ServiceProvider).all()

def create_vendor_with_otp(db: Session, data: ServiceProviderCreate):
    otp = generate_otp()
    hashed_password = get_password_hash(data.password)

    vendor = ServiceProvider(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hashed_password,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        status=VendorStatus.PENDING,
        category_id=data.category_id,
        sub_category_id=data.sub_category_id,
        service_locations=data.service_locations,
        address=data.address,
        road=data.road,
        landmark=data.landmark,
        pin_code=data.pin_code,
        experience_years=data.experience_years,
        about=data.about,
        bank_name=data.bank_name,
        account_name=data.account_name,
        account_number=data.account_number,
        ifsc_code=data.ifsc_code,
        profile_pic_path=data.profile_pic_path,
        address_proof_path=data.address_proof_path,
        bank_statement_path=data.bank_statement_path,
        work_status=data.work_status
    )

    # Assign services
    if data.service_ids:
        vendor.services = db.query(Service).filter(Service.id.in_(data.service_ids)).all()

    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    send_email_otp(vendor.email, otp)
    return vendor, otp

def verify_otp(db: Session, email: str, otp: str):
    vendor = get_vendor_by_email(db, email)
    if not vendor or vendor.otp != otp:
        return None
    if datetime.utcnow() > vendor.otp_created_at + timedelta(minutes=5):
        return "expired"
    vendor.otp = None
    vendor.otp_created_at = None
    vendor.is_verified = True
    vendor.status = VendorStatus.ACTIVE
    db.commit()
    db.refresh(vendor)
    return vendor

def resend_otp(db: Session, email: str) -> Optional[str]:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        return None
    otp = generate_otp()
    vendor.otp = otp
    vendor.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    send_email_otp(vendor.email, otp)
    return otp

def create_login_otp(db: Session, email: str) -> Optional[str]:
    vendor = get_vendor_by_email(db, email)
    if not vendor or not vendor.is_verified:
        return None
    otp = generate_otp()
    vendor.otp = otp
    vendor.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    send_email_otp(vendor.email, otp)
    return otp

def verify_login_otp(db: Session, email: str, otp: str) -> Optional[ServiceProvider]:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        return None
    if vendor.otp != otp:
        return "invalid"
    if datetime.utcnow() > vendor.otp_created_at + timedelta(minutes=5):
        return "expired"
    vendor.otp = None
    vendor.otp_created_at = None
    vendor.last_login = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    return vendor

def update_vendor(db: Session, vendor_id: int, data: ServiceProviderUpdate):
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None
    update_data = data.dict(exclude_unset=True)
    if "service_ids" in update_data:
        vendor.services = db.query(Service).filter(Service.id.in_(update_data["service_ids"])).all()
        del update_data["service_ids"]
    for field, value in update_data.items():
        setattr(vendor, field, value)
    db.commit()
    db.refresh(vendor)
    return vendor

def delete_vendor(db: Session, vendor_id: int) -> bool:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return False
    db.delete(vendor)
    db.commit()
    return True

def toggle_vendor_status(db: Session, vendor_id: int) -> Optional[ServiceProvider]:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None
    vendor.status = VendorStatus.BLOCKED if vendor.status == VendorStatus.ACTIVE else VendorStatus.ACTIVE
    db.commit()
    db.refresh(vendor)
    return vendor

def toggle_work_status(db: Session, vendor_id: int) -> Optional[ServiceProvider]:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None
    vendor.work_status = WorkStatus.ONLINE if vendor.work_status == WorkStatus.OFFLINE else WorkStatus.OFFLINE
    db.commit()
    db.refresh(vendor)
    return vendor