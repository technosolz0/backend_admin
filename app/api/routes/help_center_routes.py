from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_db
from ...crud.help_center_crud import HelpCenterCRUD
from ...schemas.help_center_schema import HelpCenter, HelpCenterCreate, HelpCenterUpdate
from ...core.security import get_current_admin

router = APIRouter()

@router.get("/", response_model=List[HelpCenter])
def get_help_faqs(
    target: Optional[str] = Query(None, regex="^(vendor|user)$"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve FAQs filtered by target (vendor/user)"""
    crud = HelpCenterCRUD(db)
    return crud.get_faqs(target=target, skip=skip, limit=limit)

# Admin routes
@router.get("/admin/all", response_model=List[HelpCenter])
def get_all_faqs_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to get all FAQs (active/inactive)"""
    crud = HelpCenterCRUD(db)
    return crud.get_all_faqs_admin(skip=skip, limit=limit)

@router.post("/admin/", response_model=HelpCenter)
def create_faq_admin(
    faq: HelpCenterCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to create a new FAQ"""
    crud = HelpCenterCRUD(db)
    return crud.create_faq(**faq.model_dump())

@router.put("/admin/{faq_id}", response_model=HelpCenter)
def update_faq_admin(
    faq_id: int,
    faq_update: HelpCenterUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to update an existing FAQ"""
    crud = HelpCenterCRUD(db)
    updated_faq = crud.update_faq(faq_id, **faq_update.model_dump(exclude_unset=True))
    if not updated_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return updated_faq

@router.delete("/admin/{faq_id}")
def delete_faq_admin(
    faq_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to delete an FAQ"""
    crud = HelpCenterCRUD(db)
    if not crud.delete_faq(faq_id):
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"message": "FAQ deleted successfully"}
