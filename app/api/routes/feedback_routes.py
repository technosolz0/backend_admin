from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...models.feedback_model import Feedback
from ...models.user import User
from ...crud.feedback_crud import FeedbackCRUD
from ...core.security import get_current_user, get_current_admin_user

router = APIRouter()

# User routes
@router.post("/")
def submit_feedback(
    subject: str,
    message: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback (for users)"""
    try:
        feedback_crud = FeedbackCRUD(db)
        feedback = feedback_crud.create_feedback(
            user_id=current_user.id,
            subject=subject,
            message=message,
            category=category
        )

        return {
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/my-feedback")
def get_user_feedback(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's own feedback"""
    feedback_crud = FeedbackCRUD(db)
    feedback_list = feedback_crud.get_feedback_by_user(current_user.id, skip=skip, limit=limit)

    return {
        "feedback": [
            {
                "id": f.id,
                "subject": f.subject,
                "message": f.message,
                "category": f.category,
                "is_resolved": f.is_resolved,
                "admin_response": f.admin_response,
                "responded_at": f.responded_at.isoformat() if f.responded_at else None,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat()
            }
            for f in feedback_list
        ],
        "total": len(feedback_list)
    }

# Admin routes
@router.get("/admin/all")
def get_all_feedback(
    skip: int = 0,
    limit: int = 100,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get all feedback for admin"""
    feedback_crud = FeedbackCRUD(db)

    if resolved is True:
        feedback_list = feedback_crud.get_resolved_feedback(skip=skip, limit=limit)
    elif resolved is False:
        feedback_list = feedback_crud.get_unresolved_feedback(skip=skip, limit=limit)
    else:
        feedback_list = feedback_crud.get_all_feedback(skip=skip, limit=limit)

    return {
        "feedback": [
            {
                "id": f.id,
                "user_id": f.user_id,
                "user_name": f.user.name if f.user else "Unknown",
                "user_email": f.user.email if f.user else "Unknown",
                "subject": f.subject,
                "message": f.message,
                "category": f.category,
                "is_resolved": f.is_resolved,
                "admin_response": f.admin_response,
                "responded_at": f.responded_at.isoformat() if f.responded_at else None,
                "responded_by": f.responded_by,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat()
            }
            for f in feedback_list
        ],
        "total": len(feedback_list)
    }

@router.get("/admin/{feedback_id}")
def get_feedback_detail(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get feedback detail for admin"""
    feedback_crud = FeedbackCRUD(db)
    feedback = feedback_crud.get_feedback_by_id(feedback_id)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "user_name": feedback.user.name if feedback.user else "Unknown",
        "user_email": feedback.user.email if feedback.user else "Unknown",
        "subject": feedback.subject,
        "message": feedback.message,
        "category": feedback.category,
        "is_resolved": feedback.is_resolved,
        "admin_response": feedback.admin_response,
        "responded_at": feedback.responded_at.isoformat() if feedback.responded_at else None,
        "responded_by": feedback.responded_by,
        "created_at": feedback.created_at.isoformat(),
        "updated_at": feedback.updated_at.isoformat()
    }

@router.post("/admin/{feedback_id}/respond")
def respond_to_feedback(
    feedback_id: int,
    response: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Respond to feedback"""
    feedback_crud = FeedbackCRUD(db)
    success = feedback_crud.respond_to_feedback(feedback_id, response, current_admin.id)

    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"message": "Response submitted successfully"}

@router.put("/admin/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    resolved: bool,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Update feedback resolution status"""
    feedback_crud = FeedbackCRUD(db)
    success = feedback_crud.mark_feedback_resolved(feedback_id, resolved)

    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"message": f"Feedback marked as {'resolved' if resolved else 'unresolved'}"}

@router.delete("/admin/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete feedback"""
    feedback_crud = FeedbackCRUD(db)
    success = feedback_crud.delete_feedback(feedback_id)

    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"message": "Feedback deleted successfully"}

@router.get("/admin/stats")
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get feedback statistics"""
    feedback_crud = FeedbackCRUD(db)
    stats = feedback_crud.get_feedback_stats()

    return stats
