import logging
import datetime
import random
import string
import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vendor_model import Vendor
from app.models.user import User
from app.models.referral_model import AdminReferralCode
from app.models.vendor_referral_model import VendorReferral, ReferralStatus
from app.models.user_referral_model import UserReferral
from app.models.booking_model import Booking, BookingStatus
from app.models.wallet_model import Wallet, WalletTransaction
from app.models.app_config_model import AppConfig
from app.utils.fcm import send_notification, NotificationType

logger = logging.getLogger(__name__)

MIN_REFERRAL_REWARD = 5
MAX_REFERRAL_REWARD = 40

def clean_referral_code(code: str) -> str:
    """Removes all non-alphanumeric characters (like '-', '_', spaces) and converts to uppercase."""
    if not code:
        return ""
    return re.sub(r'[^A-Za-z0-9]', '', code).upper()

def generate_random_reward_amount(db: Session = None, min_val: int = MIN_REFERRAL_REWARD, max_val: int = MAX_REFERRAL_REWARD) -> float:
    """Generate a random reward amount between min_val and max_val (inclusive), dynamically using AppConfig DB range if available."""
    if db:
        config = db.query(AppConfig).first()
        if config:
            if getattr(config, 'min_referral_reward', None) is not None:
                min_val = int(config.min_referral_reward)
            if getattr(config, 'max_referral_reward', None) is not None:
                max_val = int(config.max_referral_reward)

    if min_val > max_val:
        min_val, max_val = max_val, min_val

    return float(random.randint(min_val, max_val))

def get_referral_reward_configs(db: Session) -> tuple[float, float]:
    """Get dynamic vendor referral reward configuration (random range or fixed amount set by admin)."""
    config = db.query(AppConfig).first()
    is_random = getattr(config, 'is_random_referral_reward', False) if config else False

    if is_random:
        referrer_amount = generate_random_reward_amount(db)
        referred_amount = generate_random_reward_amount(db)
    else:
        referrer_amount = float(getattr(config, 'referrer_reward_amount', 100.0))
        referred_amount = float(getattr(config, 'referred_vendor_reward_amount', 50.0))

    return referrer_amount, referred_amount

def get_user_referral_reward_configs(db: Session) -> tuple[float, float]:
    """Get dynamic user referral reward configuration (random range or fixed amount set by admin)."""
    config = db.query(AppConfig).first()
    is_random = getattr(config, 'is_random_referral_reward', False) if config else False

    if is_random:
        referrer_amount = generate_random_reward_amount(db)
        referred_amount = generate_random_reward_amount(db)
    else:
        referrer_amount = float(getattr(config, 'user_referrer_reward_amount', 50.0))
        referred_amount = float(getattr(config, 'user_referred_reward_amount', 50.0))

    return referrer_amount, referred_amount

def get_or_create_vendor_wallet(db: Session, vendor_id: int) -> Wallet:
    """Ensure a wallet exists for the given vendor."""
    wallet = db.query(Wallet).filter(Wallet.vendor_id == vendor_id).first()
    if not wallet:
        wallet = Wallet(vendor_id=vendor_id, balance=0.0)
        db.add(wallet)
        db.flush()
    return wallet

def get_or_create_user_wallet(db: Session, user_id: int) -> Wallet:
    """Ensure a wallet exists for the given customer user."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.flush()
    return wallet

# ==================== CODE GENERATION (NO SPECIAL CHARACTERS) ====================

def generate_unique_user_referral_code(db: Session, user: User) -> str:
    """
    Generate a unique referral code for a customer user (e.g. SERWEXU10001).
    Strictly alphanumeric without any special characters (like '-', '_', etc.).
    """
    if user.referral_code:
        return user.referral_code
    
    base_code = f"SERWEXU{10000 + user.id}"
    existing = db.query(User).filter(User.referral_code == base_code).first()
    if not existing:
        user.referral_code = base_code
        db.commit()
        return base_code

    # Fallback to random alphanumeric suffix if collision
    while True:
        rand_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"SERWEXU{rand_suffix}"
        if not db.query(User).filter(User.referral_code == code).first():
            user.referral_code = code
            db.commit()
            return code

def generate_admin_campaign_referral_code(db: Session, campaign_name: Optional[str] = None, length: int = 6) -> str:
    """
    Generate a clean, unique alphanumeric referral code for admin campaigns without any special characters.
    e.g. CAMP739281, SUMMER2026, FESTIVE88
    """
    prefix = "CAMP"
    if campaign_name:
        clean_prefix = re.sub(r'[^A-Za-z0-9]', '', campaign_name).upper()[:6]
        if clean_prefix:
            prefix = clean_prefix

    while True:
        rand_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        code = f"{prefix}{rand_suffix}"
        
        # Check uniqueness across AdminReferralCode, User, and Vendor
        in_admin = db.query(AdminReferralCode).filter(func.upper(AdminReferralCode.code) == code).first()
        in_user = db.query(User).filter(func.upper(User.referral_code) == code).first()
        in_vendor = db.query(Vendor).filter(func.upper(Vendor.referral_code) == code).first()
        if not in_admin and not in_user and not in_vendor:
            return code

def create_admin_campaign_referral_code(
    db: Session,
    name: str,
    code: Optional[str] = None,
    no_of_bookings: int = 10,
    commission_percentage: float = 0.0
) -> AdminReferralCode:
    """
    Create an admin referral code for marketing / campaigning.
    - If code is provided: sanitizes and validates that it is strictly alphanumeric (no special characters like '-') and unique.
    - If code is not provided: automatically generates a unique alphanumeric campaign code without special characters.
    """
    if not name or not name.strip():
        raise ValueError("Campaign name is required.")

    name_clean = name.strip()

    if code and code.strip():
        code_clean = clean_referral_code(code.strip())
        if not code_clean:
            raise ValueError("Referral code must contain alphanumeric characters (no special characters allowed).")
        
        # Collision checks
        if db.query(AdminReferralCode).filter(func.upper(AdminReferralCode.code) == code_clean).first():
            raise ValueError(f"Admin referral code '{code_clean}' already exists.")
        if db.query(User).filter(func.upper(User.referral_code) == code_clean).first():
            raise ValueError(f"Referral code '{code_clean}' conflicts with an existing customer referral code.")
        if db.query(Vendor).filter(func.upper(Vendor.referral_code) == code_clean).first():
            raise ValueError(f"Referral code '{code_clean}' conflicts with an existing vendor referral code.")
        final_code = code_clean
    else:
        final_code = generate_admin_campaign_referral_code(db, campaign_name=name_clean)

    db_referral = AdminReferralCode(
        code=final_code,
        name=name_clean,
        no_of_bookings=no_of_bookings,
        commission_percentage=commission_percentage
    )
    db.add(db_referral)
    db.commit()
    db.refresh(db_referral)
    logger.info(f"Created Admin Campaign Referral Code: '{final_code}' for campaign '{name_clean}'.")
    return db_referral

# ==================== VENDOR REFERRAL LOGIC ====================

def process_vendor_referral_registration(db: Session, new_vendor: Vendor, input_code: str) -> bool:
    """
    Validates referral code and creates permanent referral relationship for vendors.
    Supports vendor-to-vendor referrals and admin campaign referral codes.
    Returns True if referral association created successfully, False otherwise.
    """
    if not input_code or not input_code.strip():
        return False
        
    code_raw = input_code.strip().upper()
    code_clean = clean_referral_code(input_code)
    
    # 1. Look up referrer vendor (case-insensitive & clean)
    referrer = db.query(Vendor).filter(
        (func.upper(Vendor.referral_code) == code_raw) |
        (func.upper(Vendor.referral_code) == code_clean)
    ).first()

    if referrer:
        # Anti-Self Referral Check
        if referrer.id == new_vendor.id:
            logger.warning(f"Self-referral attempt blocked for vendor ID {new_vendor.id}.")
            return False

        # Check if new vendor already has a referrer (Single referrer rule)
        existing_referral = db.query(VendorReferral).filter(
            VendorReferral.referred_vendor_id == new_vendor.id
        ).first()
        if existing_referral:
            logger.warning(f"Vendor {new_vendor.id} already associated with referrer {existing_referral.referrer_vendor_id}.")
            return False

        # Associate referral on Vendor model
        new_vendor.referred_by_id = referrer.id
        new_vendor.applied_referral_code = referrer.referral_code
        new_vendor.referral_type = 'vendor'

        referrer_amount, referred_amount = get_referral_reward_configs(db)

        referral_record = VendorReferral(
            referrer_vendor_id=referrer.id,
            referred_vendor_id=new_vendor.id,
            referral_code=referrer.referral_code,
            status=ReferralStatus.REGISTERED,
            referrer_reward_amount=referrer_amount,
            referred_vendor_reward_amount=referred_amount
        )
        db.add(referral_record)
        db.commit()
        logger.info(f"Successfully associated Vendor #{new_vendor.id} with Referrer #{referrer.id} via code '{referrer.referral_code}'.")
        return True

    # 2. Check if this is an Admin Campaign Referral Code
    admin_referral = db.query(AdminReferralCode).filter(
        (func.upper(AdminReferralCode.code) == code_raw) |
        (func.upper(AdminReferralCode.code) == code_clean)
    ).first()

    if admin_referral:
        existing_referral = db.query(VendorReferral).filter(
            VendorReferral.referred_vendor_id == new_vendor.id
        ).first()
        if existing_referral:
            logger.warning(f"Vendor {new_vendor.id} already associated with a referrer.")
            return False

        new_vendor.referred_by_id = None
        new_vendor.applied_referral_code = admin_referral.code
        new_vendor.referral_type = 'campaign'

        referrer_amount, referred_amount = get_referral_reward_configs(db)

        referral_record = VendorReferral(
            referrer_vendor_id=None,
            referred_vendor_id=new_vendor.id,
            referral_code=admin_referral.code,
            status=ReferralStatus.REGISTERED,
            referrer_reward_amount=0.0,
            referred_vendor_reward_amount=referred_amount
        )
        db.add(referral_record)
        db.commit()
        logger.info(f"Successfully associated Vendor #{new_vendor.id} with Admin Campaign Code '{admin_referral.code}'.")
        return True

    logger.warning(f"Referral registration failed: code '{input_code}' not found.")
    return False

def process_first_booking_referral_reward(db: Session, booking: Booking) -> bool:
    """
    Atomically processes referral rewards upon successful booking completion for vendors.
    Only triggers on the vendor's VERY FIRST COMPLETED booking.
    """
    if not booking or not booking.serviceprovider_id:
        return False

    if booking.status != BookingStatus.completed:
        return False

    vendor_id = booking.serviceprovider_id

    # 1. Find active referral relationship for this vendor
    referral = db.query(VendorReferral).filter(
        VendorReferral.referred_vendor_id == vendor_id
    ).first()

    if not referral:
        return False

    if referral.status in [ReferralStatus.REWARDED, ReferralStatus.CANCELLED]:
        logger.info(f"Referral #{referral.id} for vendor #{vendor_id} is already in terminal state '{referral.status}'. Skipping.")
        return False

    # 2. Check if this is the vendor's FIRST completed booking
    prior_completed_count = db.query(Booking).filter(
        Booking.serviceprovider_id == vendor_id,
        Booking.status == BookingStatus.completed,
        Booking.id != booking.id
    ).count()

    if prior_completed_count > 0:
        logger.info(f"Vendor #{vendor_id} already has {prior_completed_count} prior completed bookings. Referral qualification requires 1st booking.")
        return False

    try:
        # Atomic Transaction
        referral.status = ReferralStatus.QUALIFIED
        referral.qualified_booking_id = booking.id
        db.flush()

        referrer_amount = referral.referrer_reward_amount if referral.referrer_reward_amount and referral.referrer_reward_amount > 0 else generate_random_reward_amount()
        referred_amount = referral.referred_vendor_reward_amount if referral.referred_vendor_reward_amount and referral.referred_vendor_reward_amount > 0 else generate_random_reward_amount()

        # Referrer Wallet Credit (only if there is an actual referrer vendor)
        if referral.referrer_vendor_id:
            referrer_wallet = get_or_create_vendor_wallet(db, referral.referrer_vendor_id)
            referrer_wallet.balance += referrer_amount

            referrer_tx_ref = f"REF_BONUS_REFERRER_{referral.id}"
            existing_tx = db.query(WalletTransaction).filter(WalletTransaction.reference_id == referrer_tx_ref).first()
            if not existing_tx:
                db.add(WalletTransaction(
                    wallet_id=referrer_wallet.id,
                    vendor_id=referral.referrer_vendor_id,
                    referral_id=referral.id,
                    booking_id=booking.id,
                    amount=referrer_amount,
                    transaction_type="REFERRAL_BONUS_REFERRER",
                    description=f"Referral bonus for referring Vendor #{vendor_id}",
                    status="COMPLETED",
                    reference_id=referrer_tx_ref
                ))

        # Referred Vendor Wallet Credit (Welcome bonus)
        referred_wallet = get_or_create_vendor_wallet(db, referral.referred_vendor_id)
        referred_wallet.balance += referred_amount

        referred_tx_ref = f"REF_BONUS_REFERRED_{referral.id}"
        existing_tx2 = db.query(WalletTransaction).filter(WalletTransaction.reference_id == referred_tx_ref).first()
        if not existing_tx2:
            db.add(WalletTransaction(
                wallet_id=referred_wallet.id,
                vendor_id=referral.referred_vendor_id,
                referral_id=referral.id,
                booking_id=booking.id,
                amount=referred_amount,
                transaction_type="REFERRAL_BONUS_NEW_VENDOR",
                description="Welcome referral bonus for completing first booking",
                status="COMPLETED",
                reference_id=referred_tx_ref
            ))

        # Mark Rewarded
        referral.status = ReferralStatus.REWARDED
        referral.rewarded_at = datetime.datetime.utcnow()

        db.commit()
        logger.info(f"Referral #{referral.id} successfully rewarded! Referrer #{referral.referrer_vendor_id} (+₹{referrer_amount}), Referred Vendor #{vendor_id} (+₹{referred_amount}).")

        # 3. Push Notifications
        _send_referral_notifications(db, referral)
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"Error processing referral reward for booking #{booking.id}: {str(e)}")
        return False

# ==================== USER REFERRAL LOGIC ====================

def process_user_referral_registration(db: Session, new_user: User, input_code: str) -> tuple[bool, str]:
    """
    Validates referral code and creates permanent referral relationship for customer users.
    Supports user-to-user referrals and admin campaign referral codes.
    Returns (success: bool, message: str).
    """
    if not input_code or not input_code.strip():
        return False, "No referral code provided"
        
    code_raw = input_code.strip().upper()
    code_clean = clean_referral_code(input_code)
    
    # 1. Reject cross-type: Check if code is a Vendor referral code
    vendor_referrer = db.query(Vendor).filter(
        (func.upper(Vendor.referral_code) == code_raw) |
        (func.upper(Vendor.referral_code) == code_clean)
    ).first()
    if vendor_referrer:
        logger.warning(f"User registration attempted with Vendor referral code '{code_raw}'. Blocked.")
        return False, "Vendor referral code cannot be used for customer registration"

    # 2. Look up referrer user (case-insensitive & clean)
    referrer = db.query(User).filter(
        (func.upper(User.referral_code) == code_raw) |
        (func.upper(User.referral_code) == code_clean)
    ).first()

    if referrer:
        # Anti-Self Referral Check
        if referrer.id == new_user.id:
            logger.warning(f"Self-referral attempt blocked for customer user ID {new_user.id}.")
            return False, "Self-referral is not permitted"

        # Check single referrer rule
        existing_referral = db.query(UserReferral).filter(
            UserReferral.referred_user_id == new_user.id
        ).first()
        if existing_referral:
            logger.warning(f"User {new_user.id} already has referrer {existing_referral.referrer_user_id}.")
            return False, "Account already associated with a referrer"

        # Associate referral on User model
        new_user.referred_by_id = referrer.id
        new_user.applied_referral_code = referrer.referral_code
        new_user.referral_type = 'user'

        referrer_amount, referred_amount = get_user_referral_reward_configs(db)

        # Create UserReferral record in status REGISTERED
        referral_record = UserReferral(
            referrer_user_id=referrer.id,
            referred_user_id=new_user.id,
            referral_code=referrer.referral_code,
            status=ReferralStatus.REGISTERED,
            referrer_reward_amount=referrer_amount,
            referred_user_reward_amount=referred_amount
        )
        db.add(referral_record)
        db.commit()
        logger.info(f"Successfully associated User #{new_user.id} with Referrer User #{referrer.id} via code '{referrer.referral_code}'.")
        return True, "Referral code applied successfully"

    # 3. Check if this is an Admin Campaign Referral Code
    admin_referral = db.query(AdminReferralCode).filter(
        (func.upper(AdminReferralCode.code) == code_raw) |
        (func.upper(AdminReferralCode.code) == code_clean)
    ).first()

    if admin_referral:
        existing_referral = db.query(UserReferral).filter(
            UserReferral.referred_user_id == new_user.id
        ).first()
        if existing_referral:
            logger.warning(f"User {new_user.id} already has a referrer.")
            return False, "Account already associated with a referrer"

        new_user.referred_by_id = None
        new_user.applied_referral_code = admin_referral.code
        new_user.referral_type = 'campaign'

        referrer_amount, referred_amount = get_user_referral_reward_configs(db)

        referral_record = UserReferral(
            referrer_user_id=None,
            referred_user_id=new_user.id,
            referral_code=admin_referral.code,
            status=ReferralStatus.REGISTERED,
            referrer_reward_amount=0.0,
            referred_user_reward_amount=referred_amount
        )
        db.add(referral_record)
        db.commit()
        logger.info(f"Successfully associated User #{new_user.id} with Admin Campaign Code '{admin_referral.code}'.")
        return True, f"Campaign referral code '{admin_referral.code}' applied successfully"

    logger.warning(f"User referral registration failed: code '{input_code}' not found.")
    return False, "Invalid referral code"

def process_first_user_booking_referral_reward(db: Session, booking: Booking) -> bool:
    """
    Atomically processes user referral rewards upon successful booking completion.
    Triggers ONLY on the customer's VERY FIRST COMPLETED booking.
    """
    if not booking or not booking.user_id:
        return False

    if booking.status != BookingStatus.completed:
        return False

    user_id = booking.user_id

    # 1. Find active user referral relationship for this customer
    referral = db.query(UserReferral).filter(
        UserReferral.referred_user_id == user_id
    ).first()

    if not referral:
        return False

    if referral.status in [ReferralStatus.REWARDED, ReferralStatus.CANCELLED]:
        logger.info(f"UserReferral #{referral.id} for user #{user_id} is in terminal state '{referral.status}'. Skipping.")
        return False

    # 2. Check if this is the customer's FIRST completed booking
    prior_completed_count = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status == BookingStatus.completed,
        Booking.id != booking.id
    ).count()

    if prior_completed_count > 0:
        logger.info(f"Customer #{user_id} already has {prior_completed_count} prior completed bookings. Referral qualification requires 1st booking.")
        return False

    try:
        # Atomic Transaction
        referral.status = ReferralStatus.QUALIFIED
        referral.qualified_booking_id = booking.id
        db.flush()

        referrer_amount = referral.referrer_reward_amount if referral.referrer_reward_amount and referral.referrer_reward_amount > 0 else generate_random_reward_amount()
        referred_amount = referral.referred_user_reward_amount if referral.referred_user_reward_amount and referral.referred_user_reward_amount > 0 else generate_random_reward_amount()

        # Referrer User Wallet Credit (only if user referral)
        if referral.referrer_user_id:
            referrer_wallet = get_or_create_user_wallet(db, referral.referrer_user_id)
            referrer_wallet.balance += referrer_amount

            referrer_tx_ref = f"USER_REF_BONUS_REFERRER_{referral.id}"
            existing_tx = db.query(WalletTransaction).filter(WalletTransaction.reference_id == referrer_tx_ref).first()
            if not existing_tx:
                db.add(WalletTransaction(
                    wallet_id=referrer_wallet.id,
                    user_id=referral.referrer_user_id,
                    user_referral_id=referral.id,
                    booking_id=booking.id,
                    amount=referrer_amount,
                    transaction_type="USER_REFERRAL_BONUS_REFERRER",
                    description=f"Referral bonus for referring customer #{user_id}",
                    status="COMPLETED",
                    reference_id=referrer_tx_ref
                ))

        # Referred User Wallet Credit (Welcome bonus)
        referred_wallet = get_or_create_user_wallet(db, referral.referred_user_id)
        referred_wallet.balance += referred_amount

        referred_tx_ref = f"USER_REF_BONUS_REFERRED_{referral.id}"
        existing_tx2 = db.query(WalletTransaction).filter(WalletTransaction.reference_id == referred_tx_ref).first()
        if not existing_tx2:
            db.add(WalletTransaction(
                wallet_id=referred_wallet.id,
                user_id=referral.referred_user_id,
                user_referral_id=referral.id,
                booking_id=booking.id,
                amount=referred_amount,
                transaction_type="USER_REFERRAL_BONUS_NEW_USER",
                description="Welcome referral bonus for completing first booking",
                status="COMPLETED",
                reference_id=referred_tx_ref
            ))

        # Mark Rewarded
        referral.status = ReferralStatus.REWARDED
        referral.rewarded_at = datetime.datetime.utcnow()

        db.commit()
        logger.info(f"UserReferral #{referral.id} successfully rewarded! Referrer User #{referral.referrer_user_id} (+₹{referrer_amount}), Referred User #{user_id} (+₹{referred_amount}).")

        # 3. Push Notifications
        _send_user_referral_notifications(db, referral)
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"Error processing user referral reward for booking #{booking.id}: {str(e)}")
        return False

def _send_referral_notifications(db: Session, referral: VendorReferral):
    """Send FCM notifications to referrer and referred vendor upon reward crediting."""
    try:
        referrer = db.query(Vendor).filter(Vendor.id == referral.referrer_vendor_id).first() if referral.referrer_vendor_id else None
        referred = db.query(Vendor).filter(Vendor.id == referral.referred_vendor_id).first()

        if referrer:
            token = referrer.new_fcm_token or referrer.old_fcm_token
            msg = f"🎉 Referral Reward Earned! ₹{int(referral.referrer_reward_amount)} bonus has been added to your wallet."
            send_notification(
                recipient=referrer.email,
                notification_type=NotificationType.vendor_welcome,
                message=msg,
                recipient_id=referrer.id,
                fcm_token=token
            )

        if referred:
            token = referred.new_fcm_token or referred.old_fcm_token
            msg = f"🎉 Welcome Bonus! ₹{int(referral.referred_vendor_reward_amount)} referral bonus has been added to your wallet."
            send_notification(
                recipient=referred.email,
                notification_type=NotificationType.vendor_welcome,
                message=msg,
                recipient_id=referred.id,
                fcm_token=token
            )
    except Exception as e:
        logger.warning(f"Failed to send vendor referral reward notifications: {str(e)}")

def _send_user_referral_notifications(db: Session, referral: UserReferral):
    """Send FCM notifications to referrer and referred customer user upon reward crediting."""
    try:
        referrer = db.query(User).filter(User.id == referral.referrer_user_id).first() if referral.referrer_user_id else None
        referred = db.query(User).filter(User.id == referral.referred_user_id).first()

        if referrer:
            token = referrer.new_fcm_token or referrer.old_fcm_token
            msg = f"🎉 Referral Reward Earned! ₹{int(referral.referrer_reward_amount)} referral reward has been added to your account."
            send_notification(
                recipient=referrer.email,
                notification_type=NotificationType.booking_completed,
                message=msg,
                recipient_id=referrer.id,
                fcm_token=token
            )

        if referred:
            token = referred.new_fcm_token or referred.old_fcm_token
            msg = f"🎉 Welcome Referral Reward! ₹{int(referral.referred_user_reward_amount)} referral reward has been added to your account."
            send_notification(
                recipient=referred.email,
                notification_type=NotificationType.booking_completed,
                message=msg,
                recipient_id=referred.id,
                fcm_token=token
            )
    except Exception as e:
        logger.warning(f"Failed to send user referral reward notifications: {str(e)}")
