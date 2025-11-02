# app/routers/vendor_bank_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.models.service_provider_model import ServiceProvider
from app.schemas.service_provider_schema import BankAccountCreate, BankAccountOut, BankAccountUpdate
from app.crud import vendor_bank_crud
from app.database import SessionLocal
from app.core.security import get_current_vendor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendor", tags=["vendor"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Vendor Bank Account Routes
# =========================

# 1️⃣ Get all bank accounts for current vendor
@router.get("/bank-accounts", response_model=List[BankAccountOut])
def get_my_bank_accounts(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    try:
        accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
        return accounts
    except Exception as e:
        logger.error(f"[BankAccount] Error fetching bank accounts for vendor {current_vendor.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bank accounts."
        )

# 2️⃣ Create new bank account
@router.post("/bank-accounts", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
def add_bank_account(
    bank_data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    try:
        existing_accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
        if any(acc.account_number == bank_data.account_number for acc in existing_accounts):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bank account already exists.")
        account = vendor_bank_crud.create_bank_account(db, current_vendor.id, bank_data)
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error creating bank account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create bank account.")

# 3️⃣ Get specific bank account
@router.get("/bank-accounts/{account_id}", response_model=BankAccountOut)
def get_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    account = vendor_bank_crud.get_bank_account_by_id(db, account_id, current_vendor.id)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account

# 4️⃣ Update bank account
@router.put("/bank-accounts/{account_id}", response_model=BankAccountOut)
def update_bank_account(
    account_id: int,
    update_data: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    account = vendor_bank_crud.update_bank_account(db, account_id, current_vendor.id, update_data)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account

# 5️⃣ Delete bank account
@router.delete("/bank-accounts/{account_id}", status_code=status.HTTP_200_OK)
def delete_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    success = vendor_bank_crud.delete_bank_account(db, account_id, current_vendor.id)
    if not success:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"success": True, "message": "Bank account deleted successfully"}

# 6️⃣ Set bank account as primary
@router.patch("/bank-accounts/{account_id}/set-primary", response_model=BankAccountOut)
def set_primary_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    account = vendor_bank_crud.set_primary_bank_account(db, account_id, current_vendor.id)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account


# =========================
# Dynamic vendor routes (always at the bottom!)
# =========================

@router.get("/{vendor_id}", response_model=BankAccountOut)
def get_vendor_by_id(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    # return vendor with bank accounts or other details as needed
    return vendor
