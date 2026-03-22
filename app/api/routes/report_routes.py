
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_db, get_current_user, get_current_vendor, get_current_admin
from app.models.report_model import ReportRole, ReportStatus
from app.schemas.report_schema import ReportCreate, ReportOut, ReportAdminUpdate
from app.crud.report_crud import ReportCRUD

router = APIRouter(prefix="/reports", tags=["Reports"])

# User reports someone
@router.post("/user", response_model=ReportOut)
def submit_user_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit a report by a user.
    `reported_id` should be the vendor ID if reporting a vendor.
    `reported_role` should be 'vendor' if reporting a vendor.
    """
    report_crud = ReportCRUD(db)
    return report_crud.create_report(
        reporter_id=current_user.id,
        reporter_role=ReportRole.user,
        report_data=report
    )

# Vendor reports someone
@router.post("/vendor", response_model=ReportOut)
def submit_vendor_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_vendor)
):
    """
    Submit a report by a vendor.
    `reported_id` should be the user ID if reporting a user.
    `reported_role` should be 'user' if reporting a user.
    """
    report_crud = ReportCRUD(db)
    return report_crud.create_report(
        reporter_id=current_vendor.id,
        reporter_role=ReportRole.vendor,
        report_data=report
    )

# Get current user's reports
@router.get("/user/my-reports", response_model=List[ReportOut])
def get_user_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    report_crud = ReportCRUD(db)
    return report_crud.get_reports_by_reporter(current_user.id, ReportRole.user, skip, limit)

# Get current vendor's reports
@router.get("/vendor/my-reports", response_model=List[ReportOut])
def get_vendor_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_vendor)
):
    report_crud = ReportCRUD(db)
    return report_crud.get_reports_by_reporter(current_vendor.id, ReportRole.vendor, skip, limit)

# Admin routes
@router.get("/admin/all", response_model=List[ReportOut])
def get_all_reports_admin(
    status: Optional[ReportStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    report_crud = ReportCRUD(db)
    return report_crud.get_all_reports(skip, limit, status)

@router.get("/admin/{report_id}", response_model=ReportOut)
def get_report_detail_admin(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    report_crud = ReportCRUD(db)
    report = report_crud.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/admin/{report_id}", response_model=ReportOut)
def update_report_admin(
    report_id: int,
    update: ReportAdminUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    report_crud = ReportCRUD(db)
    report = report_crud.update_report_admin(report_id, update)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.delete("/admin/{report_id}")
def delete_report_admin(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    report_crud = ReportCRUD(db)
    if not report_crud.delete_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}
