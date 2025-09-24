# from datetime import datetime
# from sqlalchemy.orm import Session
# from app.models.payment_model import Payment
# from app.schemas.payment_schema import PaymentCreate

# def create_payment(db: Session, payment_data: PaymentCreate):
#     payment = Payment(**payment_data.dict())
#     db.add(payment)
#     db.commit()
#     db.refresh(payment)
#     return payment

# def get_payment_by_booking_id(db: Session, booking_id: int):
#     return db.query(Payment).filter(Payment.booking_id == booking_id).first()

# def update_payment_status(db: Session, payment: Payment, status: str):
#     payment.status = status
#     payment.updated_at = datetime.utcnow()
#     db.commit()
#     db.refresh(payment)
#     return payment


# mac changes

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.payment_model import Payment, PaymentStatus
from app.schemas.payment_schema import PaymentCreate, PaymentUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def create_payment(db: Session, payment_data: PaymentCreate):
    """Create a new payment record"""
    payment = Payment(**payment_data.dict())
    payment.created_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

def get_payment_by_id(db: Session, payment_id: int) -> Optional[Payment]:
    """Get payment by ID"""
    return db.query(Payment).filter(Payment.id == payment_id).first()

def get_payment_by_booking_id(db: Session, booking_id: int) -> Optional[Payment]:
    """Get payment by booking ID"""
    return db.query(Payment).filter(Payment.booking_id == booking_id).first()

def get_payment_by_razorpay_order_id(db: Session, razorpay_order_id: str) -> Optional[Payment]:
    """Get payment by Razorpay order ID"""
    return db.query(Payment).filter(Payment.razorpay_order_id == razorpay_order_id).first()

def get_payment_by_razorpay_payment_id(db: Session, razorpay_payment_id: str) -> Optional[Payment]:
    """Get payment by Razorpay payment ID"""
    return db.query(Payment).filter(Payment.razorpay_payment_id == razorpay_payment_id).first()

def get_payments_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get all payments for a specific user through bookings"""
    return db.query(Payment).join(Payment.booking).filter(
        Payment.booking.has(user_id=user_id)
    ).offset(skip).limit(limit).all()

def get_payments_by_vendor_id(db: Session, vendor_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get all payments for a specific vendor through bookings"""
    return db.query(Payment).join(Payment.booking).filter(
        Payment.booking.has(serviceprovider_id=vendor_id)
    ).offset(skip).limit(limit).all()

def get_payments_by_status(db: Session, status: PaymentStatus, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get payments by status"""
    return db.query(Payment).filter(Payment.status == status).offset(skip).limit(limit).all()

def get_payments_by_user_and_status(db: Session, user_id: int, status: PaymentStatus, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get payments by user ID and status"""
    return db.query(Payment).join(Payment.booking).filter(
        and_(
            Payment.booking.has(user_id=user_id),
            Payment.status == status
        )
    ).offset(skip).limit(limit).all()

def get_payments_by_vendor_and_status(db: Session, vendor_id: int, status: PaymentStatus, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get payments by vendor ID and status"""
    return db.query(Payment).join(Payment.booking).filter(
        and_(
            Payment.booking.has(serviceprovider_id=vendor_id),
            Payment.status == status
        )
    ).offset(skip).limit(limit).all()

def get_payments_by_date_range(db: Session, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get payments within a date range"""
    return db.query(Payment).filter(
        and_(Payment.created_at >= start_date, Payment.created_at <= end_date)
    ).offset(skip).limit(limit).all()

def get_all_payments(db: Session, skip: int = 0, limit: int = 100) -> List[Payment]:
    """Get all payments (admin only)"""
    return db.query(Payment).offset(skip).limit(limit).all()

def update_payment_status(db: Session, payment: Payment, status: PaymentStatus, 
                         razorpay_payment_id: Optional[str] = None,
                         razorpay_signature: Optional[str] = None):
    """Update payment status with additional Razorpay details"""
    payment.status = status
    payment.updated_at = datetime.utcnow()
    
    if razorpay_payment_id:
        payment.razorpay_payment_id = razorpay_payment_id
    
    if razorpay_signature:
        payment.razorpay_signature = razorpay_signature
    
    if status == PaymentStatus.SUCCESS:
        payment.paid_at = datetime.utcnow()
    elif status == PaymentStatus.FAILED:
        payment.failed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    return payment

def update_payment(db: Session, payment_id: int, payment_update: PaymentUpdate):
    """Update payment details"""
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        return None
    
    update_data = payment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    payment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return payment

def get_payment_analytics(db: Session, 
                         vendor_id: Optional[int] = None,
                         user_id: Optional[int] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None):
    """Get payment analytics with revenue calculations"""
    query = db.query(Payment)
    
    # Apply filters
    if vendor_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(serviceprovider_id=vendor_id))
    if user_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(user_id=user_id))
    if start_date:
        query = query.filter(Payment.created_at >= start_date)
    if end_date:
        query = query.filter(Payment.created_at <= end_date)
    
    payments = query.all()
    
    # Calculate analytics
    total_payments = len(payments)
    successful_payments = len([p for p in payments if p.status == PaymentStatus.SUCCESS])
    failed_payments = len([p for p in payments if p.status == PaymentStatus.FAILED])
    pending_payments = len([p for p in payments if p.status == PaymentStatus.PENDING])
    
    total_revenue = sum(p.amount for p in payments if p.status == PaymentStatus.SUCCESS)
    pending_revenue = sum(p.amount for p in payments if p.status == PaymentStatus.PENDING)
    
    return {
        "total_payments": total_payments,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "pending_payments": pending_payments,
        "success_rate": (successful_payments / total_payments * 100) if total_payments > 0 else 0,
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "average_payment_amount": total_revenue / successful_payments if successful_payments > 0 else 0
    }

def get_recent_payments(db: Session, 
                       vendor_id: Optional[int] = None,
                       user_id: Optional[int] = None,
                       limit: int = 10) -> List[Payment]:
    """Get recent payments"""
    query = db.query(Payment).order_by(desc(Payment.created_at))
    
    if vendor_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(serviceprovider_id=vendor_id))
    if user_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(user_id=user_id))
    
    return query.limit(limit).all()

def search_payments(db: Session,
                   user_id: Optional[int] = None,
                   vendor_id: Optional[int] = None,
                   status: Optional[PaymentStatus] = None,
                   razorpay_order_id: Optional[str] = None,
                   razorpay_payment_id: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   skip: int = 0,
                   limit: int = 100) -> List[Payment]:
    """Advanced search for payments with multiple filters"""
    query = db.query(Payment)
    
    filters = []
    
    if user_id:
        query = query.join(Payment.booking)
        filters.append(Payment.booking.has(user_id=user_id))
    
    if vendor_id:
        if user_id:  # Already joined
            filters.append(Payment.booking.has(serviceprovider_id=vendor_id))
        else:
            query = query.join(Payment.booking)
            filters.append(Payment.booking.has(serviceprovider_id=vendor_id))
    
    if status:
        filters.append(Payment.status == status)
    if razorpay_order_id:
        filters.append(Payment.razorpay_order_id == razorpay_order_id)
    if razorpay_payment_id:
        filters.append(Payment.razorpay_payment_id == razorpay_payment_id)
    if start_date:
        filters.append(Payment.created_at >= start_date)
    if end_date:
        filters.append(Payment.created_at <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.offset(skip).limit(limit).all()

def get_payment_count_by_status(db: Session, 
                               vendor_id: Optional[int] = None,
                               user_id: Optional[int] = None):
    """Get payment count by status for analytics"""
    query = db.query(Payment.status, db.func.count(Payment.id).label('count'))
    
    if vendor_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(serviceprovider_id=vendor_id))
    if user_id:
        if vendor_id:  # Already joined
            query = query.filter(Payment.booking.has(user_id=user_id))
        else:
            query = query.join(Payment.booking).filter(Payment.booking.has(user_id=user_id))
    
    return query.group_by(Payment.status).all()

def get_monthly_revenue(db: Session, 
                       vendor_id: Optional[int] = None,
                       year: Optional[int] = None):
    """Get monthly revenue breakdown"""
    from sqlalchemy import extract, func
    
    query = db.query(
        extract('month', Payment.created_at).label('month'),
        func.sum(Payment.amount).label('revenue'),
        func.count(Payment.id).label('payment_count')
    ).filter(Payment.status == PaymentStatus.SUCCESS)
    
    if vendor_id:
        query = query.join(Payment.booking).filter(Payment.booking.has(serviceprovider_id=vendor_id))
    
    if year:
        query = query.filter(extract('year', Payment.created_at) == year)
    else:
        # Default to current year
        current_year = datetime.now().year
        query = query.filter(extract('year', Payment.created_at) == current_year)
    
    return query.group_by(extract('month', Payment.created_at)).all()

def get_failed_payment_details(db: Session, payment_id: int):
    """Get detailed failure information for a payment"""
    payment = get_payment_by_id(db, payment_id)
    if not payment or payment.status != PaymentStatus.FAILED:
        return None
    
    return {
        "payment_id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "failure_reason": payment.failure_reason,
        "failed_at": payment.failed_at,
        "retry_count": getattr(payment, 'retry_count', 0)
    }