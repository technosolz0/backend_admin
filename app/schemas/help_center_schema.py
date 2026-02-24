from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class HelpCenterBase(BaseModel):
    question: str
    answer: str
    category: str
    is_for_vendor: bool = True
    is_for_user: bool = True
    priority: int = 0
    is_active: bool = True

class HelpCenterCreate(HelpCenterBase):
    pass

class HelpCenterUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    is_for_vendor: Optional[bool] = None
    is_for_user: Optional[bool] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class HelpCenter(HelpCenterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        # or orm_mode = True for older Pydantic
