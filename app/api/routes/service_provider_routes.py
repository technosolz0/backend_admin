# app/api/service_provider_routes.py - Fixed with proper error handling

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.service_provider_model import ServiceProvider
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    PaginatedVendorsResponse, VendorCreate, VendorResponse, OTPRequest, OTPVerify,
    AddressDetailsUpdate, BankDetailsUpdate, WorkDetailsUpdate, VendorLoginRequest,
    VendorChangePasswordRequest, VendorPasswordResetRequest, VendorPasswordResetConfirm
)
from app.core.security import create_access_token, get_current_vendor, get_db
from app.crud.service_provider_crud import (
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
    """
    Register a new vendor and send OTP.
    
    Returns:
    - 200: OTP sent successfully
    - 400: Registration failed (email already exists, etc.)
    """
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
    """
    Verify OTP for vendor email verification.
    
    Returns:
    - 200: OTP verified successfully with access token
    - 400: Verification failed (invalid OTP, expired, etc.)
    """
    result = verify_vendor_otp(db, data.email, data.otp)
    
    if not result["success"]:
        logger.error(f"Vendor OTP verification failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    vendor = result["data"]
    
    # ✅ Generate access token with role="vendor"
    access_token = create_access_token(
        data={"sub": vendor.email},
        role="vendor"
    )
    
    # ✅ Generate refresh token (30 days)
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


@router.post("/send-otp", response_model=dict, status_code=status.HTTP_200_OK)
def resend_otp_endpoint(data: OTPRequest, db: Session = Depends(get_db)):
    """
    Resend OTP to the vendor's email.
    
    Returns:
    - 200: OTP resent successfully
    - 400: Resend failed (cooldown, max attempts, etc.)
    """
    result = resend_otp(db, data.email)
    
    if not result["success"]:
        logger.error(f"Vendor OTP resend failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Vendor OTP resent successfully: {data.email}")
    return {
        "success": True,
        "message": result["message"]
    }


# =================== LOGIN ENDPOINT ===================

@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
def vendor_login_endpoint(data: VendorLoginRequest, db: Session = Depends(get_db)):
    """
    Login vendor with email and password.
    
    Returns:
    - 200: Login successful with access token
    - 401: Authentication failed with specific error message
    """
    result = vendor_login(db, data.email, data.password)
    
    if not result["success"]:
        logger.error(f"Vendor login failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    vendor = result["data"]
    
    # ✅ Generate access token with role="vendor"
    access_token = create_access_token(
        data={"sub": vendor.email},
        role="vendor"  # Important: Specify role for vendor authentication
    )

    # ✅ Generate refresh token (30 days)
    refresh_token = create_access_token(
        data={"sub": vendor.email},
        token_type="refresh",
        role="vendor"
    )

    logger.info(f"Vendor logged in successfully: {data.email}")
    return {
        "success": True,
        "message": result["message"],
        "access_token": access_token,
        "refresh_token": refresh_token,  # ✅ Add refresh token
        "token_type": "bearer",
        "vendor": vendor
    }


# =================== LOGOUT ENDPOINT ===================

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_vendor(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Logout vendor and clear FCM token to stop notifications.
    """
    current_vendor.new_fcm_token = None
    db.commit()
    logger.info(f"Vendor logged out: {current_vendor.email}")
    return {"success": True, "message": "Logged out successfully"}


# =================== PASSWORD MANAGEMENT ===================

@router.post("/change-password", response_model=dict, status_code=status.HTTP_200_OK)
def change_password_endpoint(
    data: VendorChangePasswordRequest,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Change vendor password.
    """
    result = change_vendor_password(db, current_vendor.id, data.old_password, data.new_password)
    
    if not result["success"]:
        logger.error(f"Vendor password change failed for {current_vendor.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Vendor password changed successfully: {current_vendor.email}")
    return {
        "success": True,
        "message": result["message"]
    }


# =================== PASSWORD RESET ===================

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def request_password_reset_vendor_endpoint(
    data: VendorPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset OTP for a vendor."""
    from app.crud.service_provider_crud import request_vendor_password_reset
    
    result = request_vendor_password_reset(db, data.email)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": result["message"]}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset_vendor_endpoint(
    data: VendorPasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with OTP for a vendor."""
    from app.crud.service_provider_crud import confirm_vendor_password_reset
    
    result = confirm_vendor_password_reset(db, data.email, data.otp, data.new_password)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": result["message"]}


# =================== VENDOR PROFILE ENDPOINTS ===================

@router.get("/me", response_model=VendorResponse)
def get_me(
    current_vendor: ServiceProvider = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    """Retrieve the current vendor's details."""
    try:
        vendor_response = build_vendor_response(db, current_vendor)
        logger.info(f"Vendor details retrieved: {current_vendor.id}")
        return vendor_response
    except Exception as e:
        logger.error(f"Error retrieving vendor details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor_by_id(vendor_id: int, db: Session = Depends(get_db)):
    """Retrieve vendor details by vendor_id."""
    try:
        vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The requested vendor profile could not be found."
            )
        vendor_response = build_vendor_response(db, vendor)
        return vendor_response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We experienced an error retrieving the profile. Please try again."
        )


# =================== PROFILE UPDATE ENDPOINTS ===================

@router.put("/profile/address", response_model=VendorResponse)
def update_address_details(
    vendor_id: int = Form(...),
    address: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    address_doc_type: str = Form(...),
    address_doc_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor address details."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        update = AddressDetailsUpdate(
            address=address,
            state=state,
            city=city,
            pincode=pincode,
            address_doc_type=address_doc_type,
            address_doc_number=address_doc_number
        )
        vendor = update_vendor_address(db, vendor_id, update)
        logger.info(f"Address updated for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating address for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't update your address. Please try again later."
        )


@router.put("/profile/bank", response_model=VendorResponse)
def update_bank_details(
    vendor_id: int = Form(...),
    account_holder_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    upi_id: Optional[str] = Form(None),
    bank_doc_type: str = Form(...),
    bank_doc_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor bank details."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        update = BankDetailsUpdate(
            account_holder_name=account_holder_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            upi_id=upi_id,
            bank_doc_type=bank_doc_type,
            bank_doc_number=bank_doc_number
        )
        vendor = update_vendor_bank(db, vendor_id, update)
        logger.info(f"Bank details updated for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating bank details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't update your bank details. Please try again later."
        )


@router.put("/profile/work", response_model=VendorResponse)
def update_work_details(
    vendor_id: int = Body(...),
    update: WorkDetailsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work details."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        vendor = update_vendor_work(db, vendor_id, update)
        logger.info(f"Work details updated for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating work details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't update your work details. Please try again later."
        )


@router.patch("/profile/work", response_model=VendorResponse)
def patch_work_details(
    vendor_id: int = Body(...),
    update: WorkDetailsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Patch vendor work details (merge/update without deleting other categories)."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        vendor = update_vendor_work(db, vendor_id, update)
        logger.info(f"Work details patched for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error patching work details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't update your work details. Please try again later."
        )


@router.post("/profile/documents", response_model=VendorResponse)
def upload_documents(
    vendor_id: int = Form(...),
    profile_pic: UploadFile = File(None),
    identity_doc: UploadFile = File(...),
    bank_doc: UploadFile = File(...),
    address_doc: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Upload vendor documents."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        vendor = update_vendor_documents(
            db, vendor_id, profile_pic, identity_doc, bank_doc, address_doc
        )
        logger.info(f"Documents uploaded for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading documents for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't upload your documents. Please try again later."
        )


@router.put("/profile/work-status", response_model=VendorResponse)
def update_work_status(
    vendor_id: int = Form(...),
    work_status: str = Form(..., pattern="^(work_on|work_off)$"),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work status."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this profile."
            )
        vendor = change_vendor_work_status(db, vendor_id, work_status)
        logger.info(f"Work status updated for vendor: {vendor_id}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating work status for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# =================== ADMIN ENDPOINTS ===================

@router.get("", response_model=PaginatedVendorsResponse)
def get_all_vendors_endpoint(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """Get all vendors with pagination, search, and status filters."""
    try:
        vendors, total = get_all_vendors(db, page, limit, search, status)
        return {"vendors": vendors, "total": total}
    except Exception as e:
        logger.error(f"Error in get_all_vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{vendor_id}")
def delete_vendor_endpoint(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Delete a vendor by ID."""
    try:
        if current_vendor.id != vendor_id:
            logger.warning(f"Unauthorized delete attempt: vendor {current_vendor.id} → {vendor_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this vendor"
            )
        delete_vendor(db, vendor_id)
        logger.info(f"Vendor deleted successfully: {vendor_id}")
        return {"message": "Vendor deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/admin/status", response_model=VendorResponse)
def update_admin_status(
    vendor_id: int = Form(...),
    admin_status: str = Form(..., pattern="^(active|inactive)$"),
    db: Session = Depends(get_db)
):
    """Update vendor admin status."""
    try:
        vendor = change_vendor_admin_status(db, vendor_id, admin_status)
        logger.info(f"Admin status updated for vendor {vendor_id}: {admin_status}")
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating admin status for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# =================== UTILITY ENDPOINTS ===================

@router.get("/categories", response_model=List[CategoryOut])
def list_all_categories(db: Session = Depends(get_db)):
    """Get all active categories."""
    return db.query(Category).filter(Category.status == 'active').all()


@router.get("/subcategories", response_model=List[SubCategoryOut])
def get_subcategories(
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieve active subcategories, optionally filtered by category_id."""
    query = db.query(SubCategory).filter(SubCategory.status == 'active')
    if category_id:
        query = query.filter(SubCategory.category_id == category_id)
    return query.all()


# =================== REFRESH TOKEN ENDPOINT ===================

@router.post("/refresh-token", response_model=dict, status_code=status.HTTP_200_OK)
def refresh_vendor_token(
    refresh_data: dict,  # {"refresh_token": "..."}
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token for vendors.

    Returns:
    - 200: New access token generated successfully
    - 401: Invalid or expired refresh token
    """
    from jose import jwt, JWTError, ExpiredSignatureError
    from app.core.security import SECRET_KEY, ALGORITHM

    refresh_token = refresh_data.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )

    try:
        # Decode and validate refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        email = payload.get("sub")
        role = payload.get("role", "vendor")

        if not email or role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Verify vendor still exists and is active
        vendor = db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vendor not found"
            )

        # Check if vendor is active
        if vendor.admin_status != 'active':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": email},
            role="vendor"
        )

        # Generate new refresh token (rotation)
        new_refresh_token = create_access_token(
            data={"sub": email},
            token_type="refresh",
            role="vendor"
        )

        logger.info(f"Access token refreshed for vendor: {email}")
        return {
            "success": True,
            "message": "Access token refreshed successfully",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# =================== DEVICE / LOCATION UPDATE ENDPOINT ===================

@router.put("/device/update")
def update_device_details(
    vendor_id: int = Body(...),
    fcm_token: Optional[str] = Body(None),
    latitude: Optional[float] = Body(None),
    longitude: Optional[float] = Body(None),
    device_name: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Update vendor device details: FCM token, GPS location, and device name.
    Called after login to keep vendor location and notification token up-to-date.
    """
    import datetime

    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this vendor's device details"
            )

        vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )

        # Update only provided fields
        if fcm_token is not None:
            vendor.new_fcm_token = fcm_token
        if latitude is not None:
            vendor.latitude = latitude
        if longitude is not None:
            vendor.longitude = longitude
        if device_name is not None:
            vendor.device_name = device_name

        vendor.last_device_update = datetime.datetime.utcnow()

        db.commit()
        db.refresh(vendor)

        logger.info(
            f"Device details updated for vendor {vendor_id}: "
            f"lat={latitude}, lon={longitude}, device={device_name}"
        )

        return {
            "success": True,
            "message": "Device details updated successfully",
            "vendor_id": vendor_id,
            "latitude": vendor.latitude,
            "longitude": vendor.longitude,
            "device_name": vendor.device_name,
            "last_device_update": vendor.last_device_update.isoformat() if vendor.last_device_update else None
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating device details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# =================== LOCATION-BASED VENDOR FILTERING ===================

@router.get("/nearby/{category_id}/{subcategory_id}")
def get_nearby_vendors(
    category_id: int,
    subcategory_id: int,
    user_lat: float,
    user_lng: float,
    user_pincode: Optional[str] = Query(None),
    radius_km: float = 5.0,  # Default 5km radius
    db: Session = Depends(get_db)
):
    """
    Get vendors within specified radius of user's location OR matching user's PIN code.

    Parameters:
    - category_id: Service category ID
    - subcategory_id: Service subcategory ID
    - user_lat: User's latitude
    - user_lng: User's longitude
    - user_pincode: User's pincode (Optional, for fallback matching)
    - radius_km: Search radius in kilometers (default: 5.0)

    Returns:
    - List of vendors with their charges and distance from user
    """
    try:
        # Import math for distance calculation
        import math

        def calculate_distance(lat1, lng1, lat2, lng2):
            """Calculate distance between two points using Haversine formula."""
            if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
                return float('inf')
            
            R = 6371  # Earth's radius in kilometers

            lat1_rad = math.radians(lat1)
            lng1_rad = math.radians(lng1)
            lat2_rad = math.radians(lat2)
            lng2_rad = math.radians(lng2)

            dlat = lat2_rad - lat1_rad
            dlng = lng2_rad - lng1_rad

            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0, 1-a)))

            return R * c

        # Only active, approved and online vendors
        all_vendors_in_db = db.query(ServiceProvider).filter(
            ServiceProvider.category_id == category_id
        ).all()
        
        logger.info(f"📍 Nearby Search: Found {len(all_vendors_in_db)} total vendors for category {category_id}")

        vendors = [v for v in all_vendors_in_db if v.status == 'approved' and v.admin_status == 'active' and v.work_status == 'work_on']
        
        logger.info(f"📍 Nearby Search: {len(vendors)} vendors are approved, active, and ONLINE")

        nearby_vendors = []

        for vendor in vendors:
            # Check if vendor has charges for the requested subcategory
            vendor_charges = []
            for charge in vendor.subcategory_charges:
                if charge.subcategory_id == subcategory_id:
                    vendor_charges.append({
                        "subcategory_id": charge.subcategory_id,
                        "subcategory_name": charge.subcategory.name if charge.subcategory else "N/A",
                        "price": charge.service_charge,
                        "description": getattr(charge, 'description', '')
                    })

            # Skip vendor if no charges for this subcategory
            if not vendor_charges:
                continue

            # Calculate distance
            distance = calculate_distance(
                user_lat, user_lng,
                float(vendor.latitude) if vendor.latitude is not None else None, 
                float(vendor.longitude) if vendor.longitude is not None else None
                
            )

            # Fallback for unknown location: show all relevant vendors
            is_nearby = (distance <= radius_km)
            is_same_pincode = (user_pincode and vendor.pincode == user_pincode)
            location_unknown = (user_lat == 0.0 and user_lng == 0.0 and not user_pincode)

            if location_unknown or is_nearby or is_same_pincode:
                vendor_data = {
                    "id": vendor.id,
                    "full_name": vendor.full_name,
                    "email": vendor.email,
                    "phone": vendor.phone,
                    "profile_pic": vendor.profile_pic,
                    "pincode": vendor.pincode,
                    "latitude": vendor.latitude,
                    "longitude": vendor.longitude,
                    "distance_km": round(distance, 2) if distance != float('inf') else None,
                    "work_status": vendor.work_status,
                    "admin_status": vendor.admin_status,
                    "charges": vendor_charges
                }
                
                # Dynamically handle model differences safely
                for field in ['rating', 'total_reviews', 'experience_years', 'description']:
                    if hasattr(vendor, field):
                        vendor_data[field] = getattr(vendor, field)
                
                nearby_vendors.append(vendor_data)

        # Sort by distance (closest first), placing those with distance None at the end
        nearby_vendors.sort(key=lambda x: (x['distance_km'] is None, x['distance_km']))

        logger.info(f"Found {len(nearby_vendors)} vendors for user at location ({user_lat}, {user_lng}) and pincode {user_pincode}")

        if not nearby_vendors:
            return {
                "success": True,
                "count": 0,
                "message": "Vendor Coming Soon in Your Area",
                "vendors": []
            }

        return {
            "success": True,
            "count": len(nearby_vendors),
            "message": "Vendors available in your area.",
            "vendors": nearby_vendors
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error fetching nearby vendors: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
