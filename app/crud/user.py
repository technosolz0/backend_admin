# app/crud/user.py - Fixed with proper error handling

from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User, UserStatus
from app.schemas import user_schema
from app.utils.otp_utils import generate_otp, send_email
from app.core.security import get_password_hash, verify_password
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.models.service_provider_model import ServiceProvider
from app.models.vendor_subcategory_charge import VendorSubcategoryCharge

logger = logging.getLogger(__name__)


# ================= HELPER FUNCTIONS =================

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    try:
        return db.query(User).filter(User.email == email).first()
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching user by email: {email}, Error: {str(e)}")
        return None


def get_user_by_mobile(db: Session, mobile: str) -> Optional[User]:
    """Get user by mobile."""
    try:
        return db.query(User).filter(User.mobile == mobile).first()
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching user by mobile: {mobile}, Error: {str(e)}")
        return None


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching user by ID: {user_id}, Error: {str(e)}")
        return None


# ================= REGISTRATION =================

def create_user_with_otp(db: Session, user: user_schema.UserCreate) -> Dict[str, Any]:
    """Create a new user and send OTP for verification."""
    try:
        # Check if email already exists and is verified
        existing_user = get_user_by_email(db, user.email)
        if existing_user and existing_user.is_verified:
            logger.warning(f"Registration attempt with existing verified email: {user.email}")
            return {
                "success": False,
                "message": "This email is already registered. Please login instead.",
                "data": None
            }

        # Check if mobile already exists and is verified
        existing_mobile = get_user_by_mobile(db, user.mobile)
        if existing_mobile and existing_mobile.is_verified and existing_mobile.email != user.email:
            logger.warning(f"Registration attempt with existing verified mobile: {user.mobile}")
            return {
                "success": False,
                "message": "This mobile number is already registered with another account.",
                "data": None
            }

        otp = generate_otp()
        hashed_password = get_password_hash(user.password)

        # Update existing unverified user
        if existing_user and not existing_user.is_verified:
            logger.info(f"Updating existing unverified user: {user.email}")
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
            
            # Send OTP email
            try:
                send_email(receiver_email=user.email, otp=otp, template="otp")
                logger.info(f"OTP sent successfully to: {user.email}")
            except Exception as e:
                logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
            
            return {
                "success": True,
                "message": "OTP sent to your email. Please verify to complete registration.",
                "data": existing_user
            }

        # Create new user
        logger.info(f"Creating new user: {user.email}")
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
        
        # Send OTP email
        try:
            send_email(receiver_email=user.email, otp=otp, template="otp")
            logger.info(f"OTP sent successfully to: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
        
        return {
            "success": True,
            "message": "Registration successful! OTP sent to your email. Please verify to complete registration.",
            "data": db_user
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in create_user_with_otp: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again later.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in create_user_with_otp: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


# ================= OTP VERIFICATION =================

def verify_otp(db: Session, email: str, otp: str) -> Dict[str, Any]:
    """Verify OTP for user email verification."""
    try:
        user = get_user_by_email(db, email)
        
        if not user:
            logger.warning(f"OTP verification attempt for non-existent email: {email}")
            return {
                "success": False,
                "message": "User not found with this email.",
                "data": None
            }
        
        if user.is_verified:
            logger.warning(f"OTP verification attempt for already verified user: {email}")
            return {
                "success": False,
                "message": "Your account is already verified. Please login.",
                "data": None
            }
        
        if not user.otp:
            logger.warning(f"OTP verification attempt but no OTP exists for: {email}")
            return {
                "success": False,
                "message": "No OTP found. Please request a new OTP.",
                "data": None
            }
        
        if user.otp != otp:
            logger.warning(f"Invalid OTP attempt for email: {email}")
            return {
                "success": False,
                "message": "Invalid OTP. Please check and try again.",
                "data": None
            }

        # Check OTP expiry
        expiry_time = user.otp_created_at + timedelta(minutes=5)
        if datetime.utcnow() > expiry_time:
            logger.warning(f"Expired OTP attempt for email: {email}")
            return {
                "success": False,
                "message": "OTP has expired. Please request a new OTP.",
                "data": None
            }

        # Verify user
        user.is_verified = True
        user.otp = None
        user.otp_created_at = None
        db.commit()
        db.refresh(user)
        
        # Send welcome email
        try:
            send_email(receiver_email=user.email, template="welcome", name=user.name)
            logger.info(f"Welcome email sent to: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        
        logger.info(f"User verified successfully: {email}")
        return {
            "success": True,
            "message": "Email verified successfully! You can now login.",
            "data": user
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in verify_otp: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in verify_otp: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


def resend_otp(db: Session, email: str) -> Dict[str, Any]:
    """Resend OTP for email verification."""
    try:
        user = get_user_by_email(db, email)
        
        if not user:
            logger.warning(f"OTP resend attempt for non-existent email: {email}")
            return {
                "success": False,
                "message": "User not found with this email.",
                "data": None
            }
        
        if user.is_verified:
            logger.warning(f"OTP resend attempt for already verified user: {email}")
            return {
                "success": False,
                "message": "Your account is already verified. Please login.",
                "data": None
            }

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Send OTP email
        try:
            send_email(receiver_email=user.email, otp=otp, template="otp")
            logger.info(f"OTP resent successfully to: {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend OTP email to {user.email}: {str(e)}")
        
        return {
            "success": True,
            "message": "OTP resent successfully to your email.",
            "data": user,
            "otp": otp  # Remove in production
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in resend_otp: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in resend_otp: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


# ================= LOGIN / AUTHENTICATION =================

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
) -> Dict[str, Any]:
    """
    Authenticate user with detailed error messages.
    Returns dict with success status, message, and user data.
    """
    try:
        # Check if user exists
        user = get_user_by_email(db, email)
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return {
                "success": False,
                "message": "No account found with this email address. Please register first.",
                "data": None
            }
        
        # Check if user is verified
        if not user.is_verified:
            logger.warning(f"Login attempt with unverified email: {email}")
            return {
                "success": False,
                "message": "Your email is not verified. Please verify your email using the OTP sent during registration.",
                "data": None
            }
        
        # Check if user is blocked
        if user.status == UserStatus.blocked:
            logger.warning(f"Login attempt by blocked user: {email}")
            return {
                "success": False,
                "message": "Your account has been blocked. Please contact support for assistance.",
                "data": None
            }
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Login attempt with incorrect password for: {email}")
            return {
                "success": False,
                "message": "Incorrect password. Please try again or reset your password.",
                "data": None
            }

        # Update login information
        user.last_login_at = datetime.utcnow()
        if ip_address:
            user.last_login_ip = ip_address

        # Update FCM token and device info if provided
        if new_fcm_token:
            user.old_fcm_token = user.new_fcm_token
            user.new_fcm_token = new_fcm_token
            user.device_id = device_id
            user.device_type = device_type
            user.os_version = os_version
            user.app_version = app_version

        db.commit()
        db.refresh(user)
        
        logger.info(f"User logged in successfully: {email}")
        return {
            "success": True,
            "message": "Login successful!",
            "data": user
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in authenticate_user: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in authenticate_user: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


# ================= PASSWORD RESET =================

def request_password_reset(db: Session, email: str) -> Dict[str, Any]:
    """Request password reset OTP."""
    try:
        user = get_user_by_email(db, email)
        
        if not user:
            logger.warning(f"Password reset request for non-existent email: {email}")
            return {
                "success": False,
                "message": "No account found with this email address.",
                "data": None
            }
        
        if not user.is_verified:
            logger.warning(f"Password reset request for unverified user: {email}")
            return {
                "success": False,
                "message": "Your email is not verified. Please verify your email first.",
                "data": None
            }

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Send reset OTP email
        try:
            send_email(receiver_email=user.email, otp=otp, template="password_reset")
            logger.info(f"Password reset OTP sent to: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset OTP to {user.email}: {str(e)}")
        
        return {
            "success": True,
            "message": "Password reset OTP sent to your email.",
            "data": otp  # Remove in production
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in request_password_reset: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in request_password_reset: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


def confirm_password_reset(db: Session, email: str, otp: str, new_password: str) -> Dict[str, Any]:
    """Confirm password reset with OTP."""
    try:
        user = get_user_by_email(db, email)
        
        if not user:
            logger.warning(f"Password reset confirmation for non-existent email: {email}")
            return {
                "success": False,
                "message": "User not found with this email.",
                "data": None
            }
        
        if not user.otp:
            logger.warning(f"Password reset confirmation but no OTP exists for: {email}")
            return {
                "success": False,
                "message": "No OTP found. Please request a password reset first.",
                "data": None
            }
        
        if user.otp != otp:
            logger.warning(f"Invalid OTP for password reset: {email}")
            return {
                "success": False,
                "message": "Invalid OTP. Please check and try again.",
                "data": None
            }

        # Check OTP expiry
        expiry_time = user.otp_created_at + timedelta(minutes=5)
        if datetime.utcnow() > expiry_time:
            logger.warning(f"Expired OTP for password reset: {email}")
            return {
                "success": False,
                "message": "OTP has expired. Please request a new password reset.",
                "data": None
            }

        # Reset password
        user.hashed_password = get_password_hash(new_password)
        user.otp = None
        user.otp_created_at = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password reset successfully for: {email}")
        return {
            "success": True,
            "message": "Password reset successfully! You can now login with your new password.",
            "data": None
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in confirm_password_reset: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in confirm_password_reset: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


# ================= USER MANAGEMENT =================

def get_users(db: Session, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    """Get list of users with pagination."""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return {
            "success": True,
            "message": "Users fetched successfully.",
            "data": users
        }
    except SQLAlchemyError as e:
        logger.exception(f"Database error in get_users: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }


def delete_user(db: Session, user_id: int) -> Dict[str, Any]:
    """Delete a user by ID."""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Delete attempt for non-existent user ID: {user_id}")
            return {
                "success": False,
                "message": "User not found.",
                "data": None
            }
        
        db.delete(user)
        db.commit()
        logger.info(f"User deleted successfully: {user_id}")
        return {
            "success": True,
            "message": "User deleted successfully.",
            "data": None
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in delete_user: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }


def update_user(
    db: Session,
    user_id: int,
    data: user_schema.UserUpdate,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """Update user data."""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Update attempt for non-existent user ID: {user_id}")
            return {
                "success": False,
                "message": "User not found.",
                "data": None
            }

        # Check email uniqueness
        if data.email and data.email != user.email:
            existing_email = get_user_by_email(db, data.email)
            if existing_email and existing_email.id != user_id:
                logger.warning(f"Update attempt with existing email: {data.email}")
                return {
                    "success": False,
                    "message": "This email is already in use by another account.",
                    "data": None
                }

        # Check mobile uniqueness
        if data.mobile and data.mobile != user.mobile:
            existing_mobile = get_user_by_mobile(db, data.mobile)
            if existing_mobile and existing_mobile.id != user_id:
                logger.warning(f"Update attempt with existing mobile: {data.mobile}")
                return {
                    "success": False,
                    "message": "This mobile number is already in use by another account.",
                    "data": None
                }

        # Update fields
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
        return {
            "success": True,
            "message": "User updated successfully.",
            "data": user
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in update_user: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in update_user: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


def toggle_user_status(db: Session, user_id: int) -> Dict[str, Any]:
    """Toggle user status between active and blocked."""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Status toggle attempt for non-existent user ID: {user_id}")
            return {
                "success": False,
                "message": "User not found.",
                "data": None
            }
        
        user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
        db.commit()
        db.refresh(user)
        logger.info(f"User status toggled to {user.status} for user: {user_id}")
        return {
            "success": True,
            "message": f"User status changed to {user.status.value}.",
            "data": user
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in toggle_user_status: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }


# ================= VENDOR SERVICE CHARGES =================

def fetch_service_charges_and_vendors(db: Session, category_id: int, sub_category_id: int):
    """Fetch vendors and their service charges for a category/subcategory."""
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        subcategory = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()

        if not category or not subcategory:
            logger.warning(f"Category or subcategory not found: cat={category_id}, subcat={sub_category_id}")
            return None

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
    except Exception as e:
        logger.exception(f"Error fetching service charges: {str(e)}")
        return None

# # app/crud/user.py - Updated with get_user_by_email (no changes needed, but ensure it's there)
# from sqlalchemy import and_
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from typing import Optional, List
# from datetime import datetime, timedelta
# import logging

# from app.models.user import User, UserStatus
# from app.schemas import user_schema
# from app.utils.otp_utils import generate_otp, send_email
# from app.core.security import get_password_hash, verify_password
# from app.models.category import Category
# from app.models.sub_category import SubCategory
# from app.models.service_provider_model import ServiceProvider
# from app.models.vendor_subcategory_charge import VendorSubcategoryCharge

# logger = logging.getLogger(__name__)

# def get_user_by_email(db: Session, email: str) -> Optional[User]:
#     """Get user by email."""
#     try:
#         return db.query(User).filter(User.email == email).first()
#     except SQLAlchemyError:
#         logger.error(f"DB error fetching user by email: {email}")
#         return None
    
# # from sqlalchemy import and_
# # from sqlalchemy.orm import Session
# # from sqlalchemy.exc import SQLAlchemyError
# # from typing import Optional, List
# # from datetime import datetime, timedelta
# # import logging

# # from app.models.user import User, UserStatus
# # from app.schemas import user_schema
# # from app.utils.otp_utils import generate_otp, send_email
# # from app.core.security import get_password_hash, verify_password
# # from app.models.category import Category
# # from app.models.sub_category import SubCategory
# # from app.models.service_provider_model import ServiceProvider
# # from app.models.vendor_subcategory_charge import VendorSubcategoryCharge

# # logger = logging.getLogger(__name__)



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

# # ------------------- Basic Getters -------------------

# def get_user_by_email(db: Session, email: str) -> Optional[User]:
#     try:
#         return db.query(User).filter(User.email == email).first()
#     except SQLAlchemyError:
#         return None


# def get_user_by_mobile(db: Session, mobile: str) -> Optional[User]:
#     try:
#         return db.query(User).filter(User.mobile == mobile).first()
#     except SQLAlchemyError:
#         return None


# def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
#     try:
#         return db.query(User).filter(User.id == user_id).first()
#     except SQLAlchemyError:
#         return None


# # ------------------- Create / OTP -------------------
# def create_user_with_otp(db: Session, user: user_schema.UserCreate) -> dict:
#     """Create a new user and send OTP for verification."""
#     try:
#         existing_user = get_user_by_email(db, user.email)
#         if existing_user and existing_user.is_verified:
#             return {"success": False, "message": "Email already registered", "data": None}

#         existing_mobile = get_user_by_mobile(db, user.mobile)
#         if existing_mobile and existing_mobile.is_verified:
#             return {"success": False, "message": "Mobile number already registered", "data": None}

#         otp = generate_otp()
#         hashed_password = get_password_hash(user.password)

#         # Update existing unverified user
#         if existing_user:
#             existing_user.name = user.name
#             existing_user.mobile = user.mobile
#             existing_user.hashed_password = hashed_password
#             existing_user.otp = otp
#             existing_user.otp_created_at = datetime.utcnow()
#             existing_user.profile_pic = user.profile_pic
#             existing_user.old_fcm_token = existing_user.new_fcm_token
#             existing_user.new_fcm_token = user.new_fcm_token
#             existing_user.device_id = user.device_id
#             existing_user.device_type = user.device_type
#             existing_user.os_version = user.os_version
#             existing_user.app_version = user.app_version
#             db.commit()
#             db.refresh(existing_user)
#             try: send_email(receiver_email=user.email, otp=otp, template="otp")
#             except: pass
#             return {"success": True, "message": "OTP sent to your email", "data": existing_user}

#         # Create new user
#         db_user = User(
#             name=user.name,
#             email=user.email,
#             mobile=user.mobile,
#             hashed_password=hashed_password,
#             otp=otp,
#             otp_created_at=datetime.utcnow(),
#             status=UserStatus.active,
#             profile_pic=user.profile_pic,
#             new_fcm_token=user.new_fcm_token,
#             device_id=user.device_id,
#             device_type=user.device_type,
#             os_version=user.os_version,
#             app_version=user.app_version
#         )
#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
#         try: send_email(receiver_email=user.email, otp=otp, template="otp")
#         except: pass
#         return {"success": True, "message": "OTP sent to your email", "data": db_user}

#     except Exception as e:
#         db.rollback()
#         logger.exception("Error in create_user_with_otp")
#         return {"success": False, "message": str(e), "data": None}


# def verify_otp(db: Session, email: str, otp: str) -> dict:
#     try:
#         user = get_user_by_email(db, email)
#         if not user: return {"success": False, "message": "User not found", "data": None}
#         if user.otp != otp: return {"success": False, "message": "Invalid OTP", "data": None}

#         if datetime.utcnow() > user.otp_created_at + timedelta(minutes=5):
#             return {"success": False, "message": "OTP expired", "data": None}

#         user.is_verified = True
#         user.otp = None
#         user.otp_created_at = None
#         db.commit()
#         db.refresh(user)
#         try: send_email(receiver_email=user.email, template="welcome", name=user.name)
#         except: pass
#         return {"success": True, "message": "OTP verified successfully", "data": user}
#     except Exception as e:
#         db.rollback()
#         logger.exception("Error in verify_otp")
#         return {"success": False, "message": str(e), "data": None}


# def resend_otp(db: Session, email: str) -> dict:
#     try:
#         user = get_user_by_email(db, email)
#         if not user: return {"success": False, "message": "User not found", "data": None}

#         otp = generate_otp()
#         user.otp = otp
#         user.otp_created_at = datetime.utcnow()
#         db.commit()
#         db.refresh(user)
#         try: send_email(receiver_email=user.email, otp=otp, template="otp")
#         except: pass
#         return {"success": True, "message": "OTP resent successfully", "data": user, "otp": otp}
#     except Exception as e:
#         db.rollback()
#         logger.exception("Error in resend_otp")
#         return {"success": False, "message": str(e), "data": None}
# # ------------------- Authentication -------------------
# from typing import Optional
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from datetime import datetime
# from app.models.user import User
# from app.core.security import verify_password
# from app.crud.user import get_user_by_email

# def authenticate_user(
#     db: Session,
#     email: str,
#     password: str,
#     new_fcm_token: Optional[str] = None,
#     device_id: Optional[str] = None,
#     device_type: Optional[str] = None,
#     os_version: Optional[str] = None,
#     app_version: Optional[str] = None,
#     ip_address: Optional[str] = None
# ) -> Optional[User]:
#     """
#     Authenticate user and update login details.
#     Returns User object on success, None on failure.
#     """
#     try:
#         user = get_user_by_email(db, email)
#         if not user or not user.is_verified or not verify_password(password, user.hashed_password):
#             return None  # Failed authentication

#         # Update last login info
#         user.last_login_at = datetime.utcnow()
#         if ip_address:
#             user.last_login_ip = ip_address

#         # Update FCM and device info
#         if new_fcm_token:
#             user.old_fcm_token = user.new_fcm_token
#             user.new_fcm_token = new_fcm_token
#             user.device_id = device_id
#             user.device_type = device_type
#             user.os_version = os_version
#             user.app_version = app_version

#         db.commit()
#         db.refresh(user)
#         return user

#     except SQLAlchemyError:
#         db.rollback()
#         return None
#     except Exception:
#         db.rollback()
#         return None

# # ------------------- Password Reset -------------------

# def request_password_reset(db: Session, email: str) -> dict:
#     try:
#         user = get_user_by_email(db, email)
#         if not user or not user.is_verified:
#             return {"success": False, "message": "User not found or not verified", "data": None}

#         otp = generate_otp()
#         user.otp = otp
#         user.otp_created_at = datetime.utcnow()
#         db.commit()
#         db.refresh(user)
#         try:
#             send_email(receiver_email=user.email, otp=otp, template="password_reset")
#         except Exception:
#             pass
#         return {"success": True, "message": "Password reset OTP sent", "data": otp}

#     except SQLAlchemyError:
#         db.rollback()
#         return {"success": False, "message": "Database error occurred", "data": None}
#     except Exception:
#         db.rollback()
#         return {"success": False, "message": "Something went wrong", "data": None}


# def confirm_password_reset(db: Session, email: str, otp: str, new_password: str) -> dict:
#     try:
#         user = get_user_by_email(db, email)
#         if not user:
#             return {"success": False, "message": "User not found", "data": None}
#         if user.otp != otp:
#             return {"success": False, "message": "Invalid OTP", "data": None}

#         expiry_time = user.otp_created_at + timedelta(minutes=5)
#         if datetime.utcnow() > expiry_time:
#             return {"success": False, "message": "OTP expired", "data": None}

#         user.hashed_password = get_password_hash(new_password)
#         user.otp = None
#         user.otp_created_at = None
#         db.commit()
#         db.refresh(user)
#         return {"success": True, "message": "Password reset successfully", "data": None}

#     except SQLAlchemyError:
#         db.rollback()
#         return {"success": False, "message": "Database error occurred", "data": None}
#     except Exception:
#         db.rollback()
#         return {"success": False, "message": "Something went wrong", "data": None}


# # ------------------- CRUD & Utilities -------------------

# def get_users(db: Session, skip: int = 0, limit: int = 10) -> dict:
#     try:
#         users = db.query(User).offset(skip).limit(limit).all()
#         return {"success": True, "message": "Users fetched successfully", "data": users}
#     except SQLAlchemyError:
#         return {"success": False, "message": "Database error occurred", "data": None}
#     except Exception:
#         return {"success": False, "message": "Something went wrong", "data": None}


# def delete_user(db: Session, user_id: int) -> dict:
#     try:
#         user = get_user_by_id(db, user_id)
#         if not user:
#             return {"success": False, "message": "User not found", "data": None}
#         db.delete(user)
#         db.commit()
#         return {"success": True, "message": "User deleted successfully", "data": None}
#     except SQLAlchemyError:
#         db.rollback()
#         return {"success": False, "message": "Database error occurred", "data": None}
#     except Exception:
#         db.rollback()
#         return {"success": False, "message": "Something went wrong", "data": None}


# def update_user(db: Session, user_id: int, data: user_schema.UserUpdate, ip_address: Optional[str] = None) -> dict:
#     try:
#         user = get_user_by_id(db, user_id)
#         if not user:
#             return {"success": False, "message": "User not found", "data": None}

#         if data.email and data.email != user.email:
#             existing_email = get_user_by_email(db, data.email)
#             if existing_email and existing_email.id != user_id:
#                 return {"success": False, "message": "Email already in use", "data": None}

#         if data.mobile and data.mobile != user.mobile:
#             existing_mobile = get_user_by_mobile(db, data.mobile)
#             if existing_mobile and existing_mobile.id != user_id:
#                 return {"success": False, "message": "Mobile number already in use", "data": None}

#         # Update fields
#         if data.name is not None: user.name = data.name
#         if data.email is not None: user.email = data.email
#         if data.mobile is not None: user.mobile = data.mobile
#         if data.password is not None: user.hashed_password = get_password_hash(data.password)
#         if data.status is not None: user.status = data.status
#         if data.is_superuser is not None: user.is_superuser = data.is_superuser
#         if data.profile_pic is not None: user.profile_pic = data.profile_pic
#         if data.new_fcm_token is not None:
#             user.old_fcm_token = user.new_fcm_token
#             user.new_fcm_token = data.new_fcm_token
#             user.device_id = data.device_id
#             user.device_type = data.device_type
#             user.os_version = data.os_version
#             user.app_version = data.app_version
#         if ip_address: user.last_login_ip = ip_address

#         db.commit()
#         db.refresh(user)
#         return {"success": True, "message": "User updated successfully", "data": user}

#     except SQLAlchemyError:
#         db.rollback()
#         return {"success": False, "message": "Database error occurred", "data": None}
#     except Exception:
#         db.rollback()
       

# # from sqlalchemy.orm import Session
# # from typing import Optional, List
# # from app.models.user import User, UserStatus
# # from app.schemas import user_schema
# # from app.utils.otp_utils import generate_otp, send_email
# # from datetime import datetime, timedelta
# # from app.core.security import get_password_hash, verify_password
# # import logging

# # logger = logging.getLogger(__name__)

# # def get_user_by_email(db: Session, email: str) -> Optional[User]:
# #     """Get user by email."""
# #     return db.query(User).filter(User.email == email).first()

# # def get_user_by_mobile(db: Session, mobile: str) -> Optional[User]:
# #     """Get user by mobile."""
# #     return db.query(User).filter(User.mobile == mobile).first()

# # def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
# #     """Get user by ID."""
# #     return db.query(User).filter(User.id == user_id).first()

# # def create_user_with_otp(db: Session, user: user_schema.UserCreate) -> tuple[User, str]:
# #     """Create a new user and send OTP for verification."""
# #     existing_user = get_user_by_email(db, user.email)
# #     if existing_user and existing_user.is_verified:
# #         logger.error(f"Email already registered: {user.email}")
# #         raise ValueError("Email already registered")
    
# #     existing_mobile = get_user_by_mobile(db, user.mobile)
# #     if existing_mobile and existing_mobile.is_verified:
# #         logger.error(f"Mobile already registered: {user.mobile}")
# #         raise ValueError("Mobile already registered")

# #     otp = generate_otp()
# #     hashed_password = get_password_hash(user.password)
    
# #     if existing_user:
# #         existing_user.name = user.name
# #         existing_user.mobile = user.mobile
# #         existing_user.hashed_password = hashed_password
# #         existing_user.otp = otp
# #         existing_user.otp_created_at = datetime.utcnow()
# #         existing_user.profile_pic = user.profile_pic
# #         existing_user.old_fcm_token = existing_user.new_fcm_token
# #         existing_user.new_fcm_token = user.new_fcm_token
# #         existing_user.device_id = user.device_id
# #         existing_user.device_type = user.device_type
# #         existing_user.os_version = user.os_version
# #         existing_user.app_version = user.app_version
# #         db.commit()
# #         db.refresh(existing_user)
# #         send_email(receiver_email=user.email, otp=otp, template="otp")
# #         logger.info(f"Updated existing unverified user: {user.email}")
# #         return existing_user, otp

# #     db_user = User(
# #         name=user.name,
# #         email=user.email,
# #         mobile=user.mobile,
# #         hashed_password=hashed_password,
# #         otp=otp,
# #         otp_created_at=datetime.utcnow(),
# #         status=UserStatus.active,
# #         profile_pic=user.profile_pic,
# #         new_fcm_token=user.new_fcm_token,
# #         device_id=user.device_id,
# #         device_type=user.device_type,
# #         os_version=user.os_version,
# #         app_version=user.app_version
# #     )
# #     db.add(db_user)
# #     db.commit()
# #     db.refresh(db_user)
# #     send_email(receiver_email=user.email, otp=otp, template="otp")
# #     logger.info(f"Created new user: {user.email}")
# #     return db_user, otp

# # def verify_otp(db: Session, email: str, otp: str) -> Optional[User | str]:
# #     """Verify OTP for user email verification and send welcome email."""
# #     user = get_user_by_email(db, email)
# #     if not user or user.otp != otp:
# #         logger.error(f"Invalid OTP for email: {email}")
# #         return None

# #     expiry_time = user.otp_created_at + timedelta(minutes=5)
# #     if datetime.utcnow() > expiry_time:
# #         logger.error(f"Expired OTP for email: {email}")
# #         return "expired"

# #     user.is_verified = True
# #     user.otp = None
# #     user.otp_created_at = None
# #     db.commit()
# #     db.refresh(user)
    
# #     try:
# #         send_email(receiver_email=user.email, template="welcome", name=user.name)
# #         logger.info(f"Welcome email sent to user: {email}")
# #     except Exception as e:
# #         logger.error(f"Failed to send welcome email to {email}: {str(e)}")
# #         # Do not fail verification if welcome email fails
    
# #     logger.info(f"OTP verified for user: {email}")
# #     return user

# # def resend_otp(db: Session, email: str) -> Optional[str]:
# #     """Resend OTP for email verification."""
# #     user = get_user_by_email(db, email)
# #     if not user:
# #         logger.error(f"User not found for OTP resend: {email}")
# #         return None

# #     otp = generate_otp()
# #     user.otp = otp
# #     user.otp_created_at = datetime.utcnow()
# #     db.commit()
# #     db.refresh(user)
# #     send_email(receiver_email=user.email, otp=otp, template="otp")
# #     logger.info(f"OTP resent for user: {email}")
# #     return otp

# # def authenticate_user(
# #     db: Session,
# #     email: str,
# #     password: str,
# #     new_fcm_token: Optional[str] = None,
# #     device_id: Optional[str] = None,
# #     device_type: Optional[str] = None,
# #     os_version: Optional[str] = None,
# #     app_version: Optional[str] = None,
# #     ip_address: Optional[str] = None
# # ) -> Optional[User]:
# #     """Authenticate user and update login details."""
# #     user = get_user_by_email(db, email)
# #     if not user or not user.is_verified or not verify_password(password, user.hashed_password):
# #         logger.error(f"Authentication failed for email: {email}")
# #         return None
    
# #     user.last_login_at = datetime.utcnow()
# #     if ip_address:
# #         user.last_login_ip = ip_address
# #     if new_fcm_token:
# #         user.old_fcm_token = user.new_fcm_token
# #         user.new_fcm_token = new_fcm_token
# #         user.device_id = device_id
# #         user.device_type = device_type
# #         user.os_version = os_version
# #         user.app_version = app_version
    
# #     db.commit()
# #     db.refresh(user)
# #     logger.info(f"User authenticated: {email}")
# #     return user

# # def request_password_reset(db: Session, email: str) -> bool:
# #     """Request password reset OTP."""
# #     user = get_user_by_email(db, email)
# #     if not user or not user.is_verified:
# #         logger.error(f"Password reset request failed for email: {email}")
# #         return False

# #     otp = generate_otp()
# #     user.otp = otp
# #     user.otp_created_at = datetime.utcnow()
# #     db.commit()
# #     db.refresh(user)
# #     send_email(receiver_email=user.email, otp=otp, template="password_reset")
# #     logger.info(f"Password reset OTP sent for email: {email}")
# #     return True

# # def confirm_password_reset(db: Session, email: str, otp: str, new_password: str) -> bool:
# #     """Confirm password reset with OTP."""
# #     user = get_user_by_email(db, email)
# #     if not user or user.otp != otp:
# #         logger.error(f"Invalid OTP for password reset: {email}")
# #         return False

# #     expiry_time = user.otp_created_at + timedelta(minutes=5)
# #     if datetime.utcnow() > expiry_time:
# #         logger.error(f"Expired OTP for password reset: {email}")
# #         return False

# #     user.hashed_password = get_password_hash(new_password)
# #     user.otp = None
# #     user.otp_created_at = None
# #     db.commit()
# #     db.refresh(user)
# #     logger.info(f"Password reset successful for email: {email}")
# #     return True

# # def get_users(db: Session, skip: int = 0, limit: int = 10) -> List[User]:
# #     """Get list of users with pagination."""
# #     return db.query(User).offset(skip).limit(limit).all()

# # def delete_user(db: Session, user_id: int) -> bool:
# #     """Delete a user by ID."""
# #     user = get_user_by_id(db, user_id)
# #     if not user:
# #         logger.error(f"User not found for deletion: {user_id}")
# #         return False
# #     db.delete(user)
# #     db.commit()
# #     logger.info(f"User deleted successfully: {user_id}")
# #     return True

# # def update_user(db: Session, user_id: int, data: user_schema.UserUpdate, ip_address: Optional[str] = None) -> Optional[User]:
# #     """Update user data."""
# #     user = get_user_by_id(db, user_id)
# #     if not user:
# #         logger.error(f"User not found for update: {user_id}")
# #         return None
    
# #     if data.email and data.email != user.email:
# #         existing_email = get_user_by_email(db, data.email)
# #         if existing_email and existing_email.id != user_id:
# #             logger.error(f"Email already in use: {data.email}")
# #             raise ValueError("Email already in use")
    
# #     if data.mobile and data.mobile != user.mobile:
# #         existing_mobile = get_user_by_mobile(db, data.mobile)
# #         if existing_mobile and existing_mobile.id != user_id:
# #             logger.error(f"Mobile already in use: {data.mobile}")
# #             raise ValueError("Mobile already in use")

# #     if data.name is not None:
# #         user.name = data.name
# #     if data.email is not None:
# #         user.email = data.email
# #     if data.mobile is not None:
# #         user.mobile = data.mobile
# #     if data.password is not None:
# #         user.hashed_password = get_password_hash(data.password)
# #     if data.status is not None:
# #         user.status = data.status
# #     if data.is_superuser is not None:
# #         user.is_superuser = data.is_superuser
# #     if data.profile_pic is not None:
# #         user.profile_pic = data.profile_pic
# #     if data.new_fcm_token is not None:
# #         user.old_fcm_token = user.new_fcm_token
# #         user.new_fcm_token = data.new_fcm_token
# #         user.device_id = data.device_id
# #         user.device_type = data.device_type
# #         user.os_version = data.os_version
# #         user.app_version = data.app_version
# #     if ip_address:
# #         user.last_login_ip = ip_address
    
# #     db.commit()
# #     db.refresh(user)
# #     logger.info(f"User updated successfully: {user_id}")
# #     return user

# # def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
# #     """Toggle user status between active and blocked."""
# #     user = get_user_by_id(db, user_id)
# #     if not user:
# #         logger.error(f"User not found for status toggle: {user_id}")
# #         return None
# #     user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
# #     db.commit()
# #     db.refresh(user)
# #     logger.info(f"User status toggled to {user.status} for user: {user_id}")
# #     return user

# # def fetch_service_charges_and_vendors(db: Session, category_id: int, subcategory_id: int) -> dict:
# #     """Fetch vendors and their service charges for a category/subcategory."""
# #     from app.models.service_provider_model import ServiceProvider  # Avoid circular import
# #     # Placeholder; replace with actual query
# #     logger.info(f"Fetching vendors for category {category_id}, subcategory {subcategory_id}")
# #     return {"vendors": []}