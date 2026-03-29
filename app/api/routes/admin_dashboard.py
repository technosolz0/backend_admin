from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.booking_model import Booking
from app.models.user import User
from app.models.service_provider_model import ServiceProvider
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.core.security import get_current_user

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])

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

@router.get("/", dependencies=[Depends(get_super_admin)])
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    
    # 1. Total Counts
    total_users = db.query(User).count()
    total_vendors = db.query(ServiceProvider).count()
    total_bookings = db.query(Booking).count()
    
    # 2. Last 5 Recent Bookings
    recent_bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(5).all()
    
    # 3. Weekly Data (Last 7 Days)
    weekly_series = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        count = db.query(Booking).filter(
            func.date(Booking.created_at) == day.date()
        ).count()
        weekly_series.append({
            "date": day.strftime("%b %d"),
            "count": count
        })
        
    # 4. Monthly Data (Last 12 Months)
    monthly_series = []
    for i in range(11, -1, -1):
        # Calculate first day of the month i months ago
        first_day = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        # Approximate month logic
        month_label = first_day.strftime("%b %Y")
        count = db.query(Booking).filter(
            extract('month', Booking.created_at) == first_day.month,
            extract('year', Booking.created_at) == first_day.year
        ).count()
        monthly_series.append({
            "month": month_label,
            "count": count
        })

    # 5. Yearly Data (Last 3 Years)
    yearly_series = []
    for i in range(2, -1, -1):
        year = now.year - i
        count = db.query(Booking).filter(
            extract('year', Booking.created_at) == year
        ).count()
        yearly_series.append({
            "year": str(year),
            "count": count
        })
    
    # 6. Category-wise stats
    category_stats_raw = db.query(
        Booking.category_id, 
        Category.name, 
        func.count(Booking.id)
    ).join(Category, Booking.category_id == Category.id).group_by(Booking.category_id, Category.name).all()
    
    category_wise = [
        {"name": row[1], "count": row[2]} 
        for row in category_stats_raw
    ]
    
    # 7. Subcategory-wise stats
    subcategory_stats_raw = db.query(
        Booking.subcategory_id, 
        SubCategory.name, 
        func.count(Booking.id)
    ).join(SubCategory, Booking.subcategory_id == SubCategory.id).group_by(Booking.subcategory_id, SubCategory.name).all()
    
    subcategory_wise = [
        {"name": row[1], "count": row[2]} 
        for row in subcategory_stats_raw
    ]
    
    # Format recent bookings for response
    formatted_recent = []
    for b in recent_bookings:
        formatted_recent.append({
            "id": b.id,
            "customerName": b.user.name if b.user else "Unknown User",
            "serviceName": b.subcategory.name if b.subcategory else (b.category.name if b.category else "Unknown Service"),
            "date": b.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": b.status.value if hasattr(b.status, 'value') else str(b.status)
        })

    return {
        "summary": {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_bookings": total_bookings,
        },
        "weekly_series": weekly_series,
        "monthly_series": monthly_series,
        "yearly_series": yearly_series,
        "recent_bookings": formatted_recent,
        "category_wise": category_wise,
        "subcategory_wise": subcategory_wise
    }
