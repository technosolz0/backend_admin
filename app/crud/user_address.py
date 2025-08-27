from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user_address import UserAddress
from app.schemas import user_address_schema

def create_address(db: Session, user_id: int, data: user_address_schema.UserAddressCreate) -> UserAddress:
    # If marked as default, reset all other addresses
    if data.is_default:
        db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": False})

    address = UserAddress(user_id=user_id, **data.dict())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

def get_addresses(db: Session, user_id: int) -> List[UserAddress]:
    return db.query(UserAddress).filter(UserAddress.user_id == user_id).all()

def get_address(db: Session, address_id: int, user_id: int) -> Optional[UserAddress]:
    return db.query(UserAddress).filter(UserAddress.id == address_id, UserAddress.user_id == user_id).first()

def update_address(db: Session, address_id: int, user_id: int, data: user_address_schema.UserAddressUpdate) -> Optional[UserAddress]:
    address = get_address(db, address_id, user_id)
    if not address:
        return None

    if data.is_default:
        db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": False})

    for key, value in data.dict(exclude_unset=True).items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address

def delete_address(db: Session, address_id: int, user_id: int) -> bool:
    address = get_address(db, address_id, user_id)
    if not address:
        return False
    db.delete(address)
    db.commit()
    return True

def set_default_address(db: Session, address_id: int, user_id: int) -> Optional[UserAddress]:
    address = get_address(db, address_id, user_id)
    if not address:
        return None
    db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": False})
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address
