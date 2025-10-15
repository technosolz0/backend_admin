

# from sqlalchemy.orm import Session
# from typing import Optional
# from app.models.user import User, UserStatus
# from app.schemas import user_schema
# from app.utils.otp_utils import generate_otp, send_email_otp
# from datetime import datetime, timedelta
# from app.core.security import get_password_hash


# def get_user_by_email(db: Session, email: str):
#     return db.query(User).filter(User.email == email).first()


# def get_user_by_id(db: Session, user_id: int):
#     return db.query(User).filter(User.id == user_id).first()


# def create_user_with_otp(db: Session, user: user_schema.UserCreate):
#     otp = generate_otp()
#     db_user = User(
#         name=user.name,
#         email=user.email,
#         mobile=user.mobile,
#         otp=otp,
#         otp_created_at=datetime.utcnow(),
#         status=UserStatus.active
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)

#     send_email_otp(user.email, otp)
#     return db_user, otp


# def verify_otp(db: Session, email: str, otp: str):
#     user = get_user_by_email(db, email)
#     if not user or user.otp != otp:
#         return None

#     expiry_time = user.otp_created_at + timedelta(minutes=5)
#     if datetime.utcnow() > expiry_time:
#         return "expired"

#     user.is_verified = True
#     user.otp = None
#     user.otp_created_at = None
#     db.commit()
#     db.refresh(user)
#     return user


# def resend_otp(db: Session, email: str):
#     user = get_user_by_email(db, email)
#     if not user:
#         return None

#     otp = generate_otp()
#     user.otp = otp
#     user.otp_created_at = datetime.utcnow()
#     db.commit()
#     db.refresh(user)

#     send_email_otp(user.email, otp)
#     return otp


# def get_users(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(User).offset(skip).limit(limit).all()


# def delete_user(db: Session, user_id: int) -> bool:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return False
#     db.delete(user)
#     db.commit()
#     return True


# def update_user(db: Session, user_id: int, data: user_schema.UserUpdate) -> Optional[User]:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
#     if data.name is not None:
#         user.name = data.name
#     if data.email is not None:
#         user.email = data.email
#     if data.mobile is not None:
#         user.mobile = data.mobile
#     if data.password is not None:
#         user.hashed_password = get_password_hash(data.password)
#     if data.status is not None:
#         user.status = data.status
#     db.commit()
#     db.refresh(user)
#     return user


# def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
#     user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
#     db.commit()
#     db.refresh(user)
#     return user

# def create_login_otp(db, email: str):
#     user = db.query(User).filter(User.email == email, User.is_verified == True).first()
#     if not user:
#         return None

#     otp = generate_otp()
#     user.otp = otp
#     user.otp_created_at = datetime.utcnow()
#     db.commit()
#     send_email_otp(email, otp)
#     return otp

# def verify_login_otp(db, email: str, otp: str):
#     user = db.query(User).filter(User.email == email, User.is_verified == True).first()
#     if not user:
#         return None
#     if user.otp != otp:
#         return "invalid"

#     expiry_time = user.otp_created_at + timedelta(minutes=5)
#     if datetime.utcnow() > expiry_time:
#         return "expired"

#     # clear OTP
#     user.otp = None
#     user.otp_created_at = None

#     # update last login time
#     user.last_login_at = datetime.utcnow()

#     db.commit()
#     db.refresh(user)

#     # ✅ Fetch addresses for this user only
#     addresses = [
#         {
#             "id": addr.id,
#             "name": addr.name,
#             "phone": addr.phone,
#             "address": addr.address,
#             "landmark": addr.landmark,
#             "city": addr.city,
#             "state": addr.state,
#             "pincode": addr.pincode,
#             "country": addr.country,
#             "address_type": addr.address_type,
#             "is_default": addr.is_default
#         }
#         for addr in user.addresses
#     ]

#     # ✅ Identify default address
#     default_address = next((addr for addr in addresses if addr["is_default"]), None)

#     return {
#         "user": user,
#         "addresses": addresses,
#         "default_address": default_address
#     }








# from sqlalchemy.orm import Session
# from sqlalchemy import and_
# from app.models.sub_category import SubCategory
# from app.models.category import Category
# from app.models.service_provider_model import ServiceProvider
# from app.models.vendor_subcategory_charge import VendorSubcategoryCharge


# def fetch_service_charges_and_vendors(db: Session, category_id: int, sub_category_id: int):
    
#     category = db.query(Category).filter(Category.id == category_id).first()
#     subcategory = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()

#     if not category or not subcategory:
#         return None

#     # Query VendorSubcategoryCharge with joins
#     results = (
#         db.query(
#             VendorSubcategoryCharge.service_charge,
#             ServiceProvider.id.label("vendor_id"),
#             ServiceProvider.full_name,
#             ServiceProvider.email,
#             ServiceProvider.phone,
#             ServiceProvider.city,
#             ServiceProvider.state,
#             ServiceProvider.profile_pic,
#         )
#         .join(ServiceProvider, ServiceProvider.id == VendorSubcategoryCharge.vendor_id)
#         .filter(
#             and_(
#                 VendorSubcategoryCharge.category_id == category_id,
#                 VendorSubcategoryCharge.subcategory_id == sub_category_id,
#             )
#         )
#         .all()
#     )

#     if not results:
#         return []

#     response = []
#     for row in results:
#         response.append({
#             "service_charge": row.service_charge,
#             "vendor_details": {
#                 "id": row.vendor_id,
#                 "name": row.full_name,
#                 "email": row.email,
#                 "contact": row.phone,
#                 "city": row.city,
#                 "state": row.state,
#                 "profile_pic": row.profile_pic
#             }
#         })

#     return {
#         "category": {"id": category.id, "name": category.name},
#         "subcategory": {"id": subcategory.id, "name": subcategory.name},
#         "vendors": response
#     }


# app/crud/user.py - Updated with password reset methods
# from sqlalchemy.orm import Session
# from typing import Optional
# from app.models.user import User, UserStatus
# from app.schemas import user_schema
# from app.utils.otp_utils import generate_otp, send_email_otp
# from datetime import datetime, timedelta
# from app.core.security import get_password_hash, verify_password  # Assume verify_password exists


# def get_user_by_email(db: Session, email: str):
#     return db.query(User).filter(User.email == email).first()


# def get_user_by_id(db: Session, user_id: int):
#     return db.query(User).filter(User.id == user_id).first()


# def create_user_with_otp(db: Session, user: user_schema.UserCreate):
#     # Check if user already exists
#     existing_user = get_user_by_email(db, user.email)
#     if existing_user:
#         if existing_user.is_verified:
#             raise ValueError("Email already registered")
#         # Update existing unverified user
#         existing_user.name = user.name
#         existing_user.mobile = user.mobile
#         existing_user.hashed_password = get_password_hash(user.password)
#         existing_user.otp = generate_otp()
#         existing_user.otp_created_at = datetime.utcnow()
#         db.commit()
#         db.refresh(existing_user)
#         send_email_otp(user.email, existing_user.otp)
#         return existing_user, existing_user.otp

#     # Create new user
#     otp = generate_otp()
#     hashed_password = get_password_hash(user.password)
#     db_user = User(
#         name=user.name,
#         email=user.email,
#         mobile=user.mobile,
#         hashed_password=hashed_password,
#         otp=otp,
#         otp_created_at=datetime.utcnow(),
#         status=UserStatus.active
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)

#     send_email_otp(user.email, otp)
#     return db_user, otp


# def verify_otp(db: Session, email: str, otp: str):
#     user = get_user_by_email(db, email)
#     if not user or user.otp != otp:
#         return None

#     expiry_time = user.otp_created_at + timedelta(minutes=5)
#     if datetime.utcnow() > expiry_time:
#         return "expired"

#     user.is_verified = True
#     user.otp = None
#     user.otp_created_at = None
#     db.commit()
#     db.refresh(user)
#     return user


# def resend_otp(db: Session, email: str):
#     user = get_user_by_email(db, email)
#     if not user:
#         return None

#     otp = generate_otp()
#     user.otp = otp
#     user.otp_created_at = datetime.utcnow()
#     db.commit()
#     db.refresh(user)

#     send_email_otp(user.email, otp)
#     return otp


# def authenticate_user(db: Session, email: str, password: str):
#     """Authenticate user with email and password"""
#     user = get_user_by_email(db, email)
#     if not user:
#         return None
#     if not user.is_verified:
#         return None
#     if not verify_password(password, user.hashed_password):
#         return None
#     return user


# def request_password_reset(db: Session, email: str):
#     """Request password reset - generate and send OTP"""
#     user = get_user_by_email(db, email)
#     if not user:
#         return False  # Don't reveal if user exists
#     if not user.is_verified:
#         return False

#     otp = generate_otp()
#     user.otp = otp
#     user.otp_created_at = datetime.utcnow()
#     db.commit()
#     db.refresh(user)

#     # Send reset OTP via email
#     send_email_otp(email, otp, template="password_reset")  # Assume template param for different emails
#     return True


# def confirm_password_reset(db: Session, email: str, otp: str, new_password: str):
#     """Confirm password reset with OTP and new password"""
#     user = get_user_by_email(db, email)
#     if not user:
#         return False

#     # Verify OTP
#     if user.otp != otp:
#         return False

#     expiry_time = user.otp_created_at + timedelta(minutes=5)
#     if datetime.utcnow() > expiry_time:
#         return False

#     # Update password
#     user.hashed_password = get_password_hash(new_password)
#     user.otp = None
#     user.otp_created_at = None
#     db.commit()
#     db.refresh(user)
#     return True


# def get_users(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(User).offset(skip).limit(limit).all()


# def delete_user(db: Session, user_id: int) -> bool:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return False
#     db.delete(user)
#     db.commit()
#     return True


# def update_user(db: Session, user_id: int, data: user_schema.UserUpdate) -> Optional[User]:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
#     if data.name is not None:
#         user.name = data.name
#     if data.email is not None:
#         user.email = data.email
#     if data.mobile is not None:
#         user.mobile = data.mobile
#     if data.password is not None:
#         user.hashed_password = get_password_hash(data.password)
#     if data.status is not None:
#         user.status = data.status
#     if data.fcm_token is not None:
#         user.fcm_token = data.fcm_token  # Update FCM token
#     db.commit()
#     db.refresh(user)
#     return user


# def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
#     user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
#     db.commit()
#     db.refresh(user)
#     return user



from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.user import User, UserStatus
from app.schemas import user_schema
from app.utils.otp_utils import generate_otp, send_email
from datetime import datetime, timedelta
from app.core.security import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_mobile(db: Session, mobile: str) -> Optional[User]:
    """Get user by mobile."""
    return db.query(User).filter(User.mobile == mobile).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def create_user_with_otp(db: Session, user: user_schema.UserCreate) -> tuple[User, str]:
    """Create a new user and send OTP for verification."""
    existing_user = get_user_by_email(db, user.email)
    if existing_user and existing_user.is_verified:
        logger.error(f"Email already registered: {user.email}")
        raise ValueError("Email already registered")
    
    existing_mobile = get_user_by_mobile(db, user.mobile)
    if existing_mobile and existing_mobile.is_verified:
        logger.error(f"Mobile already registered: {user.mobile}")
        raise ValueError("Mobile already registered")

    otp = generate_otp()
    hashed_password = get_password_hash(user.password)
    
    if existing_user:
        existing_user.name = user.name
        existing_user.mobile = user.mobile
        existing_user.hashed_password = hashed_password
        existing_user.otp = otp
        existing_user.otp_created_at = datetime.utcnow()
        existing_user.profile_pic = user.profile_pic
        existing_user.old_fcm_token = existing_user.new_fcm_token
        existing_user.new_fcm_token = user.new_fcm_token
        existing_user.device_id = user.device_id
        existing_user.device_type = user.device_type
        existing_user.os_version = user.os_version
        existing_user.app_version = user.app_version
        db.commit()
        db.refresh(existing_user)
        send_email(receiver_email=user.email, otp=otp, template="otp")
        logger.info(f"Updated existing unverified user: {user.email}")
        return existing_user, otp

    db_user = User(
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        hashed_password=hashed_password,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        status=UserStatus.active,
        profile_pic=user.profile_pic,
        new_fcm_token=user.new_fcm_token,
        device_id=user.device_id,
        device_type=user.device_type,
        os_version=user.os_version,
        app_version=user.app_version
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    send_email(receiver_email=user.email, otp=otp, template="otp")
    logger.info(f"Created new user: {user.email}")
    return db_user, otp

def verify_otp(db: Session, email: str, otp: str) -> Optional[User | str]:
    """Verify OTP for user email verification and send welcome email."""
    user = get_user_by_email(db, email)
    if not user or user.otp != otp:
        logger.error(f"Invalid OTP for email: {email}")
        return None

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        logger.error(f"Expired OTP for email: {email}")
        return "expired"

    user.is_verified = True
    user.otp = None
    user.otp_created_at = None
    db.commit()
    db.refresh(user)
    
    try:
        send_email(receiver_email=user.email, template="welcome", name=user.name)
        logger.info(f"Welcome email sent to user: {email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        # Do not fail verification if welcome email fails
    
    logger.info(f"OTP verified for user: {email}")
    return user

def resend_otp(db: Session, email: str) -> Optional[str]:
    """Resend OTP for email verification."""
    user = get_user_by_email(db, email)
    if not user:
        logger.error(f"User not found for OTP resend: {email}")
        return None

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    send_email(receiver_email=user.email, otp=otp, template="otp")
    logger.info(f"OTP resent for user: {email}")
    return otp

def authenticate_user(
    db: Session,
    email: str,
    password: str,
    new_fcm_token: Optional[str] = None,
    device_id: Optional[str] = None,
    device_type: Optional[str] = None,
    os_version: Optional[str] = None,
    app_version: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Optional[User]:
    """Authenticate user and update login details."""
    user = get_user_by_email(db, email)
    if not user or not user.is_verified or not verify_password(password, user.hashed_password):
        logger.error(f"Authentication failed for email: {email}")
        return None
    
    user.last_login_at = datetime.utcnow()
    if ip_address:
        user.last_login_ip = ip_address
    if new_fcm_token:
        user.old_fcm_token = user.new_fcm_token
        user.new_fcm_token = new_fcm_token
        user.device_id = device_id
        user.device_type = device_type
        user.os_version = os_version
        user.app_version = app_version
    
    db.commit()
    db.refresh(user)
    logger.info(f"User authenticated: {email}")
    return user

def request_password_reset(db: Session, email: str) -> bool:
    """Request password reset OTP."""
    user = get_user_by_email(db, email)
    if not user or not user.is_verified:
        logger.error(f"Password reset request failed for email: {email}")
        return False

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    send_email(receiver_email=user.email, otp=otp, template="password_reset")
    logger.info(f"Password reset OTP sent for email: {email}")
    return True

def confirm_password_reset(db: Session, email: str, otp: str, new_password: str) -> bool:
    """Confirm password reset with OTP."""
    user = get_user_by_email(db, email)
    if not user or user.otp != otp:
        logger.error(f"Invalid OTP for password reset: {email}")
        return False

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        logger.error(f"Expired OTP for password reset: {email}")
        return False

    user.hashed_password = get_password_hash(new_password)
    user.otp = None
    user.otp_created_at = None
    db.commit()
    db.refresh(user)
    logger.info(f"Password reset successful for email: {email}")
    return True

def get_users(db: Session, skip: int = 0, limit: int = 10) -> List[User]:
    """Get list of users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user by ID."""
    user = get_user_by_id(db, user_id)
    if not user:
        logger.error(f"User not found for deletion: {user_id}")
        return False
    db.delete(user)
    db.commit()
    logger.info(f"User deleted successfully: {user_id}")
    return True

def update_user(db: Session, user_id: int, data: user_schema.UserUpdate, ip_address: Optional[str] = None) -> Optional[User]:
    """Update user data."""
    user = get_user_by_id(db, user_id)
    if not user:
        logger.error(f"User not found for update: {user_id}")
        return None
    
    if data.email and data.email != user.email:
        existing_email = get_user_by_email(db, data.email)
        if existing_email and existing_email.id != user_id:
            logger.error(f"Email already in use: {data.email}")
            raise ValueError("Email already in use")
    
    if data.mobile and data.mobile != user.mobile:
        existing_mobile = get_user_by_mobile(db, data.mobile)
        if existing_mobile and existing_mobile.id != user_id:
            logger.error(f"Mobile already in use: {data.mobile}")
            raise ValueError("Mobile already in use")

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
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    if data.profile_pic is not None:
        user.profile_pic = data.profile_pic
    if data.new_fcm_token is not None:
        user.old_fcm_token = user.new_fcm_token
        user.new_fcm_token = data.new_fcm_token
        user.device_id = data.device_id
        user.device_type = data.device_type
        user.os_version = data.os_version
        user.app_version = data.app_version
    if ip_address:
        user.last_login_ip = ip_address
    
    db.commit()
    db.refresh(user)
    logger.info(f"User updated successfully: {user_id}")
    return user

def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
    """Toggle user status between active and blocked."""
    user = get_user_by_id(db, user_id)
    if not user:
        logger.error(f"User not found for status toggle: {user_id}")
        return None
    user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
    db.commit()
    db.refresh(user)
    logger.info(f"User status toggled to {user.status} for user: {user_id}")
    return user

def fetch_service_charges_and_vendors(db: Session, category_id: int, subcategory_id: int) -> dict:
    """Fetch vendors and their service charges for a category/subcategory."""
    from app.models.service_provider_model import ServiceProvider  # Avoid circular import
    # Placeholder; replace with actual query
    logger.info(f"Fetching vendors for category {category_id}, subcategory {subcategory_id}")
    return {"vendors": []}