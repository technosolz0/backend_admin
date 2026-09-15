from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class CategoryStatus(str, Enum):
    active = "Active"
    inactive = "Inactive"

class CategoryBase(BaseModel):
    name: str
    status: CategoryStatus
    image: str

class CategoryCreate(BaseModel):
    name: str
    status: CategoryStatus = CategoryStatus.active
    image: str

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[CategoryStatus] = None
    image: Optional[str] = None

class CategoryOut(BaseModel):
    id: int
    name: str
    status: CategoryStatus
    image: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True