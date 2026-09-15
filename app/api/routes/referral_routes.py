from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.referral_schema import AdminReferralCodeCreate, AdminReferralCodeUpdate, AdminReferralCodeOut
from app.crud.referral_crud import (
    create_admin_referral_code, get_admin_referral_codes, 
    get_admin_referral_code_by_id, update_admin_referral_code, 
    delete_admin_referral_code, get_admin_referral_code_by_code
)

router = APIRouter(prefix="/admin/referrals", tags=["admin-referrals"])

@router.post("/", response_model=AdminReferralCodeOut)
@router.post("/campaign", response_model=AdminReferralCodeOut)
def create_referral(referral: AdminReferralCodeCreate, db: Session = Depends(get_db)):
    try:
        return create_admin_referral_code(db, referral)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[AdminReferralCodeOut])
def list_referrals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_admin_referral_codes(db, skip=skip, limit=limit)

@router.get("/{referral_id}", response_model=AdminReferralCodeOut)
def get_referral(referral_id: int, db: Session = Depends(get_db)):
    db_referral = get_admin_referral_code_by_id(db, referral_id)
    if not db_referral:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return db_referral

@router.put("/{referral_id}", response_model=AdminReferralCodeOut)
def update_referral(referral_id: int, referral_update: AdminReferralCodeUpdate, db: Session = Depends(get_db)):
    try:
        db_referral = update_admin_referral_code(db, referral_id, referral_update)
        if not db_referral:
            raise HTTPException(status_code=404, detail="Referral code not found")
        return db_referral
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{referral_id}")
def delete_referral(referral_id: int, db: Session = Depends(get_db)):
    success = delete_admin_referral_code(db, referral_id)
    if not success:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return {"message": "Referral code deleted successfully"}


# =================== VENDOR REFERRAL ADMIN CONTROLS ===================

from pydantic import BaseModel
from typing import Optional
from app.models.vendor_referral_model import VendorReferral, ReferralStatus
from app.models.vendor_model import Vendor
from app.models.app_config_model import AppConfig

class RewardConfigUpdate(BaseModel):
    referrer_reward_amount: float
    referred_vendor_reward_amount: float

@router.get("/vendor/list")
def list_vendor_referrals(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Admin endpoint to view and filter vendor referrals."""
    query = db.query(VendorReferral)
    if status:
        query = query.filter(VendorReferral.status == status)

    if search:
        search_filter = f"%{search}%"
        matching_vendor_ids = db.query(Vendor.id).filter(
            (Vendor.full_name.ilike(search_filter)) |
            (Vendor.email.ilike(search_filter)) |
            (Vendor.phone.ilike(search_filter)) |
            (Vendor.referral_code.ilike(search_filter))
        ).subquery()
        query = query.filter(
            (VendorReferral.referrer_vendor_id.in_(matching_vendor_ids)) |
            (VendorReferral.referred_vendor_id.in_(matching_vendor_ids)) |
            (VendorReferral.referral_code.ilike(search_filter))
        )

    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(VendorReferral.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for r in results:
        referrer = db.query(Vendor).filter(Vendor.id == r.referrer_vendor_id).first()
        referred = db.query(Vendor).filter(Vendor.id == r.referred_vendor_id).first()
        items.append({
            "id": r.id,
            "referral_code": r.referral_code,
            "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
            "referrer_vendor_id": r.referrer_vendor_id,
            "referrer_name": referrer.full_name if referrer else "Unknown",
            "referrer_phone": referrer.phone if referrer else "",
            "referred_vendor_id": r.referred_vendor_id,
            "referred_name": referred.full_name if referred else "Unknown",
            "referred_phone": referred.phone if referred else "",
            "referrer_reward_amount": r.referrer_reward_amount,
            "referred_vendor_reward_amount": r.referred_vendor_reward_amount,
            "qualified_booking_id": r.qualified_booking_id,
            "rewarded_at": r.rewarded_at.isoformat() if r.rewarded_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    import math
    return {
        "referrals": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if total > 0 else 1
    }


from app.schemas.referral_config_schema import ReferralConfigOut, ReferralConfigUpdate
from app.crud.referral_config_crud import get_referral_config, update_referral_config

@router.get("/config", response_model=ReferralConfigOut)
@router.get("/reward-config")
def get_referral_reward_config_endpoint(db: Session = Depends(get_db)):
    """Get full configured referral reward settings from ReferralConfig table."""
    return get_referral_config(db)

@router.put("/config", response_model=ReferralConfigOut)
@router.put("/reward-config")
def update_referral_reward_config_endpoint(
    payload: ReferralConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update full referral reward settings in ReferralConfig table."""
    return update_referral_config(db, payload)


@router.put("/vendor/{referral_id}/cancel")
def cancel_vendor_referral(
    referral_id: int,
    db: Session = Depends(get_db)
):
    """Admin endpoint to cancel/invalidate a referral."""
    referral = db.query(VendorReferral).filter(VendorReferral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    referral.status = ReferralStatus.CANCELLED
    db.commit()
    return {"success": True, "message": f"Referral #{referral_id} cancelled"}

