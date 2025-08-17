from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, get_db
from app.schemas import user_schema
from app.crud import user as crud_user
from app.models.user import User
from app.core.dependencies import get_super_admin


router = APIRouter(prefix="/users", tags=["User Management & Auth"])

# 🔐 User Auth — Login via OTP
@router.post("/send-login-otp")
def send_login_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
    otp_sent = crud_user.create_login_otp(db, data.email)
    if not otp_sent:
        raise HTTPException(status_code=404, detail="User not found or not verified")
    return {"message": "Login OTP sent successfully."}


@router.post("/verify-login-otp")
def verify_login_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
    result = crud_user.verify_login_otp(db, data.email, data.otp)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if result == "invalid":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if result == "expired":
        raise HTTPException(status_code=400, detail="OTP expired")
    access_token = create_access_token(data={"sub": result.email})

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": result.id,
            "name": result.name,
            "email": result.email,
            "mobile": result.mobile
        }
    }


# 🔐 User Registration via OTP
@router.post("/register-otp")
def register_user_with_otp(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud_user.get_user_by_email(db, user.email)
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")
        otp = crud_user.resend_otp(db, user.email)
        return {"message": "New OTP sent successfully to unverified email."}

    created_user, otp = crud_user.create_user_with_otp(db, user)
    return {"message": "OTP sent successfully."}


@router.post("/verify-otp")
def verify_user_otp(data: user_schema.OTPVerify, db: Session = Depends(get_db)):
    result = crud_user.verify_otp(db, data.email, data.otp)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if result == "expired":
        raise HTTPException(status_code=400, detail="OTP expired")
    access_token = create_access_token(data={"sub": result.email})

    return {
        "message": "OTP verified successfully.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": result.id,
            "email": result.email,
            "name": result.name,
        }
    }


# 🔄 Resend OTP
@router.post("/resend-otp")
def resend_user_otp(data: user_schema.OTPResend, db: Session = Depends(get_db)):
    otp = crud_user.resend_otp(db, data.email)
    if not otp:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "New OTP sent successfully."}


# 👤 Current Logged-in User Data
@router.get("/me")
def get_current_user_data(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "last_login_at": current_user.last_login_at
    }


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
