# app/crud/vendor_bank_crud.py (NEW FILE)

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.vendor_bank_account_model import VendorBankAccount
from app.schemas.service_provider_schema import BankAccountCreate, BankAccountUpdate
import logging

logger = logging.getLogger(__name__)


def get_vendor_bank_accounts(db: Session, vendor_id: int) -> List[VendorBankAccount]:
    """Vendor ke saare bank accounts fetch karo"""
    print('vendor ###########################################',vendor_id)
    return db.query(VendorBankAccount).filter(
        VendorBankAccount.vendor_id == vendor_id
    ).order_by(
        VendorBankAccount.is_primary.desc(), 
        VendorBankAccount.created_at.desc()
    ).all()


def get_bank_account_by_id(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
    """Specific bank account fetch karo"""
    return db.query(VendorBankAccount).filter(
        and_(
            VendorBankAccount.id == account_id,
            VendorBankAccount.vendor_id == vendor_id
        )
    ).first()


def get_primary_bank_account(db: Session, vendor_id: int) -> Optional[VendorBankAccount]:
    """Vendor ka primary bank account fetch karo"""
    return db.query(VendorBankAccount).filter(
        and_(
            VendorBankAccount.vendor_id == vendor_id,
            VendorBankAccount.is_primary == True
        )
    ).first()


def create_bank_account(db: Session, vendor_id: int, bank_data: BankAccountCreate) -> VendorBankAccount:
    """Naya bank account add karo"""
    
    # Check existing accounts
    existing_accounts = get_vendor_bank_accounts(db, vendor_id)
    
    # Agar yeh first bank hai ya is_primary=True hai
    is_primary = bank_data.is_primary or len(existing_accounts) == 0
    
    # Agar naya account primary hai, purane primary ko remove karo
    if is_primary:
        for account in existing_accounts:
            if account.is_primary:
                account.is_primary = False
        db.commit()
    
    bank_account = VendorBankAccount(
        vendor_id=vendor_id,
        account_holder_name=bank_data.account_holder_name,
        account_number=bank_data.account_number,
        ifsc_code=bank_data.ifsc_code,
        bank_name=bank_data.bank_name,
        branch_name=bank_data.branch_name,
        upi_id=bank_data.upi_id,
        is_primary=is_primary
    )
    
    db.add(bank_account)
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account created: ID {bank_account.id} for vendor {vendor_id}")
    return bank_account


def update_bank_account(
    db: Session, 
    account_id: int, 
    vendor_id: int, 
    update_data: BankAccountUpdate
) -> Optional[VendorBankAccount]:
    """Bank account update karo"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return None
    
    # Agar is_primary update ho raha hai
    if update_data.is_primary is not None and update_data.is_primary:
        # Purane primary ko non-primary banao
        for account in get_vendor_bank_accounts(db, vendor_id):
            if account.id != account_id and account.is_primary:
                account.is_primary = False
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(bank_account, field, value)
    
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account updated: ID {account_id} for vendor {vendor_id}")
    return bank_account


def delete_bank_account(db: Session, account_id: int, vendor_id: int) -> bool:
    """Bank account delete karo"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return False
    
    was_primary = bank_account.is_primary
    
    db.delete(bank_account)
    db.commit()
    
    # Agar deleted account primary tha, next ko primary banao
    if was_primary:
        remaining = get_vendor_bank_accounts(db, vendor_id)
        if remaining:
            remaining[0].is_primary = True
            db.commit()
    
    logger.info(f"Bank account deleted: ID {account_id} for vendor {vendor_id}")
    return True


def set_primary_bank_account(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
    """Kisi account ko primary banao"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return None
    
    # Sabhi ko non-primary banao
    for account in get_vendor_bank_accounts(db, vendor_id):
        account.is_primary = False
    
    # Is account ko primary banao
    bank_account.is_primary = True
    
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account set as primary: ID {account_id} for vendor {vendor_id}")
    return bank_account