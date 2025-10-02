# app/crud/delete_request_crud.py
from sqlalchemy.orm import Session
from app.models.delete_request_model import DeleteRequest
from app.schemas.delete_request_schema import DeleteRequestCreate
from app.models.service_provider_model import ServiceProvider
from app.models.user import User

def create_delete_request(db: Session, req: DeleteRequestCreate):
    name, phone = None, None

    if req.role == "vendor" and req.vendor_id:
        vendor = db.query(ServiceProvider).filter(ServiceProvider.id == req.vendor_id).first()
        if not vendor:
            return None
        name, phone = vendor.full_name, vendor.phone

    elif req.role == "user" and req.user_id:
        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            return None
        name, phone = user.name, user.mobile

    new_req = DeleteRequest(
        user_id=req.user_id,
        vendor_id=req.vendor_id,
        name=name,
        phone=phone,
        reason=req.reason,
        role=req.role,
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

def get_delete_requests(db: Session, skip: int = 0, limit: int = 50):
    return db.query(DeleteRequest).order_by(DeleteRequest.request_date.desc()).offset(skip).limit(limit).all()

def delete_request_by_id(db: Session, request_id: int):
    req = db.query(DeleteRequest).filter(DeleteRequest.id == request_id).first()
    if req:
        db.delete(req)
        db.commit()
        return True
    return False
