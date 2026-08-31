from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_db, get_current_vendor
from app.models.vendor_model import Vendor
from app.models.vendor_referral_model import VendorReferral, ReferralStatus
from app.models.wallet_model import Wallet, WalletTransaction
from app.services.referral_service import get_referral_reward_configs

router = APIRouter(prefix="/vendor/referral", tags=["Vendor Referral"])
wallet_router = APIRouter(prefix="/vendor/wallet", tags=["Vendor Wallet"])

# Schemas
class ValidateReferralRequest(BaseModel):
    referral_code: str

class ValidateReferralResponse(BaseModel):
    valid: bool
    referrer_name: Optional[str] = None
    message: str

class ReferralItemOut(BaseModel):
    id: int
    referred_vendor_name: str
    phone_masked: str
    status: str
    reward_earned: float
    created_at: datetime

    class Config:
        from_attributes = True

class ReferralDashboardOut(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    registered_count: int
    pending_count: int
    successful_count: int
    total_rewards_earned: float
    referrals: List[ReferralItemOut]

class WalletTransactionOut(BaseModel):
    id: int
    amount: float
    transaction_type: str
    description: Optional[str] = None
    status: str
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VendorWalletOut(BaseModel):
    wallet_id: int
    vendor_id: int
    balance: float
    transactions: List[WalletTransactionOut]


def mask_phone(phone: Optional[str]) -> str:
    """Mask phone number for privacy e.g. 98****1234"""
    if not phone or len(phone) < 6:
        return "Hidden"
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]

def mask_name(name: Optional[str]) -> str:
    """Mask full name for privacy e.g. Rahul S."""
    if not name:
        return "Vendor"
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][0]}."
    return parts[0]


@router.get("/me", response_model=ReferralDashboardOut)
@router.get("/stats", response_model=ReferralDashboardOut)
def get_vendor_referral_dashboard(
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    """Get current vendor's referral code, share link, statistics, and history."""
    vendor_id = current_vendor.id

    # 1. Referral records where current vendor is referrer
    referrals_query = db.query(VendorReferral).filter(
        VendorReferral.referrer_vendor_id == vendor_id
    ).order_by(VendorReferral.created_at.desc()).all()

    total_referrals = len(referrals_query)
    registered_count = sum(1 for r in referrals_query if r.status == ReferralStatus.REGISTERED)
    pending_count = sum(1 for r in referrals_query if r.status == ReferralStatus.PENDING)
    successful_count = sum(1 for r in referrals_query if r.status in [ReferralStatus.QUALIFIED, ReferralStatus.REWARDED])

    total_rewards_earned = sum(r.referrer_reward_amount for r in referrals_query if r.status == ReferralStatus.REWARDED)

    # 2. Build list items
    referrals_list = []
    for r in referrals_query:
        referred_vendor = db.query(Vendor).filter(Vendor.id == r.referred_vendor_id).first()
        name_display = mask_name(referred_vendor.full_name) if referred_vendor else "Referred Vendor"
        phone_display = mask_phone(referred_vendor.phone) if referred_vendor else "Hidden"

        earned = r.referrer_reward_amount if r.status == ReferralStatus.REWARDED else 0.0

        referrals_list.append(ReferralItemOut(
            id=r.id,
            referred_vendor_name=name_display,
            phone_masked=phone_display,
            status=r.status.value if hasattr(r.status, 'value') else str(r.status),
            reward_earned=earned,
            created_at=r.created_at
        ))

    domain = "https://serwex.in"
    referral_code = current_vendor.referral_code or f"SERWEX-{current_vendor.id}"
    referral_link = f"{domain}/partner/register?ref={referral_code}"

    return ReferralDashboardOut(
        referral_code=referral_code,
        referral_link=referral_link,
        total_referrals=total_referrals,
        registered_count=registered_count,
        pending_count=pending_count,
        successful_count=successful_count,
        total_rewards_earned=float(total_rewards_earned),
        referrals=referrals_list
    )


@router.post("/validate", response_model=ValidateReferralResponse)
def validate_referral_code(
    payload: ValidateReferralRequest,
    db: Session = Depends(get_db)
):
    """Validate a referral code before registration."""
    code_clean = payload.referral_code.strip().upper() if payload.referral_code else ""
    if not code_clean:
        return ValidateReferralResponse(valid=False, message="Referral code cannot be empty")

    referrer = db.query(Vendor).filter(func.upper(Vendor.referral_code) == code_clean).first()
    if not referrer:
        return ValidateReferralResponse(valid=False, message="Invalid referral code")

    if referrer.status in ['rejected', 'inactive']:
        return ValidateReferralResponse(valid=False, message="Referral code belongs to an inactive account")

    return ValidateReferralResponse(
        valid=True,
        referrer_name=mask_name(referrer.full_name),
        message=f"Valid referral code from {mask_name(referrer.full_name)}"
    )


@wallet_router.get("/me", response_model=VendorWalletOut)
def get_vendor_wallet_details(
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    """Get current vendor's wallet balance and transactions."""
    wallet = db.query(Wallet).filter(Wallet.vendor_id == current_vendor.id).first()
    if not wallet:
        wallet = Wallet(vendor_id=current_vendor.id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    txs = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.created_at.desc()).all()

    tx_out = [
        WalletTransactionOut(
            id=t.id,
            amount=t.amount,
            transaction_type=t.transaction_type,
            description=t.description,
            status=t.status,
            reference_id=t.reference_id,
            created_at=t.created_at
        )
        for t in txs
    ]

    return VendorWalletOut(
        wallet_id=wallet.id,
        vendor_id=current_vendor.id,
        balance=wallet.balance,
        transactions=tx_out
    )
