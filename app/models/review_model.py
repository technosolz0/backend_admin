from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who gave the review
    service_provider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    rating = Column(Float, nullable=False)  # 1.0 to 5.0
    review_text = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    admin_approved = Column(Boolean, default=True)  # Auto-approve for now
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id], back_populates="reviews")
    service_provider = relationship("ServiceProvider", back_populates="reviews")

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1.0 AND rating <= 5.0', name='rating_range'),
    )

    def __repr__(self):
        return f"<Review(id={self.id}, booking_id={self.booking_id}, rating={self.rating})>"
