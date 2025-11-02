# app/api/routes/vendor_routes.py

# Add these imports at the top
from app.crud import vendor_bank_crud
from app.schemas.service_provider_schema import BankAccountCreate, BankAccountUpdate, BankAccountOut

# ==================== BANK ACCOUNT ROUTES ====================

@router.get("/bank-accounts", response_model=List[BankAccountOut])
def get_my_bank_accounts(
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Vendor ke saare bank accounts fetch karo"""
    try:
        accounts = vendor_bank_crud.get_vendor_bank_accounts(db, current_vendor.id)
        return accounts
    except Exception as e:
        logger.error(f"Error fetching bank accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch bank accounts")


@router.post("/bank-accounts", response_model=BankAccountOut)
def add_bank_account(
    bank_data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Naya bank account add karo"""
    try:
        account = vendor_bank_crud.create_bank_account(db, current_vendor.id, bank_data)
        return account
    except Exception as e:
        logger.error(f"Error creating bank account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create bank account")


@router.get("/bank-accounts/{account_id}", response_model=BankAccountOut)
def get_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Specific bank account fetch karo"""
    account = vendor_bank_crud.get_bank_account_by_id(db, account_id, current_vendor.id)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account


@router.put("/bank-accounts/{account_id}", response_model=BankAccountOut)
def update_bank_account(
    account_id: int,
    update_data: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Bank account update karo"""
    account = vendor_bank_crud.update_bank_account(db, account_id, current_vendor.id, update_data)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account


@router.delete("/bank-accounts/{account_id}")
def delete_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Bank account delete karo"""
    success = vendor_bank_crud.delete_bank_account(db, account_id, current_vendor.id)
    if not success:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"success": True, "message": "Bank account deleted successfully"}


@router.patch("/bank-accounts/{account_id}/set-primary", response_model=BankAccountOut)
def set_primary_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Bank account ko primary banao"""
    account = vendor_bank_crud.set_primary_bank_account(db, account_id, current_vendor.id)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account