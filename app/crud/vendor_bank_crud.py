# # app/crud/vendor_bank_crud.py (NEW FILE)

# from sqlalchemy.orm import Session
# from sqlalchemy import and_
# from typing import List, Optional
# from app.models.vendor_bank_account_model import VendorBankAccount
# from app.schemas.service_provider_schema import BankAccountCreate, BankAccountUpdate
# import logging

# logger = logging.getLogger(__name__)


# def get_vendor_bank_accounts(db: Session, vendor_id: int) -> List[VendorBankAccount]:
#     """Vendor ke saare bank accounts fetch karo"""
#     print('vendor ###########################################',vendor_id)
#     return db.query(VendorBankAccount).filter(
#         VendorBankAccount.vendor_id == vendor_id
#     ).order_by(
#         VendorBankAccount.is_primary.desc(), 
#         VendorBankAccount.created_at.desc()
#     ).all()


# def get_bank_account_by_id(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
#     """Specific bank account fetch karo"""
#     return db.query(VendorBankAccount).filter(
#         and_(
#             VendorBankAccount.id == account_id,
#             VendorBankAccount.vendor_id == vendor_id
#         )
#     ).first()


# def get_primary_bank_account(db: Session, vendor_id: int) -> Optional[VendorBankAccount]:
#     """Vendor ka primary bank account fetch karo"""
#     return db.query(VendorBankAccount).filter(
#         and_(
#             VendorBankAccount.vendor_id == vendor_id,
#             VendorBankAccount.is_primary == True
#         )
#     ).first()


# def create_bank_account(db: Session, vendor_id: int, bank_data: BankAccountCreate) -> VendorBankAccount:
#     """Naya bank account add karo"""
    
#     # Check existing accounts
#     existing_accounts = get_vendor_bank_accounts(db, vendor_id)
    
#     # Agar yeh first bank hai ya is_primary=True hai
#     is_primary = bank_data.is_primary or len(existing_accounts) == 0
    
#     # Agar naya account primary hai, purane primary ko remove karo
#     if is_primary:
#         for account in existing_accounts:
#             if account.is_primary:
#                 account.is_primary = False
#         db.commit()
    
#     bank_account = VendorBankAccount(
#         vendor_id=vendor_id,
#         account_holder_name=bank_data.account_holder_name,
#         account_number=bank_data.account_number,
#         ifsc_code=bank_data.ifsc_code,
#         bank_name=bank_data.bank_name,
#         branch_name=bank_data.branch_name,
#         upi_id=bank_data.upi_id,
#         is_primary=is_primary
#     )
    
#     db.add(bank_account)
#     db.commit()
#     db.refresh(bank_account)
    
#     logger.info(f"Bank account created: ID {bank_account.id} for vendor {vendor_id}")
#     return bank_account


# def update_bank_account(
#     db: Session, 
#     account_id: int, 
#     vendor_id: int, 
#     update_data: BankAccountUpdate
# ) -> Optional[VendorBankAccount]:
#     """Bank account update karo"""
    
#     bank_account = get_bank_account_by_id(db, account_id, vendor_id)
#     if not bank_account:
#         return None
    
#     # Agar is_primary update ho raha hai
#     if update_data.is_primary is not None and update_data.is_primary:
#         # Purane primary ko non-primary banao
#         for account in get_vendor_bank_accounts(db, vendor_id):
#             if account.id != account_id and account.is_primary:
#                 account.is_primary = False
    
#     # Update fields
#     update_dict = update_data.dict(exclude_unset=True)
#     for field, value in update_dict.items():
#         setattr(bank_account, field, value)
    
#     db.commit()
#     db.refresh(bank_account)
    
#     logger.info(f"Bank account updated: ID {account_id} for vendor {vendor_id}")
#     return bank_account


# def delete_bank_account(db: Session, account_id: int, vendor_id: int) -> bool:
#     """Bank account delete karo"""
    
#     bank_account = get_bank_account_by_id(db, account_id, vendor_id)
#     if not bank_account:
#         return False
    
#     was_primary = bank_account.is_primary
    
#     db.delete(bank_account)
#     db.commit()
    
#     # Agar deleted account primary tha, next ko primary banao
#     if was_primary:
#         remaining = get_vendor_bank_accounts(db, vendor_id)
#         if remaining:
#             remaining[0].is_primary = True
#             db.commit()
    
#     logger.info(f"Bank account deleted: ID {account_id} for vendor {vendor_id}")
#     return True


# def set_primary_bank_account(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
#     """Kisi account ko primary banao"""
    
#     bank_account = get_bank_account_by_id(db, account_id, vendor_id)
#     if not bank_account:
#         return None
    
#     # Sabhi ko non-primary banao
#     for account in get_vendor_bank_accounts(db, vendor_id):
#         account.is_primary = False
    
#     # Is account ko primary banao
#     bank_account.is_primary = True
    
#     db.commit()
#     db.refresh(bank_account)
    
#     logger.info(f"Bank account set as primary: ID {account_id} for vendor {vendor_id}")
#     return bank_account

# app/crud/vendor_bank_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.vendor_bank_account_model import VendorBankAccount
from app.schemas.service_provider_schema import BankAccountCreate, BankAccountUpdate
import logging

logger = logging.getLogger(__name__)


def get_vendor_bank_accounts(db: Session, vendor_id: int) -> List[VendorBankAccount]:
    """Get all bank accounts for a vendor"""
    return db.query(VendorBankAccount).filter(
        VendorBankAccount.vendor_id == vendor_id
    ).order_by(
        VendorBankAccount.is_primary.desc(), 
        VendorBankAccount.created_at.desc()
    ).all()


def get_bank_account_by_id(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
    """Get specific bank account by ID"""
    return db.query(VendorBankAccount).filter(
        and_(
            VendorBankAccount.id == account_id,
            VendorBankAccount.vendor_id == vendor_id
        )
    ).first()


def get_primary_bank_account(db: Session, vendor_id: int) -> Optional[VendorBankAccount]:
    """Get vendor's primary bank account"""
    return db.query(VendorBankAccount).filter(
        and_(
            VendorBankAccount.vendor_id == vendor_id,
            VendorBankAccount.is_primary == True
        )
    ).first()


def create_bank_account(db: Session, vendor_id: int, bank_data: BankAccountCreate) -> VendorBankAccount:
    """Create new bank account"""
    
    # Check existing accounts
    existing_accounts = get_vendor_bank_accounts(db, vendor_id)
    
    # If first bank or explicitly set as primary
    is_primary = bank_data.is_primary or len(existing_accounts) == 0
    
    # If new account is primary, remove primary from others
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
        is_primary=is_primary,
        is_verified=False  # Always start as unverified
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
    """Update bank account"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return None
    
    # If updating to primary
    if update_data.is_primary is not None and update_data.is_primary:
        # Remove primary from other accounts
        for account in get_vendor_bank_accounts(db, vendor_id):
            if account.id != account_id and account.is_primary:
                account.is_primary = False
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(bank_account, field, value)
    
    # If account details changed, reset verification
    if any(k in update_dict for k in ['account_number', 'ifsc_code', 'account_holder_name']):
        bank_account.is_verified = False
        logger.info(f"Bank account {account_id} marked for re-verification due to detail changes")
    
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account updated: ID {account_id} for vendor {vendor_id}")
    return bank_account


def delete_bank_account(db: Session, account_id: int, vendor_id: int) -> bool:
    """Delete bank account"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return False
    
    was_primary = bank_account.is_primary
    
    db.delete(bank_account)
    db.commit()
    
    # If deleted account was primary, set next as primary
    if was_primary:
        remaining = get_vendor_bank_accounts(db, vendor_id)
        if remaining:
            remaining[0].is_primary = True
            db.commit()
    
    logger.info(f"Bank account deleted: ID {account_id} for vendor {vendor_id}")
    return True


def set_primary_bank_account(db: Session, account_id: int, vendor_id: int) -> Optional[VendorBankAccount]:
    """Set account as primary"""
    
    bank_account = get_bank_account_by_id(db, account_id, vendor_id)
    if not bank_account:
        return None
    
    # Set all to non-primary
    for account in get_vendor_bank_accounts(db, vendor_id):
        account.is_primary = False
    
    # Set this account as primary
    bank_account.is_primary = True
    
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account set as primary: ID {account_id} for vendor {vendor_id}")
    return bank_account


def verify_bank_account(
    db: Session, 
    account_id: int, 
    is_verified: bool,
    admin_notes: Optional[str] = None
) -> Optional[VendorBankAccount]:
    """Verify or reject bank account (Admin function)"""
    
    bank_account = db.query(VendorBankAccount).filter(
        VendorBankAccount.id == account_id
    ).first()
    
    if not bank_account:
        return None
    
    bank_account.is_verified = is_verified
    # If you add admin_notes field to model, set it here
    
    db.commit()
    db.refresh(bank_account)
    
    logger.info(f"Bank account {account_id} verification status: {is_verified}")
    return bank_account