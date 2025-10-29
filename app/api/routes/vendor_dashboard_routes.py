# app/api/routes/vendor_dashboard_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, date, timedelta
from typing import Optional
import logging

from app.core.security import get_db, get_current_vendor
from app.models.booking_model import Booking, BookingStatus
from app.models.payment_model import Payment, PaymentStatus
from app.models.vendor_earnings_model import VendorEarnings
from app.models.user import User

logger = logging.getLogger(__name__)

# IMPORTANT: Use a specific prefix to avoid route conflicts
router = APIRouter(prefix="/vendor/dashboard", tags=["Vendor Dashboard"])


@router.get("")  # This maps to /api/vendor/dashboard
def get_vendor_dashboard(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """
    Comprehensive vendor dashboard with all stats including:
    - Booking statistics
    - Payment analytics
    - Earnings after commission
    - Today's data
    - Recent bookings with payment info
    """
    try:
        vendor_id = vendor.id
        today = datetime.now().date()
        
        # ==================== BOOKING STATISTICS ====================
        total_bookings = db.query(func.count(Booking.id)).filter(
            Booking.serviceprovider_id == vendor_id
        ).scalar() or 0
        
        pending_bookings = db.query(func.count(Booking.id)).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.status == BookingStatus.pending
            )
        ).scalar() or 0
        
        accepted_bookings = db.query(func.count(Booking.id)).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.status == BookingStatus.accepted
            )
        ).scalar() or 0
        
        completed_bookings = db.query(func.count(Booking.id)).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.status == BookingStatus.completed
            )
        ).scalar() or 0
        
        cancelled_bookings = db.query(func.count(Booking.id)).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.status == BookingStatus.cancelled
            )
        ).scalar() or 0
        
        # ==================== TODAY'S BOOKINGS ====================
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_bookings = db.query(func.count(Booking.id)).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.scheduled_time >= today_start,
                Booking.scheduled_time <= today_end
            )
        ).scalar() or 0
        
        # ==================== PAYMENT ANALYTICS ====================
        payment_stats = db.query(
            func.count(Payment.id).label('total_payments'),
            func.sum(Payment.amount).label('total_revenue'),
            func.avg(Payment.amount).label('avg_payment')
        ).join(Booking, Payment.booking_id == Booking.id).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Payment.status == PaymentStatus.SUCCESS
            )
        ).first()
        
        total_payments_count = payment_stats.total_payments or 0
        total_revenue = float(payment_stats.total_revenue or 0)
        avg_payment = float(payment_stats.avg_payment or 0)
        
        # Success rate calculation
        all_payments = db.query(func.count(Payment.id)).join(
            Booking, Payment.booking_id == Booking.id
        ).filter(Booking.serviceprovider_id == vendor_id).scalar() or 0
        
        success_rate = (total_payments_count / all_payments * 100) if all_payments > 0 else 0
        
        # Pending and failed payments
        pending_payments = db.query(func.count(Payment.id)).join(
            Booking, Payment.booking_id == Booking.id
        ).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Payment.status == PaymentStatus.PENDING
            )
        ).scalar() or 0
        
        failed_payments = db.query(func.count(Payment.id)).join(
            Booking, Payment.booking_id == Booking.id
        ).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Payment.status == PaymentStatus.FAILED
            )
        ).scalar() or 0
        
        # ==================== VENDOR EARNINGS (After Commission) ====================
        earnings_stats = db.query(
            func.sum(VendorEarnings.final_amount).label('total_earnings'),
            func.sum(VendorEarnings.commission_amount).label('total_commission'),
            func.count(VendorEarnings.id).label('earnings_count')
        ).filter(
            VendorEarnings.vendor_id == vendor_id
        ).first()
        
        total_earnings = float(earnings_stats.total_earnings or 0)
        total_commission = float(earnings_stats.total_commission or 0)
        earnings_count = earnings_stats.earnings_count or 0
        
        # Today's earnings
        today_earnings_stats = db.query(
            func.sum(VendorEarnings.final_amount).label('today_earnings')
        ).filter(
            and_(
                VendorEarnings.vendor_id == vendor_id,
                func.date(VendorEarnings.earned_at) == today
            )
        ).first()
        
        today_earnings = float(today_earnings_stats.today_earnings or 0)
        
        # ==================== RECENT BOOKINGS WITH PAYMENT INFO ====================
        recent_bookings_query = db.query(
            Booking,
            User.name.label('user_name'),
            Payment.amount.label('payment_amount'),
            Payment.status.label('payment_status')
        ).outerjoin(
            User, Booking.user_id == User.id
        ).outerjoin(
            Payment, Booking.id == Payment.booking_id
        ).filter(
            Booking.serviceprovider_id == vendor_id
        ).order_by(
            Booking.created_at.desc()
        ).limit(10).all()
        
        recent_bookings = []
        for booking, user_name, payment_amount, payment_status in recent_bookings_query:
            # Get category and subcategory names
            from app.crud import category, subcategory
            cat = category.get_category_by_id(db, booking.category_id)
            subcat = subcategory.get_subcategory_by_id(db, booking.subcategory_id)
            
            recent_bookings.append({
                'id': booking.id,
                'user_id': booking.user_id,
                'user_name': user_name or 'Unknown User',
                'service_name': subcat.name if subcat else 'Unknown Service',
                'category_name': cat.name if cat else None,
                'status': booking.status.value,
                'scheduled_time': booking.scheduled_time.isoformat() if booking.scheduled_time else None,
                'address': booking.address,
                'created_at': booking.created_at.isoformat(),
                'payment_amount': float(payment_amount) if payment_amount else 0.0,
                'payment_status': payment_status.value if payment_status else None,
            })
        
        # ==================== MONTHLY REVENUE BREAKDOWN ====================
        current_year = datetime.now().year
        monthly_revenue = db.query(
            extract('month', VendorEarnings.earned_at).label('month'),
            func.sum(VendorEarnings.final_amount).label('revenue'),
            func.count(VendorEarnings.id).label('count')
        ).filter(
            and_(
                VendorEarnings.vendor_id == vendor_id,
                extract('year', VendorEarnings.earned_at) == current_year
            )
        ).group_by(extract('month', VendorEarnings.earned_at)).all()
        
        monthly_data = [
            {
                'month': int(month),
                'revenue': float(revenue or 0),
                'count': count,
                'average': float(revenue / count) if count > 0 and revenue else 0
            }
            for month, revenue, count in monthly_revenue
        ]
        
        # ==================== RESPONSE ====================
        return {
            'success': True,
            'booking_stats': {
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'accepted_bookings': accepted_bookings,
                'completed_bookings': completed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'today_bookings': today_bookings,
                'status_counts': {
                    'pending': pending_bookings,
                    'accepted': accepted_bookings,
                    'completed': completed_bookings,
                    'cancelled': cancelled_bookings,
                }
            },
            'payment_analytics': {
                'total_payments': total_payments_count,
                'total_revenue': total_revenue,
                'average_payment': avg_payment,
                'success_rate': success_rate,
                'successful_payments': total_payments_count,
                'pending_payments': pending_payments,
                'failed_payments': failed_payments,
            },
            'earnings': {
                'total_earnings': total_earnings,
                'total_commission': total_commission,
                'total_paid': total_revenue,
                'earnings_count': earnings_count,
                'today_earnings': today_earnings,
            },
            'recent_bookings': recent_bookings,
            'monthly_revenue': {
                'year': current_year,
                'monthly_data': monthly_data,
                'total_annual_revenue': sum(m['revenue'] for m in monthly_data),
            },
            'metadata': {
                'vendor_id': vendor_id,
                'generated_at': datetime.now().isoformat(),
                'last_refresh': datetime.now().strftime('%H:%M'),
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating vendor dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


@router.get("/today")  # This maps to /api/vendor/dashboard/today
def get_today_summary(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Get today's summary data only"""
    try:
        vendor_id = vendor.id
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Today's bookings
        today_bookings = db.query(Booking).filter(
            and_(
                Booking.serviceprovider_id == vendor_id,
                Booking.scheduled_time >= today_start,
                Booking.scheduled_time <= today_end
            )
        ).all()
        
        # Today's earnings
        today_earnings = db.query(
            func.sum(VendorEarnings.final_amount)
        ).filter(
            and_(
                VendorEarnings.vendor_id == vendor_id,
                func.date(VendorEarnings.earned_at) == today
            )
        ).scalar() or 0
        
        return {
            'success': True,
            'today_bookings_count': len(today_bookings),
            'today_earnings': float(today_earnings),
            'today_date': today.isoformat(),
            'bookings': [
                {
                    'id': b.id,
                    'status': b.status.value,
                    'scheduled_time': b.scheduled_time.isoformat() if b.scheduled_time else None,
                }
                for b in today_bookings
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting today's summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get today's summary: {str(e)}"
        )