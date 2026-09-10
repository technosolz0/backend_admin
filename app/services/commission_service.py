import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vendor_earnings_model import VendorEarnings
from app.models.commission_tier_model import CommissionTier
from app.models.booking_model import Booking, BookingStatus

logger = logging.getLogger(__name__)

# ==================== DEFAULT COMMISSION TIERS ====================
# Default: standard 10%, reduced to 7% after 5 to 10 bookings in a day, and 5% after more than 10 bookings in a day
DEFAULT_COMMISSION_TIER_STANDARD = 10.0      # 1 to 4 bookings (10%)
DEFAULT_COMMISSION_TIER_5_TO_10 = 7.0        # 5 to 10 bookings (7%)
DEFAULT_COMMISSION_TIER_ABOVE_10 = 5.0       # > 10 bookings (5%)

DEFAULT_COMMISSION_TIERS = [
    {
        "tier_name": "Standard Tier",
        "min_bookings": 1,
        "max_bookings": 4,
        "commission_percentage": DEFAULT_COMMISSION_TIER_STANDARD,
        "is_active": True
    },
    {
        "tier_name": "Reduced Tier (5 - 10 Bookings)",
        "min_bookings": 5,
        "max_bookings": 10,
        "commission_percentage": DEFAULT_COMMISSION_TIER_5_TO_10,
        "is_active": True
    },
    {
        "tier_name": "Super Partner Tier (> 10 Bookings)",
        "min_bookings": 11,
        "max_bookings": None,
        "commission_percentage": DEFAULT_COMMISSION_TIER_ABOVE_10,
        "is_active": True
    }
]

def seed_default_commission_tiers(db: Session) -> List[CommissionTier]:
    """Seed the default commission tiers into the database if not present."""
    created = []
    for t in DEFAULT_COMMISSION_TIERS:
        tier = CommissionTier(
            tier_name=t["tier_name"],
            min_bookings=t["min_bookings"],
            max_bookings=t["max_bookings"],
            commission_percentage=t["commission_percentage"],
            is_active=t["is_active"]
        )
        db.add(tier)
        created.append(tier)
    db.commit()
    for tier in created:
        db.refresh(tier)
    logger.info("Seeded default daily commission tiers into database.")
    return created

def reset_commission_tiers_to_default(db: Session) -> List[CommissionTier]:
    """Admin feature: Reset all commission tiers back to the default configuration."""
    db.query(CommissionTier).delete()
    db.commit()
    return seed_default_commission_tiers(db)

def get_active_commission_tiers(db: Optional[Session] = None) -> List[Any]:
    """
    Get all active commission tiers ordered by min_bookings ascending.
    If database is available and empty, seeds default tiers.
    """
    if db:
        tiers = db.query(CommissionTier).filter(
            CommissionTier.is_active == True
        ).order_by(CommissionTier.min_bookings.asc()).all()

        if not tiers:
            # Check if any tiers exist at all
            total_count = db.query(CommissionTier).count()
            if total_count == 0:
                tiers = seed_default_commission_tiers(db)
        if tiers:
            return tiers

    # Fallback to default dictionary definitions
    return DEFAULT_COMMISSION_TIERS

def calculate_daily_commission_tier(
    daily_booking_ordinal: int,
    db: Optional[Session] = None
) -> Tuple[float, str]:
    """
    Determine commission percentage and tier name for a booking based on its ordinal number today.
    Uses database tiers if available, otherwise falls back to defaults.
    """
    active_tiers = get_active_commission_tiers(db)

    for tier in active_tiers:
        min_b = getattr(tier, "min_bookings", tier.get("min_bookings") if isinstance(tier, dict) else 1)
        max_b = getattr(tier, "max_bookings", tier.get("max_bookings") if isinstance(tier, dict) else None)
        pct = float(getattr(tier, "commission_percentage", tier.get("commission_percentage") if isinstance(tier, dict) else 10.0))
        name = getattr(tier, "tier_name", tier.get("tier_name") if isinstance(tier, dict) else "Standard Tier")

        if min_b <= daily_booking_ordinal and (max_b is None or daily_booking_ordinal <= max_b):
            return pct, name

    # Hardcoded Fallbacks if no tier matched
    if daily_booking_ordinal <= 4:
        return DEFAULT_COMMISSION_TIER_STANDARD, "Standard Tier (10%)"
    elif 5 <= daily_booking_ordinal <= 10:
        return DEFAULT_COMMISSION_TIER_5_TO_10, "Reduced Tier (7%)"
    else:
        return DEFAULT_COMMISSION_TIER_ABOVE_10, "Super Partner Tier (5%)"

def get_vendor_daily_completed_bookings_count(
    db: Session,
    vendor_id: int,
    target_date: Optional[date] = None,
    exclude_booking_id: Optional[int] = None
) -> int:
    """
    Get the count of bookings completed by this vendor today (or on target_date).
    Counts completed VendorEarnings for the day.
    """
    if target_date is None:
        target_date = datetime.utcnow().date()

    earnings_query = db.query(VendorEarnings.booking_id).filter(
        VendorEarnings.vendor_id == vendor_id,
        func.date(VendorEarnings.earned_at) == target_date
    )
    if exclude_booking_id:
        earnings_query = earnings_query.filter(VendorEarnings.booking_id != exclude_booking_id)

    count = earnings_query.distinct().count()
    return count

def get_vendor_current_commission_tier_status(
    db: Session,
    vendor_id: int,
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Get the current tier status and progress for a vendor.
    """
    if target_date is None:
        target_date = datetime.utcnow().date()

    completed_today = get_vendor_daily_completed_bookings_count(db, vendor_id, target_date=target_date)
    next_booking_ordinal = completed_today + 1
    current_pct, current_tier_name = calculate_daily_commission_tier(next_booking_ordinal, db=db)

    active_tiers = get_active_commission_tiers(db)
    tiers_info = []
    next_tier_desc = "You have unlocked the lowest commission tier for today!"
    bookings_to_next = 0

    # Format tiers for output and find next tier target
    found_next = False
    for t in active_tiers:
        min_b = getattr(t, "min_bookings", t.get("min_bookings") if isinstance(t, dict) else 1)
        max_b = getattr(t, "max_bookings", t.get("max_bookings") if isinstance(t, dict) else None)
        pct = float(getattr(t, "commission_percentage", t.get("commission_percentage") if isinstance(t, dict) else 10.0))
        name = getattr(t, "tier_name", t.get("tier_name") if isinstance(t, dict) else "")

        label = f"{min_b} - {max_b} bookings/day: {pct}%" if max_b else f"> {min_b - 1} bookings/day: {pct}%"
        tiers_info.append({
            "id": getattr(t, "id", None),
            "tier_name": name,
            "min_bookings": min_b,
            "max_bookings": max_b,
            "commission_percentage": pct,
            "label": label
        })

        if not found_next and min_b > next_booking_ordinal:
            bookings_to_next = min_b - (next_booking_ordinal - 1)
            next_tier_desc = f"{bookings_to_next} more booking(s) today to unlock {pct}% commission ({name})"
            found_next = True

    return {
        "vendor_id": vendor_id,
        "date": target_date.isoformat(),
        "today_completed_bookings": completed_today,
        "next_booking_commission_percentage": current_pct,
        "current_tier_name": current_tier_name,
        "bookings_to_next_tier": bookings_to_next,
        "next_tier_message": next_tier_desc,
        "tiers": tiers_info
    }

def record_vendor_booking_earnings(
    db: Session,
    booking_id: int,
    vendor_id: int,
    total_paid: float,
    custom_commission_percentage: Optional[float] = None
) -> VendorEarnings:
    """
    Idempotently calculates dynamic daily commission and records VendorEarnings.
    """
    # 1. Idempotency check: don't create duplicate earnings
    existing = db.query(VendorEarnings).filter(VendorEarnings.booking_id == booking_id).first()
    if existing:
        logger.info(f"VendorEarnings already exists for booking #{booking_id}. Returning existing.")
        return existing

    # 2. Determine commission percentage
    if custom_commission_percentage is not None:
        comm_pct = float(custom_commission_percentage)
        tier_name = "Custom"
    else:
        today_completed = get_vendor_daily_completed_bookings_count(db, vendor_id)
        current_ordinal = today_completed + 1
        comm_pct, tier_name = calculate_daily_commission_tier(current_ordinal, db=db)

    # 3. Calculate commission and final net earning
    comm_amount = round(total_paid * (comm_pct / 100.0), 2)
    final_amount = round(total_paid - comm_amount, 2)

    earning = VendorEarnings(
        booking_id=booking_id,
        vendor_id=vendor_id,
        total_paid=total_paid,
        commission_percentage=comm_pct,
        commission_amount=comm_amount,
        final_amount=final_amount,
        earned_at=datetime.utcnow()
    )
    db.add(earning)
    db.commit()
    db.refresh(earning)
    logger.info(
        f"Recorded Vendor #{vendor_id} earnings for booking #{booking_id}: "
        f"Paid=₹{total_paid}, Commission={comm_pct}% ({tier_name}), Amount=₹{comm_amount}, Net=₹{final_amount}"
    )
    return earning
