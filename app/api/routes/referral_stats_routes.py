from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.security import get_db, get_current_vendor
from app.models.service_provider_model import ServiceProvider
from app.models.vendor_earnings_model import VendorEarnings

router = APIRouter(prefix="/vendor/referral", tags=["vendor-referral"])

@router.get("/stats")
def get_referral_stats(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    try:
        vendor_id = current_vendor.id

        # Total referred (started registration)
        total_referred = db.query(ServiceProvider).filter(
            ServiceProvider.referred_by_id == vendor_id
        ).count()

        # Total registered (OTP verified / step > 0)
        total_registered = db.query(ServiceProvider).filter(
            ServiceProvider.referred_by_id == vendor_id,
            ServiceProvider.otp_verified == True
        ).count()

        # Total referral earnings — use final_amount from bookings done by referred vendors
        # (VendorEarnings does not have a dedicated referral_incentive column yet)
        try:
            total_earnings = db.query(func.sum(VendorEarnings.final_amount)).filter(
                VendorEarnings.vendor_id.in_(
                    db.query(ServiceProvider.id).filter(
                        ServiceProvider.referred_by_id == vendor_id
                    )
                )
            ).scalar() or 0.0
        except Exception:
            total_earnings = 0.0

        return {
            "total_referred": total_referred,
            "total_registered": total_registered,
            "total_earnings": float(total_earnings),
            "referral_code": current_vendor.referral_code
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in get_referral_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch referral stats: {str(e)}")
