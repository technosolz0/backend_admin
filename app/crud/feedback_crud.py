from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.feedback_model import Feedback
from ..models.user import User
from typing import List, Optional

class FeedbackCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, user_id: int, subject: str, message: str,
                       category: Optional[str] = None) -> Feedback:
        """Create a new feedback entry"""
        feedback = Feedback(
            user_id=user_id,
            subject=subject,
            message=message,
            category=category
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID"""
        return self.db.query(Feedback).filter(Feedback.id == feedback_id).first()

    def get_all_feedback(self, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """Get all feedback with pagination"""
        return self.db.query(Feedback).offset(skip).limit(limit).all()

    def get_feedback_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Feedback]:
        """Get feedback submitted by a specific user"""
        return self.db.query(Feedback).filter(Feedback.user_id == user_id).offset(skip).limit(limit).all()

    def get_unresolved_feedback(self, skip: int = 0, limit: int = 50) -> List[Feedback]:
        """Get unresolved feedback"""
        return self.db.query(Feedback).filter(Feedback.is_resolved == False).offset(skip).limit(limit).all()

    def get_resolved_feedback(self, skip: int = 0, limit: int = 50) -> List[Feedback]:
        """Get resolved feedback"""
        return self.db.query(Feedback).filter(Feedback.is_resolved == True).offset(skip).limit(limit).all()

    def respond_to_feedback(self, feedback_id: int, admin_response: str, responded_by: int) -> bool:
        """Respond to feedback"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            feedback.admin_response = admin_response
            feedback.responded_by = responded_by
            feedback.responded_at = self.db.func.now()
            feedback.is_resolved = True
            self.db.commit()
            return True
        return False

    def mark_feedback_resolved(self, feedback_id: int, resolved: bool = True) -> bool:
        """Mark feedback as resolved/unresolved"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            feedback.is_resolved = resolved
            if resolved:
                feedback.responded_at = self.db.func.now()
            self.db.commit()
            return True
        return False

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete feedback"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            self.db.delete(feedback)
            self.db.commit()
            return True
        return False

    def update_feedback(self, feedback_id: int, **kwargs) -> Optional[Feedback]:
        """Update feedback fields"""
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            for key, value in kwargs.items():
                if hasattr(feedback, key):
                    setattr(feedback, key, value)
            self.db.commit()
            self.db.refresh(feedback)
            return feedback
        return None

    def get_feedback_stats(self) -> dict:
        """Get feedback statistics"""
        total = self.db.query(Feedback).count()
        resolved = self.db.query(Feedback).filter(Feedback.is_resolved == True).count()
        unresolved = total - resolved

        return {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": (resolved / total * 100) if total > 0 else 0
        }
