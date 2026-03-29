
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.report_model import ReportStatus, ReportRole

class ReportBase(BaseModel):
    booking_id: Optional[int] = None
    reason: str
    description: str

class ReportCreate(ReportBase):
    reported_id: int
    reported_role: ReportRole

class ReportAdminUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    admin_comment: Optional[str] = None

class ReportOut(ReportBase):
    id: int
    reporter_id: int
    reporter_role: ReportRole
    reporter_name: Optional[str] = None
    reported_id: int
    reported_role: ReportRole
    reported_name: Optional[str] = None
    status: ReportStatus
    admin_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
