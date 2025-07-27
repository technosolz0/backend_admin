from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_db, create_access_token, get_current_vendor, get_password_hash
from app.schemas.service_provider_schema import (
    ServiceProviderCreate, ServiceProviderUpdate, ServiceProviderOut,
    VendorOTPRequest, VendorOTPVerify, VendorResetPassword
)
from app.crud import service_provider_crud as crud
from app.models.service_provider_model import ServiceProvider

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.post("/register-otp")
def register_vendor_with_otp(data: ServiceProviderCreate, db: Session = Depends(get_db)):
    existing = crud.get_vendor_by_email(db, data.email)
    if existing:
        if existing.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")
        otp = crud.resend_otp(db, data.email)
        return {"message": "OTP resent to unverified email."}
    vendor, otp = crud.create_vendor_with_otp(db, data)
    return {"message": "OTP sent to your email."}

@router.post("/verify-otp")
def verify_vendor_otp(data: VendorOTPVerify, db: Session = Depends(get_db)):
    result = crud.verify_otp(db, data.email, data.otp)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if result == "expired":
        raise HTTPException(status_code=400, detail="OTP expired")
    token = create_access_token({"sub": result.email})
    return {
        "message": "Vendor verified successfully.",
        "access_token": token,
        "token_type": "bearer",
        "vendor": {
            "id": result.id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone
        }
    }

@router.post("/resend-otp")
def resend_vendor_otp(data: VendorOTPRequest, db: Session = Depends(get_db)):
    otp = crud.resend_otp(db, data.email)
    if not otp:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"message": "New OTP sent to your email."}

@router.post("/send-login-otp")
def send_vendor_login_otp(data: VendorOTPRequest, db: Session = Depends(get_db)):
    otp = crud.create_login_otp(db, data.email)
    if not otp:
        raise HTTPException(status_code=404, detail="Vendor not found or not verified")
    return {"message": "Login OTP sent successfully."}

@router.post("/verify-login-otp")
def verify_vendor_login_otp(data: VendorOTPVerify, db: Session = Depends(get_db)):
    result = crud.verify_login_otp(db, data.email, data.otp)
    if result is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if result == "invalid":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if result == "expired":
        raise HTTPException(status_code=400, detail="OTP expired")
    token = create_access_token({"sub": result.email})
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "vendor": {
            "id": result.id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone
        }
    }

@router.post("/reset-password")
def reset_vendor_password(data: VendorResetPassword, db: Session = Depends(get_db)):
    vendor = crud.get_vendor_by_email(db, data.email)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.password_hash = get_password_hash(data.new_password)
    db.commit()
    db.refresh(vendor)
    return {"message": "Password reset successfully."}

@router.get("/me", response_model=ServiceProviderOut)
def get_current_vendor_profile(current_vendor: ServiceProvider = Depends(get_current_vendor)):
    return current_vendor

@router.get("/", response_model=list[ServiceProviderOut])
def list_vendors(db: Session = Depends(get_db)):
    return crud.get_all_providers(db)

@router.get("/{vendor_id}", response_model=ServiceProviderOut)
def get_vendor_by_id(vendor_id: int, db: Session = Depends(get_db)):
    vendor = crud.get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.put("/{vendor_id}", response_model=ServiceProviderOut)
def update_vendor(vendor_id: int, data: ServiceProviderUpdate, db: Session = Depends(get_db)):
    updated = crud.update_vendor(db, vendor_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return updated

@router.post("/{vendor_id}/toggle-status", response_model=ServiceProviderOut)
def toggle_vendor_status(vendor_id: int, db: Session = Depends(get_db)):
    vendor = crud.toggle_vendor_status(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.post("/{vendor_id}/toggle-work-status", response_model=ServiceProviderOut)
def toggle_vendor_work_status(vendor_id: int, db: Session = Depends(get_db)):
    vendor = crud.toggle_work_status(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    success = crud.delete_vendor(db, vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")