

from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User, UserStatus
from app.schemas import user_schema
from app.utils.otp_utils import generate_otp, send_email_otp
from datetime import datetime, timedelta
from app.core.security import get_password_hash


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user_with_otp(db: Session, user: user_schema.UserCreate):
    otp = generate_otp()
    db_user = User(
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        status=UserStatus.active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    send_email_otp(user.email, otp)
    return db_user, otp


def verify_otp(db: Session, email: str, otp: str):
    user = get_user_by_email(db, email)
    if not user or user.otp != otp:
        return None

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        return "expired"

    user.is_verified = True
    user.otp = None
    user.otp_created_at = None
    db.commit()
    db.refresh(user)
    return user


def resend_otp(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        return None

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    send_email_otp(user.email, otp)
    return otp


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def update_user(db: Session, user_id: int, data: user_schema.UserUpdate) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.mobile is not None:
        user.mobile = data.mobile
    if data.password is not None:
        user.hashed_password = get_password_hash(data.password)
    if data.status is not None:
        user.status = data.status
    db.commit()
    db.refresh(user)
    return user


def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
    db.commit()
    db.refresh(user)
    return user

def create_login_otp(db, email: str):
    user = db.query(User).filter(User.email == email, User.is_verified == True).first()
    if not user:
        return None

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    send_email_otp(email, otp)
    return otp

def verify_login_otp(db, email: str, otp: str):
    user = db.query(User).filter(User.email == email, User.is_verified == True).first()
    if not user:
        return None
    if user.otp != otp:
        return "invalid"

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        return "expired"

    # clear OTP
    user.otp = None
    user.otp_created_at = None

    # update last login time
    user.last_login_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # ✅ Fetch addresses for this user only
    addresses = [
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
    ]

    # ✅ Identify default address
    default_address = next((addr for addr in addresses if addr["is_default"]), None)

    return {
        "user": user,
        "addresses": addresses,
        "default_address": default_address
    }








from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.sub_category import SubCategory
from app.models.category import Category
from app.models.service_provider_model import ServiceProvider
from app.models.vendor_subcategory_charge import VendorSubcategoryCharge


def fetch_service_charges_and_vendors(db: Session, category_id: int, sub_category_id: int):
    
    category = db.query(Category).filter(Category.id == category_id).first()
    subcategory = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()

    if not category or not subcategory:
        return None

    # Query VendorSubcategoryCharge with joins
    results = (
        db.query(
            VendorSubcategoryCharge.service_charge,
            ServiceProvider.id.label("vendor_id"),
            ServiceProvider.full_name,
            ServiceProvider.email,
            ServiceProvider.phone,
            ServiceProvider.city,
            ServiceProvider.state,
            ServiceProvider.profile_pic,
        )
        .join(ServiceProvider, ServiceProvider.id == VendorSubcategoryCharge.vendor_id)
        .filter(
            and_(
                VendorSubcategoryCharge.category_id == category_id,
                VendorSubcategoryCharge.subcategory_id == sub_category_id,
            )
        )
        .all()
    )

    if not results:
        return []

    response = []
    for row in results:
        response.append({
            "service_charge": row.service_charge,
            "vendor_details": {
                "id": row.vendor_id,
                "name": row.full_name,
                "email": row.email,
                "contact": row.phone,
                "city": row.city,
                "state": row.state,
                "profile_pic": row.profile_pic
            }
        })

    return {
        "category": {"id": category.id, "name": category.name},
        "subcategory": {"id": subcategory.id, "name": subcategory.name},
        "vendors": response
    }
