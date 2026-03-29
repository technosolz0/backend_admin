from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.payment_model import Payment
from app.models.booking_model import Booking
from app.models.user import User
from app.models.sub_category import SubCategory
from app.core.security import get_current_user

router = APIRouter(prefix="/admin/payments", tags=["Admin Payments"])

# 🔌 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Superadmin-only Dependency
def get_super_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions (Admin only)",
        )
    return current_user

@router.get("/stats", dependencies=[Depends(get_super_admin)])
def get_admin_payment_stats(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    
    # 1. Totals
    total_transactions = db.query(Payment).count()
    successful_payments = db.query(Payment).filter(Payment.status == "SUCCESS").count()
    failed_payments = db.query(Payment).filter(Payment.status == "FAILED").count()
    pending_payments = db.query(Payment).filter(Payment.status == "PENDING").count()
    
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "SUCCESS").scalar() or 0
    pending_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "PENDING").scalar() or 0
    
    # 2. Weekly Income (Last 7 Days)
    weekly_series = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        income = db.query(func.sum(Payment.amount)).filter(
            func.date(Payment.created_at) == day.date(),
            Payment.status == "SUCCESS"
        ).scalar() or 0
        weekly_series.append({
            "date": day.strftime("%b %d"),
            "amount": float(income)
        })
        
    # 3. Monthly Income (Last 12 Months)
    monthly_series = []
    for i in range(11, -1, -1):
        # Calculate approximate month logic
        first_day = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_label = first_day.strftime("%b %Y")
        income = db.query(func.sum(Payment.amount)).filter(
            extract('month', Payment.created_at) == first_day.month,
            extract('year', Payment.created_at) == first_day.year,
            Payment.status == "SUCCESS"
        ).scalar() or 0
        monthly_series.append({
            "month": month_label,
            "amount": float(income)
        })

    # 4. Yearly Income (Last 3 Years)
    yearly_series = []
    for i in range(2, -1, -1):
        year = now.year - i
        income = db.query(func.sum(Payment.amount)).filter(
            extract('year', Payment.created_at) == year,
            Payment.status == "SUCCESS"
        ).scalar() or 0
        yearly_series.append({
            "year": str(year),
            "amount": float(income)
        })
        
    # 5. All Transactions Table (Limit to 100 for performance)
    transactions_raw = db.query(Payment).order_by(Payment.created_at.desc()).limit(100).all()
    formatted_transactions = []
    for t in transactions_raw:
        formatted_transactions.append({
            "transactionId": t.razorpay_payment_id or f"TXN{t.id}",
            "bookingId": str(t.booking_id),
            "customerName": t.booking.user.name if t.booking and t.booking.user else "Unknown User",
            "serviceName": t.booking.subcategory.name if t.booking and t.booking.subcategory else (
                t.booking.category.name if t.booking and t.booking.category else "Generic Service"
            ),
            "amount": float(t.amount),
            "date": t.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": "Completed" if t.status == "SUCCESS" else ("Pending" if t.status == "PENDING" else "Failed")
        })

    return {
        "summary": {
            "totalTransactions": total_transactions,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "total_revenue": float(total_revenue),
            "pending_revenue": float(pending_revenue),
        },
        "weekly_series": weekly_series,
        "monthly_series": monthly_series,
        "yearly_series": yearly_series,
        "transactions": formatted_transactions
    }
