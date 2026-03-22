from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.referral_schema import AdminReferralCodeCreate, AdminReferralCodeUpdate, AdminReferralCodeOut
from app.crud.referral_crud import (
    create_admin_referral_code, get_admin_referral_codes, 
    get_admin_referral_code_by_id, update_admin_referral_code, 
    delete_admin_referral_code, get_admin_referral_code_by_code
)

router = APIRouter(prefix="/admin/referrals", tags=["admin-referrals"])

@router.post("/", response_model=AdminReferralCodeOut)
def create_referral(referral: AdminReferralCodeCreate, db: Session = Depends(get_db)):
    existing = get_admin_referral_code_by_code(db, referral.code)
    if existing:
        raise HTTPException(status_code=400, detail="Referral code already exists")
    return create_admin_referral_code(db, referral)

@router.get("/", response_model=List[AdminReferralCodeOut])
def list_referrals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_admin_referral_codes(db, skip=skip, limit=limit)

@router.get("/{referral_id}", response_model=AdminReferralCodeOut)
def get_referral(referral_id: int, db: Session = Depends(get_db)):
    db_referral = get_admin_referral_code_by_id(db, referral_id)
    if not db_referral:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return db_referral

@router.put("/{referral_id}", response_model=AdminReferralCodeOut)
def update_referral(referral_id: int, referral_update: AdminReferralCodeUpdate, db: Session = Depends(get_db)):
    db_referral = update_admin_referral_code(db, referral_id, referral_update)
    if not db_referral:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return db_referral

@router.delete("/{referral_id}")
def delete_referral(referral_id: int, db: Session = Depends(get_db)):
    success = delete_admin_referral_code(db, referral_id)
    if not success:
        raise HTTPException(status_code=404, detail="Referral code not found")
    return {"message": "Referral code deleted successfully"}
