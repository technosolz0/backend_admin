

# from fastapi import APIRouter, Depends, HTTPException, status, Request
# from sqlalchemy.orm import Session
# from app.core.security import create_access_token, get_current_user, get_db
# from app.schemas import user_schema
# from app.crud import user as crud_user
# from app.models.user import User
# from app.core.dependencies import get_super_admin
# import logging

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/users", tags=["User Management & Auth"])

# @router.post("/register-otp", response_model=dict)
# def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
#     """Register a new user and send OTP for email verification."""
#     result = crud_user.create_user_with_otp(db, user)
#     if not result["success"]:
#         logger.error(f"Registration failed: {result['message']}")
#         raise HTTPException(status_code=400, detail=result["message"])

#     logger.info(f"User registration OTP sent: {user.email}")
#     return {
#         "message": result["message"],
#         "user": user_schema.UserOut.from_orm(result["data"]) if result["data"] else None
#     }


# @router.post("/verify-otp", response_model=dict)
# def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
#     """Verify OTP for user email verification."""
#     result = crud_user.verify_otp(db, data.email, data.otp)
#     if not result["success"]:
#         logger.error(f"OTP verification failed for {data.email}: {result['message']}")
#         raise HTTPException(status_code=400, detail=result["message"])

#     access_token = create_access_token(data={"sub": result["data"].email})
#     logger.info(f"User verified successfully: {data.email}")
#     return {
#         "message": "Email verified successfully. You can now login.",
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": user_schema.UserOut.from_orm(result["data"])
#     }


# @router.post("/resend-otp", response_model=dict)
# def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
#     """Resend OTP for email verification."""
#     result = crud_user.resend_otp(db, data.email)
#     if not result["success"]:
#         logger.error(f"OTP resend failed: {result['message']}")
#         raise HTTPException(status_code=404, detail=result["message"])

#     logger.info(f"OTP resent successfully for {data.email}")
#     return {
#         "message": result["message"],
#         "otp": result.get("otp")  # optional, can remove in production
#     }

# @router.post("/login")
# def login_user(login_data: user_schema.LoginRequest, db: Session = Depends(get_db)):
#     """
#     Login user with email and password.
#     Returns access token and user data.
#     """
#     user = crud_user.authenticate_user(
#         db,
#         email=login_data.email,
#         password=login_data.password,
#         new_fcm_token=login_data.fcm_token if hasattr(login_data, "fcm_token") else None,
#         device_id=login_data.device_id if hasattr(login_data, "device_id") else None,
#         device_type=login_data.device_type if hasattr(login_data, "device_type") else None,
#         os_version=login_data.os_version if hasattr(login_data, "os_version") else None,
#         app_version=login_data.app_version if hasattr(login_data, "app_version") else None,
#     )

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password, or user not verified",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     access_token = create_access_token(data={"sub": user.email})

#     return {
#         "message": "Login successful",
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": user.id,
#             "name": user.name,
#             "email": user.email,
#             "mobile": user.mobile,
#             "last_login_at": user.last_login_at,
#             "fcm_token": user.new_fcm_token,
#             "addresses": [
#                 {
#                     "id": addr.id,
#                     "name": addr.name,
#                     "phone": addr.phone,
#                     "address": addr.address,
#                     "landmark": addr.landmark,
#                     "city": addr.city,
#                     "state": addr.state,
#                     "pincode": addr.pincode,
#                     "country": addr.country,
#                     "address_type": addr.address_type,
#                     "is_default": addr.is_default
#                 }
#                 for addr in user.addresses
#             ],
#             "default_address": next((addr for addr in user.addresses if addr.is_default), None)
#         }
#     }
# @router.post("/password-reset/request", response_model=dict)
# def request_password_reset(request: user_schema.PasswordResetRequest, db: Session = Depends(get_db)):
#     """Request password reset OTP."""
#     success = crud_user.request_password_reset(db, request.email)
#     if not success:
#         logger.error(f"Password reset request failed for email: {request.email}")
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found or not verified"
#         )
#     logger.info(f"Password reset OTP sent for email: {request.email}")
#     return {"message": "Password reset OTP sent to your email"}

# @router.post("/password-reset/confirm", response_model=dict)
# def confirm_password_reset(confirm: user_schema.PasswordResetConfirm, db: Session = Depends(get_db)):
#     """Confirm password reset with OTP."""
#     success = crud_user.confirm_password_reset(db, confirm.email, confirm.otp, confirm.new_password)
#     if not success:
#         logger.error(f"Password reset failed for email: {confirm.email}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid OTP or expired"
#         )
#     logger.info(f"Password reset successful for email: {confirm.email}")
#     return {"message": "Password reset successfully"}

# @router.get("/me", response_model=user_schema.UserOut)
# def get_current_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """Get current user data."""
#     user = crud_user.get_user_by_id(db, current_user.id)
#     logger.info(f"User data retrieved for user ID: {current_user.id}")
#     return user

# @router.get("/admin-only", response_model=dict, dependencies=[Depends(get_super_admin)])
# def protected_admin_route():
#     """Protected route for super admins only."""
#     logger.info("Super admin accessed protected route")
#     return {"message": "You're a verified super admin ✅"}

# @router.get("/", response_model=list[user_schema.UserOut], dependencies=[Depends(get_super_admin)])
# def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     """List all users (super admin only)."""
#     users = crud_user.get_users(db, skip, limit)
#     logger.info(f"Retrieved {len(users)} users with skip={skip}, limit={limit}")
#     return users

# @router.get("/{user_id}", response_model=user_schema.UserOut)
# def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """Get user by ID (authenticated users, super admins can access any user)."""
#     if not current_user.is_superuser and current_user.id != user_id:
#         logger.error(f"User {current_user.id} attempted unauthorized access to user {user_id}")
#         raise HTTPException(status_code=403, detail="Not authorized to access this user")
#     user = crud_user.get_user_by_id(db, user_id)
#     if not user:
#         logger.error(f"User not found: {user_id}")
#         raise HTTPException(status_code=404, detail="User not found")
#     logger.info(f"User data retrieved for user ID: {user_id}")
#     return user

# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_super_admin)])
# def remove_user(user_id: int, db: Session = Depends(get_db)):
#     """Delete a user (super admin only)."""
#     if not crud_user.delete_user(db, user_id):
#         logger.error(f"Failed to delete user: {user_id}")
#         raise HTTPException(status_code=404, detail="User not found")
#     logger.info(f"User deleted successfully: {user_id}")

# @router.put("/{user_id}", response_model=user_schema.UserOut)
# def update_user(user_id: int, data: user_schema.UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """Update user data (self or super admin)."""
#     if not current_user.is_superuser and current_user.id != user_id:
#         logger.error(f"User {current_user.id} attempted unauthorized update of user {user_id}")
#         raise HTTPException(status_code=403, detail="Not authorized to update this user")
#     if data.is_superuser is not None and not current_user.is_superuser:
#         logger.error(f"User {current_user.id} attempted to update is_superuser")
#         raise HTTPException(status_code=403, detail="Only superusers can update is_superuser")
#     updated = crud_user.update_user(db, user_id, data, ip_address=None)
#     if not updated:
#         logger.error(f"Failed to update user: {user_id}")
#         raise HTTPException(status_code=404, detail="User not found")
#     logger.info(f"User updated successfully: {user_id}")
#     return updated

# @router.post("/{user_id}/toggle-status", response_model=user_schema.UserOut, dependencies=[Depends(get_super_admin)])
# def toggle_user_status(user_id: int, db: Session = Depends(get_db)):
#     """Toggle user status between active and blocked (super admin only)."""
#     user = crud_user.toggle_user_status(db, user_id)
#     if not user:
#         logger.error(f"Failed to toggle status for user: {user_id}")
#         raise HTTPException(status_code=404, detail="User not found")
#     logger.info(f"User status toggled to {user.status} for user: {user_id}")
#     return user

# @router.post("/me/fcm-token", response_model=dict)
# def update_fcm_token(
#     new_fcm_token: str,
#     device_id: str,
#     device_type: str = None,
#     os_version: str = None,
#     app_version: str = None,
#     request: Request = None,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Update FCM token and device details for the current user."""
#     updated_user = crud_user.update_user(
#         db,
#         current_user.id,
#         user_schema.UserUpdate(
#             new_fcm_token=new_fcm_token,
#             device_id=device_id,
#             device_type=device_type,
#             os_version=os_version,
#             app_version=app_version
#         ),
#         ip_address=request.client.host if request else None
#     )
#     if not updated_user:
#         logger.error(f"Failed to update FCM token for user: {current_user.id}")
#         raise HTTPException(status_code=400, detail="Failed to update FCM token")
#     logger.info(f"FCM token updated for user: {current_user.id}")
#     return {"message": "FCM token and device details updated successfully"}

# @router.post("/me/profile-pic", response_model=dict)
# def update_profile_pic(
#     profile_pic: str,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Update profile picture for the current user."""
#     updated_user = crud_user.update_user(
#         db,
#         current_user.id,
#         user_schema.UserUpdate(profile_pic=profile_pic)
#     )
#     if not updated_user:
#         logger.error(f"Failed to update profile picture for user: {current_user.id}")
#         raise HTTPException(status_code=400, detail="Failed to update profile picture")
#     logger.info(f"Profile picture updated for user: {current_user.id}")
#     return {"message": "Profile picture updated successfully", "profile_pic": updated_user.profile_pic}

# @router.delete("/me/profile-pic", response_model=dict)
# def clear_profile_pic(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """Clear profile picture for the current user."""
#     updated_user = crud_user.update_user(
#         db,
#         current_user.id,
#         user_schema.UserUpdate(profile_pic=None)
#     )
#     if not updated_user:
#         logger.error(f"Failed to clear profile picture for user: {current_user.id}")
#         raise HTTPException(status_code=400, detail="Failed to clear profile picture")
#     logger.info(f"Profile picture cleared for user: {current_user.id}")
#     return {"message": "Profile picture cleared successfully"}

# @router.get("/vendors-charges/{category_id}/{subcategory_id}", response_model=dict)
# def get_vendors_and_charges(
#     category_id: int,
#     subcategory_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get vendors and their charges for a category/subcategory."""
#     data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)
#     if not data:
#         logger.error(f"No vendors found for category {category_id}, subcategory {subcategory_id}")
#         raise HTTPException(status_code=404, detail="No vendors found for this category/subcategory")
#     logger.info(f"Retrieved vendors for category {category_id}, subcategory {subcategory_id}")
#     return data




# app/api/user_routes.py - Fixed with proper error handling

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, get_db
from app.schemas import user_schema
from app.crud import user as crud_user
from app.models.user import User
from app.core.dependencies import get_super_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management & Auth"])


# ================= REGISTRATION ENDPOINTS =================

@router.post("/register-otp", response_model=dict, status_code=status.HTTP_200_OK)
def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send OTP for email verification.
    
    Returns:
    - 200: OTP sent successfully
    - 400: Registration failed (email/mobile already exists, etc.)
    """
    result = crud_user.create_user_with_otp(db, user)
    
    if not result["success"]:
        logger.error(f"Registration failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    logger.info(f"User registration OTP sent: {user.email}")
    return {
        "success": True,
        "message": result["message"],
        "user": {
            "id": result["data"].id,
            "name": result["data"].name,
            "email": result["data"].email,
            "mobile": result["data"].mobile,
            "is_verified": result["data"].is_verified
        }
    }


@router.post("/verify-otp", response_model=dict, status_code=status.HTTP_200_OK)
def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP for user email verification.
    
    Returns:
    - 200: OTP verified successfully with access token
    - 400: Verification failed (invalid OTP, expired, user not found, etc.)
    """
    result = crud_user.verify_otp(db, data.email, data.otp)
    
    if not result["success"]:
        logger.error(f"OTP verification failed for {data.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    # Generate access token with role
    access_token = create_access_token(
        data={"sub": result["data"].email},
        role="user"  # ✅ Important: Specify role for user
    )
    
    logger.info(f"User verified successfully: {data.email}")
    return {
        "success": True,
        "message": result["message"],
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": result["data"].id,
            "name": result["data"].name,
            "email": result["data"].email,
            "mobile": result["data"].mobile,
            "is_verified": result["data"].is_verified,
            "profile_pic": result["data"].profile_pic
        }
    }


@router.post("/resend-otp", response_model=dict, status_code=status.HTTP_200_OK)
def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
    """
    Resend OTP for email verification.
    
    Returns:
    - 200: OTP resent successfully
    - 400: Resend failed (user not found, already verified, etc.)
    """
    result = crud_user.resend_otp(db, data.email)
    
    if not result["success"]:
        logger.error(f"OTP resend failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    logger.info(f"OTP resent successfully for {data.email}")
    return {
        "success": True,
        "message": result["message"]
        # "otp": result.get("otp")  # Remove in production for security
    }


# ================= LOGIN ENDPOINT =================

@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
def login_user(
    login_data: user_schema.LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login user with email and password.
    
    Returns:
    - 200: Login successful with access token and user data
    - 401: Authentication failed with specific error message:
        * User not found
        * Email not verified
        * Account blocked
        * Incorrect password
    """
    # Get client IP address
    ip_address = request.client.host if request.client else None
    
    # Authenticate user
    result = crud_user.authenticate_user(
        db,
        email=login_data.email,
        password=login_data.password,
        new_fcm_token=login_data.new_fcm_token,
        device_id=login_data.device_id,
        device_type=login_data.device_type,
        os_version=login_data.os_version,
        app_version=login_data.app_version,
        ip_address=ip_address
    )

    if not result["success"]:
        logger.error(f"Login failed for {login_data.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = result["data"]
    
    # Generate access token with role (24 hours for persistent login)
    access_token = create_access_token(
        data={"sub": user.email},
        role="user"  # ✅ Important: Specify role for user
    )

    # Generate refresh token (30 days)
    refresh_token = create_access_token(
        data={"sub": user.email},
        token_type="refresh",
        role="user"
    )

    logger.info(f"User logged in successfully: {login_data.email}")
    return {
        "success": True,
        "message": result["message"],
        "access_token": access_token,
        "refresh_token": refresh_token,  # ✅ Add refresh token
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "status": user.status.value,
            "is_verified": user.is_verified,
            "profile_pic": user.profile_pic,
            "last_login_at": user.last_login_at,
            "fcm_token": user.new_fcm_token,
            "addresses": [
                {
                    "id": addr.id,
                    "name": addr.name,
                    "phone": addr.phone,
                    "address": addr.address,
                    "landmark": addr.landmark,
                    "city": addr.city,
                    "state": addr.state,
                    "pincode": addr.pincode,
                    "country": addr.country,
                    "address_type": addr.address_type,
                    "is_default": addr.is_default
                }
                for addr in user.addresses
            ],
            "default_address": next(
                (
                    {
                        "id": addr.id,
                        "name": addr.name,
                        "phone": addr.phone,
                        "address": addr.address,
                        "landmark": addr.landmark,
                        "city": addr.city,
                        "state": addr.state,
                        "pincode": addr.pincode,
                        "country": addr.country,
                        "address_type": addr.address_type,
                        "is_default": addr.is_default
                    }
                    for addr in user.addresses if addr.is_default
                ),
                None
            )
        }
    }


# ================= PASSWORD RESET ENDPOINTS =================

@router.post("/password-reset/request", response_model=dict, status_code=status.HTTP_200_OK)
def request_password_reset(
    request_data: user_schema.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset OTP.
    
    Returns:
    - 200: OTP sent successfully
    - 400: Request failed (user not found, not verified, etc.)
    """
    result = crud_user.request_password_reset(db, request_data.email)
    
    if not result["success"]:
        logger.error(f"Password reset request failed for {request_data.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Password reset OTP sent for email: {request_data.email}")
    return {
        "success": True,
        "message": result["message"]
    }


@router.post("/password-reset/confirm", response_model=dict, status_code=status.HTTP_200_OK)
def confirm_password_reset(
    confirm: user_schema.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with OTP.
    
    Returns:
    - 200: Password reset successfully
    - 400: Confirmation failed (invalid OTP, expired, etc.)
    """
    result = crud_user.confirm_password_reset(
        db, confirm.email, confirm.otp, confirm.new_password
    )
    
    if not result["success"]:
        logger.error(f"Password reset failed for {confirm.email}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Password reset successful for email: {confirm.email}")
    return {
        "success": True,
        "message": result["message"]
    }


# ================= USER PROFILE ENDPOINTS =================

@router.get("/me", response_model=user_schema.UserOut)
def get_current_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user data."""
    user = crud_user.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    logger.info(f"User data retrieved for user ID: {current_user.id}")
    return user


@router.post("/me/fcm-token", response_model=dict, status_code=status.HTTP_200_OK)
def update_fcm_token(
    fcm_data: dict,  # {"new_fcm_token": "...", "device_id": "...", etc.}
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update FCM token and device details for the current user."""
    result = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(
            new_fcm_token=fcm_data.get("new_fcm_token"),
            device_id=fcm_data.get("device_id"),
            device_type=fcm_data.get("device_type"),
            os_version=fcm_data.get("os_version"),
            app_version=fcm_data.get("app_version")
        ),
        ip_address=request.client.host if request.client else None
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"FCM token updated for user: {current_user.id}")
    return {
        "success": True,
        "message": "FCM token and device details updated successfully"
    }


@router.post("/me/profile-pic", response_model=dict, status_code=status.HTTP_200_OK)
def update_profile_pic(
    profile_data: dict,  # {"profile_pic": "url_or_path"}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile picture for the current user."""
    result = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(profile_pic=profile_data.get("profile_pic"))
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Profile picture updated for user: {current_user.id}")
    return {
        "success": True,
        "message": "Profile picture updated successfully",
        "profile_pic": result["data"].profile_pic
    }


@router.delete("/me/profile-pic", response_model=dict, status_code=status.HTTP_200_OK)
def clear_profile_pic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear profile picture for the current user."""
    result = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(profile_pic=None)
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"Profile picture cleared for user: {current_user.id}")
    return {
        "success": True,
        "message": "Profile picture cleared successfully"
    }


# ================= ADMIN ENDPOINTS =================

@router.get("/admin-only", response_model=dict, dependencies=[Depends(get_super_admin)])
def protected_admin_route():
    """Protected route for super admins only."""
    logger.info("Super admin accessed protected route")
    return {
        "success": True,
        "message": "You're a verified super admin ✅"
    }


@router.get("/", response_model=dict, dependencies=[Depends(get_super_admin)])
def list_users(
    search: str = None,
    status_filter: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all users with search and filter capabilities (super admin only)."""
    from sqlalchemy import or_, and_

    # Build query
    query = db.query(User)

    # Apply filters
    if status_filter:
        query = query.filter(User.status == status_filter)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term),
                User.mobile.ilike(search_term)
            )
        )

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    users = query.offset(skip).limit(limit).all()

    logger.info(f"Retrieved {len(users)} users with search='{search}', status='{status_filter}', skip={skip}, limit={limit}")

    return {
        "success": True,
        "message": f"Retrieved {len(users)} users",
        "users": [user_schema.UserOut.from_orm(user) for user in users],
        "total": total,
        "page": (skip // limit) + 1,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "filters_applied": {
            "search": search,
            "status": status_filter
        }
    }


@router.get("/{user_id}", response_model=user_schema.UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID (authenticated users, super admins can access any user)."""
    if not current_user.is_superuser and current_user.id != user_id:
        logger.error(f"User {current_user.id} attempted unauthorized access to user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's information"
        )
    
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        logger.error(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User data retrieved for user ID: {user_id}")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(get_super_admin)])
def remove_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (super admin only)."""
    result = crud_user.delete_user(db, user_id)
    
    if not result["success"]:
        logger.error(f"Failed to delete user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    logger.info(f"User deleted successfully: {user_id}")
    return {
        "success": True,
        "message": result["message"]
    }


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    data: user_schema.UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user data (self or super admin)."""
    if not current_user.is_superuser and current_user.id != user_id:
        logger.error(f"User {current_user.id} attempted unauthorized update of user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this user"
        )
    
    if data.is_superuser is not None and not current_user.is_superuser:
        logger.error(f"User {current_user.id} attempted to update is_superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update superuser status"
        )
    
    result = crud_user.update_user(
        db,
        user_id,
        data,
        ip_address=request.client.host if request.client else None
    )
    
    if not result["success"]:
        logger.error(f"Failed to update user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    logger.info(f"User updated successfully: {user_id}")
    return {
        "success": True,
        "message": result["message"],
        "user": user_schema.UserOut.from_orm(result["data"])
    }


@router.post("/{user_id}/toggle-status", response_model=dict, dependencies=[Depends(get_super_admin)])
def toggle_user_status(user_id: int, db: Session = Depends(get_db)):
    """Toggle user status between active and blocked (super admin only)."""
    result = crud_user.toggle_user_status(db, user_id)
    
    if not result["success"]:
        logger.error(f"Failed to toggle status for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    logger.info(f"User status toggled for user: {user_id}")
    return {
        "success": True,
        "message": result["message"],
        "user": user_schema.UserOut.from_orm(result["data"])
    }


# ================= REFRESH TOKEN ENDPOINT =================

@router.post("/refresh-token", response_model=dict, status_code=status.HTTP_200_OK)
def refresh_access_token(
    refresh_data: dict,  # {"refresh_token": "..."}
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Returns:
    - 200: New access token generated successfully
    - 401: Invalid or expired refresh token
    """
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
        role = payload.get("role", "user")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Verify user still exists and is active
        if role == "vendor":
            user = db.query(ServiceProvider).filter(ServiceProvider.email == email).first()
        else:
            user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Check if user is active (for regular users)
        if hasattr(user, 'status') and user.status.value != 'active':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": email},
            role=role
        )

        logger.info(f"Access token refreshed for user: {email}")
        return {
            "success": True,
            "message": "Access token refreshed successfully",
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# ================= VENDOR SERVICE CHARGES ENDPOINT =================

@router.get("/vendors-charges/{category_id}/{subcategory_id}", response_model=dict)
def get_vendors_and_charges(
    category_id: int,
    subcategory_id: int,
    db: Session = Depends(get_db)
):
    """Get vendors and their charges for a category/subcategory."""
    data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)

    if data is None:
        logger.error(f"Category or subcategory not found: cat={category_id}, subcat={subcategory_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category or subcategory not found"
        )

    if data == []:
        logger.warning(f"No vendors found for category {category_id}, subcategory {subcategory_id}")
        return {
            "success": True,
            "message": "No vendors available for this category/subcategory",
            "data": {
                "category": {"id": category_id},
                "subcategory": {"id": subcategory_id},
                "vendors": []
            }
        }

    logger.info(f"Retrieved vendors for category {category_id}, subcategory {subcategory_id}")
    return {
        "success": True,
        "message": "Vendors fetched successfully",
        "data": data
    }
