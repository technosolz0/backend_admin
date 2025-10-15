# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.core.security import create_access_token, get_current_user, get_db
# from app.schemas import user_schema
# from app.crud import user as crud_user
# from app.models.user import User
# from app.core.dependencies import get_super_admin


# router = APIRouter(prefix="/users", tags=["User Management & Auth"])

# # 🔐 User Auth — Login via OTP
# @router.post("/send-login-otp")
# def send_login_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
#     otp_sent = crud_user.create_login_otp(db, data.email)
#     if not otp_sent:
#         raise HTTPException(status_code=404, detail="User not found or not verified")
#     return {"message": "Login OTP sent successfully."}


# @router.post("/verify-login-otp")
# def verify_login_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
#     result = crud_user.verify_login_otp(db, data.email, data.otp)
#     if result is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     if result == "invalid":
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#     if result == "expired":
#         raise HTTPException(status_code=400, detail="OTP expired")

#     user_obj = result["user"]
#     access_token = create_access_token(data={"sub": user_obj.email})

#     return {
#         "message": "Login successful",
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": user_obj.id,
#             "name": user_obj.name,
#             "email": user_obj.email,
#             "mobile": user_obj.mobile,
#             "last_login_at": user_obj.last_login_at,
#             "addresses": result["addresses"],
#             "default_address": result["default_address"]
#         }
#     }


# # 🔐 User Registration via OTP
# @router.post("/register-otp")
# def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
#     existing_user = crud_user.get_user_by_email(db, user.email)
#     if existing_user:
#         if existing_user.is_verified:
#             raise HTTPException(status_code=400, detail="Email already registered")
#         otp = crud_user.resend_otp(db, user.email)
#         return {"message": "New OTP sent successfully to unverified email."}

#     created_user, otp = crud_user.create_user_with_otp(db, user)
#     return {"message": "OTP sent successfully."}


# @router.post("/verify-otp")
# def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
#     result = crud_user.verify_otp(db, data.email, data.otp)
#     if result is None:
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#     if result == "expired":
#         raise HTTPException(status_code=400, detail="OTP expired")
#     access_token = create_access_token(data={"sub": result.email})

#     return {
#         "message": "OTP verified successfully.",
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": result.id,
#             "email": result.email,
#             "name": result.name,
#         }
#     }


# # 🔄 Resend OTP
# @router.post("/resend-otp")
# def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
#     otp = crud_user.resend_otp(db, data.email)
#     if not otp:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"message": "New OTP sent successfully."}


# # 👤 Current Logged-in User Data
# @router.get("/me")
# def get_current_user_data(current_user: User = Depends(get_current_user)):
#     return {
#         "id": current_user.id,
#         "name": current_user.name,
#         "email": current_user.email,
#         "mobile": current_user.mobile,
#         "last_login_at": current_user.last_login_at
#     }


# # 📝 Admin-only route
# @router.get("/admin-only", dependencies=[Depends(get_super_admin)])
# def protected_admin_route():
#     return {"message": "You're a verified super admin ✅"}


# # 📑 List, Get, Update, Delete users
# @router.get("/", response_model=list[user_schema.UserOut])
# def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     return crud_user.get_users(db, skip, limit)


# @router.get("/{user_id}", response_model=user_schema.UserOut)
# def get_user_by_id(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     user = crud_user.get_user_by_id(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     if not crud_user.delete_user(db, user_id):
#         raise HTTPException(status_code=404, detail="User not found")


# @router.put("/{user_id}", response_model=user_schema.UserOut)
# def update_user(user_id: int, data: user_schema.UserUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     updated = crud_user.update_user(db, user_id, data)
#     if not updated:
#         raise HTTPException(status_code=404, detail="User not found")
#     return updated


# @router.post("/{user_id}/toggle-status", response_model=user_schema.UserOut)
# def toggle_user_status(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     user = crud_user.toggle_user_status(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user




# # ⚡ Get Vendors & Charges by Category & Subcategory
# @router.get("/vendors-charges/{category_id}/{subcategory_id}")
# def get_vendors_and_charges(
#     category_id: int,
#     subcategory_id: int,
#     db: Session = Depends(get_db)
# ):
#     data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)
#     if not data:
#         raise HTTPException(status_code=404, detail="No vendors found for this category/subcategory")
#     return data


# app/routers/users_router.py - Updated with password reset endpoints
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.core.security import create_access_token, get_current_user, get_db
# from app.schemas import user_schema
# from app.crud import user as crud_user
# from app.models.user import User
# from app.core.dependencies import get_super_admin


# router = APIRouter(prefix="/users", tags=["User Management & Auth"])

# # 🔐 User Registration via OTP (keep for email verification)
# @router.post("/register-otp")
# def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
#     existing_user = crud_user.get_user_by_email(db, user.email)
#     if existing_user and existing_user.is_verified:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     created_user, otp = crud_user.create_user_with_otp(db, user)
#     return {"message": "OTP sent successfully for email verification."}


# @router.post("/verify-otp")
# def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
#     result = crud_user.verify_otp(db, data.email, data.otp)
#     if result is None:
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#     if isinstance(result, str) and result == "expired":
#         raise HTTPException(status_code=400, detail="OTP expired")
#     access_token = create_access_token(data={"sub": result.email})

#     return {
#         "message": "Email verified successfully. You can now login with email and password.",
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": result.id,
#             "email": result.email,
#             "name": result.name,
#             "fcm_token": result.fcm_token,
#         }
#     }


# # 🔄 Resend OTP (for registration verification)
# @router.post("/resend-otp")
# def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
#     otp = crud_user.resend_otp(db, data.email)
#     if not otp:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"message": "New OTP sent successfully."}


# # 🔐 Email/Password Login
# @router.post("/login")
# def login_user(login_data: user_schema.LoginRequest, db: Session = Depends(get_db)):
#     """Login with email and password"""
#     user = crud_user.authenticate_user(db, login_data.email, login_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
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
#             "fcm_token": user.fcm_token,
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


# # 🔐 Password Reset Flow
# @router.post("/password-reset/request")
# def request_password_reset(request: user_schema.PasswordResetRequest, db: Session = Depends(get_db)):
#     """Request password reset - send OTP to email"""
#     success = crud_user.request_password_reset(db, request.email)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found or not verified"  # Generic message for security
#         )
#     return {"message": "Password reset OTP sent to your email"}


# @router.post("/password-reset/confirm")
# def confirm_password_reset(confirm: user_schema.PasswordResetConfirm, db: Session = Depends(get_db)):
#     """Confirm password reset with OTP and new password"""
#     success = crud_user.confirm_password_reset(db, confirm.email, confirm.otp, confirm.new_password)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid OTP or expired"
#         )
#     return {"message": "Password reset successfully"}


# # 👤 Current Logged-in User Data
# @router.get("/me", response_model=user_schema.UserOut)
# def get_current_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     return crud_user.get_user_by_id(db, current_user.id)


# # 📝 Admin-only route
# @router.get("/admin-only", dependencies=[Depends(get_super_admin)])
# def protected_admin_route():
#     return {"message": "You're a verified super admin ✅"}


# # 📑 List, Get, Update, Delete users
# @router.get("/", response_model=list[user_schema.UserOut])
# def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     return crud_user.get_users(db, skip, limit)


# @router.get("/{user_id}", response_model=user_schema.UserOut)
# def get_user_by_id(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     user = crud_user.get_user_by_id(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     if not crud_user.delete_user(db, user_id):
#         raise HTTPException(status_code=404, detail="User not found")


# @router.put("/{user_id}", response_model=user_schema.UserOut)
# def update_user(user_id: int, data: user_schema.UserUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     updated = crud_user.update_user(db, user_id, data)
#     if not updated:
#         raise HTTPException(status_code=404, detail="User not found")
#     return updated


# @router.post("/{user_id}/toggle-status", response_model=user_schema.UserOut)
# def toggle_user_status(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
#     user = crud_user.toggle_user_status(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# # New endpoint for updating FCM token
# @router.post("/me/fcm-token")
# def update_fcm_token(fcm_token: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """Update user's FCM token for push notifications"""
#     update_data = user_schema.UserUpdate(fcm_token=fcm_token)
#     updated_user = crud_user.update_user(db, current_user.id, update_data)
#     if not updated_user:
#         raise HTTPException(status_code=400, detail="Failed to update FCM token")
#     return {"message": "FCM token updated successfully"}


# # ⚡ Get Vendors & Charges by Category & Subcategory
# @router.get("/vendors-charges/{category_id}/{subcategory_id}")
# def get_vendors_and_charges(
#     category_id: int,
#     subcategory_id: int,
#     db: Session = Depends(get_db)
# ):
#     data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)
#     if not data:
#         raise HTTPException(status_code=404, detail="No vendors found for this category/subcategory")
#     return data




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

@router.post("/register-otp", response_model=dict)
def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send OTP for email verification."""
    try:
        created_user, otp = crud_user.create_user_with_otp(db, user)
        logger.info(f"User registration initiated for email: {user.email}")
        return {"message": "OTP sent successfully for email verification."}
    except ValueError as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp", response_model=dict)
def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP for user email verification."""
    result = crud_user.verify_otp(db, data.email, data.otp)
    if result is None:
        logger.error(f"Invalid OTP for email: {data.email}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if isinstance(result, str) and result == "expired":
        logger.error(f"Expired OTP for email: {data.email}")
        raise HTTPException(status_code=400, detail="OTP expired")
    access_token = create_access_token(data={"sub": result.email})
    logger.info(f"User verified successfully: {data.email}")
    return {
        "message": "Email verified successfully. A welcome email has been sent. You can now login with email and password.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": result.id,
            "email": result.email,
            "name": result.name,
            "profile_pic": result.profile_pic,
            "new_fcm_token": result.new_fcm_token,
            "is_superuser": result.is_superuser
        }
    }

@router.post("/resend-otp", response_model=dict)
def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
    """Resend OTP for email verification."""
    otp = crud_user.resend_otp(db, data.email)
    if not otp:
        logger.error(f"User not found for OTP resend: {data.email}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"OTP resent successfully for email: {data.email}")
    return {"message": "New OTP sent successfully."}

@router.post("/login", response_model=dict)
def login_user(login_data: user_schema.LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = crud_user.authenticate_user(
        db,
        login_data.email,
        login_data.password,
        new_fcm_token=login_data.new_fcm_token,
        device_id=login_data.device_id,
        device_type=login_data.device_type,
        os_version=login_data.os_version,
        app_version=login_data.app_version,
        ip_address=request.client.host
    )
    if not user:
        logger.error(f"Login failed for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"User logged in successfully: {user.email}")
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "profile_pic": user.profile_pic,
            "is_superuser": user.is_superuser,
            "last_login_at": user.last_login_at,
            "last_login_ip": user.last_login_ip,
            "old_fcm_token": user.old_fcm_token,
            "new_fcm_token": user.new_fcm_token,
            "device_id": user.device_id,
            "device_type": user.device_type,
            "os_version": user.os_version,
            "app_version": user.app_version,
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
            "default_address": next((addr for addr in user.addresses if addr.is_default), None)
        }
    }

@router.post("/password-reset/request", response_model=dict)
def request_password_reset(request: user_schema.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset OTP."""
    success = crud_user.request_password_reset(db, request.email)
    if not success:
        logger.error(f"Password reset request failed for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not verified"
        )
    logger.info(f"Password reset OTP sent for email: {request.email}")
    return {"message": "Password reset OTP sent to your email"}

@router.post("/password-reset/confirm", response_model=dict)
def confirm_password_reset(confirm: user_schema.PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with OTP."""
    success = crud_user.confirm_password_reset(db, confirm.email, confirm.otp, confirm.new_password)
    if not success:
        logger.error(f"Password reset failed for email: {confirm.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP or expired"
        )
    logger.info(f"Password reset successful for email: {confirm.email}")
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=user_schema.UserOut)
def get_current_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user data."""
    user = crud_user.get_user_by_id(db, current_user.id)
    logger.info(f"User data retrieved for user ID: {current_user.id}")
    return user

@router.get("/admin-only", response_model=dict, dependencies=[Depends(get_super_admin)])
def protected_admin_route():
    """Protected route for super admins only."""
    logger.info("Super admin accessed protected route")
    return {"message": "You're a verified super admin ✅"}

@router.get("/", response_model=list[user_schema.UserOut], dependencies=[Depends(get_super_admin)])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all users (super admin only)."""
    users = crud_user.get_users(db, skip, limit)
    logger.info(f"Retrieved {len(users)} users with skip={skip}, limit={limit}")
    return users

@router.get("/{user_id}", response_model=user_schema.UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get user by ID (authenticated users, super admins can access any user)."""
    if not current_user.is_superuser and current_user.id != user_id:
        logger.error(f"User {current_user.id} attempted unauthorized access to user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        logger.error(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User data retrieved for user ID: {user_id}")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_super_admin)])
def remove_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (super admin only)."""
    if not crud_user.delete_user(db, user_id):
        logger.error(f"Failed to delete user: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User deleted successfully: {user_id}")

@router.put("/{user_id}", response_model=user_schema.UserOut)
def update_user(user_id: int, data: user_schema.UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update user data (self or super admin)."""
    if not current_user.is_superuser and current_user.id != user_id:
        logger.error(f"User {current_user.id} attempted unauthorized update of user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    if data.is_superuser is not None and not current_user.is_superuser:
        logger.error(f"User {current_user.id} attempted to update is_superuser")
        raise HTTPException(status_code=403, detail="Only superusers can update is_superuser")
    updated = crud_user.update_user(db, user_id, data, ip_address=None)
    if not updated:
        logger.error(f"Failed to update user: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User updated successfully: {user_id}")
    return updated

@router.post("/{user_id}/toggle-status", response_model=user_schema.UserOut, dependencies=[Depends(get_super_admin)])
def toggle_user_status(user_id: int, db: Session = Depends(get_db)):
    """Toggle user status between active and blocked (super admin only)."""
    user = crud_user.toggle_user_status(db, user_id)
    if not user:
        logger.error(f"Failed to toggle status for user: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User status toggled to {user.status} for user: {user_id}")
    return user

@router.post("/me/fcm-token", response_model=dict)
def update_fcm_token(
    new_fcm_token: str,
    device_id: str,
    device_type: str = None,
    os_version: str = None,
    app_version: str = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update FCM token and device details for the current user."""
    updated_user = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(
            new_fcm_token=new_fcm_token,
            device_id=device_id,
            device_type=device_type,
            os_version=os_version,
            app_version=app_version
        ),
        ip_address=request.client.host if request else None
    )
    if not updated_user:
        logger.error(f"Failed to update FCM token for user: {current_user.id}")
        raise HTTPException(status_code=400, detail="Failed to update FCM token")
    logger.info(f"FCM token updated for user: {current_user.id}")
    return {"message": "FCM token and device details updated successfully"}

@router.post("/me/profile-pic", response_model=dict)
def update_profile_pic(
    profile_pic: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile picture for the current user."""
    updated_user = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(profile_pic=profile_pic)
    )
    if not updated_user:
        logger.error(f"Failed to update profile picture for user: {current_user.id}")
        raise HTTPException(status_code=400, detail="Failed to update profile picture")
    logger.info(f"Profile picture updated for user: {current_user.id}")
    return {"message": "Profile picture updated successfully", "profile_pic": updated_user.profile_pic}

@router.delete("/me/profile-pic", response_model=dict)
def clear_profile_pic(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear profile picture for the current user."""
    updated_user = crud_user.update_user(
        db,
        current_user.id,
        user_schema.UserUpdate(profile_pic=None)
    )
    if not updated_user:
        logger.error(f"Failed to clear profile picture for user: {current_user.id}")
        raise HTTPException(status_code=400, detail="Failed to clear profile picture")
    logger.info(f"Profile picture cleared for user: {current_user.id}")
    return {"message": "Profile picture cleared successfully"}

@router.get("/vendors-charges/{category_id}/{subcategory_id}", response_model=dict)
def get_vendors_and_charges(
    category_id: int,
    subcategory_id: int,
    db: Session = Depends(get_db)
):
    """Get vendors and their charges for a category/subcategory."""
    data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)
    if not data:
        logger.error(f"No vendors found for category {category_id}, subcategory {subcategory_id}")
        raise HTTPException(status_code=404, detail="No vendors found for this category/subcategory")
    logger.info(f"Retrieved vendors for category {category_id}, subcategory {subcategory_id}")
    return data