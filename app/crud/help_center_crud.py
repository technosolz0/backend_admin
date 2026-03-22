from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.help_center_model import HelpCenter
from typing import List, Optional

class HelpCenterCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_faq(self, question: str, answer: str, category: str,
                   is_for_vendor: bool = True, is_for_user: bool = True,
                   priority: int = 0) -> HelpCenter:
        """Create a new FAQ entry"""
        faq = HelpCenter(
            question=question,
            answer=answer,
            category=category,
            is_for_vendor=is_for_vendor,
            is_for_user=is_for_user,
            priority=priority
        )
        self.db.add(faq)
        self.db.commit()
        self.db.refresh(faq)
        return faq

    def get_faqs(self, target: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[HelpCenter]:
        """Get FAQs filtered by target (vendor/user) and active status"""
        query = self.db.query(HelpCenter).filter(HelpCenter.is_active == True)
        
        if target == 'vendor':
            query = query.filter(HelpCenter.is_for_vendor == True)
        elif target == 'user':
            query = query.filter(HelpCenter.is_for_user == True)
            
        return query.order_by(HelpCenter.priority.desc(), HelpCenter.created_at.desc()).offset(skip).limit(limit).all()

    def get_all_faqs_admin(self, skip: int = 0, limit: int = 100) -> List[HelpCenter]:
        """Get all FAQs for admin management"""
        return self.db.query(HelpCenter).order_by(HelpCenter.created_at.desc()).offset(skip).limit(limit).all()

    def get_faq_by_id(self, faq_id: int) -> Optional[HelpCenter]:
        """Get FAQ by ID"""
        return self.db.query(HelpCenter).filter(HelpCenter.id == faq_id).first()

    def update_faq(self, faq_id: int, **kwargs) -> Optional[HelpCenter]:
        """Update FAQ fields"""
        faq = self.get_faq_by_id(faq_id)
        if faq:
            for key, value in kwargs.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)
            self.db.commit()
            self.db.refresh(faq)
            return faq
        return None

    def delete_faq(self, faq_id: int) -> bool:
        """Delete FAQ"""
        faq = self.get_faq_by_id(faq_id)
        if faq:
            self.db.delete(faq)
            self.db.commit()
            return True
        return False
