import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_db
from app.models.commission_tier_model import CommissionTier
from app.schemas.commission_tier_schema import (
    CommissionTierCreate, CommissionTierUpdate, CommissionTierOut
)
from app.services.commission_service import (
    get_active_commission_tiers,
    reset_commission_tiers_to_default,
    seed_default_commission_tiers
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Commission Tiers Admin"])

@router.get("/admin/commission-tiers/", response_model=List[CommissionTierOut])
def list_commission_tiers(db: Session = Depends(get_db)):
    """Admin endpoint to list all daily commission tiers ordered by minimum bookings."""
    tiers = db.query(CommissionTier).order_by(CommissionTier.min_bookings.asc()).all()
    if not tiers:
        tiers = seed_default_commission_tiers(db)
    return tiers

@router.post("/admin/commission-tiers/", response_model=CommissionTierOut, status_code=status.HTTP_201_CREATED)
def create_commission_tier(
    tier_in: CommissionTierCreate,
    db: Session = Depends(get_db)
):
    """Admin endpoint to add a new dynamic daily commission tier."""
    if tier_in.commission_percentage < 0 or tier_in.commission_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commission percentage must be between 0% and 100%."
        )

    if tier_in.min_bookings < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum bookings must be at least 1."
        )

    if tier_in.max_bookings is not None and tier_in.max_bookings < tier_in.min_bookings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum bookings must be greater than or equal to minimum bookings."
        )

    new_tier = CommissionTier(
        tier_name=tier_in.tier_name.strip(),
        min_bookings=tier_in.min_bookings,
        max_bookings=tier_in.max_bookings,
        commission_percentage=tier_in.commission_percentage,
        is_active=tier_in.is_active
    )
    db.add(new_tier)
    db.commit()
    db.refresh(new_tier)
    logger.info(f"Created new commission tier #{new_tier.id}: '{new_tier.tier_name}' ({new_tier.commission_percentage}%)")
    return new_tier

@router.get("/admin/commission-tiers/{tier_id}", response_model=CommissionTierOut)
def get_commission_tier(tier_id: int, db: Session = Depends(get_db)):
    """Admin endpoint to get a single commission tier by ID."""
    tier = db.query(CommissionTier).filter(CommissionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commission tier not found.")
    return tier

@router.put("/admin/commission-tiers/{tier_id}", response_model=CommissionTierOut)
def update_commission_tier(
    tier_id: int,
    tier_update: CommissionTierUpdate,
    db: Session = Depends(get_db)
):
    """Admin endpoint to update an existing daily commission tier."""
    tier = db.query(CommissionTier).filter(CommissionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commission tier not found.")

    update_data = tier_update.model_dump(exclude_unset=True)

    if "commission_percentage" in update_data:
        pct = update_data["commission_percentage"]
        if pct < 0 or pct > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Commission percentage must be between 0% and 100%.")

    if "min_bookings" in update_data and update_data["min_bookings"] < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum bookings must be at least 1.")

    target_min = update_data.get("min_bookings", tier.min_bookings)
    target_max = update_data.get("max_bookings", tier.max_bookings)
    if target_max is not None and target_max < target_min:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum bookings cannot be less than minimum bookings.")

    for key, value in update_data.items():
        if key == "tier_name" and value:
            setattr(tier, key, value.strip())
        else:
            setattr(tier, key, value)

    db.commit()
    db.refresh(tier)
    logger.info(f"Updated commission tier #{tier.id}: '{tier.tier_name}' to {tier.commission_percentage}%")
    return tier

@router.delete("/admin/commission-tiers/{tier_id}")
def delete_commission_tier(tier_id: int, db: Session = Depends(get_db)):
    """Admin endpoint to delete a daily commission tier."""
    tier = db.query(CommissionTier).filter(CommissionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commission tier not found.")

    db.delete(tier)
    db.commit()
    logger.info(f"Deleted commission tier #{tier_id}")
    return {"success": True, "message": f"Commission tier #{tier_id} deleted successfully."}

@router.post("/admin/commission-tiers/reset-defaults", response_model=List[CommissionTierOut])
def reset_tiers_to_defaults(db: Session = Depends(get_db)):
    """Admin endpoint to reset all commission tiers to standard defaults (10%, 7%, 5%)."""
    return reset_commission_tiers_to_default(db)

@router.get("/commission-tiers/active")
def get_active_tiers_public(db: Session = Depends(get_db)):
    """Public / Vendor endpoint to fetch active daily commission tiers."""
    tiers = get_active_commission_tiers(db)
    result = []
    for t in tiers:
        min_b = getattr(t, "min_bookings", t.get("min_bookings") if isinstance(t, dict) else 1)
        max_b = getattr(t, "max_bookings", t.get("max_bookings") if isinstance(t, dict) else None)
        pct = float(getattr(t, "commission_percentage", t.get("commission_percentage") if isinstance(t, dict) else 10.0))
        name = getattr(t, "tier_name", t.get("tier_name") if isinstance(t, dict) else "")

        label = f"{min_b} - {max_b} bookings/day: {pct}%" if max_b else f"> {min_b - 1} bookings/day: {pct}%"
        result.append({
            "id": getattr(t, "id", None),
            "tier_name": name,
            "min_bookings": min_b,
            "max_bookings": max_b,
            "commission_percentage": pct,
            "label": label
        })
    return {"success": True, "tiers": result}
