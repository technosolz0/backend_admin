
from sqlalchemy.orm import Session
from app.models.report_model import Report, ReportStatus, ReportRole
from app.schemas.report_schema import ReportCreate, ReportAdminUpdate
from typing import List, Optional

class ReportCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, reporter_id: int, reporter_role: ReportRole, report_data: ReportCreate) -> Report:
        db_report = Report(
            reporter_id=reporter_id,
            reporter_role=reporter_role,
            **report_data.dict()
        )
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def get_report_by_id(self, report_id: int) -> Optional[Report]:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_reports_by_reporter(self, reporter_id: int, reporter_role: ReportRole, skip: int = 0, limit: int = 50) -> List[Report]:
        return self.db.query(Report).filter(
            Report.reporter_id == reporter_id,
            Report.reporter_role == reporter_role
        ).offset(skip).limit(limit).all()

    def get_all_reports(self, skip: int = 0, limit: int = 100, status: Optional[ReportStatus] = None) -> List[Report]:
        query = self.db.query(Report)
        if status:
            query = query.filter(Report.status == status)
        return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

    def update_report_admin(self, report_id: int, update_data: ReportAdminUpdate) -> Optional[Report]:
        db_report = self.get_report_by_id(report_id)
        if not db_report:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_report, field, value)
        
        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def delete_report(self, report_id: int) -> bool:
        db_report = self.get_report_by_id(report_id)
        if not db_report:
            return False
        self.db.delete(db_report)
        self.db.commit()
        return True
