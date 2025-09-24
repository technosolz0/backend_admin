
# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# import razorpay
# from app.core.config import settings
# from app.core.security import get_current_user
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/payments", tags=["Payment"])

# # Initialize Razorpay client
# try:
#     if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
#         logger.error("Razorpay credentials missing in configuration")
#         raise ValueError("Razorpay API credentials are not configured")
#     razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
# except Exception as e:
#     logger.error(f"Failed to initialize Razorpay client: {str(e)}")
#     raise ValueError(f"Razorpay initialization failed: {str(e)}")

# class OrderCreate(BaseModel):
#     amount: int  # Amount in rupees
#     currency: str = "INR"

# @router.post("/create-order")
# def create_order(order: OrderCreate, user=Depends(get_current_user)):
#     try:
#         order_data = {
#             "amount": order.amount * 100,  # Convert to paise
#             "currency": order.currency,
#             "payment_capture": 1  # Auto-capture payment
#         }
#         razorpay_order = razorpay_client.order.create(data=order_data)
#         logger.info(f"Razorpay order created for user {user.id}: order_id={razorpay_order['id']}")
#         return {
#             "order_id": razorpay_order["id"],
#             "key": settings.RAZORPAY_KEY_ID,
#             "amount": order.amount,
#             "currency": order.currency
#         }
#     except razorpay.errors.BadRequestError as e:
#         logger.error(f"Razorpay API error for user {user.id}: {str(e)}")
#         if "Authentication failed" in str(e):
#             raise HTTPException(status_code=500, detail="Razorpay authentication failed. Please check API credentials.")
#         raise HTTPException(status_code=400, detail=f"Razorpay API error: {str(e)}")
#     except Exception as e:
#         logger.error(f"Error creating Razorpay order for user {user.id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


# mac changes 
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import razorpay
import hmac
import hashlib
import json
from app.core.config import settings
from app.core.security import get_db, get_current_user, get_current_vendor
from app.crud import payment_crud, booking_crud
from app.schemas.payment_schema import PaymentCreate, PaymentOut, PaymentVerification
from app.models.payment_model import PaymentStatus, PaymentMethod
from datetime import datetime, date
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payment"])

# Initialize Razorpay client
try:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay credentials missing in configuration")
        raise ValueError("Razorpay API credentials are not configured")
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception as e:
    logger.error(f"Failed to initialize Razorpay client: {str(e)}")
    raise ValueError(f"Razorpay initialization failed: {str(e)}")

# ================== ENHANCED ORDER CREATION ==================

class OrderCreate(BaseModel):
    amount: int  # Amount in rupees
    currency: str = "INR"
    booking_id: int
    notes: Optional[str] = None

@router.post("/create-order")
def create_order(
    order: OrderCreate, 
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Create a Razorpay order for payment with booking validation"""
    try:
        # Verify booking exists and belongs to user
        booking = booking_crud.get_booking_by_id(db, order.booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.user_id != user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to booking")
        
        # Check if payment already exists for this booking
        existing_payment = payment_crud.get_payment_by_booking_id(db, order.booking_id)
        if existing_payment and existing_payment.status == PaymentStatus.SUCCESS:
            raise HTTPException(status_code=400, detail="Payment already completed for this booking")
        
        # Create Razorpay order
        order_data = {
            "amount": order.amount * 100,  # Convert to paise
            "currency": order.currency,
            "payment_capture": 1,  # Auto-capture payment
            "notes": {
                "booking_id": str(order.booking_id),
                "user_id": str(user.id),
                "notes": order.notes or ""
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Create or update payment record
        if existing_payment and existing_payment.status != PaymentStatus.SUCCESS:
            # Update existing payment record
            existing_payment.razorpay_order_id = razorpay_order["id"]
            existing_payment.amount = order.amount
            existing_payment.status = PaymentStatus.PENDING
            db.commit()
            db.refresh(existing_payment)
            logger.info(f"Updated existing payment record for booking {order.booking_id}")
        else:
            # Create new payment record
            payment_data = PaymentCreate(
                booking_id=order.booking_id,
                amount=order.amount,
                currency=order.currency,
                payment_method=PaymentMethod.RAZORPAY,
                razorpay_order_id=razorpay_order["id"],
                notes=order.notes
            )
            payment_crud.create_payment(db, payment_data)
            logger.info(f"Created new payment record for booking {order.booking_id}")
        
        logger.info(f"Razorpay order created for user {user.id}: order_id={razorpay_order['id']}")
        
        return {
            "order_id": razorpay_order["id"],
            "key": settings.RAZORPAY_KEY_ID,
            "amount": order.amount,
            "currency": order.currency,
            "booking_id": order.booking_id
        }
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay API error for user {user.id}: {str(e)}")
        if "Authentication failed" in str(e):
            raise HTTPException(status_code=500, detail="Razorpay authentication failed. Please check API credentials.")
        raise HTTPException(status_code=400, detail=f"Razorpay API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating Razorpay order for user {user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

# ================== PAYMENT VERIFICATION ==================

@router.post("/verify-payment")
def verify_payment(
    verification: PaymentVerification,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Verify Razorpay payment signature and update payment status"""
    try:
        # Get payment record
        payment = payment_crud.get_payment_by_razorpay_order_id(db, verification.razorpay_order_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")
        
        # Verify user authorization
        booking = booking_crud.get_booking_by_id(db, payment.booking_id)
        if booking.user_id != user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Verify payment signature
        signature_params = {
            'razorpay_order_id': verification.razorpay_order_id,
            'razorpay_payment_id': verification.razorpay_payment_id,
            'razorpay_signature': verification.razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(signature_params)
            
            # Update payment status to success
            updated_payment = payment_crud.update_payment_status(
                db, payment, PaymentStatus.SUCCESS,
                verification.razorpay_payment_id,
                verification.razorpay_signature
            )
            
            logger.info(f"Payment verified successfully: Payment ID {payment.id}")
            
            return {
                "status": "success",
                "message": "Payment verified successfully",
                "payment_id": payment.id,
                "booking_id": payment.booking_id
            }
            
        except razorpay.errors.SignatureVerificationError:
            # Update payment status to failed
            payment_crud.update_payment_status(
                db, payment, PaymentStatus.FAILED,
                verification.razorpay_payment_id
            )
            logger.warning(f"Payment signature verification failed: Payment ID {payment.id}")
            raise HTTPException(status_code=400, detail="Payment signature verification failed")
            
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")

# ================== USER PAYMENT ENDPOINTS ==================

@router.get("/my-payments", response_model=List[PaymentOut])
def get_my_payments(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all payments for the current user"""
    try:
        if status:
            payments = payment_crud.get_payments_by_user_and_status(db, user.id, status, skip, limit)
        else:
            payments = payment_crud.get_payments_by_user_id(db, user.id, skip, limit)
        
        logger.info(f"Retrieved {len(payments)} payments for user {user.id}")
        return payments
    except Exception as e:
        logger.error(f"Error retrieving user payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payments")

@router.get("/recent", response_model=List[PaymentOut])
def get_recent_payments(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20)
):
    """Get recent payments for the current user"""
    try:
        payments = payment_crud.get_recent_payments(db, user_id=user.id, limit=limit)
        return payments
    except Exception as e:
        logger.error(f"Error retrieving recent payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent payments")

@router.get("/analytics")
def get_user_payment_analytics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics")
):
    """Get payment analytics for the current user"""
    try:
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        analytics = payment_crud.get_payment_analytics(
            db, user_id=user.id, 
            start_date=start_datetime, 
            end_date=end_datetime
        )
        
        recent_payments = payment_crud.get_recent_payments(db, user_id=user.id, limit=5)
        
        return {
            **analytics,
            "recent_payments": recent_payments
        }
    except Exception as e:
        logger.error(f"Error retrieving user payment analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment analytics")

# ================== VENDOR PAYMENT ENDPOINTS ==================

@router.get("/vendor/earnings", response_model=List[PaymentOut])
def get_vendor_earnings(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    status: Optional[PaymentStatus] = Query(PaymentStatus.SUCCESS, description="Filter by payment status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get earnings/payments for the current vendor"""
    try:
        if status:
            payments = payment_crud.get_payments_by_vendor_and_status(db, vendor.id, status, skip, limit)
        else:
            payments = payment_crud.get_payments_by_vendor_id(db, vendor.id, skip, limit)
        
        logger.info(f"Retrieved {len(payments)} payments for vendor {vendor.id}")
        return payments
    except Exception as e:
        logger.error(f"Error retrieving vendor payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendor payments")

@router.get("/vendor/analytics")
def get_vendor_payment_analytics(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics")
):
    """Get payment analytics for the current vendor"""
    try:
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        analytics = payment_crud.get_payment_analytics(
            db, vendor_id=vendor.id, 
            start_date=start_datetime, 
            end_date=end_datetime
        )
        
        recent_payments = payment_crud.get_recent_payments(db, vendor_id=vendor.id, limit=10)
        
        return {
            **analytics,
            "recent_payments": recent_payments
        }
    except Exception as e:
        logger.error(f"Error retrieving vendor payment analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment analytics")

@router.get("/vendor/monthly-revenue")
def get_vendor_monthly_revenue(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    year: Optional[int] = Query(None, description="Year for revenue breakdown")
):
    """Get monthly revenue breakdown for vendor"""
    try:
        revenue_data = payment_crud.get_monthly_revenue(db, vendor_id=vendor.id, year=year)
        
        # Format the response
        monthly_data = []
        for month, revenue, count in revenue_data:
            monthly_data.append({
                "month": month,
                "revenue": float(revenue or 0),
                "payment_count": count,
                "average_payment": float(revenue / count) if count > 0 and revenue else 0
            })
        
        return {
            "year": year or datetime.now().year,
            "monthly_data": monthly_data,
            "total_annual_revenue": sum(item["revenue"] for item in monthly_data),
            "total_payments": sum(item["payment_count"] for item in monthly_data)
        }
    except Exception as e:
        logger.error(f"Error retrieving monthly revenue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monthly revenue")

@router.get("/vendor/stats")
def get_vendor_payment_stats(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Get payment statistics for the current vendor"""
    try:
        stats = payment_crud.get_payment_count_by_status(db, vendor_id=vendor.id)
        recent_payments = payment_crud.get_recent_payments(db, vendor_id=vendor.id, limit=5)
        
        stats_dict = {stat.status.value: stat.count for stat in stats}
        
        return {
            "total_payments": sum(stats_dict.values()),
            "status_counts": stats_dict,
            "recent_payments": recent_payments
        }
    except Exception as e:
        logger.error(f"Error retrieving vendor payment stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment statistics")

# ================== PAYMENT DETAILS ==================

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_details(
    payment_id: int, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """Get specific payment details"""
    payment = payment_crud.get_payment_by_id(db, payment_id)
    if not payment:
        logger.error(f"Payment not found for ID {payment_id}")
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify user authorization through booking
    booking = booking_crud.get_booking_by_id(db, payment.booking_id)
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to payment {payment_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    logger.info(f"Payment retrieved successfully: ID {payment_id}")
    return payment

@router.get("/booking/{booking_id}", response_model=PaymentOut)
def get_payment_by_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """Get payment by booking ID"""
    # Verify booking exists and user authorization
    booking = booking_crud.get_booking_by_id(db, booking_id)
    if not booking:
        logger.error(f"Booking not found for ID {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != user.id:
        logger.warning(f"Unauthorized access to booking {booking_id} by user {user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    payment = payment_crud.get_payment_by_booking_id(db, booking_id)
    if not payment:
        logger.info(f"No payment found for booking ID {booking_id}")
        raise HTTPException(status_code=404, detail="Payment not found")
    
    logger.info(f"Payment retrieved successfully for booking ID {booking_id}")
    return payment

@router.get("/razorpay/{razorpay_payment_id}/details")
def get_razorpay_payment_details(
    razorpay_payment_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Get detailed payment information from Razorpay"""
    try:
        # Get payment record from database
        payment = payment_crud.get_payment_by_razorpay_payment_id(db, razorpay_payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")
        
        # Verify user authorization
        booking = booking_crud.get_booking_by_id(db, payment.booking_id)
        if booking.user_id != user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Fetch details from Razorpay
        razorpay_payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        return {
            "payment_id": payment.id,
            "booking_id": payment.booking_id,
            "razorpay_details": {
                "id": razorpay_payment["id"],
                "order_id": razorpay_payment["order_id"],
                "amount": razorpay_payment["amount"] / 100,  # Convert from paise
                "currency": razorpay_payment["currency"],
                "status": razorpay_payment["status"],
                "method": razorpay_payment.get("method"),
                "created_at": razorpay_payment["created_at"],
                "captured": razorpay_payment.get("captured", False),
                "error_code": razorpay_payment.get("error_code"),
                "error_description": razorpay_payment.get("error_description")
            }
        }
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay API error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Razorpay API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching payment details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment details")

# ================== WEBHOOK HANDLING ==================

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(None)
):
    """Handle Razorpay webhooks for payment updates"""
    try:
        body = await request.body()
        
        # Verify webhook signature if webhook secret is configured
        if hasattr(settings, 'RAZORPAY_WEBHOOK_SECRET') and settings.RAZORPAY_WEBHOOK_SECRET:
            if not verify_webhook_signature(body, x_razorpay_signature):
                logger.warning("Invalid webhook signature received")
                raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(body.decode('utf-8'))
        event = webhook_data.get('event')
        payment_entity = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
        
        if not payment_entity:
            logger.warning("No payment entity found in webhook")
            return {"status": "ignored"}
        
        razorpay_payment_id = payment_entity.get('id')
        razorpay_order_id = payment_entity.get('order_id')
        status = payment_entity.get('status')
        
        if not razorpay_order_id:
            logger.warning(f"No order ID found in webhook for payment {razorpay_payment_id}")
            return {"status": "ignored"}
        
        # Find payment record
        payment = payment_crud.get_payment_by_razorpay_order_id(db, razorpay_order_id)
        if not payment:
            logger.warning(f"Payment record not found for order ID {razorpay_order_id}")
            return {"status": "ignored"}
        
        # Update payment status based on webhook event
        if event == 'payment.captured' and status == 'captured':
            payment_crud.update_payment_status(
                db, payment, PaymentStatus.SUCCESS, razorpay_payment_id
            )
            logger.info(f"Payment captured via webhook: Payment ID {payment.id}")
            
        elif event == 'payment.failed' and status == 'failed':
            failure_reason = payment_entity.get('error_description', 'Payment failed')
            payment.failure_reason = failure_reason
            payment_crud.update_payment_status(
                db, payment, PaymentStatus.FAILED, razorpay_payment_id
            )
            logger.info(f"Payment failed via webhook: Payment ID {payment.id}, Reason: {failure_reason}")
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# ================== SEARCH AND FILTERING ==================

@router.get("/search")
def search_payments(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Advanced search for user's payments with multiple filters"""
    try:
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        payments = payment_crud.search_payments(
            db,
            user_id=user.id,
            status=status,
            start_date=start_datetime,
            end_date=end_datetime,
            skip=skip,
            limit=limit
        )
        
        return {
            "payments": payments,
            "total": len(payments),
            "filters_applied": {
                "status": status.value if status else None,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Error searching payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search payments")

# ================== FAILED PAYMENTS ==================

@router.get("/failed/{payment_id}/details")
def get_failed_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Get detailed failure information for a failed payment"""
    payment = payment_crud.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify user authorization
    booking = booking_crud.get_booking_by_id(db, payment.booking_id)
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    failure_details = payment_crud.get_failed_payment_details(db, payment_id)
    if not failure_details:
        raise HTTPException(status_code=400, detail="Payment is not in failed state or details not found")
    
    return failure_details

# ================== UTILITY FUNCTIONS ==================

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature"""
    try:
        if not hasattr(settings, 'RAZORPAY_WEBHOOK_SECRET') or not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
            
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False