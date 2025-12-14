from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models.review_model import Review
from ..models.user import User
from ..models.service_provider_model import ServiceProvider
from ..models.booking_model import Booking
from typing import List, Optional, Tuple

class ReviewCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_review(self, booking_id: int, user_id: int, service_provider_id: int,
                     rating: float, review_text: Optional[str] = None,
                     is_anonymous: bool = False) -> Review:
        """Create a new review"""
        review = Review(
            booking_id=booking_id,
            user_id=user_id,
            service_provider_id=service_provider_id,
            rating=rating,
            review_text=review_text,
            is_anonymous=is_anonymous
        )

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        """Get review by ID"""
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_reviews_by_booking(self, booking_id: int) -> List[Review]:
        """Get all reviews for a specific booking"""
        return self.db.query(Review).filter(Review.booking_id == booking_id).all()

    def get_reviews_by_service_provider(self, service_provider_id: int,
                                       skip: int = 0, limit: int = 50) -> List[Review]:
        """Get reviews for a service provider"""
        return self.db.query(Review).filter(
            Review.service_provider_id == service_provider_id
        ).offset(skip).limit(limit).all()

    def get_reviews_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Review]:
        """Get reviews submitted by a user"""
        return self.db.query(Review).filter(Review.user_id == user_id).offset(skip).limit(limit).all()

    def get_service_provider_rating_stats(self, service_provider_id: int) -> dict:
        """Get rating statistics for a service provider"""
        reviews = self.db.query(Review).filter(Review.service_provider_id == service_provider_id).all()

        if not reviews:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        total_reviews = len(reviews)
        average_rating = sum(review.rating for review in reviews) / total_reviews

        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[int(review.rating)] += 1

        return {
            "total_reviews": total_reviews,
            "average_rating": round(average_rating, 1),
            "rating_distribution": rating_distribution
        }

    def update_review(self, review_id: int, rating: Optional[float] = None,
                     review_text: Optional[str] = None) -> Optional[Review]:
        """Update review rating and/or text"""
        review = self.get_review_by_id(review_id)
        if review:
            if rating is not None:
                review.rating = rating
            if review_text is not None:
                review.review_text = review_text
            self.db.commit()
            self.db.refresh(review)
            return review
        return None

    def delete_review(self, review_id: int) -> bool:
        """Delete a review"""
        review = self.get_review_by_id(review_id)
        if review:
            self.db.delete(review)
            self.db.commit()
            return True
        return False

    def can_user_review_booking(self, user_id: int, booking_id: int) -> bool:
        """Check if user can review a booking (booking completed and no existing review)"""
        # Check if booking exists and is completed
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id,
            Booking.status == "completed"
        ).first()

        if not booking:
            return False

        # Check if review already exists
        existing_review = self.db.query(Review).filter(
            Review.booking_id == booking_id,
            Review.user_id == user_id
        ).first()

        return existing_review is None

    def get_recent_reviews(self, limit: int = 10) -> List[Review]:
        """Get recent reviews across all service providers"""
        return self.db.query(Review).order_by(Review.created_at.desc()).limit(limit).all()

    def get_top_rated_providers(self, limit: int = 10) -> List[Tuple[ServiceProvider, float, int]]:
        """Get top-rated service providers with their average rating and review count"""
        from sqlalchemy import func

        # Subquery to get average ratings and counts
        rating_stats = self.db.query(
            Review.service_provider_id,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).group_by(Review.service_provider_id).subquery()

        # Join with service providers and order by average rating
        result = self.db.query(
            ServiceProvider,
            rating_stats.c.avg_rating,
            rating_stats.c.review_count
        ).join(
            rating_stats,
            ServiceProvider.id == rating_stats.c.service_provider_id
        ).filter(
            rating_stats.c.review_count >= 5  # Only providers with at least 5 reviews
        ).order_by(
            rating_stats.c.avg_rating.desc()
        ).limit(limit).all()

        return result

    def approve_review(self, review_id: int, approved: bool = True) -> bool:
        """Approve or reject a review (for admin moderation)"""
        review = self.get_review_by_id(review_id)
        if review:
            review.admin_approved = approved
            self.db.commit()
            return True
        return False
