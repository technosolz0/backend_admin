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
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, get_db
from app.schemas import user_schema
from app.crud import user as crud_user
from app.models.user import User
from app.core.dependencies import get_super_admin


router = APIRouter(prefix="/users", tags=["User Management & Auth"])

# 🔐 User Registration via OTP (keep for email verification)
@router.post("/register-otp")
def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud_user.get_user_by_email(db, user.email)
    if existing_user and existing_user.is_verified:
        raise HTTPException(status_code=400, detail="Email already registered")

    created_user, otp = crud_user.create_user_with_otp(db, user)
    return {"message": "OTP sent successfully for email verification."}


@router.post("/verify-otp")
def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
    result = crud_user.verify_otp(db, data.email, data.otp)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if isinstance(result, str) and result == "expired":
        raise HTTPException(status_code=400, detail="OTP expired")
    access_token = create_access_token(data={"sub": result.email})

    return {
        "message": "Email verified successfully. You can now login with email and password.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": result.id,
            "email": result.email,
            "name": result.name,
            "fcm_token": result.fcm_token,
        }
    }


# 🔄 Resend OTP (for registration verification)
@router.post("/resend-otp")
def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
    otp = crud_user.resend_otp(db, data.email)
    if not otp:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "New OTP sent successfully."}


# 🔐 Email/Password Login
@router.post("/login")
def login_user(login_data: user_schema.LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = crud_user.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "last_login_at": user.last_login_at,
            "fcm_token": user.fcm_token,
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


# 🔐 Password Reset Flow
@router.post("/password-reset/request")
def request_password_reset(request: user_schema.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset - send OTP to email"""
    success = crud_user.request_password_reset(db, request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not verified"  # Generic message for security
        )
    return {"message": "Password reset OTP sent to your email"}


@router.post("/password-reset/confirm")
def confirm_password_reset(confirm: user_schema.PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with OTP and new password"""
    success = crud_user.confirm_password_reset(db, confirm.email, confirm.otp, confirm.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP or expired"
        )
    return {"message": "Password reset successfully"}


# 👤 Current Logged-in User Data
@router.get("/me", response_model=user_schema.UserOut)
def get_current_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud_user.get_user_by_id(db, current_user.id)


# 📝 Admin-only route
@router.get("/admin-only", dependencies=[Depends(get_super_admin)])
def protected_admin_route():
    return {"message": "You're a verified super admin ✅"}


# 📑 List, Get, Update, Delete users
@router.get("/", response_model=list[user_schema.UserOut])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud_user.get_users(db, skip, limit)


@router.get("/{user_id}", response_model=user_schema.UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not crud_user.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")


@router.put("/{user_id}", response_model=user_schema.UserOut)
def update_user(user_id: int, data: user_schema.UserUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    updated = crud_user.update_user(db, user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.post("/{user_id}/toggle-status", response_model=user_schema.UserOut)
def toggle_user_status(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = crud_user.toggle_user_status(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# New endpoint for updating FCM token
@router.post("/me/fcm-token")
def update_fcm_token(fcm_token: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user's FCM token for push notifications"""
    update_data = user_schema.UserUpdate(fcm_token=fcm_token)
    updated_user = crud_user.update_user(db, current_user.id, update_data)
    if not updated_user:
        raise HTTPException(status_code=400, detail="Failed to update FCM token")
    return {"message": "FCM token updated successfully"}


# ⚡ Get Vendors & Charges by Category & Subcategory
@router.get("/vendors-charges/{category_id}/{subcategory_id}")
def get_vendors_and_charges(
    category_id: int,
    subcategory_id: int,
    db: Session = Depends(get_db)
):
    data = crud_user.fetch_service_charges_and_vendors(db, category_id, subcategory_id)
    if not data:
        raise HTTPException(status_code=404, detail="No vendors found for this category/subcategory")
    return data