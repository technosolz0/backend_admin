from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.service_provider_model import ServiceProvider
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    VendorCreate, VendorResponse, OTPRequest, OTPVerify,
    AddressDetailsUpdate, BankDetailsUpdate, WorkDetailsUpdate,VendorLoginRequest
)
from app.core.security import create_access_token, get_current_vendor,verify_password
from app.crud.service_provider_crud import (
    create_vendor, verify_vendor_otp, resend_otp,
    update_vendor_address, update_vendor_bank, update_vendor_work, 
    update_vendor_documents, change_vendor_admin_status, change_vendor_work_status,vendor_login
)
from app.database import SessionLocal
from app.schemas.category_schema import CategoryOut
from app.schemas.sub_category_schema import SubCategoryOut

router = APIRouter(prefix="/vendor", tags=["vendor"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/categories", response_model=list[CategoryOut])
def list_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.get("/subcategories", response_model=List[SubCategoryOut])
def get_subcategories(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve active subcategories, optionally filtered by category_id."""
    query = db.query(SubCategory).filter(SubCategory.status == 'active')
    if category_id:
        query = query.filter(SubCategory.category_id == category_id)
    return query.all()




# @router.post("/login")
# def vendor_login(data: VendorLoginRequest, db: Session = Depends(get_db)):
#     try:
#         vendor = db.query(ServiceProvider).filter(ServiceProvider.email == data.email).first()
#         if not vendor:
#             raise HTTPException(status_code=404, detail="Vendor not found")
        
#         if not verify_password(data.password, vendor.password):
#             raise HTTPException(status_code=401, detail="Invalid credentials")
        
#         token = create_access_token({"sub": vendor.email, "role": "vendor"})
#         return {"access_token": token, "token_type": "bearer"}
#     except Exception as e:
#         import traceback
#         print("Vendor login error:", e)
#         traceback.print_exc()
#         raise
@router.post("/login", response_model=dict)
def vendor_login(data: VendorLoginRequest, db: Session = Depends(get_db)):
    try:
        # Find vendor by email
        vendor = db.query(ServiceProvider).filter(ServiceProvider.email == data.email).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Verify password
        if not verify_password(data.password, vendor.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create JWT token
        token = create_access_token({"sub": vendor.email, "role": "vendor"})
        
        # Prepare vendor data for response
        vendor_data = {
            "id": vendor.id,
            "name": vendor.full_name,
            "email": vendor.email,
            "phone": vendor.phone,
            "address": vendor.address,
            "state": vendor.state,
            "city": vendor.city,
            "pincode": vendor.pincode,
            "address_doc_type": vendor.address_doc_type,
            "address_doc_number": vendor.address_doc_number,
            "bank_account_holder_name": vendor.account_holder_name,
            "bank_account_number": vendor.account_number,
            "ifsc_code": vendor.ifsc_code,
            "upi_id": vendor.upi_id,
            "bank_doc_type": vendor.bank_doc_type,
            "bank_doc_number": vendor.bank_doc_number,
            "work_status": vendor.work_status,
            "admin_status": vendor.admin_status,
            "created_at": vendor.created_at,
            "updated_at": vendor.updated_at
        }
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "vendor": vendor_data
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Vendor login error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/register", response_model=dict)
def register_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    """Register a new vendor and send OTP."""
    db_vendor = create_vendor(db, vendor)
    return {"message": "OTP sent", "vendor_id": db_vendor.id}

@router.post("/verify-otp", response_model=dict)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP and generate access token."""
    vendor, message = verify_vendor_otp(db, data.email, data.otp)
    if not vendor:
        raise HTTPException(status_code=400, detail=message)
    access_token = create_access_token(data={"sub": vendor.email})
    return {"message": message, "vendor_id": vendor.id, "access_token": access_token}

@router.post("/send-otp", response_model=dict)
def resend_otp_endpoint(data: OTPRequest, db: Session = Depends(get_db)):
    """Resend OTP to the vendor's email."""
    resend_otp(db, data.email)
    return {"message": "OTP resent"}

@router.get("/me", response_model=VendorResponse)
def get_me(current_vendor: ServiceProvider = Depends(get_current_vendor)):
    """Retrieve the current vendor's details."""
    return current_vendor

@router.put("/profile/address", response_model=VendorResponse)
def update_address_details(
    vendor_id: int = Form(...),
    address: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    address_doc_type: str = Form(...),
    address_doc_number: str = Form(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor address details."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
        
    update = AddressDetailsUpdate(
        address=address,
        state=state,
        city=city,
        pincode=pincode,
        address_doc_type=address_doc_type,
        address_doc_number=address_doc_number
    )
    vendor = update_vendor_address(db, vendor_id, update)
    return vendor

@router.put("/profile/bank", response_model=VendorResponse)
def update_bank_details(
    vendor_id: int = Form(...),
    account_holder_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    upi_id: str = Form(...),
    bank_doc_type: str = Form(...),
    bank_doc_number: str = Form(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor bank details."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
    update = BankDetailsUpdate(
        account_holder_name=account_holder_name,
        account_number=account_number,
        ifsc_code=ifsc_code,
        upi_id=upi_id,
        bank_doc_type=bank_doc_type,
        bank_doc_number=bank_doc_number
    )
    vendor = update_vendor_bank(db, vendor_id, update)
    return vendor

@router.put("/profile/work", response_model=VendorResponse)
def update_work_details(
    vendor_id: int,
    update: WorkDetailsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work details."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
    vendor = update_vendor_work(db, vendor_id, update)
    return vendor
router.put("/profile/work", response_model=VendorResponse)



def update_work_details(
    vendor_id: int = Body(...),  # Changed to Body to match request structure
    update: WorkDetailsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work details."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
    print(update, "updardrrtd")
    vendor = update_vendor_work(db, vendor_id, update)
    print(vendor, "Vendor Work Details Updated")
    return vendor
@router.post("/profile/documents", response_model=VendorResponse)
def upload_documents(
    vendor_id: int = Form(...),
    profile_pic: UploadFile = File(None),
    identity_doc: UploadFile = File(...),
    bank_doc: UploadFile = File(...),
    address_doc: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Upload vendor documents."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
    vendor = update_vendor_documents(db, vendor_id, profile_pic, identity_doc, bank_doc, address_doc)
    return vendor

@router.put("/profile/work-status", response_model=VendorResponse)
def update_work_status(
    vendor_id: int = Form(...),
    work_status: str = Form(..., pattern="^(work_on|work_off)$"),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work status."""
    if current_vendor.id != vendor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
    vendor = change_vendor_work_status(db, vendor_id, work_status)
    return vendor

@router.put("/admin/status", response_model=VendorResponse)
def update_admin_status(
    vendor_id: int = Form(...),
    admin_status: str = Form(..., pattern="^(active|inactive)$"),
    db: Session = Depends(get_db)
):
    """Update vendor admin status."""
    vendor = change_vendor_admin_status(db, vendor_id, admin_status)
    return vendor