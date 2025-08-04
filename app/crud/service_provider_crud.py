from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.utils.otp_utils import generate_otp, send_email_otp
from app.core.security import get_password_hash
from app.models.service_provider_model import ServiceProvider,  VendorStatus, vendor_subcategory_charges
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    VendorCreate, VendorDeviceUpdate, AddressDetailsUpdate, 
    BankDetailsUpdate, WorkDetailsUpdate, SubCategoryCharge
)

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

def create_vendor(db: Session, vendor: VendorCreate) -> ServiceProvider:
    existing = get_vendor_by_email(db, vendor.email)
    if existing and existing.otp_verified:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if existing and not existing.otp_verified:
        existing.full_name = vendor.full_name
        existing.phone = vendor.phone
        existing.password = get_password_hash(vendor.password)
        existing.terms_accepted = vendor.terms_accepted
        existing.fcm_token = vendor.fcm_token
        existing.latitude = vendor.latitude
        existing.longitude = vendor.longitude
        existing.device_name = vendor.device_name
        existing.otp = generate_otp()
        existing.otp_created_at = datetime.utcnow()
        existing.otp_last_sent = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        send_email_otp(vendor.email, existing.otp)
        return existing
    
    hashed_password = get_password_hash(vendor.password)
    otp = generate_otp()
    now = datetime.utcnow()
    
    db_vendor = ServiceProvider(
        **vendor.dict(exclude={"password"}),
        password=hashed_password,
        otp=otp,
        otp_created_at=now,
        otp_last_sent=now,
        otp_verified=False,
        last_login=now,
        last_device_update=now,
        status=VendorStatus.PENDING
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
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

def update_vendor_address(db: Session, vendor_id: int, update: AddressDetailsUpdate) -> ServiceProvider:
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
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def update_vendor_bank(db: Session, vendor_id: int, update: BankDetailsUpdate) -> ServiceProvider:
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
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def update_vendor_work(db: Session, vendor_id: int, update: WorkDetailsUpdate) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    vendor.category_id = update.category_id
    
    db.execute(vendor_subcategory_charges.delete().where(vendor_subcategory_charges.c.vendor_id == vendor_id))
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
    
    vendor.status = VendorStatus.APPROVED
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def update_vendor_documents(db: Session, vendor_id: int, profile_pic: UploadFile, document_file: UploadFile) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    profile_pic_extension = profile_pic.filename.split(".")[-1]
    profile_pic_path = f"uploads/profiles/{vendor_id}.{profile_pic_extension}"
    with open(profile_pic_path, "wb") as buffer:
        buffer.write(profile_pic.file.read())
    
    document_extension = document_file.filename.split(".")[-1]
    document_path = f"uploads/documents/{vendor_id}.{document_extension}"
    with open(document_path, "wb") as buffer:
        buffer.write(document_file.file.read())
    
    vendor.profile_pic_url = profile_pic_path
    vendor.document_url = document_path
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def update_vendor_device(db: Session, vendor_id: int, update: VendorDeviceUpdate) -> ServiceProvider:
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
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

def change_vendor_status(db: Session, vendor_id: int, status: VendorStatus) -> ServiceProvider:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.status = status
    db.commit()
    db.refresh(vendor)
    
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor_id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor