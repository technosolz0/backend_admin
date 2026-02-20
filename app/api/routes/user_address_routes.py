from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_current_user, get_db
from app.models.user import User
from app.schemas import user_address_schema
from app.crud import user_address_crud as crud_address

router = APIRouter(prefix="/user", tags=["User Address"])

@router.post("/address", response_model=user_address_schema.UserAddressOut)
def add_address(data: user_address_schema.UserAddressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_address.create_address(db, current_user.id, data)

@router.get("/", response_model=List[user_address_schema.UserAddressOut])
def list_addresses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_address.get_addresses(db, current_user.id)

@router.get("/address/{address_id}", response_model=user_address_schema.UserAddressOut)
def get_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    address = crud_address.get_address(db, address_id, current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address

@router.put("/address/{address_id}", response_model=user_address_schema.UserAddressOut)
def update_address(address_id: int, data: user_address_schema.UserAddressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = crud_address.update_address(db, address_id, current_user.id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Address not found")
    return updated

@router.delete("/address/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = crud_address.delete_address(db, address_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"message": "Address deleted successfully"}

@router.post("/address/{address_id}/set-default", response_model=user_address_schema.UserAddressOut)
def set_default(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    address = crud_address.set_default_address(db, address_id, current_user.id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address
