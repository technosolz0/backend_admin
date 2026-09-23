# # app/routers/vendor_bank_router.py

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# import logging

# from app.models.service_provider_model import ServiceProvider
# from app.schemas.service_provider_schema import BankAccountCreate, BankAccountOut, BankAccountUpdate
# from app.crud import vendor_bank_crud
# from app.database import SessionLocal
# from app.core.security import get_current_vendor

# logger = logging.getLogger(__name__)

# # IMPORTANT: Don't use /vendor prefix here if you're including this router with a prefix
# router = APIRouter(tags=["vendor-bank-accounts"])

# # -------------------
# # DB dependency
# # -------------------
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # -------------------
# # 1️⃣ Get all bank accounts for current vendor
# # -------------------
# @router.get("/bank-accounts", response_model=List[BankAccountOut])
# def get_my_bank_accounts(
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Get all bank accounts for the authenticated vendor
#     """
#     try:
#         accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
#         return accounts
#     except Exception as e:
#         logger.error(f"[BankAccount] Error fetching bank accounts for vendor {current_vendor.id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to fetch bank accounts."
#         )


# # -------------------
# # 2️⃣ Create new bank account
# # -------------------
# @router.post("/bank-accounts", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
# def add_bank_account(
#     bank_data: BankAccountCreate,
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Create a new bank account for the authenticated vendor
#     """
#     try:
#         existing_accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
#         if any(acc.account_number == bank_data.account_number for acc in existing_accounts):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="Bank account with this account number already exists."
#             )
#         account = vendor_bank_crud.create_bank_account(db, current_vendor.id, bank_data)
#         return account
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[BankAccount] Error creating bank account: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to create bank account."
#         )


# # -------------------
# # 3️⃣ Get specific bank account
# # -------------------
# @router.get("/bank-accounts/{account_id}", response_model=BankAccountOut)
# def get_bank_account(
#     account_id: int,
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Get a specific bank account by ID
#     """
#     account = vendor_bank_crud.get_bank_account_by_id(db, account_id, current_vendor.id)
#     if not account:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Bank account not found"
#         )
#     return account


# # -------------------
# # 4️⃣ Update bank account
# # -------------------
# @router.put("/bank-accounts/{account_id}", response_model=BankAccountOut)
# def update_bank_account(
#     account_id: int,
#     update_data: BankAccountUpdate,
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Update a bank account
#     """
#     try:
#         account = vendor_bank_crud.update_bank_account(db, account_id, current_vendor.id, update_data)
#         if not account:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Bank account not found"
#             )
#         return account
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[BankAccount] Error updating bank account {account_id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to update bank account."
#         )


# # -------------------
# # 5️⃣ Delete bank account
# # -------------------
# @router.delete("/bank-accounts/{account_id}", status_code=status.HTTP_200_OK)
# def delete_bank_account(
#     account_id: int,
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Delete a bank account
#     """
#     try:
#         success = vendor_bank_crud.delete_bank_account(db, account_id, current_vendor.id)
#         if not success:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Bank account not found"
#             )
#         return {"success": True, "message": "Bank account deleted successfully"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[BankAccount] Error deleting bank account {account_id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete bank account."
#         )


# # -------------------
# # 6️⃣ Set bank account as primary
# # -------------------
# @router.patch("/bank-accounts/{account_id}/set-primary", response_model=BankAccountOut)
# def set_primary_bank_account(
#     account_id: int,
#     db: Session = Depends(get_db),
#     current_vendor: ServiceProvider = Depends(get_current_vendor)
# ):
#     """
#     Set a bank account as primary
#     """
#     try:
#         account = vendor_bank_crud.set_primary_bank_account(db, account_id, current_vendor.id)
#         if not account:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Bank account not found"
#             )
#         return account
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[BankAccount] Error setting primary bank account {account_id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to set primary bank account."
#         )


# app/routers/vendor_bank_router.py
# app/routers/vendor_bank_router.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import os
import shutil
from datetime import datetime

from app.models.service_provider_model import ServiceProvider
from app.models.vendor_bank_account_model import VendorBankAccount
from app.schemas.service_provider_schema import BankAccountCreate, BankAccountOut, BankAccountUpdate
from app.crud import vendor_bank_crud
from app.database import SessionLocal
from app.core.security import get_current_vendor
from app.core.security import get_current_admin
from app.core.firebase_storage import upload_to_firebase, delete_from_firebase

logger = logging.getLogger(__name__)

# ✅ UPDATED PREFIX
router = APIRouter(prefix="/banks", tags=["vendor-bank-accounts"])

# Configure upload directory
UPLOAD_DIR = "uploads/bank_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
# Pydantic Models
# -------------------
class BankVerificationRequest(BaseModel):
    is_verified: bool
    admin_notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════
#                    VENDOR ENDPOINTS
# ═══════════════════════════════════════════════════════════

# -------------------
# 1️⃣ Get all bank accounts for current vendor
# -------------------
@router.get("/accounts", response_model=List[BankAccountOut])
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
@router.post("/accounts", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
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
@router.get("/accounts/{account_id}", response_model=BankAccountOut)
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
@router.put("/accounts/{account_id}", response_model=BankAccountOut)
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
@router.delete("/accounts/{account_id}", status_code=status.HTTP_200_OK)
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
@router.patch("/accounts/{account_id}/set-primary", response_model=BankAccountOut)
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


# -------------------
# 7️⃣ Upload bank document
# -------------------
@router.post("/accounts/{account_id}/upload-document", response_model=BankAccountOut)
async def upload_bank_document(
    account_id: int,
    bank_doc_type: str = Form(..., description="Type: passbook, cancelled_cheque, bank_statement"),
    bank_doc_number: str = Form(..., description="Document number/reference"),
    bank_document: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """
    Upload bank proof document (passbook, cancelled cheque, etc.)
    """
    try:
        # Verify account belongs to vendor
        account = vendor_bank_crud.get_bank_account_by_id(db, account_id, current_vendor.id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )

        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(bank_document.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Validate file size (5MB max)
        file_content = await bank_document.read()
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum 5MB allowed."
            )

        # Delete old document from Firebase if exists
        if account.bank_doc_url:
            delete_from_firebase(account.bank_doc_url)

        # Upload to Firebase Storage under dedicated vendor folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = f"vendors/{current_vendor.id}/bank_accounts/{account_id}"
        download_url = upload_to_firebase(
            file_content,
            folder_path=folder,
            custom_filename=f"bank_{current_vendor.id}_{account_id}_{timestamp}{file_ext}"
        )

        # Update account with document info
        account.bank_doc_type = bank_doc_type
        account.bank_doc_number = bank_doc_number
        account.bank_doc_url = download_url
        account.is_verified = False  # Set to pending verification
        
        db.commit()
        db.refresh(account)

        logger.info(f"Bank document uploaded for account {account_id}")
        return account

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BankAccount] Error uploading document for account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload bank document."
        )


# ═══════════════════════════════════════════════════════════
#                    ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════

# -------------------
# 8️⃣ Get all pending bank accounts (ADMIN)
# -------------------
@router.get("/admin/accounts/pending", response_model=List[BankAccountOut], tags=["admin-bank-verification"])
def admin_get_pending_bank_accounts(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get all unverified bank accounts (Admin only)
    """
    try:
        accounts = db.query(VendorBankAccount).filter(
            VendorBankAccount.is_verified == False,
            VendorBankAccount.bank_doc_url.isnot(None)
        ).order_by(
            VendorBankAccount.created_at.desc()
        ).all()
        
        return accounts
    except Exception as e:
        logger.error(f"[Admin] Error fetching pending bank accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending bank accounts."
        )


# -------------------
# 9️⃣ Get all bank accounts with filters (ADMIN)
# -------------------
@router.get("/admin/accounts", response_model=List[BankAccountOut], tags=["admin-bank-verification"])
def admin_get_all_bank_accounts(
    vendor_id: Optional[int] = None,
    is_verified: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get all bank accounts with optional filters (Admin only)
    """
    try:
        query = db.query(VendorBankAccount)
        
        if vendor_id:
            query = query.filter(VendorBankAccount.vendor_id == vendor_id)
        
        if is_verified is not None:
            query = query.filter(VendorBankAccount.is_verified == is_verified)
        
        accounts = query.order_by(
            VendorBankAccount.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return accounts
    except Exception as e:
        logger.error(f"[Admin] Error fetching bank accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bank accounts."
        )


# -------------------
# 🔟 Get specific bank account details (ADMIN)
# -------------------
@router.get("/admin/accounts/{account_id}", response_model=BankAccountOut, tags=["admin-bank-verification"])
def admin_get_bank_account_details(
    account_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get specific bank account details (Admin only)
    """
    account = db.query(VendorBankAccount).filter(
        VendorBankAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    return account


# -------------------
# 1️⃣1️⃣ Verify/Reject bank account (ADMIN)
# -------------------
@router.patch("/admin/accounts/{account_id}/verify", response_model=BankAccountOut, tags=["admin-bank-verification"])
def admin_verify_bank_account(
    account_id: int,
    verification_data: BankVerificationRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Verify or reject bank account verification (Admin only)
    """
    try:
        account = vendor_bank_crud.verify_bank_account(
            db=db,
            account_id=account_id,
            is_verified=verification_data.is_verified,
            admin_notes=verification_data.admin_notes
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )
        
        status_text = "verified" if verification_data.is_verified else "rejected"
        logger.info(f"[Admin] Bank account {account_id} {status_text}")
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Error verifying account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify bank account."
        )


# -------------------
# 1️⃣2️⃣ Get verification statistics (ADMIN)
# -------------------
@router.get("/admin/accounts/stats/verification", tags=["admin-bank-verification"])
def admin_get_verification_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get bank account verification statistics (Admin only)
    """
    try:
        total = db.query(VendorBankAccount).count()
        verified = db.query(VendorBankAccount).filter(
            VendorBankAccount.is_verified == True
        ).count()
        pending = db.query(VendorBankAccount).filter(
            VendorBankAccount.is_verified == False,
            VendorBankAccount.bank_doc_url.isnot(None)
        ).count()
        without_docs = db.query(VendorBankAccount).filter(
            VendorBankAccount.bank_doc_url.is_(None)
        ).count()
        
        return {
            "total_accounts": total,
            "verified": verified,
            "pending_verification": pending,
            "without_documents": without_docs,
            "verification_rate": round((verified / total * 100), 2) if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"[Admin] Error fetching verification stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch verification statistics."
        )