from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.vendor_earnings_schema import VendorEarningsCreate, VendorEarningsOut
from app.crud import vendor_earnings_crud

router = APIRouter(prefix="/vendor-earnings", tags=["Vendor Earnings"])

@router.post("/", response_model=VendorEarningsOut)
def create_vendor_earnings(earnings: VendorEarningsCreate, db: Session = Depends(get_db)):
    return vendor_earnings_crud.create_vendor_earnings(
        db=db,
        booking_id=earnings.booking_id,
        vendor_id=earnings.vendor_id,
        total_paid=earnings.total_paid,
        commission_percentage=earnings.commission_percentage,
        commission_amount=earnings.commission_amount,
        final_amount=earnings.final_amount
    )

@router.get("/vendor/{vendor_id}", response_model=List[VendorEarningsOut])
def get_vendor_earnings_by_vendor(vendor_id: int, db: Session = Depends(get_db)):
    return vendor_earnings_crud.get_vendor_earnings_by_vendor(db, vendor_id)

@router.get("/booking/{booking_id}", response_model=List[VendorEarningsOut])
def get_vendor_earnings_by_booking(booking_id: int, db: Session = Depends(get_db)):
    return vendor_earnings_crud.get_vendor_earnings_by_booking(db, booking_id)

@router.get("/{earnings_id}", response_model=VendorEarningsOut)
def get_vendor_earnings_by_id(earnings_id: int, db: Session = Depends(get_db)):
    earnings = vendor_earnings_crud.get_vendor_earnings_by_id(db, earnings_id)
    if not earnings:
        raise HTTPException(status_code=404, detail="Vendor earnings not found")
    return earnings

@router.get("/", response_model=List[VendorEarningsOut])
def get_all_vendor_earnings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return vendor_earnings_crud.get_all_vendor_earnings(db, skip, limit)

@router.delete("/{earnings_id}")
def delete_vendor_earnings(earnings_id: int, db: Session = Depends(get_db)):
    success = vendor_earnings_crud.delete_vendor_earnings(db, earnings_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor earnings not found")
    return {"message": "Vendor earnings deleted successfully"}
