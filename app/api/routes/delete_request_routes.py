# app/api/delete_request_api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_db
from app.schemas.delete_request_schema import DeleteRequestCreate, DeleteRequestResponse
from app.crud import delete_request_crud
from fastapi import Query



router = APIRouter(prefix="/delete-request", tags=["Delete Request"])

@router.post("/submit", response_model=DeleteRequestResponse)
def submit_delete_request(req: DeleteRequestCreate, db: Session = Depends(get_db)):
    new_req = delete_request_crud.create_delete_request(db, req)
    if not new_req:
        raise HTTPException(status_code=404, detail="User/Vendor not found")
    return new_req

# @router.get("/list", response_model=List[DeleteRequestResponse])
# def list_delete_requests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     return delete_request_crud.get_delete_requests(db, skip, limit)


@router.get("/list", response_model=dict)  # now returns {"data": [...], "total": ...}
def list_delete_requests(
    skip: int = 0,
    limit: int = 10,
    name: str = Query(None, description="Filter by name"),
    role: str = Query(None, description="Filter by role"),
    phone: str = Query(None, description="Filter by phone"),
    db: Session = Depends(get_db)
):
    return delete_request_crud.get_delete_requests(db, skip, limit, name, role, phone)

@router.delete("/{request_id}")
def delete_request(request_id: int, db: Session = Depends(get_db)):
    result = delete_request_crud.delete_request_by_id(db, request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"result": 1, "message": "Request deleted successfully"}
