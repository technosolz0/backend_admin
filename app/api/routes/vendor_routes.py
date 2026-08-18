from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.vendor_model import Vendor
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    PaginatedVendorsResponse, VendorCreate, VendorResponse, OTPRequest, OTPVerify,
    AddressDetailsUpdate, BankDetailsUpdate, WorkDetailsUpdate, VendorLoginRequest,
    VendorChangePasswordRequest, VendorPasswordResetRequest, VendorPasswordResetConfirm
)
from app.core.security import create_access_token, get_current_vendor, get_db
from app.crud.vendor_crud import (
    create_vendor, verify_vendor_otp, resend_otp,
    update_vendor_address, update_vendor_bank, update_vendor_work, 
    update_vendor_documents, change_vendor_admin_status, change_vendor_work_status, 
    vendor_login, get_all_vendors, delete_vendor, build_vendor_response,
    change_vendor_password
)
from app.schemas.category_schema import CategoryOut
from app.schemas.sub_category_schema import SubCategoryOut
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendor", tags=["Vendor"])


# =================== REGISTRATION ENDPOINTS ===================

@router.post("/register", response_model=dict, status_code=status.HTTP_200_OK)
def register_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    """Register a new vendor and send OTP."""
    result = create_vendor(db, vendor)
    
    if not result["success"]:
        logger.error(f"Vendor registration failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Vendor registration OTP sent: {vendor.email}")
    return {
        "success": True,
        "message": result["message"],
        "vendor_id": result["data"]["vendor_id"],
        "step": result["data"]["step"]
    }


@router.post("/verify-otp", response_model=dict, status_code=status.HTTP_200_OK)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP for vendor email verification."""
    result = verify_vendor_otp(db, email=data.email, otp=data.otp, phone=data.phone)
    
    if not result["success"]:
        logger.error(f"Vendor OTP verification failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    vendor = result["data"]
    
    access_token = create_access_token(
        data={"sub": vendor.email},
        role="vendor"
    )
    
    refresh_token = create_access_token(
        data={"sub": vendor.email},
        token_type="refresh",
        role="vendor"
    )
    
    logger.info(f"Vendor OTP verified successfully: {data.email}")
    return {
        "success": True,
        "message": result["message"],
        "vendor_id": vendor.id,
        "step": vendor.step,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "vendor": vendor
    }


@router.post("/resend-otp", response_model=dict, status_code=status.HTTP_200_OK)
def resend_vendor_otp(data: OTPRequest, db: Session = Depends(get_db)):
    """Resend OTP to vendor email."""
    result = resend_otp(db, email=data.email)
    
    if not result["success"]:
        logger.error(f"Failed to resend OTP to {data.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"OTP resent to {data.email}")
    return {
        "success": True,
        "message": result["message"]
    }


# =================== LOGIN ENDPOINTS ===================

@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
def login(credentials: VendorLoginRequest, db: Session = Depends(get_db)):
    """Login vendor with email and password."""
    result = vendor_login(db, email=credentials.email, password=credentials.password)
    
    if not result["success"]:
        logger.error(f"Vendor login failed for {credentials.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    vendor = result["data"]
    
    access_token = create_access_token(
        data={"sub": vendor.email},
        role="vendor"
    )
    
    refresh_token = create_access_token(
        data={"sub": vendor.email},
        token_type="refresh",
        role="vendor"
    )
    
    logger.info(f"Vendor logged in: {credentials.email}")
    return {
        "success": True,
        "message": result["message"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "vendor": vendor
    }


# =================== PASSWORD RESET ===================

@router.post("/forgot-password", response_model=dict, status_code=status.HTTP_200_OK)
def forgot_password(data: VendorPasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset OTP."""
    from app.crud.vendor_crud import request_vendor_password_reset
    result = request_vendor_password_reset(db, email=data.email)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "success": True,
        "message": result["message"]
    }


@router.post("/reset-password", response_model=dict, status_code=status.HTTP_200_OK)
def reset_password(data: VendorPasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with OTP."""
    from app.crud.vendor_crud import confirm_vendor_password_reset
    result = confirm_vendor_password_reset(db, email=data.email, otp=data.otp, new_password=data.new_password)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "success": True,
        "message": result["message"]
    }


# =================== VENDOR PROFILE ENDPOINTS ===================

@router.get("/me", response_model=VendorResponse)
def get_vendor_profile(
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Get current logged-in vendor's profile."""
    return build_vendor_response(db, current_vendor)


@router.put("/update-address", response_model=VendorResponse)
def update_address(
    update: AddressDetailsUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Update address details."""
    return update_vendor_address(db, current_vendor.id, update)


@router.put("/update-bank", response_model=VendorResponse)
def update_bank(
    update: BankDetailsUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Update bank details."""
    return update_vendor_bank(db, current_vendor.id, update)


@router.put("/update-work", response_model=VendorResponse)
def update_work(
    update: WorkDetailsUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Update work details."""
    return update_vendor_work(db, current_vendor.id, update)


@router.put("/update-documents", response_model=VendorResponse)
def update_documents(
    profile_pic: UploadFile = File(None),
    identity_doc: UploadFile = File(...),
    bank_doc: UploadFile = File(...),
    address_doc: UploadFile = File(...),
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Update document uploads."""
    return update_vendor_documents(
        db, current_vendor.id, profile_pic, identity_doc, bank_doc, address_doc
    )


@router.put("/change-password", response_model=dict)
def change_password(
    data: VendorChangePasswordRequest,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Change current logged-in vendor's password."""
    result = change_vendor_password(db, current_vendor.id, data.old_password, data.new_password)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return {"success": True, "message": result["message"]}


@router.put("/work-status", response_model=VendorResponse)
def update_work_status(
    work_status: str = Body(..., embed=True),
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Update vendor work status (work_on / work_off)."""
    return change_vendor_work_status(db, current_vendor.id, work_status)


# =================== ADMIN & PUBLIC ENDPOINTS ===================

@router.get("/all", response_model=PaginatedVendorsResponse)
def get_vendors(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of vendors."""
    vendors, total = get_all_vendors(db, page=page, limit=limit, search=search, status=status)
    return PaginatedVendorsResponse(
        vendors=vendors,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.delete("/{vendor_id}", response_model=dict)
def remove_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """Delete vendor by ID."""
    delete_vendor(db, vendor_id)
    return {"success": True, "message": f"Vendor {vendor_id} deleted successfully"}


@router.put("/{vendor_id}/admin-status", response_model=VendorResponse)
def update_admin_status(
    vendor_id: int,
    admin_status: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Update vendor admin status (active / inactive)."""
    return change_vendor_admin_status(db, vendor_id, admin_status)
