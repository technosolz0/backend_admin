from pydantic import BaseModel
from typing import Optional
from enum import Enum

class SubCategoryStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class SubCategoryBase(BaseModel):
    name: str
    status: SubCategoryStatus
    image: Optional[str] = None
    category_id: int

class SubCategoryCreate(SubCategoryBase):
    pass

class SubCategoryUpdate(BaseModel):
    name: Optional[str]
    status: Optional[SubCategoryStatus]
    image: Optional[str]
    category_id: Optional[int]

class SubCategoryOut(BaseModel):
    id: int
    name: str
    status: SubCategoryStatus
    image: Optional[str]
    category_id: int

    class Config:
        from_attributes = True
