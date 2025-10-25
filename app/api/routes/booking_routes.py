
# from typing import List, Optional, Union
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from datetime import datetime, date
# from enum import Enum
# import logging
# import jwt
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from app.core.security import get_db, get_current_user, get_current_vendor, SECRET_KEY, ALGORITHM
# from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
# from app.schemas.payment_schema import PaymentCreate, PaymentOut
# from app.crud import booking_crud, payment_crud, category, subcategory, user as user_crud, service_provider_crud
# from app.models.booking_model import BookingStatus
# from app.models.user import User
# from app.models.service_provider_model import ServiceProvider as Vendor
# from app.utils.fcm import send_notification

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# router = APIRouter(prefix="/bookings", tags=["Booking"])

# security = HTTPBearer()

# def get_current_identity(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Union[dict, None]]:
#     """
#     Unified dependency to get either user or vendor identity from token.
#     Returns {'type': 'user' or 'vendor', 'id': id, 'email': email, ...} or None if invalid.
#     Does not raise exceptions; returns None on failure.
#     """
#     try:
#         payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         role = payload.get('role')  # 'role' distinguishes user ('None') from vendor ('vendor')
#         email = payload.get('sub')  # 'sub' contains email
#         if not email:
#             return None

#         # Fetch full details from DB
#         if role == 'vendor':
#             vendor = service_provider_crud.get_vendor_by_email(db, email)
#             if vendor:
#                 return {
#                     'type': 'vendor',
#                     'id': vendor.id,
#                     'email': vendor.email,
#                     'new_fcm_token': vendor.new_fcm_token,
#                     'old_fcm_token': vendor.old_fcm_token
#                 }
#         else:
#             # Assume user if no role or role != 'vendor'
#             user = user_crud.get_user_by_email(db, email)
#             if user:
#                 return {
#                     'type': 'user',
#                     'id': user.id,
#                     'email': user.email,
#                     'new_fcm_token': user.new_fcm_token,
#                     'old_fcm_token': user.old_fcm_token
#                 }

#         return None
#     except Exception as e:
#         logger.warning(f"Token validation failed: {e}")
#         return None

# class NotificationType(str, Enum):
#     booking_created = "booking_created"
#     booking_accepted = "booking_accepted"
#     booking_cancelled = "booking_cancelled"
#     booking_completed = "booking_completed"
#     otp_sent = "otp_sent"
#     payment_created = "payment_created"

# def send_booking_notification(
#     db: Session,
#     booking,
#     notification_type: NotificationType,
#     recipient: str,
#     recipient_id: int,
#     fcm_token: Optional[str] = None
# ):
#     """Helper function to send standardized booking notifications."""
#     messages = {
#         NotificationType.booking_created: f"Your booking #{booking.id} has been created successfully.",
#         NotificationType.booking_accepted: f"Your booking #{booking.id} has been accepted by the vendor.",
#         NotificationType.booking_cancelled: f"Your booking #{booking.id} has been cancelled.",
#         NotificationType.booking_completed: f"Your booking #{booking.id} has been completed.",
#         NotificationType.otp_sent: f"An OTP for booking #{booking.id} completion has been sent to your email.",
#         NotificationType.payment_created: f"Payment for booking #{booking.id} has been created."
#     }
    
#     message = messages.get(notification_type, f"Booking #{booking.id} status updated to {notification_type.value}.")
    
#     try:
#         send_notification(
#             recipient=recipient,
#             notification_type=notification_type,
#             message=message,
#             recipient_id=recipient_id,
#             fcm_token=fcm_token
#         )
#         logger.info(f"Notification sent: {notification_type} to {recipient} for booking {booking.id}")
#     except Exception as e:
#         logger.error(f"Failed to send notification {notification_type} to {recipient}: {str(e)}")

# def enrich_booking(db: Session, booking) -> dict:
#     """Attach user name, category/subcategory names, and service name to booking output."""
#     cat = category.get_category_by_id(db, booking.category_id)
#     subcat = subcategory.get_subcategory_by_id(db, booking.subcategory_id)
#     user = db.query(User).filter(User.id == booking.user_id).first()
    
#     booking_dict = {
#         "id": booking.id,
#         "user_id": booking.user_id,
#         "serviceprovider_id": booking.serviceprovider_id,
#         "category_id": booking.category_id,
#         "subcategory_id": booking.subcategory_id,
#         "status": booking.status,
#         "scheduled_time": booking.scheduled_time.isoformat() if booking.scheduled_time else None,
#         "address": booking.address,
#         "otp": booking.otp,
#         "created_at": booking.created_at.isoformat() if booking.created_at else None,
#         "user_name": user.name if user else "Unknown User",
#         "category_name": cat.name if cat else None,
#         "subcategory_name": subcat.name if subcat else None,
#         "service_name": subcat.name if subcat else None,
#     }
    
#     return booking_dict

# @router.post("/", response_model=dict)
# def create_booking(
#     booking: BookingCreate,
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     if booking.user_id != current_user.id:
#         logger.warning(f"Unauthorized attempt to create booking for user_id {booking.user_id} by user {current_user.id}")
#         raise HTTPException(status_code=403, detail="You can't create booking for another user.")

#     booking_result = booking_crud.create_booking(db, booking)
#     logger.info(f"Booking created successfully: ID {booking_result.id}")

#     user_fcm_token = current_user.new_fcm_token or current_user.old_fcm_token
#     send_booking_notification(
#         db, booking_result, NotificationType.booking_created,
#         recipient=current_user.email, recipient_id=current_user.id, fcm_token=user_fcm_token
#     )
    
#     vendor = booking_crud.get_vendor_by_serviceprovider_id(db, booking_result.serviceprovider_id)
#     if vendor:
#         vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
#         send_booking_notification(
#             db, booking_result, NotificationType.booking_created, 
#             recipient=vendor.email, recipient_id=vendor.id, fcm_token=vendor_fcm_token
#         )

#     return enrich_booking(db, booking_result)

# @router.get("/", response_model=List[dict])
# def get_all_bookings(
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user),
#     status: Optional[BookingStatus] = Query(None),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(10, ge=1, le=100)
# ):
#     if status:
#         bookings = booking_crud.get_bookings_by_user_and_status(db, user.id, status, skip, limit)
#     else:
#         bookings = booking_crud.get_bookings_by_user_id(db, user.id, skip, limit)
#     return [enrich_booking(db, b) for b in bookings]

# @router.get("/{booking_id}", response_model=dict)
# def get_booking(
#     booking_id: int,
#     db: Session = Depends(get_db),
#     identity: Optional[dict] = Depends(get_current_identity),
# ):
#     booking = booking_crud.get_booking_by_id(db, booking_id)
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found")

#     if not identity:
#         raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

#     if identity['type'] == 'user' and booking.user_id == identity['id']:
#         return enrich_booking(db, booking)
#     elif identity['type'] == 'vendor' and booking.serviceprovider_id == identity['id']:
#         return enrich_booking(db, booking)
#     else:
#         raise HTTPException(status_code=403, detail="Unauthorized access to this booking")


# app/api/routes/booking_routes.py - Updated get_current_identity to use role/sub
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from enum import Enum
import logging
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import get_db, get_current_user, get_current_vendor, SECRET_KEY, ALGORITHM, get_current_identity  # Use unified
from app.schemas.booking_schema import BookingCreate, BookingOut, BookingStatusUpdate
from app.schemas.payment_schema import PaymentCreate, PaymentOut
from app.crud import booking_crud, payment_crud, category, subcategory, user as user_crud, service_provider_crud as vendor_crud
from app.models.booking_model import BookingStatus
from app.models.user import User
from app.models.service_provider_model import ServiceProvider as Vendor
from app.utils.fcm import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["Booking"])

# Remove custom get_current_identity - use the one from security.py
# (If you still need it, alias it, but unified is better)

class NotificationType(str, Enum):
    booking_created = "booking_created"
    booking_accepted = "booking_accepted"
    booking_cancelled = "booking_cancelled"
    booking_completed = "booking_completed"
    otp_sent = "otp_sent"
    payment_created = "payment_created"

def send_booking_notification(
    db: Session,
    booking,
    notification_type: NotificationType,
    recipient: str,
    recipient_id: int,
    fcm_token: Optional[str] = None
):
    """Helper function to send standardized booking notifications."""
    messages = {
        NotificationType.booking_created: f"Your booking #{booking.id} has been created successfully.",
        NotificationType.booking_accepted: f"Your booking #{booking.id} has been accepted by the vendor.",
        NotificationType.booking_cancelled: f"Your booking #{booking.id} has been cancelled.",
        NotificationType.booking_completed: f"Your booking #{booking.id} has been completed.",
        NotificationType.otp_sent: f"An OTP for booking #{booking.id} completion has been sent to your email.",
        NotificationType.payment_created: f"Payment for booking #{booking.id} has been created."
    }
    
    message = messages.get(notification_type, f"Booking #{booking.id} status updated to {notification_type.value}.")
    
    try:
        send_notification(
            recipient=recipient,
            notification_type=notification_type,
            message=message,
            recipient_id=recipient_id,
            fcm_token=fcm_token
        )
        logger.info(f"Notification sent: {notification_type} to {recipient} for booking {booking.id}")
    except Exception as e:
        logger.error(f"Failed to send notification {notification_type} to {recipient}: {str(e)}")

def enrich_booking(db: Session, booking) -> dict:
    """Attach user name, category/subcategory names, and service name to booking output."""
    cat = category.get_category_by_id(db, booking.category_id)
    subcat = subcategory.get_subcategory_by_id(db, booking.subcategory_id)
    user = db.query(User).filter(User.id == booking.user_id).first()
    
    booking_dict = {
        "id": booking.id,
        "user_id": booking.user_id,
        "serviceprovider_id": booking.serviceprovider_id,
        "category_id": booking.category_id,
        "subcategory_id": booking.subcategory_id,
        "status": booking.status,
        "scheduled_time": booking.scheduled_time.isoformat() if booking.scheduled_time else None,
        "address": booking.address,
        "otp": booking.otp,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
        "user_name": user.name if user else "Unknown User",
        "category_name": cat.name if cat else None,
        "subcategory_name": subcat.name if subcat else None,
        "service_name": subcat.name if subcat else None,
    }
    
    return booking_dict

@router.post("/", response_model=dict)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if booking.user_id != current_user.id:
        logger.warning(f"Unauthorized attempt to create booking for user_id {booking.user_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail="You can't create booking for another user.")

    booking_result = booking_crud.create_booking(db, booking)
    logger.info(f"Booking created successfully: ID {booking_result.id}")

    user_fcm_token = current_user.new_fcm_token or current_user.old_fcm_token
    send_booking_notification(
        db, booking_result, NotificationType.booking_created,
        recipient=current_user.email, recipient_id=current_user.id, fcm_token=user_fcm_token
    )
    
    vendor = booking_crud.get_vendor_by_serviceprovider_id(db, booking_result.serviceprovider_id)
    if vendor:
        vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
        send_booking_notification(
            db, booking_result, NotificationType.booking_created, 
            recipient=vendor.email, recipient_id=vendor.id, fcm_token=vendor_fcm_token
        )

    return enrich_booking(db, booking_result)

@router.get("/", response_model=List[dict])
def get_all_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    status: Optional[BookingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if status:
        bookings = booking_crud.get_bookings_by_user_and_status(db, user.id, status, skip, limit)
    else:
        bookings = booking_crud.get_bookings_by_user_id(db, user.id, skip, limit)
    return [enrich_booking(db, b) for b in bookings]

@router.get("/{booking_id}", response_model=dict)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    identity=Depends(get_current_identity),  # Unified identity
):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check based on identity type
    if hasattr(identity, 'id') and hasattr(identity, 'email'):  # Valid identity
        if identity.id == booking.user_id:  # User or Vendor ID match
            return enrich_booking(db, booking)
        else:
            raise HTTPException(status_code=403, detail="Unauthorized access to this booking")
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

@router.patch("/{booking_id}/status", response_model=dict)
def update_booking_status(
    booking_id: int,
    update_data: BookingStatusUpdate,
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    from app.utils.otp_utils import send_receipt_email

    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized provider")

    try:
        booking_result = booking_crud.update_booking_status(db, booking, update_data.status, update_data.otp)
        
        notification_type = None
        if update_data.status == BookingStatus.accepted:
            notification_type = NotificationType.booking_accepted
        elif update_data.status == BookingStatus.completed:
            notification_type = NotificationType.booking_completed
        elif update_data.status == BookingStatus.cancelled:
            notification_type = NotificationType.booking_cancelled

        if notification_type:
            user = booking_crud.get_user_by_id(db, booking.user_id)
            if user:
                user_fcm_token = user.new_fcm_token or user.old_fcm_token
                send_booking_notification(
                    db, booking_result, notification_type, 
                    recipient=user.email, recipient_id=user.id, fcm_token=user_fcm_token
                )
                
                # Send receipt email when booking is completed
                if notification_type == NotificationType.booking_completed:
                    payment = payment_crud.get_payment_by_booking_id(db, booking_id)
                    if payment:
                        send_receipt_email(db, booking_result, payment, user.email)
                    else:
                        logger.warning(f"No payment found for completed booking {booking_id}")
            
            # Notify vendor as well for consistency
            vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
            send_booking_notification(
                db, booking_result, notification_type, 
                recipient=vendor.email, recipient_id=vendor.id, fcm_token=vendor_fcm_token
            )

        return enrich_booking(db, booking_result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{booking_id}/payment", response_model=PaymentOut)
def create_payment(
    booking_id: int,
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    if payment.booking_id != booking_id:
        raise HTTPException(status_code=400, detail="Payment booking_id mismatch")

    existing_payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this booking")

    payment_result = payment_crud.create_payment(db, payment)
    
    # Send notification to user and vendor
    user_fcm_token = user.new_fcm_token or user.old_fcm_token
    send_booking_notification(
        db, booking, NotificationType.payment_created,
        recipient=user.email, recipient_id=user.id, fcm_token=user_fcm_token
    )
    vendor = booking_crud.get_vendor_by_serviceprovider_id(db, booking.serviceprovider_id)
    if vendor:
        vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
        send_booking_notification(
            db, booking, NotificationType.payment_created,
            recipient=vendor.email, recipient_id=vendor.id, fcm_token=vendor_fcm_token
        )

    return payment_result

@router.get("/{booking_id}/payment", response_model=PaymentOut)
def get_payment(
    booking_id: int,
    db: Session = Depends(get_db),
    identity: Optional[dict] = Depends(get_current_identity),
):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

    if (identity['type'] == 'user' and booking.user_id == identity['id']) or \
       (identity['type'] == 'vendor' and booking.serviceprovider_id == identity['id']):
        payment = payment_crud.get_payment_by_booking_id(db, booking_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access to this payment")

@router.get("/vendor/my-bookings", response_model=List[dict])
def get_vendor_bookings(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    status: Optional[BookingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    logger.info(f"Fetching bookings for vendor ID: {vendor.id}")
    
    if status:
        bookings = booking_crud.get_bookings_by_vendor_and_status(db, vendor.id, status, skip, limit)
    else:
        bookings = booking_crud.get_bookings_by_vendor_id(db, vendor.id, skip, limit)
    
    logger.info(f"Found {len(bookings)} bookings for vendor ID: {vendor.id}")
    return [enrich_booking(db, b) for b in bookings]

@router.get("/vendor/stats")
def get_vendor_booking_stats(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    logger.info(f"Fetching stats for vendor ID: {vendor.id}")
    
    stats = booking_crud.get_booking_count_by_status(db, vendor_id=vendor.id)
    recent_bookings = booking_crud.get_recent_bookings(db, vendor_id=vendor.id, limit=5)
    
    return {
        "total_bookings": sum(stat.count for stat in stats),
        "status_counts": {stat.status: stat.count for stat in stats},
        "recent_bookings": [enrich_booking(db, b) for b in recent_bookings],
    }

@router.get("/user/recent", response_model=List[dict])
def get_user_recent_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = Query(5, ge=1, le=50)
):
    bookings = booking_crud.get_recent_bookings(db, user_id=user.id, limit=limit)
    return [enrich_booking(db, b) for b in bookings]

@router.get("/user/search")
def search_user_bookings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    vendor_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=None) if start_date else None
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=None) if end_date else None

    bookings = booking_crud.search_bookings(
        db,
        user_id=user.id,
        vendor_id=vendor_id,
        status=status,
        start_date=start_dt,
        end_date=end_dt,
        skip=skip,
        limit=limit,
    )

    return {
        "bookings": [enrich_booking(db, b) for b in bookings],
        "total": len(bookings),
        "filters_applied": {
            "vendor_id": vendor_id,
            "status": status.value if status else None,
            "start_date": start_date,
            "end_date": end_date,
        },
    }

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    success, error_msg = booking_crud.cancel_booking(db, booking_id, user.id)
    if not success:
        raise HTTPException(status_code=400, detail=error_msg or "Failed to cancel booking")

    if booking.status in [BookingStatus.pending, BookingStatus.accepted]:
        # Send notifications to user and vendor
        user_fcm_token = user.new_fcm_token or user.old_fcm_token
        send_booking_notification(
            db, booking, NotificationType.booking_cancelled,
            recipient=user.email, recipient_id=user.id, fcm_token=user_fcm_token
        )
        vendor = booking_crud.get_vendor_by_serviceprovider_id(db, booking.serviceprovider_id)
        if vendor:
            vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
            send_booking_notification(
                db, booking, NotificationType.booking_cancelled,
                recipient=vendor.email, recipient_id=vendor.id, fcm_token=vendor_fcm_token
            )
        
        return {"message": "Booking cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status {booking.status}")

@router.post("/{booking_id}/send-completion-otp")
def send_completion_otp(
    booking_id: int,
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Send OTP to user for booking completion"""
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized provider")
    if booking.status != BookingStatus.accepted:
        raise HTTPException(status_code=400, detail="Booking must be accepted to send completion OTP")

    from app.utils.otp_utils import generate_otp, send_email
    otp = generate_otp()
    booking.otp = otp
    booking.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)

    user = booking_crud.get_user_by_id(db, booking.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    send_email(receiver_email=user.email, otp=otp, template="otp")
    logger.info(f"Completion OTP sent to user for booking {booking_id}")

    # Send notification to user
    user_fcm_token = user.new_fcm_token or user.old_fcm_token
    send_booking_notification(
        db, booking, NotificationType.otp_sent, 
        recipient=user.email, recipient_id=user.id, fcm_token=user_fcm_token
    )

    return {"message": "OTP sent to user email"}
