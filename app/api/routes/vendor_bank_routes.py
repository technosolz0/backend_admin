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

# IMPORTANT: Don't use /vendor prefix here if you're including this router with a prefix
router = APIRouter(tags=["vendor-bank-accounts"])

# -------------------
# DB dependency
# -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------
# 1️⃣ Get all bank accounts for current vendor
# -------------------
@router.get("/bank-accounts", response_model=List[BankAccountOut])
def get_my_bank_accounts(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Get all bank accounts for the authenticated vendor
    """
    try:
        accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
        return accounts
    except Exception as e:
        logger.error(f"[BankAccount] Error fetching bank accounts for vendor {current_vendor.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bank accounts."
        )


# -------------------
# 2️⃣ Create new bank account
# -------------------
@router.post("/bank-accounts", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
def add_bank_account(
    bank_data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Create a new bank account for the authenticated vendor
    """
    try:
        existing_accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
        if any(acc.account_number == bank_data.account_number for acc in existing_accounts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Bank account with this account number already exists."
            )
        account = vendor_bank_crud.create_bank_account(db, current_vendor.id, bank_data)
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error creating bank account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bank account."
        )


# -------------------
# 3️⃣ Get specific bank account
# -------------------
@router.get("/bank-accounts/{account_id}", response_model=BankAccountOut)
def get_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Get a specific bank account by ID
    """
    account = vendor_bank_crud.get_bank_account_by_id(db, account_id, current_vendor.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    return account


# -------------------
# 4️⃣ Update bank account
# -------------------
@router.put("/bank-accounts/{account_id}", response_model=BankAccountOut)
def update_bank_account(
    account_id: int,
    update_data: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Update a bank account
    """
    try:
        account = vendor_bank_crud.update_bank_account(db, account_id, current_vendor.id, update_data)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error updating bank account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bank account."
        )


# -------------------
# 5️⃣ Delete bank account
# -------------------
@router.delete("/bank-accounts/{account_id}", status_code=status.HTTP_200_OK)
def delete_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Delete a bank account
    """
    try:
        success = vendor_bank_crud.delete_bank_account(db, account_id, current_vendor.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )
        return {"success": True, "message": "Bank account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error deleting bank account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bank account."
        )


# -------------------
# 6️⃣ Set bank account as primary
# -------------------
@router.patch("/bank-accounts/{account_id}/set-primary", response_model=BankAccountOut)
def set_primary_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Set a bank account as primary
    """
    try:
        account = vendor_bank_crud.set_primary_bank_account(db, account_id, current_vendor.id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error setting primary bank account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary bank account."
        )