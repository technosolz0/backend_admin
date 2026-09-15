from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class SubCategoryStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class SubCategoryBase(BaseModel):
    name: str
    status: SubCategoryStatus
    image: Optional[str] = None
    service_charge: Optional[float] = 0.0
    category_id: int

class SubCategoryCreate(SubCategoryBase):
    pass

class SubCategoryUpdate(BaseModel):
    name: Optional[str]
    status: Optional[SubCategoryStatus]
    image: Optional[str]
    service_charge: Optional[float]
    category_id: Optional[int]

class SubCategoryOut(BaseModel):
    id: int
    name: str
    status: SubCategoryStatus
    image: Optional[str]
    service_charge: float
    category_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
