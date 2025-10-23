from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.wallet_model import Wallet
from app.models.user import User
from app.models.service_provider_model import ServiceProvider

def create_wallet(db: Session, user_id: int = None, vendor_id: int = None, balance: float = 0.0):
    # Validate that exactly one of user_id or vendor_id is provided
    if (user_id is None and vendor_id is None) or (user_id is not None and vendor_id is not None):
        raise ValueError("Wallet must belong to either a user OR a vendor, but not both or neither")

    # Validate that the referenced user/vendor exists
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")
        # Check if user already has a wallet
        existing_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if existing_wallet:
            raise ValueError(f"User with id {user_id} already has a wallet")

    if vendor_id:
        vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Service provider with id {vendor_id} does not exist")
        # Check if vendor already has a wallet
        existing_wallet = db.query(Wallet).filter(Wallet.vendor_id == vendor_id).first()
        if existing_wallet:
            raise ValueError(f"Service provider with id {vendor_id} already has a wallet")

    # Validate balance
    if balance < 0:
        raise ValueError("Wallet balance cannot be negative")

    try:
        wallet = Wallet(
            user_id=user_id,
            vendor_id=vendor_id,
            balance=balance
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return wallet
    except IntegrityError:
        db.rollback()
        raise ValueError("Failed to create wallet due to database constraint violation")

def get_wallet_by_user_id(db: Session, user_id: int):
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()

def get_wallet_by_vendor_id(db: Session, vendor_id: int):
    return db.query(Wallet).filter(Wallet.vendor_id == vendor_id).first()

def get_wallet_by_id(db: Session, wallet_id: int):
    return db.query(Wallet).filter(Wallet.id == wallet_id).first()

def update_wallet_balance(db: Session, wallet_id: int, new_balance: float):
    if new_balance < 0:
        raise ValueError("Wallet balance cannot be negative")

    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        wallet.balance = new_balance
        db.commit()
        db.refresh(wallet)
    return wallet

def get_all_wallets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Wallet).offset(skip).limit(limit).all()

def delete_wallet(db: Session, wallet_id: int):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        db.delete(wallet)
        db.commit()
        return True
    return False
