from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models.service_provider_model import ServiceProvider, VendorStatus, vendor_subcategory_charges
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    SubCategoryCharge, VendorCreate, VendorResponse, OTPRequest, OTPVerify,
    AddressDetailsUpdate, BankDetailsUpdate, WorkDetailsUpdate
)
from app.core.security import create_access_token, get_current_vendor
from app.crud.service_provider_crud import (
    create_vendor, verify_vendor_otp, resend_otp,
    update_vendor_address, update_vendor_bank, update_vendor_work, update_vendor_documents
)
from app.database import SessionLocal
import json

router = APIRouter(prefix="/vendor", tags=["vendor"])

# OTP config
OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.status == 'Active').all()

@router.get("/subcategories")
def get_subcategories(category_id: int = None, db: Session = Depends(get_db)):
    query = db.query(SubCategory).filter(SubCategory.status == 'Active')
    if category_id:
        query = query.filter(SubCategory.category_id == category_id)
    return query.all()

@router.post("/register", response_model=dict)
def register_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    db_vendor = create_vendor(db, vendor)
    return {"message": "OTP sent", "vendor_id": db_vendor.id}

@router.post("/verify-otp", response_model=dict)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    vendor, message = verify_vendor_otp(db, data.email, data.otp)
    if not vendor:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message, "vendor_id": vendor.id}

@router.post("/send-otp")
def resend_otp(data: OTPRequest, db: Session = Depends(get_db)):
    resend_otp(db, data.email)
    return {"message": "OTP resent"}

@router.get("/me", response_model=VendorResponse)
def get_me(current_vendor: ServiceProvider = Depends(get_current_vendor)):
    return current_vendor

@router.put("/profile/address", response_model=dict)
async def update_address_details(
    vendor_id: int = Form(...),
    address: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    document_type: str = Form(...),
    document_number: str = Form(...),
    db: Session = Depends(get_db)
):
    update = AddressDetailsUpdate(
        address=address,
        state=state,
        city=city,
        pincode=pincode,
        document_type=document_type,
        document_number=document_number
    )
    vendor = update_vendor_address(db, vendor_id, update)
    return {"message": "Address details updated", "vendor_id": vendor.id}

@router.put("/profile/bank", response_model=dict)
async def update_bank_details(
    vendor_id: int = Form(...),
    account_holder_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    upi_id: str = Form(...),
    db: Session = Depends(get_db)
):
    update = BankDetailsUpdate(
        account_holder_name=account_holder_name,
        account_number=account_number,
        ifsc_code=ifsc_code,
        upi_id=upi_id
    )
    vendor = update_vendor_bank(db, vendor_id, update)
    return {"message": "Bank details updated", "vendor_id": vendor.id}

@router.put("/profile/work", response_model=dict)
async def update_work_details(
    vendor_id: int = Form(...),
    category_id: int = Form(...),
    subcategory_charges: str = Form(...),  # JSON string
    db: Session = Depends(get_db)
):
    try:
        charges = json.loads(subcategory_charges)
        update = WorkDetailsUpdate(
            category_id=category_id,
            subcategory_charges=[SubCategoryCharge(**charge) for charge in charges]
        )
        vendor = update_vendor_work(db, vendor_id, update)
        return {"message": "Work details updated", "vendor_id": vendor.id}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid subcategory charges format")

@router.post("/profile/documents", response_model=dict)
async def upload_documents(
    vendor_id: int = Form(...),
    profile_pic: UploadFile = File(...),
    document_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    vendor = update_vendor_documents(db, vendor_id, profile_pic, document_file)
    return {"message": "Documents uploaded", "vendor_id": vendor.id}