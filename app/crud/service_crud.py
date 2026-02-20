# from typing import List, Optional
# from sqlalchemy.orm import Session
# from app.models.service import Service
# from app.schemas.service_schema import ServiceCreate, ServiceUpdate


# def create_service(db: Session, service: ServiceCreate) -> Service:
#     db_service = Service(**service.dict())
#     db.add(db_service)
#     db.commit()
#     db.refresh(db_service)
#     return db_service


# def get_services(db: Session) -> List[Service]:
#     return db.query(Service).all()


# def get_service(db: Session, service_id: int) -> Optional[Service]:
#     return db.query(Service).filter(Service.id == service_id).first()


# def update_service(db: Session, service_id: int, service: ServiceUpdate) -> Optional[Service]:
#     db_service = get_service(db, service_id)
#     if not db_service:
#         return None
#     for key, value in service.dict(exclude_unset=True).items():
#         setattr(db_service, key, value)
#     db.commit()
#     db.refresh(db_service)
#     return db_service


# def delete_service(db: Session, service_id: int) -> Optional[Service]:
#     db_service = get_service(db, service_id)
#     if not db_service:
#         return None
#     db.delete(db_service)
#     db.commit()
#     return db_service


# def toggle_service_status(db: Session, service_id: int) -> Optional[Service]:
#     db_service = get_service(db, service_id)
#     if not db_service:
#         return None
#     db_service.status = 'Inactive' if db_service.status == 'Active' else 'Active'
#     db.commit()
#     db.refresh(db_service)
#     return db_service
