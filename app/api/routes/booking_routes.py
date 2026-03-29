# app/api/routes/booking_routes.py
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from enum import Enum
import logging

from app.core.security import (
    get_db, 
    get_current_user, 
    get_current_vendor, 
    get_current_admin, 
    get_current_identity
)
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.schemas.payment_schema import PaymentCreate, PaymentOut
from app.crud import (
    booking_crud, 
    payment_crud, 
    category_crud as category, 
    subcategory_crud as subcategory
)
from app.models.booking_model import Booking, BookingStatus
from app.models.user import User
from app.models.service_provider_model import ServiceProvider as Vendor
from app.models.vendor_subcategory_charge import VendorSubcategoryCharge
from app.models.payment_model import Payment
from app.utils.fcm import send_notification

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Booking"])

class NotificationType(str, Enum):
    booking_created = "booking_created"
    booking_accepted = "booking_accepted"
    booking_cancelled = "booking_cancelled"
    booking_rejected = "booking_rejected"
    booking_completed = "booking_completed"
    otp_sent = "otp_sent"
    payment_created = "payment_created"

# --- HELPERS ---

def send_booking_notification(
    db: Session,
    booking: Booking,
    notification_type: NotificationType,
    recipient: str,
    recipient_id: int,
    fcm_token: Optional[str] = None,
    custom_message: Optional[str] = None
):
    """Orchestrates Firing FCM notifications for bookings."""
    if not custom_message:
        messages = {
            NotificationType.booking_created: f"Your booking #{booking.id} has been created successfully.",
            NotificationType.booking_accepted: f"Your booking #{booking.id} has been accepted by the vendor.",
            NotificationType.booking_cancelled: f"Your booking #{booking.id} has been cancelled.",
            NotificationType.booking_rejected: f"Your booking #{booking.id} has been rejected by the service provider.",
            NotificationType.booking_completed: f"Your booking #{booking.id} has been completed.",
            NotificationType.otp_sent: f"An OTP for booking #{booking.id} completion has been sent to your email.",
            NotificationType.payment_created: f"Payment for booking #{booking.id} has been created."
        }
        message = messages.get(notification_type, f"Booking #{booking.id} status updated to {notification_type.value}.")
    else:
        message = custom_message
    
    try:
        send_notification(
            recipient=recipient,
            notification_type=notification_type,
            message=message,
            recipient_id=recipient_id,
            fcm_token=fcm_token
        )
    except Exception as e:
        logger.error(f"FCM Notification Error for {recipient}: {str(e)}")

def enrich_booking_object(booking: Booking, db: Session) -> Booking:
    """
    Populates dynamic fields on the ORM object for Pydantic serialization.
    Using attributes instead of dictionary reconstruction for cleaner structure.
    """
    # Vendor naming logic
    vendor = booking.service_provider
    vendor_name = "Unknown Provider"
    if vendor:
        vendor_name = vendor.full_name or vendor.business_name or vendor.email or f"Provider #{vendor.id}"
    
    # Map fields for BookingOut schema
    booking.user_name = booking.user.name if booking.user else "Unknown User"
    booking.service_provider_name = vendor_name
    booking.category_name = booking.category.name if booking.category else None
    booking.subcategory_name = booking.subcategory.name if booking.subcategory else None
    booking.service_name = booking.subcategory.name if booking.subcategory else None # Default service_name to subcat
    
    # Coordinates
    booking.vendor_latitude = vendor.latitude if vendor else None
    booking.vendor_longitude = vendor.longitude if vendor else None
    
    # Calculate Amount
    amount = 0.0
    # 1. Try to get from payment record
    payment = booking.payments[0] if booking.payments else None
    if payment:
        amount = payment.amount
    elif vendor:
        # 2. Fallback to vendor charge for this subcategory
        charge = db.query(VendorSubcategoryCharge).filter(
            VendorSubcategoryCharge.vendor_id == vendor.id,
            VendorSubcategoryCharge.subcategory_id == booking.subcategory_id
        ).first()
        if charge:
            amount = charge.service_charge
            
    booking.amount = amount
    
    return booking

# --- USER ROUTES ---

@router.post("", response_model=BookingOut)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new service booking"""
    if booking_data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized user ID")

    booking = booking_crud.create_booking(db, booking_data)
    
    # Notify involved parties
    user_token = current_user.new_fcm_token or current_user.old_fcm_token
    send_booking_notification(db, booking, NotificationType.booking_created, current_user.email, current_user.id, user_token)
    
    # Vendor will be notified after successful payment in payment_routes.py
    # vendor = booking.service_provider
    # if vendor:
    #     vendor_token = vendor.new_fcm_token or vendor.old_fcm_token
    #     send_booking_notification(
    #         db, booking, NotificationType.booking_created, 
    #         vendor.email, vendor.id, vendor_token,
    #         custom_message=f"New booking request received! Booking #{booking.id}"
    #     )

    return enrich_booking_object(booking, db)

@router.get("", response_model=List[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    identity=Depends(get_current_identity),
    status: Optional[BookingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Polymorphic listing based on logged-in role"""
    bookings = []
    
    if isinstance(identity, User) and identity.is_superuser:
        bookings = booking_crud.get_bookings_by_status(db, status, skip, limit) if status else booking_crud.get_all_bookings(db, skip, limit)
    elif isinstance(identity, User):
        bookings = booking_crud.get_bookings_by_user_and_status(db, identity.id, status, skip, limit) if status else booking_crud.get_bookings_by_user_id(db, identity.id, skip, limit)
    elif isinstance(identity, Vendor):
        bookings = booking_crud.get_bookings_by_vendor_and_status(db, identity.id, status, skip, limit) if status else booking_crud.get_bookings_by_vendor_id(db, identity.id, skip, limit)
            
    return [enrich_booking_object(b, db) for b in bookings]

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking_details(
    booking_id: int,
    db: Session = Depends(get_db),
    identity=Depends(get_current_identity),
):
    """Get detailed view of a single booking"""
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Access control
    is_admin = isinstance(identity, User) and identity.is_superuser
    is_owner = isinstance(identity, User) and identity.id == booking.user_id
    is_assigned_vendor = isinstance(identity, Vendor) and identity.id == booking.serviceprovider_id
    
    if not (is_admin or is_owner or is_assigned_vendor):
        raise HTTPException(status_code=403, detail="Unauthorized access")

    return enrich_booking_object(booking, db)

# --- ADMIN ROUTES ---

@router.get("/admin/all", response_model=dict)
def get_all_bookings_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    status: Optional[BookingStatus] = Query(None),
    user_id: Optional[int] = Query(None),
    vendor_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Advanced admin view with filtering and search"""
    skip = (page - 1) * limit
    
    query = db.query(Booking)
    
    # Apply filters
    if status:
        query = query.filter(Booking.status == status)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if vendor_id:
        query = query.filter(Booking.serviceprovider_id == vendor_id)

    # Search Logic
    if search:
        from sqlalchemy import or_
        search_term = f"%{search}%"
        # Find related user IDs and vendor IDs
        found_user_ids = db.query(User.id).filter(or_(User.name.ilike(search_term), User.email.ilike(search_term), User.phone_number.ilike(search_term))).subquery()
        found_vendor_ids = db.query(Vendor.id).filter(or_(Vendor.full_name.ilike(search_term), Vendor.business_name.ilike(search_term), Vendor.email.ilike(search_term))).subquery()
        
        query = query.filter(
            or_(
                Booking.id.cast(str).ilike(search_term),
                Booking.user_id.in_(found_user_ids),
                Booking.serviceprovider_id.in_(found_vendor_ids),
                Booking.address.ilike(search_term)
            )
        )

    total = query.count()
    import math
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    results = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()

    # Pre-serialize to dict to ensure all enriched fields are captured correctly
    serialized_bookings = []
    for b in results:
        enriched = enrich_booking_object(b, db)
        # Convert to dict and ensure all expected fields from BookingOut are present
        data = {
            "id": b.id,
            "user_id": b.user_id,
            "serviceprovider_id": b.serviceprovider_id,
            "category_id": b.category_id,
            "subcategory_id": b.subcategory_id,
            "user_name": getattr(enriched, "user_name", "Unknown User"),
            "service_provider_name": getattr(enriched, "service_provider_name", "Unknown Provider"),
            "category_name": getattr(enriched, "category_name", "N/A"),
            "subcategory_name": getattr(enriched, "subcategory_name", "N/A"),
            "service_name": getattr(enriched, "service_name", "N/A"),
            "amount": getattr(enriched, "amount", 0.0),
            "status": b.status.value if hasattr(b.status, 'value') else str(b.status),
            "scheduled_time": b.scheduled_time.isoformat() if b.scheduled_time else None,
            "address": b.address,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        serialized_bookings.append(data)

    return {
        "bookings": serialized_bookings,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

# --- VENDOR (PARTNER APP) ROUTES ---

@router.get("/vendor/my-bookings", response_model=List[BookingOut])
def get_vendor_bookings(
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(get_current_vendor),
    status: Optional[BookingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Vendor's assigned bookings view"""
    bookings = booking_crud.get_bookings_by_vendor_and_status(db, vendor.id, status, skip, limit) if status else booking_crud.get_bookings_by_vendor_id(db, vendor.id, skip, limit)
    return [enrich_booking_object(b, db) for b in bookings]

# --- ACTIONS & STATUS UPDATES ---

@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: int,
    update_data: BookingStatusUpdate,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(get_current_vendor)
):
    """Update status, send notifications, and handle completion logic (earnings/receipts)"""
    from app.utils.otp_utils import send_receipt_email

    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking or booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized or missing booking")

    try:
        updated_booking = booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
        
        # Determine notification message
        notif_map = {
            BookingStatus.accepted: f"Good news! Your booking #{booking_id} has been accepted.",
            BookingStatus.cancelled: f"Notice: Your booking #{booking_id} was cancelled.",
            BookingStatus.rejected: f"Notice: Your booking #{booking_id} was rejected.",
            BookingStatus.completed: f"Service for booking #{booking_id} marked as completed. Thank you!"
        }
        
        user = booking.user
        if user:
            token = user.new_fcm_token or user.old_fcm_token
            send_booking_notification(db, updated_booking, NotificationType.booking_created, user.email, user.id, token, custom_message=notif_map.get(update_data.status))
            
            # Completion specific side-effects
            if update_data.status == BookingStatus.completed:
                payment = payment_crud.get_payment_by_booking_id(db, booking_id)
                if payment:
                    send_receipt_email(db, updated_booking, payment, user.email)
                    try:
                        from app.crud import vendor_earnings_crud
                        vendor_earnings_crud.create_vendor_earnings(db, booking_id=booking_id, vendor_id=vendor.id, total_paid=payment.amount)
                    except Exception as e:
                        logger.error(f"Earning creation failed for {booking_id}: {str(e)}")

        return enrich_booking_object(updated_booking, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{booking_id}/send-completion-otp")
def initiate_completion_otp(
    booking_id: int,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(get_current_vendor)
):
    """Triggers OTP for secure service completion"""
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking or booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized provider")
    if booking.status != BookingStatus.accepted:
        raise HTTPException(status_code=400, detail="Must be in accepted status")

    from app.utils.otp_utils import generate_otp, send_email
    otp = generate_otp()
    booking.otp = otp
    booking.otp_created_at = datetime.utcnow()
    db.commit()

    user = booking.user
    if user:
        send_email(receiver_email=user.email, otp=otp, template="otp")
        token = user.new_fcm_token or user.old_fcm_token
        send_booking_notification(db, booking, NotificationType.otp_sent, user.email, user.id, token)

    return {"message": "OTP sent successfully"}

@router.delete("/{booking_id}")
def delete_or_cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """User-side cancellation"""
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    success, error = booking_crud.cancel_booking(db, booking_id, user.id)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    # Notify parties
    vendor = booking.service_provider
    if vendor:
        token = vendor.new_fcm_token or vendor.old_fcm_token
        send_booking_notification(db, booking, NotificationType.booking_cancelled, vendor.email, vendor.id, token)

    return {"message": "Booking cancelled successfully"}
