from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.service_provider_model import ServiceProvider
from app.models.category import Category
from app.models.sub_category import SubCategory
from app.schemas.service_provider_schema import (
    PaginatedVendorsResponse, VendorCreate, VendorResponse, OTPRequest, OTPVerify,
    AddressDetailsUpdate, BankDetailsUpdate, WorkDetailsUpdate, VendorLoginRequest
)
from app.core.security import create_access_token, get_current_vendor
from app.crud.service_provider_crud import (
    create_vendor, verify_vendor_otp, resend_otp,
    update_vendor_address, update_vendor_bank, update_vendor_work, 
    update_vendor_documents, change_vendor_admin_status, change_vendor_work_status, 
    vendor_login, get_all_vendors, delete_vendor, build_vendor_response
)
from app.database import SessionLocal
from app.schemas.category_schema import CategoryOut
from app.schemas.sub_category_schema import SubCategoryOut
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendor", tags=["vendor"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def transform_vendor_for_frontend(vendor: VendorResponse, db: Session) -> dict:
    """Transform VendorResponse to frontend format"""
    return {
        "id": str(vendor.id),
        "name": vendor.full_name,
        "categoryId": str(vendor.category_id) if vendor.category_id else "",
        "categoryName": db.query(Category).filter(Category.id == vendor.category_id).first().name if vendor.category_id else "N/A",
        "subcategoryId": str(vendor.subcategory_charges[0].subcategory_id) if vendor.subcategory_charges else "",
        "subcategoryName": db.query(SubCategory).filter(SubCategory.id == vendor.subcategory_charges[0].subcategory_id).first().name if vendor.subcategory_charges else "N/A",
        "serviceId": str(vendor.subcategory_charges[0].subcategory_id) if vendor.subcategory_charges else "",
        "serviceName": db.query(SubCategory).filter(SubCategory.id == vendor.subcategory_charges[0].subcategory_id).first().name if vendor.subcategory_charges else "N/A",
        "contactInfo": vendor.email or vendor.phone or "N/A",
        "status": vendor.admin_status.capitalize(),
        "step": vendor.step  # Include step for frontend
    }

@router.get("/", response_model=PaginatedVendorsResponse)
def get_all_vendors_endpoint(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10
):
    try:
        vendors, total = get_all_vendors(db, page, limit)
        return {"vendors": vendors, "total": total}
    except Exception as e:
        logger.error(f"Error in get_all_vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

    
@router.delete("/{vendor_id}")
def delete_vendor_endpoint(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Delete a vendor by ID."""
    try:
        if current_vendor.id != vendor_id:
            logger.warning(f"Unauthorized attempt to delete vendor {vendor_id} by vendor {current_vendor.id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this vendor")
        delete_vendor(db, vendor_id)
        logger.info(f"Vendor deleted successfully: ID {vendor_id}")
        return {"message": "Vendor deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories", response_model=List[CategoryOut])
def list_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.get("/subcategories", response_model=List[SubCategoryOut])
def get_subcategories(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve active subcategories, optionally filtered by category_id."""
    query = db.query(SubCategory).filter(SubCategory.status == 'active')
    if category_id:
        query = query.filter(SubCategory.category_id == category_id)
    return query.all()

@router.post("/login", response_model=dict)
def vendor_login_endpoint(data: VendorLoginRequest, db: Session = Depends(get_db)):
    try:
        vendor, message = vendor_login(db, data.email, data.password)
        token = create_access_token({"sub": vendor.email, "role": "vendor"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "vendor": build_vendor_response(db, vendor),  # Full VendorResponse with step
            "message": message  # Ensure message included
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Vendor login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register", response_model=dict)
def register_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    """Register a new vendor and send OTP."""
    try:
        db_vendor = create_vendor(db, vendor)
        return {"message": "OTP sent", "vendor_id": db_vendor.id, "step": db_vendor.step}  # Include initial step
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Vendor registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/verify-otp", response_model=dict)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP and generate access token."""
    try:
        vendor, message = verify_vendor_otp(db, data.email, data.otp)
        if not vendor:
            raise HTTPException(status_code=400, detail=message)
        access_token = create_access_token(data={"sub": vendor.email})
        return {
            "message": message,
            "vendor_id": vendor.id,
            "step": vendor.step,  # Include step after OTP
            "access_token": access_token,
            "vendor": vendor  # Full VendorResponse object with step
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/send-otp", response_model=dict)
def resend_otp_endpoint(data: OTPRequest, db: Session = Depends(get_db)):
    """Resend OTP to the vendor's email."""
    try:
        resend_otp(db, data.email)
        return {"message": "OTP resent"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"OTP resend error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me", response_model=VendorResponse)
def get_me(current_vendor: ServiceProvider = Depends(get_current_vendor), db: Session = Depends(get_db)):
    """Retrieve the current vendor's details."""
    try:
        vendor_response = build_vendor_response(db, current_vendor)
        return vendor_response  # Full VendorResponse object with step
    except Exception as e:
        logger.error(f"Error retrieving vendor details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor_by_id(vendor_id: int, db: Session = Depends(get_db)):
    """Retrieve vendor details by vendor_id."""
    try:
        vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        vendor_response = build_vendor_response(db, vendor)
        return vendor_response  # Full VendorResponse object with step
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    try:
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating address for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    try:
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating bank details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile/work", response_model=VendorResponse)
def update_work_details(
    vendor_id: int = Body(...),
    update: WorkDetailsUpdate = Body(...),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work details."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
        vendor = update_vendor_work(db, vendor_id, update)
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating work details for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
        vendor = update_vendor_documents(db, vendor_id, profile_pic, identity_doc, bank_doc, address_doc)
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading documents for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile/work-status", response_model=VendorResponse)
def update_work_status(
    vendor_id: int = Form(...),
    work_status: str = Form(..., pattern="^(work_on|work_off)$"),
    db: Session = Depends(get_db),
    current_vendor: ServiceProvider = Depends(get_current_vendor)
):
    """Update vendor work status."""
    try:
        if current_vendor.id != vendor_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this vendor")
        vendor = change_vendor_work_status(db, vendor_id, work_status)
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating work status for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# @router.put("/admin/status", response_model=VendorResponse)
# def update_admin_status(
#     vendor_id: int = Form(...),
#     admin_status: str = Form(..., pattern="^(active|inactive)$"),
#     db: Session = Depends(get_db)
# ):
#     """Update vendor admin status."""
#     try:
#         vendor = change_vendor_admin_status(db, vendor_id, admin_status)
#         return vendor
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error updating admin status for vendor {vendor_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
@router.put("/admin/status", response_model=VendorResponse)
def update_admin_status(
    vendor_id: int = Form(...),
    admin_status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update vendor admin status."""
    try:
        vendor = change_vendor_admin_status(db, vendor_id, admin_status)
        return vendor
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        logger.error(f"Error updating admin status for vendor {vendor_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
