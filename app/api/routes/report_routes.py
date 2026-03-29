
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_db, get_current_user, get_current_vendor, get_current_admin
from app.models.report_model import ReportRole, ReportStatus
from app.schemas.report_schema import ReportCreate, ReportOut, ReportAdminUpdate
from app.crud.report_crud import ReportCRUD

from app.models.user import User
from app.models.service_provider_model import ServiceProvider as Vendor

def enrich_report(report, db: Session):
    # Reporter
    if report.reporter_role == ReportRole.user:
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        report.reporter_name = reporter.name if reporter else "Unknown User"
    else:
        reporter = db.query(Vendor).filter(Vendor.id == report.reporter_id).first()
        # In vendor, full_name is often used from professional details
        report.reporter_name = reporter.full_name or reporter.business_name if reporter else "Unknown Vendor"
    
    # Reported
    if report.reported_role == ReportRole.user:
        reported = db.query(User).filter(User.id == report.reported_id).first()
        report.reported_name = reported.name if reported else "Unknown User"
    else:
        reported = db.query(Vendor).filter(Vendor.id == report.reported_id).first()
        report.reported_name = reported.full_name or reported.business_name if reported else "Unknown Vendor"
    
    return report

# User reports someone
@router.post("/user", response_model=ReportOut)
def submit_user_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    report_crud = ReportCRUD(db)
    new_report = report_crud.create_report(
        reporter_id=current_user.id,
        reporter_role=ReportRole.user,
        report_data=report
    )
    return enrich_report(new_report, db)

# Vendor reports someone
@router.post("/vendor", response_model=ReportOut)
def submit_vendor_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_vendor)
):
    report_crud = ReportCRUD(db)
    new_report = report_crud.create_report(
        reporter_id=current_vendor.id,
        reporter_role=ReportRole.vendor,
        report_data=report
    )
    return enrich_report(new_report, db)

# Get current user's reports
@router.get("/user/my-reports", response_model=List[ReportOut])
def get_user_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    report_crud = ReportCRUD(db)
    reports = report_crud.get_reports_by_reporter(current_user.id, ReportRole.user, skip, limit)
    return [enrich_report(r, db) for r in reports]

# Get current vendor's reports
@router.get("/vendor/my-reports", response_model=List[ReportOut])
def get_vendor_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_vendor)
):
    report_crud = ReportCRUD(db)
    reports = report_crud.get_reports_by_reporter(current_vendor.id, ReportRole.vendor, skip, limit)
    return [enrich_report(r, db) for r in reports]

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
    reports = report_crud.get_all_reports(skip, limit, status)
    return [enrich_report(r, db) for r in reports]

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
    return enrich_report(report, db)

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
    return enrich_report(report, db)

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
