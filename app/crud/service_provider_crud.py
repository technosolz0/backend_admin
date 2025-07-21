from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.models.service_provider_model import ServiceProvider
from app.schemas.service_provider_schema import (
    ServiceProviderCreate, ServiceProviderUpdate
)
from app.utils.otp_utils import generate_otp, send_email_otp
from app.core.security import get_password_hash


def get_vendor_by_email(db: Session, email: str) -> Optional[ServiceProvider]:
    return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()


def get_vendor_by_id(db: Session, vendor_id: int) -> Optional[ServiceProvider]:
    return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()


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
        status=VendorStatus.pending,
        # other fields from data...
    )

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
    vendor.status = VendorStatus.active
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


def update_vendor(db: Session, vendor_id: int, data: ServiceProviderUpdate):
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None

    for field, value in data.dict(exclude_unset=True).items():
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
    vendor.status = (
        VendorStatus.blocked if vendor.status == VendorStatus.active else VendorStatus.active
    )
    db.commit()
    db.refresh(vendor)
    return vendor


