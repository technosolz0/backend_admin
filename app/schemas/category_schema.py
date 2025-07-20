from pydantic import BaseModel
from typing import Optional
from enum import Enum

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

    class Config:
        from_attributes = True