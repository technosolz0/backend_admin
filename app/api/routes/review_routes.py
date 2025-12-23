from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_db
from ...models.review_model import Review
from ...models.user import User
from ...models.booking_model import Booking
from ...crud.review_crud import ReviewCRUD
from ...core.security import get_current_user, get_current_admin

router = APIRouter()

# User routes
@router.post("/")
def submit_review(
    booking_id: int,
    rating: float,
    review_text: Optional[str] = None,
    is_anonymous: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a review for a completed booking"""
    try:
        review_crud = ReviewCRUD(db)

        # Check if user can review this booking
        can_review = review_crud.can_user_review_booking(current_user.id, booking_id)
        if not can_review:
            raise HTTPException(
                status_code=400,
                detail="Cannot submit review: booking not completed or already reviewed"
            )

        # Get booking details to find service provider
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        review = review_crud.create_review(
            booking_id=booking_id,
            user_id=current_user.id,
            service_provider_id=booking.service_provider_id,
            rating=rating,
            review_text=review_text,
            is_anonymous=is_anonymous
        )

        return {
            "message": "Review submitted successfully",
            "review_id": review.id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")

@router.get("/my-reviews")
def get_user_reviews(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's submitted reviews"""
    review_crud = ReviewCRUD(db)
    reviews = review_crud.get_reviews_by_user(current_user.id, skip=skip, limit=limit)

    return {
        "reviews": [
            {
                "id": r.id,
                "booking_id": r.booking_id,
                "service_provider_id": r.service_provider_id,
                "service_provider_name": r.service_provider.business_name if r.service_provider else "Unknown",
                "rating": r.rating,
                "review_text": r.review_text,
                "is_anonymous": r.is_anonymous,
                "admin_approved": r.admin_approved,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat()
            }
            for r in reviews
        ],
        "total": len(reviews)
    }

@router.put("/{review_id}")
def update_review(
    review_id: int,
    rating: Optional[float] = None,
    review_text: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's own review"""
    review_crud = ReviewCRUD(db)

    # Check if review belongs to user
    review = review_crud.get_review_by_id(review_id)
    if not review or review.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found or access denied")

    updated_review = review_crud.update_review(review_id, rating=rating, review_text=review_text)
    if not updated_review:
        raise HTTPException(status_code=500, detail="Failed to update review")

    return {"message": "Review updated successfully"}

@router.delete("/{review_id}")
def delete_user_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user's own review"""
    review_crud = ReviewCRUD(db)

    # Check if review belongs to user
    review = review_crud.get_review_by_id(review_id)
    if not review or review.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found or access denied")

    success = review_crud.delete_review(review_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete review")

    return {"message": "Review deleted successfully"}

# Public routes (no auth required)
@router.get("/provider/{provider_id}")
def get_provider_reviews(
    provider_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get reviews for a service provider (public)"""
    review_crud = ReviewCRUD(db)
    reviews = review_crud.get_reviews_by_service_provider(provider_id, skip=skip, limit=limit)

    # Only return approved reviews for public view
    approved_reviews = [r for r in reviews if r.admin_approved]

    return {
        "reviews": [
            {
                "id": r.id,
                "user_name": "Anonymous" if r.is_anonymous else (r.user.name if r.user else "Unknown"),
                "rating": r.rating,
                "review_text": r.review_text,
                "created_at": r.created_at.isoformat()
            }
            for r in approved_reviews
        ],
        "total": len(approved_reviews)
    }

@router.get("/provider/{provider_id}/stats")
def get_provider_rating_stats(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Get rating statistics for a service provider (public)"""
    review_crud = ReviewCRUD(db)
    stats = review_crud.get_service_provider_rating_stats(provider_id)

    return stats

# Admin routes
@router.get("/admin/all")
def get_all_reviews(
    skip: int = 0,
    limit: int = 100,
    approved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get all reviews for admin"""
    review_crud = ReviewCRUD(db)

    # For now, get recent reviews - you might want to add filtering
    reviews = review_crud.get_recent_reviews(limit=limit)

    if approved is not None:
        reviews = [r for r in reviews if r.admin_approved == approved]

    return {
        "reviews": [
            {
                "id": r.id,
                "booking_id": r.booking_id,
                "user_id": r.user_id,
                "user_name": r.user.name if r.user else "Unknown",
                "service_provider_id": r.service_provider_id,
                "service_provider_name": r.service_provider.business_name if r.service_provider else "Unknown",
                "rating": r.rating,
                "review_text": r.review_text,
                "is_anonymous": r.is_anonymous,
                "admin_approved": r.admin_approved,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat()
            }
            for r in reviews
        ],
        "total": len(reviews)
    }

@router.put("/admin/{review_id}/approve")
def approve_review(
    review_id: int,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Approve or reject a review"""
    review_crud = ReviewCRUD(db)
    success = review_crud.approve_review(review_id, approved)

    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"message": f"Review {'approved' if approved else 'rejected'}"}

@router.delete("/admin/{review_id}")
def delete_review_admin(
    review_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete any review (admin only)"""
    review_crud = ReviewCRUD(db)
    success = review_crud.delete_review(review_id)

    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"message": "Review deleted successfully"}

@router.get("/admin/top-providers")
def get_top_rated_providers(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get top-rated service providers"""
    review_crud = ReviewCRUD(db)
    top_providers = review_crud.get_top_rated_providers(limit=limit)

    return {
        "providers": [
            {
                "provider_id": provider.id,
                "business_name": provider.business_name,
                "average_rating": float(avg_rating),
                "total_reviews": review_count
            }
            for provider, avg_rating, review_count in top_providers
        ]
    }
