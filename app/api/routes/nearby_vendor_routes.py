# app/api/routes/nearby_vendor_routes.py
# Implements: Nearby Vendor Detection, Live Location Update, Vendor Location Tracking
# Compatible with the existing Serwex architecture.

import math
import datetime
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import get_current_vendor, get_current_user, get_current_identity, get_db
from app.models.service_provider_model import ServiceProvider
from app.models.booking_model import Booking, BookingStatus
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Nearby & Location"])


# ─────────────────────────────────────────────
# UTILS: Haversine distance calculation
# ─────────────────────────────────────────────

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in kilometers between two GPS coordinates (Haversine formula)."""
    if any(v is None for v in [lat1, lng1, lat2, lng2]):
        return float('inf')
    R = 6371.0  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class LocationUpdateRequest(BaseModel):
    lat: float
    lng: float
    fcm_token: Optional[str] = None


class NearbyVendorItem(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    profile_pic: Optional[str] = None
    category_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    work_status: Optional[str] = None
    admin_status: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    pincode: Optional[str] = None
    charges: List[dict] = []


class VendorLiveLocation(BaseModel):
    vendor_id: int
    latitude: Optional[float]
    longitude: Optional[float]
    work_status: Optional[str]
    last_updated: Optional[str]


# ─────────────────────────────────────────────
# 1. POST /vendor/update-location
#    Vendor app calls this every 5-10 seconds when online
# ─────────────────────────────────────────────

@router.post("/vendor/update-location", response_model=dict)
def update_vendor_location(
    body: LocationUpdateRequest,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Update vendor's live GPS location.
    Called by serwex_partner app every 5-10 seconds while vendor is online (work_on).
    """
    try:
        current_vendor.latitude = body.lat
        current_vendor.longitude = body.lng
        current_vendor.last_device_update = datetime.datetime.utcnow()

        if body.fcm_token:
            current_vendor.new_fcm_token = body.fcm_token

        db.commit()
        db.refresh(current_vendor)

        logger.info(
            f"📍 Vendor {current_vendor.id} location updated: ({body.lat}, {body.lng})"
        )
        return {
            "success": True,
            "message": "Location updated",
            "vendor_id": current_vendor.id,
            "latitude": current_vendor.latitude,
            "longitude": current_vendor.longitude,
            "last_updated": current_vendor.last_device_update.isoformat()
            if current_vendor.last_device_update else None,
        }
    except Exception as e:
        logger.error(f"Error updating vendor location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )


# ─────────────────────────────────────────────
# 2. GET /vendors/nearby
#    User app calls this to get nearby vendors
# ─────────────────────────────────────────────

@router.get("/vendors/nearby", response_model=dict)
def get_nearby_vendors(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    radius_km: float = Query(5.0, description="Search radius in km (default 5)"),
    user_pincode: Optional[str] = Query(None, description="Fallback pincode filter"),
    db: Session = Depends(get_db),
):
    """
    Returns vendors within `radius_km` of the user's location.
    Filtered by: online status, approved status, and optionally category/subcategory.
    Sorted by nearest distance first.
    Falls back to pincode match if no GPS-close vendors found.
    """
    try:
        # Build base vendor query — only online approved vendors
        query = db.query(ServiceProvider).filter(
            ServiceProvider.status == 'approved',
            ServiceProvider.admin_status == 'active',
            ServiceProvider.work_status == 'work_on',
        )

        if category_id:
            query = query.filter(ServiceProvider.category_id == category_id)

        all_vendors = query.all()

        nearby: list = []
        for vendor in all_vendors:
            # Build charge list (optionally filtered by subcategory)
            charges = []
            for charge in vendor.subcategory_charges:
                if subcategory_id is None or charge.subcategory_id == subcategory_id:
                    charges.append({
                        "subcategory_id": charge.subcategory_id,
                        "subcategory_name": charge.subcategory.name if charge.subcategory else "N/A",
                        "price": charge.service_charge,
                        "description": getattr(charge, 'description', ''),
                    })

            # Skip vendor if subcategory filter given and vendor has no matching charges
            if subcategory_id and not charges:
                continue

            # Calculate distance
            distance = haversine_distance(
                lat, lng,
                float(vendor.latitude) if vendor.latitude is not None else None,
                float(vendor.longitude) if vendor.longitude is not None else None,
            )

            is_nearby = distance <= radius_km
            is_same_pincode = bool(user_pincode and vendor.pincode == user_pincode)

            if is_nearby or is_same_pincode:
                nearby.append({
                    "id": vendor.id,
                    "full_name": vendor.full_name or "",
                    "email": vendor.email or "",
                    "phone": vendor.phone or "",
                    "profile_pic": vendor.profile_pic,
                    "category_id": vendor.category_id,
                    "pincode": vendor.pincode,
                    "latitude": vendor.latitude,
                    "longitude": vendor.longitude,
                    "distance_km": round(distance, 2) if distance != float('inf') else None,
                    "work_status": vendor.work_status,
                    "admin_status": vendor.admin_status,
                    "rating": getattr(vendor, "rating", 0.0),
                    "total_reviews": getattr(vendor, "total_reviews", 0),
                    "charges": charges,
                })

        # Sort by distance (nearest first), None distances at end
        nearby.sort(key=lambda v: (v["distance_km"] is None, v["distance_km"] or float('inf')))

        logger.info(
            f"🔍 Nearby vendor query (lat={lat}, lng={lng}, r={radius_km}km) → {len(nearby)} vendors found"
        )
        return {
            "success": True,
            "user_lat": lat,
            "user_lng": lng,
            "radius_km": radius_km,
            "total": len(nearby),
            "vendors": nearby,
        }

    except Exception as e:
        logger.error(f"Error in nearby vendor search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch nearby vendors"
        )


# ─────────────────────────────────────────────
# 3. GET /bookings/{booking_id}/vendor-location
#    User app polls this to track vendor live position
# ─────────────────────────────────────────────

@router.get("/bookings/{booking_id}/vendor-location", response_model=VendorLiveLocation)
def get_vendor_live_location(
    booking_id: int,
    db: Session = Depends(get_db),
    identity=Depends(get_current_identity),
):
    """
    Returns vendor's current GPS location for tracking on the user's map.
    Only accessible by the user or vendor associated with this booking.
    Called by serwex app every 5 seconds to animate vendor marker.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Authorization: the user who booked or the assigned vendor
    is_authorized = False
    if isinstance(identity, User) and identity.id == booking.user_id:
        is_authorized = True
    elif isinstance(identity, ServiceProvider) and identity.id == booking.serviceprovider_id:
        is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Only return vendor location for active bookings
    if booking.status not in [BookingStatus.accepted]:
        raise HTTPException(
            status_code=400,
            detail=f"Vendor location not available for booking status: {booking.status}"
        )

    vendor = db.query(ServiceProvider).filter(
        ServiceProvider.id == booking.serviceprovider_id
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return VendorLiveLocation(
        vendor_id=vendor.id,
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        work_status=vendor.work_status,
        last_updated=vendor.last_device_update.isoformat()
        if vendor.last_device_update else None,
    )


# ─────────────────────────────────────────────
# 4. PATCH /bookings/{booking_id}/accept
#    Convenience wrapper: vendor accepts a booking
# ─────────────────────────────────────────────

@router.patch("/bookings/{booking_id}/accept", response_model=dict)
def accept_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    vendor: ServiceProvider = Depends(get_current_vendor),
):
    """
    Vendor accepts a pending booking.
    After acceptance, the user can start polling vendor-location.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Can only accept pending bookings. Current: {booking.status}"
        )

    booking.status = BookingStatus.accepted
    db.commit()
    db.refresh(booking)

    logger.info(f"✅ Booking {booking_id} accepted by vendor {vendor.id}")

    # Return booking details with user's booking address coordinates for navigation
    return {
        "success": True,
        "message": "Booking accepted",
        "booking_id": booking.id,
        "status": booking.status,
        "user_address": booking.address,
        "user_lat": booking.booking_latitude,
        "user_lng": booking.booking_longitude,
        "vendor_lat": vendor.latitude,
        "vendor_lng": vendor.longitude,
    }


# ─────────────────────────────────────────────
# 5. PATCH /bookings/{booking_id}/reject
#    Convenience wrapper: vendor rejects a booking
# ─────────────────────────────────────────────

@router.patch("/bookings/{booking_id}/reject", response_model=dict)
def reject_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Vendor rejects a pending booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject pending bookings. Current: {booking.status}"
        )

    booking.status = BookingStatus.rejected
    db.commit()
    db.refresh(booking)

    logger.info(f"❌ Booking {booking_id} rejected by vendor {vendor.id}")
    return {
        "success": True,
        "message": "Booking rejected",
        "booking_id": booking.id,
        "status": booking.status,
    }


# ─────────────────────────────────────────────
# 6. GET /vendor/online-status
#    Toggle vendor online/offline (go_online / go_offline)
# ─────────────────────────────────────────────

@router.post("/vendor/go-online", response_model=dict)
def vendor_go_online(
    lat: Optional[float] = Body(None),
    lng: Optional[float] = Body(None),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Mark vendor as online (work_on) and set initial location."""
    current_vendor.work_status = "work_on"
    if lat is not None:
        current_vendor.latitude = lat
    if lng is not None:
        current_vendor.longitude = lng
    current_vendor.last_device_update = datetime.datetime.utcnow()
    db.commit()
    logger.info(f"🟢 Vendor {current_vendor.id} went ONLINE")
    return {"success": True, "work_status": "work_on", "message": "You are now online"}


@router.post("/vendor/go-offline", response_model=dict)
def vendor_go_offline(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor),
):
    """Mark vendor as offline (work_off). Stops appearing in nearby searches."""
    current_vendor.work_status = "work_off"
    db.commit()
    logger.info(f"🔴 Vendor {current_vendor.id} went OFFLINE")
    return {"success": True, "work_status": "work_off", "message": "You are now offline"}
