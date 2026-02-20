


from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from passlib.context import CryptContext
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.utils.otp_utils import generate_otp, send_email, send_email
from app.core.security import get_password_hash
from app.models.service_provider_model import ServiceProvider
from app.models.vendor_subcategory_charge import VendorSubcategoryCharge
from app.models.sub_category import SubCategory
from app.models.category import Category

from app.models.vendor_bank_account_model import VendorBankAccount
from app.schemas.service_provider_schema import (
    VendorCreate, VendorDeviceUpdate, AddressDetailsUpdate, 
    BankDetailsUpdate, WorkDetailsUpdate, SubCategoryCharge, VendorResponse
)

from app.schemas.service_provider_schema import BankAccountOut
from app.schemas.sub_category_schema import SubCategoryStatus
from app.utils.fcm import send_notification, NotificationType
import logging
# from typing import List, Tuple
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
MAX_OTP_RESENDS = 3
OTP_RESEND_COOLDOWN_MINUTES = 1

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

# def get_vendor_by_id(db: Session, vendor_id: int) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()

# def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
#     return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

# def get_category_by_id(db: Session, category_id: int) -> Category:
#     return db.query(Category).filter(Category.id == category_id).first()

# def attach_subcategory_charges(db: Session, vendor_id: int) -> List[SubCategoryCharge]:
#     charges = db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).all()
#     return [
#         SubCategoryCharge(
#             subcategory_id=charge.subcategory_id,
#             subcategory_name=get_subcategory_by_id(db, charge.subcategory_id).name if get_subcategory_by_id(db, charge.subcategory_id) else None,
#             service_charge=charge.service_charge
#         )
#         for charge in charges
#     ]

# # Add this import at top
# from app.models.vendor_bank_account_model import VendorBankAccount

# # Update build_vendor_response function
# def build_vendor_response(db: Session, vendor: ServiceProvider) -> VendorResponse:
#     """Build vendor response with all details"""
    
#     # Get Category Name
#     category_name = None
#     if vendor.category_id:
#         category = db.query(Category).filter(Category.id == vendor.category_id).first()
#         category_name = category.name if category else None

#     # Get SubCategory Names + Charges
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
    
#     # ✅ Get bank accounts
#     from app.schemas.service_provider_schema import BankAccountOut
#     bank_accounts = db.query(VendorBankAccount).filter(
#         VendorBankAccount.vendor_id == vendor.id
#     ).order_by(
#         VendorBankAccount.is_primary.desc(),
#         VendorBankAccount.created_at.desc()
#     ).all()
    
#     bank_accounts_out = [BankAccountOut.from_orm(ba) for ba in bank_accounts]

#     return VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         category_name=category_name,
#         profile_pic=vendor.profile_pic,
#         step=vendor.step,
#         status=vendor.status,
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges,
#         bank_accounts=bank_accounts_out  # ✅ Add this
#     )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
    """Get vendor by email."""
    try:
        return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching vendor by email: {str(e)}")
        return None


def get_vendor_by_id(db: Session, vendor_id: int) -> ServiceProvider:
    """Get vendor by ID."""
    try:
        return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching vendor by ID: {str(e)}")
        return None


def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
    """Get subcategory by ID."""
    return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()


def get_category_by_id(db: Session, category_id: int) -> Category:
    """Get category by ID."""
    return db.query(Category).filter(Category.id == category_id).first()


def attach_subcategory_charges(db: Session, vendor_id: int) -> List[SubCategoryCharge]:
    """Attach subcategory charges for vendor."""
    charges = db.query(VendorSubcategoryCharge).filter(
        VendorSubcategoryCharge.vendor_id == vendor_id
    ).all()
    return [
        SubCategoryCharge(
            subcategory_id=charge.subcategory_id,
            subcategory_name=get_subcategory_by_id(db, charge.subcategory_id).name 
                if get_subcategory_by_id(db, charge.subcategory_id) else None,
            service_charge=charge.service_charge
        )
        for charge in charges
    ]


def build_vendor_response(db: Session, vendor: ServiceProvider) -> VendorResponse:
    """Build vendor response with all details."""
    
    # Get Category Name
    category_name = None
    if vendor.category_id:
        category = db.query(Category).filter(Category.id == vendor.category_id).first()
        category_name = category.name if category else None

    # Get SubCategory Names + Charges
    subcategory_charges = attach_subcategory_charges(db, vendor.id)
    
    # Get bank accounts
    bank_accounts = db.query(VendorBankAccount).filter(
        VendorBankAccount.vendor_id == vendor.id
    ).order_by(
        VendorBankAccount.is_primary.desc(),
        VendorBankAccount.created_at.desc()
    ).all()
    
    bank_accounts_out = [BankAccountOut.model_validate(ba) for ba in bank_accounts]

    return VendorResponse(
        id=vendor.id,
        full_name=vendor.full_name,
        email=vendor.email,
        phone=vendor.phone,
        address=vendor.address,
        state=vendor.state,
        city=vendor.city,
        pincode=vendor.pincode,
        account_holder_name=vendor.account_holder_name,
        account_number=vendor.account_number,
        ifsc_code=vendor.ifsc_code,
        upi_id=vendor.upi_id,
        identity_doc_type=vendor.identity_doc_type,
        identity_doc_number=vendor.identity_doc_number,
        identity_doc_url=vendor.identity_doc_url,
        bank_doc_type=vendor.bank_doc_type,
        bank_doc_number=vendor.bank_doc_number,
        bank_doc_url=vendor.bank_doc_url,
        address_doc_type=vendor.address_doc_type,
        address_doc_number=vendor.address_doc_number,
        address_doc_url=vendor.address_doc_url,
        category_id=vendor.category_id,
        category_name=category_name,
        profile_pic=vendor.profile_pic,
        step=vendor.step,
        status=vendor.status,
        admin_status=vendor.admin_status,
        work_status=vendor.work_status,
        subcategory_charges=subcategory_charges,
        bank_accounts=bank_accounts_out
    )


# =================== VENDOR REGISTRATION ===================

def create_vendor(db: Session, vendor: VendorCreate) -> Dict[str, Any]:
    """
    Create a new vendor and send OTP.
    Returns dict with success status and message.
    """
    try:
        # Check if vendor already exists
        existing = get_vendor_by_email(db, email=vendor.email)
        
        if existing and existing.otp_verified:
            logger.warning(f"Vendor registration attempt with existing verified email: {vendor.email}")
            return {
                "success": False,
                "message": "This email is already registered with us. Please log in to your account.",
                "data": None
            }
        
        # Update existing unverified vendor
        if existing and not existing.otp_verified:
            logger.info(f"Updating existing unverified vendor: {vendor.email}")
            existing.full_name = vendor.full_name
            existing.phone = vendor.phone
            existing.password = get_password_hash(vendor.password)
            existing.terms_accepted = vendor.terms_accepted
            existing.identity_doc_type = vendor.identity_doc_type
            existing.identity_doc_number = vendor.identity_doc_number
            existing.new_fcm_token = vendor.new_fcm_token
            existing.old_fcm_token = vendor.old_fcm_token
            existing.latitude = vendor.latitude
            existing.longitude = vendor.longitude
            existing.device_name = vendor.device_name
            existing.step = 0
            existing.otp = generate_otp()
            existing.otp_created_at = datetime.utcnow()
            existing.otp_last_sent_at = datetime.utcnow()
            existing.otp_attempts = 0
            db.commit()
            db.refresh(existing)
            
            # Send OTP
            try:
                send_email(vendor.email, existing.otp, template="otp")
                logger.info(f"OTP sent to existing unverified vendor: {vendor.email}")
            except Exception as e:
                logger.error(f"Failed to send OTP to {vendor.email}: {str(e)}")
            
            return {
                "success": True,
                "message": f"OTP sent to {vendor.email}",
                "data": {"vendor_id": existing.id, "step": existing.step}
            }
        
        # Create new vendor
        logger.info(f"Creating new vendor: {vendor.email}")
        hashed_password = get_password_hash(vendor.password)
        otp = generate_otp()
        now = datetime.utcnow()
        
        db_vendor = ServiceProvider(
            full_name=vendor.full_name,
            email=vendor.email,
            phone=vendor.phone,
            password=hashed_password,
            terms_accepted=vendor.terms_accepted,
            identity_doc_type=vendor.identity_doc_type,
            identity_doc_number=vendor.identity_doc_number,
            new_fcm_token=vendor.new_fcm_token,
            old_fcm_token=vendor.old_fcm_token,
            latitude=vendor.latitude,
            longitude=vendor.longitude,
            device_name=vendor.device_name,
            step=0,
            otp=otp,
            otp_created_at=now,
            otp_last_sent_at=now,
            otp_verified=False,
            otp_attempts=0,
            last_login=now,
            last_device_update=now,
            status='pending',
            admin_status='inactive',
            work_status='work_on'
        )
        db.add(db_vendor)
        db.commit()
        db.refresh(db_vendor)
        
        # Send OTP
        try:
            send_email(vendor.email, otp, template="otp")
            logger.info(f"OTP sent to new vendor: {vendor.email}")
        except Exception as e:
            logger.error(f"Failed to send OTP to {vendor.email}: {str(e)}")
        
        return {
            "success": True,
            "message": f"OTP sent to {vendor.email}",
            "data": {"vendor_id": db_vendor.id, "step": db_vendor.step}
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in create_vendor: {str(e)}")
        return {
            "success": False,
            "message": "Our servers are experiencing a hiccup. Please try again later.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in create_vendor: {str(e)}")
        return {
            "success": False,
            "message": "Something went wrong while processing your request. Please try again.",
            "data": None
        }


def get_all_vendors(db: Session, page: int = 1, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None):
    """Get all vendors with pagination, search, and status filters."""
    try:
        offset = (page - 1) * limit
        query = (
            db.query(ServiceProvider)
            .options(
                joinedload(ServiceProvider.category),
                joinedload(ServiceProvider.subcategory_charges).joinedload(VendorSubcategoryCharge.subcategory)
            )
        )

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (ServiceProvider.full_name.ilike(search_filter)) |
                (ServiceProvider.email.ilike(search_filter)) |
                (ServiceProvider.phone.ilike(search_filter))
            )

        if status:
            query = query.filter(ServiceProvider.admin_status == status)

        total = query.count()
        vendors = query.order_by(ServiceProvider.created_at.desc()).offset(offset).limit(limit).all()

        vendor_responses = []
        for vendor in vendors:
            vendor_responses.append(build_vendor_response(db, vendor))

        return vendor_responses, total
    except Exception as e:
        logger.error(f"Error fetching vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def delete_vendor(db: Session, vendor_id: int) -> None:
    """Delete vendor by ID."""
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        logger.error(f"Vendor not found for ID {vendor_id}")
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    try:
        db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).delete()
        db.delete(vendor)
        db.commit()
        logger.info(f"Vendor deleted successfully: ID {vendor_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")





def verify_vendor_otp(db: Session, email: str, otp: str) -> Dict[str, Any]:
    """
    Verify OTP for vendor email verification.
    Returns dict with success status, message, and vendor data.
    """
    try:
        vendor = get_vendor_by_email(db, email)
        
        if not vendor:
            logger.warning(f"OTP verification attempt for non-existent email: {email}")
            return {
                "success": False,
                "message": "Vendor not found with this email.",
                "data": None
            }
        
        if vendor.otp_verified:
            logger.warning(f"OTP verification attempt for already verified vendor: {email}")
            return {
                "success": False,
                "message": "Your account is already verified! You can log in now.",
                "data": None
            }
        
        if vendor.otp_attempts >= MAX_OTP_ATTEMPTS:
            logger.warning(f"Maximum OTP attempts exceeded for: {email}")
            return {
                "success": False,
                "message": "You've exceeded the maximum attempts. Please request a new OTP to continue.",
                "data": None
            }
        
        if not vendor.otp:
            logger.warning(f"No OTP found for vendor: {email}")
            return {
                "success": False,
                "message": "No active OTP found for this account. Please request a new one.",
                "data": None
            }
        
        if vendor.otp != otp:
            vendor.otp_attempts += 1
            db.commit()
            logger.warning(f"Invalid OTP attempt for: {email} (Attempts: {vendor.otp_attempts})")
            return {
                "success": False,
                "message": f"The OTP you entered is incorrect. You have {MAX_OTP_ATTEMPTS - vendor.otp_attempts} attempt(s) left.",
                "data": None
            }
        
        if (datetime.utcnow() - vendor.otp_created_at) > timedelta(minutes=OTP_EXPIRY_MINUTES):
            logger.warning(f"Expired OTP attempt for: {email}")
            return {
                "success": False,
                "message": "This OTP has expired. Please request a new one.",
                "data": None
            }
        
        # Verify vendor
        vendor.otp_verified = True
        vendor.otp_attempts = 0
        vendor.otp = None
        vendor.otp_created_at = None
        vendor.status = 'pending'
        vendor.step = 1
        vendor.last_login = datetime.utcnow()
        db.commit()
        db.refresh(vendor)
        
        # Send welcome email
        try:
            send_email(
                receiver_email=vendor.email,
                template="welcome",
                name=vendor.full_name
            )
            logger.info(f"Welcome email sent to vendor: {vendor.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {vendor.email}: {str(e)}")
        
        # Send notification if FCM token available
        fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
        if fcm_token:
            try:
                send_notification(
                    recipient=vendor.email,
                    notification_type=NotificationType.vendor_welcome,
                    message=f"Welcome, {vendor.full_name}! Your account has been verified.",
                    recipient_id=vendor.id,
                    fcm_token=fcm_token
                )
                logger.info(f"Welcome notification sent to vendor {vendor.id}")
            except Exception as e:
                logger.warning(f"Failed to send welcome notification: {str(e)}")
        
        vendor_response = build_vendor_response(db, vendor)
        logger.info(f"Vendor OTP verified successfully: {email}")
        
        return {
            "success": True,
            "message": "Email verified successfully! You can now complete your profile.",
            "data": vendor_response
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in verify_vendor_otp: {str(e)}")
        return {
            "success": False,
            "message": "Our servers are experiencing a hiccup. Please try again later.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in verify_vendor_otp: {str(e)}")
        return {
            "success": False,
            "message": "Something went wrong while verifying your OTP. Please try again.",
            "data": None
        }


def resend_otp(db: Session, email: str) -> Dict[str, Any]:
    """Resend OTP for vendor email verification."""
    try:
        vendor = get_vendor_by_email(db, email)
        
        if not vendor:
            logger.warning(f"OTP resend attempt for non-existent email: {email}")
            return {
                "success": False,
                "message": "We couldn't find an account with this email. Please check and try again.",
                "data": None
            }
        
        if vendor.otp_verified:
            logger.warning(f"OTP resend attempt for already verified vendor: {email}")
            return {
                "success": False,
                "message": "Your account is already verified! You can log in now.",
                "data": None
            }
        
        # Check cooldown
        if vendor.otp_last_sent_at:
            time_since_last = datetime.utcnow() - vendor.otp_last_sent_at
            if time_since_last < timedelta(minutes=OTP_RESEND_COOLDOWN_MINUTES):
                remaining = OTP_RESEND_COOLDOWN_MINUTES * 60 - time_since_last.seconds
                logger.warning(f"OTP resend cooldown for: {email}")
                return {
                    "success": False,
                    "message": f"Please wait {remaining} seconds before requesting a new OTP.",
                    "data": None
                }
        
        if vendor.otp_attempts >= MAX_OTP_RESENDS:
            logger.warning(f"Maximum OTP resend attempts exceeded for: {email}")
            return {
                "success": False,
                "message": "You've exceeded the maximum resend attempts. Please try again later.",
                "data": None
            }
        
        otp = generate_otp()
        vendor.otp = otp
        vendor.otp_created_at = datetime.utcnow()
        vendor.otp_last_sent_at = datetime.utcnow()
        vendor.otp_attempts = 0
        db.commit()
        db.refresh(vendor)
        
        # Send OTP
        try:
            send_email(email, otp, template="otp")
            logger.info(f"OTP resent to: {email}")
        except Exception as e:
            logger.error(f"Failed to resend OTP to {email}: {str(e)}")
        
        return {
            "success": True,
            "message": "OTP resent successfully to your email.",
            "data": None
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in resend_otp: {str(e)}")
        return {
            "success": False,
            "message": "Our servers are experiencing a hiccup. Please try again later.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in resend_otp: {str(e)}")
        return {
            "success": False,
            "message": "Something went wrong while resending your OTP. Please try again.",
            "data": None
        }


# =================== VENDOR LOGIN ===================

def vendor_login(db: Session, email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate vendor with email and password.
    Returns dict with success status, message, and vendor data.
    """
    try:
        vendor = get_vendor_by_email(db, email)
        
        if not vendor:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return {
                "success": False,
                "message": "We couldn't find an account with this email. Please check the email or register.",
                "data": None
            }
            
        if vendor.status in ['rejected', 'inactive']:
            logger.warning(f"Login attempt by deactivated vendor: {email}")
            return {
                "success": False,
                "message": "Your account has been deactivated or rejected. Please contact support.",
                "data": None
            }
        
        if not vendor.otp_verified:
            logger.warning(f"Login attempt with unverified email: {email}")
            return {
                "success": False,
                "message": "Your email is not verified yet. Please check your inbox for the OTP we sent you.",
                "data": None
            }
        
        if not verify_password(password, vendor.password):
            logger.warning(f"Login attempt with incorrect password for: {email}")
            return {
                "success": False,
                "message": "The password you entered is incorrect. Double-check and try again.",
                "data": None
            }
        
        # Update last login
        vendor.last_login = datetime.utcnow()
        db.commit()
        db.refresh(vendor)
        
        vendor_response = build_vendor_response(db, vendor)
        logger.info(f"Vendor logged in successfully: {email}")
        
        return {
            "success": True,
            "message": "Login successful!",
            "data": vendor_response
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error in vendor_login: {str(e)}")
        return {
            "success": False,
            "message": "Database error occurred. Please try again.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error in vendor_login: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "data": None
        }


def update_vendor_address(db: Session, vendor_id: int, update: AddressDetailsUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    if vendor.step == 0:
        vendor.step = 2
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)



def update_vendor_bank(db: Session, vendor_id: int, update: BankDetailsUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")
    
    # ✅ Step 1: Update legacy fields (backward compatibility)
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    # ✅ Step 2: Create entry in vendor_bank_accounts table
    from app.crud import vendor_bank_crud
    from app.schemas.service_provider_schema import BankAccountCreate
    
    # Check if primary bank already exists
    existing_primary = vendor_bank_crud.get_primary_bank_account(db, vendor_id)
    
    if not existing_primary:
        # Create new primary bank account from registration data
        bank_data = BankAccountCreate(
            account_holder_name=update.account_holder_name,
            account_number=update.account_number,
            ifsc_code=update.ifsc_code,
            bank_name=None,  # Not in registration
            branch_name=None,
            upi_id=update.upi_id,
            is_primary=True
        )
        vendor_bank_crud.create_bank_account(db, vendor_id, bank_data)
        logger.info(f"Created primary bank account for vendor {vendor_id} from registration")
    
    if vendor.step == 1:
        vendor.step = 3
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)
def update_vendor_work(db: Session, vendor_id: int, update: WorkDetailsUpdate) -> VendorResponse:
    logger.debug(f"Updating work details for vendor_id: {vendor_id}, update: {update.dict()}")
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        logger.error(f"Vendor with ID {vendor_id} not found")
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")

    if not vendor.otp_verified:
        logger.error(f"Vendor {vendor_id} not OTP verified")
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")

    if not update.subcategory_charges:
        logger.error("No subcategory charges provided")
        raise HTTPException(status_code=400, detail="Please select at least one service and its charge.")

    category = get_category_by_id(db, update.category_id)
    if not category:
        logger.error(f"Category {update.category_id} not found")
        raise HTTPException(status_code=404, detail="Selected category is invalid or no longer exists.")

    try:
        logger.debug(f"Setting category_id: {update.category_id}")
        vendor.category_id = update.category_id

        # Delete existing charges for this category only (to allow multiple categories)
        db.query(VendorSubcategoryCharge).filter(
            VendorSubcategoryCharge.vendor_id == vendor_id,
            VendorSubcategoryCharge.category_id == update.category_id
        ).delete()

        for charge in update.subcategory_charges:
            logger.debug(f"Processing subcategory charge: {charge}")
            if charge.service_charge < 0:
                logger.error(f"Negative service charge: {charge.service_charge}")
                raise HTTPException(status_code=400, detail="Service charge cannot be negative. Please enter a valid amount.")
            subcategory = get_subcategory_by_id(db, charge.subcategory_id)
            if not subcategory:
                logger.error(f"Subcategory {charge.subcategory_id} not found")
                raise HTTPException(status_code=404, detail="One of the selected services is invalid or no longer exists.")
            if subcategory.category_id != update.category_id:
                logger.error(f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
                raise HTTPException(status_code=400, detail="The selected service does not belong to the chosen category.")
            if subcategory.status not in [SubCategoryStatus.active, SubCategoryStatus.inactive]:
                logger.error(f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}"
                )

            new_charge = VendorSubcategoryCharge(
                subcategory_id=charge.subcategory_id,
                category_id=update.category_id,
                service_charge=charge.service_charge,
            )
            logger.debug(f"Inserting charge: vendor_id={vendor_id}, subcategory_id={charge.subcategory_id}, service_charge={charge.service_charge}")
            vendor.subcategory_charges.append(new_charge)

        if vendor.step == 2:
            vendor.step = 4
        vendor.status = 'approved'
        vendor.last_device_update = datetime.utcnow()
        logger.debug(f"Committing changes for vendor_id: {vendor_id}")
        db.commit()
        db.refresh(vendor)

        logger.info(f"Vendor work details updated successfully: {vendor.id}")
        return build_vendor_response(db, vendor)
    except HTTPException as e:
        db.rollback()
        logger.error(f"HTTPException in update_vendor_work: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError in update_vendor_work: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in update_vendor_work: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def update_vendor_documents(db: Session, vendor_id: int, profile_pic: UploadFile | None, identity_doc: UploadFile, bank_doc: UploadFile, address_doc: UploadFile) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
    max_file_size = 5 * 1024 * 1024
    upload_base_dir = os.getenv("UPLOAD_DIR", "uploads")

    def save_file(file: UploadFile, subdir: str, prefix: str) -> str:
        try:
            ext = file.filename.split(".")[-1].lower() if file.filename else ""
            if ext not in allowed_extensions:
                logger.error(f"Invalid file type for {prefix}: {ext}")
                raise HTTPException(status_code=400, detail=f"The {prefix} file type is not valid. Please upload one of: {', '.join(allowed_extensions)}")
            if file.size > max_file_size:
                logger.error(f"{prefix} file too large: {file.size} bytes")
                raise HTTPException(status_code=400, detail=f"The {prefix} file is too large. The maximum size is {max_file_size // (1024*1024)}MB.")
            
            file_path = Path(upload_base_dir) / subdir / f"{prefix}_{vendor_id}.{ext}"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("wb") as buffer:
                buffer.write(file.file.read())
            logger.debug(f"Saved {prefix} file to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving {prefix} file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"We couldn't save your {prefix} file. Please try again.")

    try:
        if profile_pic:
            vendor.profile_pic = save_file(profile_pic, "profiles", "profile")
        
        vendor.identity_doc_url = save_file(identity_doc, "documents", "identity")
        vendor.bank_doc_url = save_file(bank_doc, "documents", "bank")
        vendor.address_doc_url = save_file(address_doc, "documents", "address")
        
        if vendor.step == 3:
            vendor.step = 5
        vendor.last_device_update = datetime.utcnow()
        db.commit()
        db.refresh(vendor)
        
        logger.info(f"Documents updated successfully for vendor_id: {vendor_id}")
        return build_vendor_response(db, vendor)
    except HTTPException as e:
        db.rollback()
        logger.error(f"HTTPException in update_vendor_documents: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError in update_vendor_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in update_vendor_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def update_vendor_device(db: Session, vendor_id: int, update: VendorDeviceUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)

def change_vendor_admin_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if status not in ['active', 'inactive']:
        raise HTTPException(status_code=400, detail="The provided account status is invalid.")
    
    vendor.admin_status = status
    db.commit()
    db.refresh(vendor)
    
    fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
    if fcm_token:
        try:
            send_notification(
                recipient=vendor.email,
                notification_type=NotificationType.admin_status_updated,
                message=f"Your account status has been updated to {status}",
                recipient_id=vendor.id,
                fcm_token=fcm_token
            )
            logger.info(f"Admin status notification sent to vendor {vendor_id}")
        except Exception as e:
            logger.warning(f"Failed to send admin status notification to vendor {vendor_id}: {str(e)}")
    
    return build_vendor_response(db, vendor)

def change_vendor_work_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="We couldn't find your profile. Please check if you're logged in correctly.")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to continue.")
    
    if vendor.admin_status != 'active':
        raise HTTPException(status_code=403, detail="Your account must be active by an admin to change your work status.")
    
    if status not in ['work_on', 'work_off']:
        raise HTTPException(status_code=400, detail="The provided work status is invalid.")
    
    vendor.work_status = status
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)
