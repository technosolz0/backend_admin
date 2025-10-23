from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.cancel_reason_schema import CancelReasonCreate, CancelReasonOut
from app.crud import cancel_reason_crud

router = APIRouter(prefix="/cancel-reasons", tags=["Cancel Reasons"])

@router.post("/", response_model=CancelReasonOut)
def create_cancel_reason(reason: CancelReasonCreate, db: Session = Depends(get_db)):
    return cancel_reason_crud.create_cancel_reason(
        db=db,
        booking_id=reason.booking_id,
        reason=reason.reason,
        cancelled_by=reason.cancelled_by
    )

@router.get("/booking/{booking_id}", response_model=List[CancelReasonOut])
def get_cancel_reasons_by_booking(booking_id: int, db: Session = Depends(get_db)):
    return cancel_reason_crud.get_cancel_reasons_by_booking(db, booking_id)

@router.get("/{reason_id}", response_model=CancelReasonOut)
def get_cancel_reason_by_id(reason_id: int, db: Session = Depends(get_db)):
    reason = cancel_reason_crud.get_cancel_reason_by_id(db, reason_id)
    if not reason:
        raise HTTPException(status_code=404, detail="Cancel reason not found")
    return reason

@router.get("/", response_model=List[CancelReasonOut])
def get_all_cancel_reasons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return cancel_reason_crud.get_all_cancel_reasons(db, skip, limit)

@router.delete("/{reason_id}")
def delete_cancel_reason(reason_id: int, db: Session = Depends(get_db)):
    success = cancel_reason_crud.delete_cancel_reason(db, reason_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cancel reason not found")
    return {"message": "Cancel reason deleted successfully"}
