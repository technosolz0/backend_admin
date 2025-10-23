from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.wallet_schema import WalletCreate, WalletUpdate, WalletOut
from app.crud import wallet_crud

router = APIRouter(prefix="/wallets", tags=["Wallets"])

@router.post("/", response_model=WalletOut)
def create_wallet(wallet: WalletCreate, db: Session = Depends(get_db)):
    try:
        return wallet_crud.create_wallet(
            db=db,
            user_id=wallet.user_id,
            vendor_id=wallet.vendor_id,
            balance=wallet.balance
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{user_id}", response_model=WalletOut)
def get_wallet_by_user_id(user_id: int, db: Session = Depends(get_db)):
    wallet = wallet_crud.get_wallet_by_user_id(db, user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.get("/vendor/{vendor_id}", response_model=WalletOut)
def get_wallet_by_vendor_id(vendor_id: int, db: Session = Depends(get_db)):
    wallet = wallet_crud.get_wallet_by_vendor_id(db, vendor_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.get("/{wallet_id}", response_model=WalletOut)
def get_wallet_by_id(wallet_id: int, db: Session = Depends(get_db)):
    wallet = wallet_crud.get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.put("/{wallet_id}/balance", response_model=WalletOut)
def update_wallet_balance(wallet_id: int, update_data: WalletUpdate, db: Session = Depends(get_db)):
    try:
        wallet = wallet_crud.update_wallet_balance(db, wallet_id, update_data.balance)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[WalletOut])
def get_all_wallets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return wallet_crud.get_all_wallets(db, skip, limit)

@router.delete("/{wallet_id}")
def delete_wallet(wallet_id: int, db: Session = Depends(get_db)):
    success = wallet_crud.delete_wallet(db, wallet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"message": "Wallet deleted successfully"}
