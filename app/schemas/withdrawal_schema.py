# app/schemas/withdrawal_schema.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.withdrawal_model import WithdrawalStatus


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw (after commission)")
    bank_account: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)


class WithdrawalUpdate(BaseModel):
    status: WithdrawalStatus
    admin_message: Optional[str] = Field(None, max_length=500, description="Custom message from admin")


class WithdrawalOut(BaseModel):
    id: int
    vendor_id: int
    amount: float
    gross_amount: float
    commission_amount: float
    status: WithdrawalStatus
    bank_account: Optional[str]
    notes: Optional[str]
    admin_message: Optional[str]
    admin_id: Optional[int]
    requested_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WithdrawalStats(BaseModel):
    total_withdrawals: int
    pending_count: int
    approved_count: int
    rejected_count: int
    total_withdrawn: float
    pending_amount: float