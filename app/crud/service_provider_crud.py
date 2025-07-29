from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, UploadFile
from passlib.context import CryptContext
from requests import Session
from app.utils.otp_utils import generate_otp, send_email_otp
from app.core.security import create_access_token, get_db, get_current_vendor, get_current_admin, get_password_hash
import enum
import os

from servex_admin.backend_admin.app.models.service_provider_model import ServiceProvider, SubCategory, VendorStatus, vendor_subcategory_charges
from servex_admin.backend_admin.app.schemas.service_provider_schema import ServiceProviderCreate, ServiceProviderDeviceUpdate, ServiceProviderUpdate, SubCategoryCharge

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
MAX_OTP_RESENDS = 3
OTP_RESEND_COOLDOWN_MINUTES = 1


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
    return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
    return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

def create_vendor(db: Session, vendor: ServiceProviderCreate) -> ServiceProvider:
    existing = get_vendor_by_email(db, vendor.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(vendor.password)
    otp = generate_otp()
    now = datetime.utcnow()
    
    db_vendor = ServiceProvider(
        **vendor.dict(exclude={"password", "subcategory_charges"}),
        password=hashed_password,
        otp=otp,
        otp_created_at=now,
        otp_last_sent=now,
        otp_verified=False,
        last_login=now,
        last_device_update=now
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    # Handle subcategory charges
    if vendor.subcategory_charges:
        for charge in vendor.subcategory_charges:
            if charge.service_charge < 0:
                raise HTTPException(status_code=400, detail="Service charge cannot be negative")
            subcategory = get_subcategory_by_id(db, charge.subcategory_id)
            if not subcategory:
                raise HTTPException(status_code=404, detail=f"Subcategory {charge.subcategory_id} not found")
            db.execute(
                vendor_subcategory_charges.insert().values(
                    vendor_id=db_vendor.id,
                    subcategory_id=charge.subcategory_id,
                    service_charge=charge.service_charge
                )
            )
        db.commit()
    
    send_email_otp(vendor.email, otp)
    return db_vendor

def verify_vendor_otp(db: Session, email: str, otp: str) -> tuple[ServiceProvider, str]:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        return None, "Vendor not found"
    
    if vendor.otp_attempts >= MAX_OTP_ATTEMPTS:
        return None, "Maximum OTP attempts exceeded"
    
    if vendor.otp != otp:
        vendor.otp_attempts += 1
        db.commit()
        return None, "Invalid OTP"
    
    if (datetime.utcnow() - vendor.otp_created_at) > timedelta(minutes=OTP_EXPIRY_MINUTES):
        return None, "OTP expired"
    
    vendor.otp_verified = True
    vendor.otp_attempts = 0
    vendor.status = VendorStatus.PENDING
    vendor.last_login = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    return vendor, "OTP verified successfully"

def resend_otp(db: Session, email: str) -> None:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if vendor.otp_last_sent and (datetime.utcnow() - vendor.otp_last_sent) < timedelta(minutes=OTP_RESEND_COOLDOWN_MINUTES):
        raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")
    
    if vendor.otp_attempts >= MAX_OTP_RESENDS:
        raise HTTPException(status_code=429, detail="Maximum OTP resend attempts exceeded")
    
    otp = generate_otp()
    vendor.otp = otp
    vendor.otp_created_at = datetime.utcnow()
    vendor.otp_last_sent = datetime.utcnow()
    vendor.otp_attempts = 0
    send_email_otp(email, otp)
    db.commit()

def complete_vendor_profile(db: Session, vendor_id: int, update: ServiceProviderUpdate) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    if update.terms_accepted is not None and not update.terms_accepted:
        raise HTTPException(status_code=400, detail="Terms and conditions must be accepted")
    
    # Update basic fields
    for field, value in update.dict(exclude_unset=True, exclude={"subcategory_charges"}).items():
        setattr(vendor, field, value)
    
    # Update subcategory charges
    if update.subcategory_charges is not None:
        # Clear existing charges
        db.execute(vendor_subcategory_charges.delete().where(vendor_subcategory_charges.c.vendor_id == vendor_id))
        # Add new charges
        for charge in update.subcategory_charges:
            if charge.service_charge < 0:
                raise HTTPException(status_code=400, detail="Service charge cannot be negative")
            subcategory = get_subcategory_by_id(db, charge.subcategory_id)
            if not subcategory:
                raise HTTPException(status_code=404, detail=f"Subcategory {charge.subcategory_id} not found")
            db.execute(
                vendor_subcategory_charges.insert().values(
                    vendor_id=vendor_id,
                    subcategory_id=charge.subcategory_id,
                    service_charge=charge.service_charge
                )
            )
    
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def update_vendor_device(db: Session, vendor_id: int, update: ServiceProviderDeviceUpdate) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def change_vendor_status(db: Session, vendor_id: int, status: VendorStatus, admin=Depends(get_current_admin)) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.status = status
    db.commit()
    db.refresh(vendor)
    
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def upload_profile_pic(db: Session, vendor_id: int, file: UploadFile) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    file_extension = file.filename.split(".")[-1]
    file_path = f"uploads/profiles/{vendor_id}.{file_extension}"
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    vendor.profile_pic = file_path
    db.commit()
    db.refresh(vendor)
    
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor
