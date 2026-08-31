import logging
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vendor_model import Vendor
from app.models.vendor_referral_model import VendorReferral, ReferralStatus
from app.models.booking_model import Booking, BookingStatus
from app.models.wallet_model import Wallet, WalletTransaction
from app.models.app_config_model import AppConfig
from app.utils.fcm import send_notification, NotificationType

logger = logging.getLogger(__name__)

DEFAULT_REFERRER_REWARD = 100.0
DEFAULT_REFERRED_REWARD = 50.0

def get_referral_reward_configs(db: Session) -> tuple[float, float]:
    """Get dynamic referral reward configuration from AppConfig table or fallback defaults."""
    config = db.query(AppConfig).first()
    if config:
        referrer_amount = getattr(config, 'referrer_reward_amount', DEFAULT_REFERRER_REWARD)
        referred_amount = getattr(config, 'referred_vendor_reward_amount', DEFAULT_REFERRED_REWARD)
        return float(referrer_amount), float(referred_amount)
    return DEFAULT_REFERRER_REWARD, DEFAULT_REFERRED_REWARD

def get_or_create_vendor_wallet(db: Session, vendor_id: int) -> Wallet:
    """Ensure a wallet exists for the given vendor."""
    wallet = db.query(Wallet).filter(Wallet.vendor_id == vendor_id).first()
    if not wallet:
        wallet = Wallet(vendor_id=vendor_id, balance=0.0)
        db.add(wallet)
        db.flush()
    return wallet

def process_vendor_referral_registration(db: Session, new_vendor: Vendor, input_code: str) -> bool:
    """
    Validates referral code and creates permanent referral relationship.
    Returns True if referral association created successfully, False otherwise.
    """
    if not input_code or not input_code.strip():
        return False
        
    code_clean = input_code.strip().upper()
    
    # 1. Look up referrer vendor (case-insensitive)
    referrer = db.query(Vendor).filter(func.upper(Vendor.referral_code) == code_clean).first()
    if not referrer:
        logger.warning(f"Referral registration failed: code '{input_code}' not found.")
        return False

    # 2. Anti-Self Referral Check
    if referrer.id == new_vendor.id:
        logger.warning(f"Self-referral attempt blocked for vendor ID {new_vendor.id}.")
        return False

    # 3. Check if new vendor already has a referrer (Single referrer rule)
    existing_referral = db.query(VendorReferral).filter(
        VendorReferral.referred_vendor_id == new_vendor.id
    ).first()
    if existing_referral:
        logger.warning(f"Vendor {new_vendor.id} already associated with referrer {existing_referral.referrer_vendor_id}.")
        return False

    # 4. Associate referral on Vendor model
    new_vendor.referred_by_id = referrer.id
    new_vendor.applied_referral_code = referrer.referral_code
    new_vendor.referral_type = 'vendor'

    referrer_amount, referred_amount = get_referral_reward_configs(db)

    # 5. Create VendorReferral record in status REGISTERED
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
    logger.info(f"Successfully associated Vendor #{new_vendor.id} with Referrer #{referrer.id} via code '{code_clean}'.")
    return True

def process_first_booking_referral_reward(db: Session, booking: Booking) -> bool:
    """
    Atomically processes referral rewards upon successful booking completion.
    Only triggers on the vendor's VERY FIRST COMPLETED booking.
    """
    if not booking or not booking.serviceprovider_id:
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
        # Mark Qualified
        referral.status = ReferralStatus.QUALIFIED
        referral.qualified_booking_id = booking.id
        db.flush()

        # Fetch latest amounts snapshot
        referrer_amount = referral.referrer_reward_amount or DEFAULT_REFERRER_REWARD
        referred_amount = referral.referred_vendor_reward_amount or DEFAULT_REFERRED_REWARD

        # Referrer Wallet Credit
        referrer_wallet = get_or_create_vendor_wallet(db, referral.referrer_vendor_id)
        referrer_wallet.balance += referrer_amount

        referrer_tx_ref = f"REF_BONUS_REFERRER_{referral.id}"
        # Check idempotency constraint for transaction
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

        # Referred Vendor Wallet Credit
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

def _send_referral_notifications(db: Session, referral: VendorReferral):
    """Send FCM notifications to referrer and referred vendor upon reward crediting."""
    try:
        referrer = db.query(Vendor).filter(Vendor.id == referral.referrer_vendor_id).first()
        referred = db.query(Vendor).filter(Vendor.id == referral.referred_vendor_id).first()

        if referrer:
            token = referrer.new_fcm_token or referrer.old_fcm_token
            msg = f"🎉 Referral Reward Earned! ₹{int(referral.referrer_reward_amount)} bonus has been added to your wallet."
            send_notification(
                recipient=referrer.email,
                notification_type=NotificationType.vendor_welcome, # reuse or generic notif
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
        logger.warning(f"Failed to send referral reward notifications: {str(e)}")
