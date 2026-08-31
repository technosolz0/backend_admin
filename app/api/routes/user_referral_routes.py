import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.security import get_db, get_current_user
from app.models.user import User
from app.models.vendor_model import Vendor
from app.models.user_referral_model import UserReferral, ReferralStatus
from app.schemas.user_schema import (
    UserReferralStatsResponse, UserReferralItem,
    UserReferralValidateRequest, UserReferralValidateResponse
)
from app.services.referral_service import (
    generate_unique_user_referral_code, get_user_referral_reward_configs
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/referral", tags=["User Referrals"])

@router.get("/stats", response_model=UserReferralStatsResponse)
def get_user_referral_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get referral stats, referral code, share link, reward balance, and history for customer user.
    """
    try:
        user_id = current_user.id
        referral_code = generate_unique_user_referral_code(db, current_user)
        
        # Share link base URL
        referral_link = f"https://users.serwex.in/register?ref={referral_code}"

        # Fetch referral records sent by this user
        referral_records = db.query(UserReferral).filter(
            UserReferral.referrer_user_id == user_id
        ).order_by(UserReferral.created_at.desc()).all()

        total_referrals = len(referral_records)
        registered_count = sum(1 for r in referral_records if r.status == ReferralStatus.REGISTERED)
        successful_count = sum(1 for r in referral_records if r.status in [ReferralStatus.QUALIFIED, ReferralStatus.REWARDED])
        pending_count = sum(1 for r in referral_records if r.status in [ReferralStatus.PENDING, ReferralStatus.REGISTERED])
        
        total_rewards = sum(
            float(r.referrer_reward_amount or 0.0) 
            for r in referral_records 
            if r.status == ReferralStatus.REWARDED
        )

        items = []
        for r in referral_records:
            referred_user = db.query(User).filter(User.id == r.referred_user_id).first()
            name = referred_user.name if referred_user else "Referred Customer"
            items.append(UserReferralItem(
                id=r.id,
                referred_user_name=name,
                status=r.status.value if hasattr(r.status, 'value') else str(r.status),
                created_at=r.created_at,
                qualification_date=r.rewarded_at,
                reward_amount=float(r.referrer_reward_amount or 0.0)
            ))

        return UserReferralStatsResponse(
            referral_code=referral_code,
            referral_link=referral_link,
            total_referrals=total_referrals,
            registered_count=registered_count,
            successful_count=successful_count,
            pending_count=pending_count,
            total_rewards=total_rewards,
            referrals=items
        )
    except Exception as e:
        logger.exception(f"Error fetching user referral stats for user #{current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch referral stats")


@router.post("/validate", response_model=UserReferralValidateResponse)
def validate_user_referral_code(
    payload: UserReferralValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate referral code entered during registration.
    """
    if not payload.referral_code or not payload.referral_code.strip():
        return UserReferralValidateResponse(
            valid=False,
            message="Referral code cannot be empty"
        )

    code_clean = payload.referral_code.strip().upper()

    # 1. Cross-type check: Reject Vendor referral codes
    vendor = db.query(Vendor).filter(func.upper(Vendor.referral_code) == code_clean).first()
    if vendor:
        return UserReferralValidateResponse(
            valid=False,
            message="This is a Partner referral code. Please enter a valid Customer referral code.",
            referral_type="vendor"
        )

    # 2. Look up User referral code
    referrer = db.query(User).filter(func.upper(User.referral_code) == code_clean).first()
    if not referrer:
        return UserReferralValidateResponse(
            valid=False,
            message="Invalid referral code. Please check and try again."
        )

    return UserReferralValidateResponse(
        valid=True,
        message="Valid referral code!",
        referral_type="user",
        referrer_name=referrer.name
    )
