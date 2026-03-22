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
    vendor_id = current_vendor.id
    # Total referred (started registration)
    total_referred = db.query(ServiceProvider).filter(ServiceProvider.referred_by_id == vendor_id).count()
    
    # Total registered (OTP verified / step > 0)
    total_registered = db.query(ServiceProvider).filter(
        ServiceProvider.referred_by_id == vendor_id,
        ServiceProvider.otp_verified == True
    ).count()
    
    # Total referral earnings
    total_earnings = db.query(func.sum(VendorEarnings.referral_incentive)).filter(
        VendorEarnings.referrer_id == vendor_id
    ).scalar() or 0.0
    
    return {
        "total_referred": total_referred,
        "total_registered": total_registered,
        "total_earnings": total_earnings,
        "referral_code": current_vendor.referral_code
    }
