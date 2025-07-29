from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.service_provider_schema import (
    ServiceProviderCreate, ServiceProviderDeviceUpdate, ServiceProviderOut, ServiceProviderUpdate, SubCategoryCharge,
    VendorOTPRequest, VendorOTPVerify, VendorResetPassword, ServiceProviderLoginResponse
)
from passlib.context import CryptContext
from app.utils.otp_utils import generate_otp, send_email_otp
from app.core.security import create_access_token, get_db, get_current_vendor, get_current_admin
import enum
import os
from app.core.security import create_access_token, get_db, get_current_vendor
from app.crud import service_provider_crud as crud
from app.core.security import get_db, create_access_token, get_current_vendor
from app.models.service_provider_model import VendorStatus, vendor_subcategory_charges, WorkStatus


# Router
router = APIRouter(prefix="/vendor", tags=["Vendors"])

@router.post("/register", response_model=ServiceProviderOut)
def register_vendor(data: ServiceProviderCreate, db: Session = Depends(get_db)):
    if not data.terms_accepted:
        raise HTTPException(status_code=400, detail="Terms and conditions must be accepted")
    return crud.create_vendor(db, data)

@router.post("/send-otp")
def send_otp(data: VendorOTPRequest, db: Session = Depends(get_db)):
    crud.resend_otp(db, data.email)
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=ServiceProviderLoginResponse)
def verify_otp(data: VendorOTPVerify, db: Session = Depends(get_db)):
    vendor, msg = crud.verify_vendor_otp(db, data.email, data.otp)
    if not vendor:
        raise HTTPException(status_code=400, detail=msg)
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor.id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    token = create_access_token({"sub": vendor.email, "vendor_id": vendor.id})
    return ServiceProviderLoginResponse(access_token=token, vendor=vendor)

@router.post("/login", response_model=ServiceProviderLoginResponse)
def login_vendor(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    vendor = crud.get_vendor_by_email(db, data.username)
    if not vendor or not crud.verify_password(data.password, vendor.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not vendor.otp_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OTP verification required")
    if not vendor.terms_accepted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Terms and conditions not accepted")
    vendor.last_login = datetime.utcnow()
    db.commit()
    # Populate subcategory charges for response
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor.id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    token = create_access_token({"sub": vendor.email, "vendor_id": vendor.id})
    return ServiceProviderLoginResponse(access_token=token, vendor=vendor)

@router.put("/profile/complete", response_model=ServiceProviderOut)
def complete_profile(
    data: ServiceProviderUpdate,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor)
):
    return crud.complete_vendor_profile(db, current_vendor.id, data)

@router.put("/device/update", response_model=ServiceProviderOut)
def update_device_details(
    data: ServiceProviderDeviceUpdate,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor)
):
    return crud.update_vendor_device(db, current_vendor.id, data)

@router.post("/profile/upload-pic", response_model=ServiceProviderOut)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor)
):
    return crud.upload_profile_pic(db, current_vendor.id, file)

@router.put("/status/{vendor_id}/{status}", response_model=ServiceProviderOut)
def update_status(
    vendor_id: int,
    status: VendorStatus,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    return crud.change_vendor_status(db, vendor_id, status, admin)

@router.get("/me", response_model=ServiceProviderOut)
def get_me(vendor=Depends(get_current_vendor), db: Session = Depends(get_db)):
    charges = db.execute(
        vendor_subcategory_charges.select().where(vendor_subcategory_charges.c.vendor_id == vendor.id)
    ).fetchall()
    vendor.subcategory_charges = [
        SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
        for charge in charges
    ]
    return vendor

@router.post("/reset-password")
def reset_password(data: VendorResetPassword, db: Session = Depends(get_db)):
    vendor = crud.get_vendor_by_email(db, data.email)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    vendor.password = crud.get_password_hash(data.password)
    db.commit()
    return {"message": "Password reset successfully"}