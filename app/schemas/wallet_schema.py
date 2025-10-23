from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional

class WalletCreate(BaseModel):
    user_id: Optional[int] = None
    vendor_id: Optional[int] = None
    balance: float = 0.0

    @field_validator('balance')
    @classmethod
    def balance_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Balance cannot be negative')
        return v

    @field_validator('user_id', 'vendor_id')
    @classmethod
    def check_exclusive_ids(cls, v, info: ValidationInfo):
        user_id = info.data.get('user_id')
        vendor_id = info.data.get('vendor_id')

        if info.field_name == 'user_id' and user_id is not None and vendor_id is not None:
            raise ValueError('Wallet cannot belong to both user and vendor')
        if info.field_name == 'vendor_id' and vendor_id is not None and user_id is not None:
            raise ValueError('Wallet cannot belong to both user and vendor')

        # Ensure at least one is provided
        if info.field_name == 'vendor_id' and user_id is None and vendor_id is None:
            raise ValueError('Wallet must belong to either a user or vendor')

        return v

class WalletUpdate(BaseModel):
    balance: float

    @field_validator('balance')
    @classmethod
    def balance_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Balance cannot be negative')
        return v

class WalletOut(BaseModel):
    id: int
    user_id: Optional[int]
    vendor_id: Optional[int]
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True
