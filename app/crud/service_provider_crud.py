




# from datetime import datetime, timedelta
# from fastapi import HTTPException, UploadFile
# from passlib.context import CryptContext
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from app.utils.otp_utils import generate_otp, send_email_otp
# from app.core.security import get_password_hash
# from app.models.service_provider_model import ServiceProvider
# from app.models.vendor_subcategory_charge import VendorSubcategoryCharge
# from app.models.sub_category import SubCategory
# from app.models.category import Category
# from app.schemas.service_provider_schema import (
#     VendorCreate, VendorDeviceUpdate, AddressDetailsUpdate, 
#     BankDetailsUpdate, WorkDetailsUpdate, SubCategoryCharge, VendorResponse
# )
# from app.schemas.sub_category_schema import SubCategoryStatus
# import logging
# from typing import List, Tuple
# import os
# from pathlib import Path

# from app.utils.fcm import send_push_notification  
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OTP_EXPIRY_MINUTES = 5
# MAX_OTP_ATTEMPTS = 3
# MAX_OTP_RESENDS = 3
# OTP_RESEND_COOLDOWN_MINUTES = 1

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

# def get_vendor_by_id(db: Session, vendor_id: int) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()

# def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
#     return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

# def get_category_by_id(db: Session, category_id: int) -> Category:
#     return db.query(Category).filter(Category.id == category_id).first()

# def attach_subcategory_charges(db: Session, vendor_id: int) -> List[SubCategoryCharge]:
#     charges = db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).all()
#     return [
#         SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
#         for charge in charges
#     ]

# def get_all_vendors(db: Session, page: int = 1, limit: int = 10) -> Tuple[List[VendorResponse], int]:
#     """Retrieve all vendors with pagination."""
#     try:
#         offset = (page - 1) * limit
#         query = db.query(ServiceProvider).join(
#             Category, ServiceProvider.category_id == Category.id, isouter=True
#         ).join(
#             VendorSubcategoryCharge, ServiceProvider.id == VendorSubcategoryCharge.vendor_id, isouter=True
#         ).join(
#             SubCategory, VendorSubcategoryCharge.subcategory_id == SubCategory.id, isouter=True
#         )
        
#         total = query.distinct(ServiceProvider.id).count()
#         vendors = query.distinct(ServiceProvider.id).offset(offset).limit(limit).all()

#         vendor_responses = []
#         for vendor in vendors:
#             subcategory_charges = attach_subcategory_charges(db, vendor.id)
#             vendor_response = VendorResponse(
#                 id=vendor.id,
#                 full_name=vendor.full_name,
#                 email=vendor.email,
#                 phone=vendor.phone,
#                 address=vendor.address,
#                 state=vendor.state,
#                 city=vendor.city,
#                 pincode=vendor.pincode,
#                 account_holder_name=vendor.account_holder_name,
#                 account_number=vendor.account_number,
#                 ifsc_code=vendor.ifsc_code,
#                 upi_id=vendor.upi_id,
#                 identity_doc_type=vendor.identity_doc_type,
#                 identity_doc_number=vendor.identity_doc_number,
#                 identity_doc_url=vendor.identity_doc_url,
#                 bank_doc_type=vendor.bank_doc_type,
#                 bank_doc_number=vendor.bank_doc_number,
#                 bank_doc_url=vendor.bank_doc_url,
#                 address_doc_type=vendor.address_doc_type,
#                 address_doc_number=vendor.address_doc_number,
#                 address_doc_url=vendor.address_doc_url,
#                 category_id=vendor.category_id,
#                 profile_pic=vendor.profile_pic,
#                 status=vendor.admin_status,  # Map admin_status to status for frontend
#                 admin_status=vendor.admin_status,
#                 work_status=vendor.work_status,
#                 subcategory_charges=subcategory_charges
#             )
#             vendor_responses.append(vendor_response)
        
#         logger.info(f"Retrieved {len(vendor_responses)} vendors for page {page}, limit {limit}")
#         return vendor_responses, total
#     except SQLAlchemyError as e:
#         logger.error(f"Database error in get_all_vendors: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         logger.error(f"Unexpected error in get_all_vendors: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def delete_vendor(db: Session, vendor_id: int) -> None:
#     """Delete a vendor by ID."""
#     vendor = get_vendor_by_id(db, vendor_id)
#     if not vendor:
#         logger.error(f"Vendor not found for ID {vendor_id}")
#         raise HTTPException(status_code=404, detail="Vendor not found")
    
#     try:
#         db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).delete()
#         db.delete(vendor)
#         db.commit()
#         logger.info(f"Vendor deleted successfully: ID {vendor_id}")
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"Database error in delete_vendor: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in delete_vendor: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def vendor_login(db: Session, email: str, password: str) -> Tuple[VendorResponse, str]:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     if not verify_password(password, vendor.password):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     vendor.last_login = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response, "Login successful"

# def create_vendor(db: Session, vendor: VendorCreate) -> ServiceProvider:
#     existing = get_vendor_by_email(db, email=vendor.email)
#     if existing and existing.otp_verified:
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     if existing and not existing.otp_verified:
#         existing.full_name = vendor.full_name
#         existing.phone = vendor.phone
#         existing.password = get_password_hash(vendor.password)
#         existing.terms_accepted = vendor.terms_accepted
#         existing.identity_doc_type = vendor.identity_doc_type
#         existing.identity_doc_number = vendor.identity_doc_number
#         existing.fcm_token = vendor.fcm_token
#         existing.latitude = vendor.latitude
#         existing.longitude = vendor.longitude
#         existing.device_name = vendor.device_name
#         existing.profile_pic = vendor.profile_pic
#         existing.otp = generate_otp()
#         existing.otp_created_at = datetime.utcnow()
#         existing.otp_last_sent_at = datetime.utcnow()
#         db.commit()
#         db.refresh(existing)
#         send_email_otp(vendor.email, existing.otp)
#         return existing
    
#     hashed_password = get_password_hash(vendor.password)
#     otp = generate_otp()
#     now = datetime.utcnow()
    
#     db_vendor = ServiceProvider(
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         password=hashed_password,
#         profile_pic=vendor.profile_pic,
#         terms_accepted=vendor.terms_accepted,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         fcm_token=vendor.fcm_token,
#         latitude=vendor.latitude,
#         longitude=vendor.longitude,
#         device_name=vendor.device_name,
#         otp=otp,
#         otp_created_at=now,
#         otp_last_sent_at=now,
#         otp_verified=False,
#         last_login=now,
#         last_device_update=now,
#         status='pending',
#         admin_status='inactive',
#         work_status='work_on'
#     )
#     db.add(db_vendor)
#     db.commit()
#     db.refresh(db_vendor)
    
#     send_email_otp(vendor.email, otp)
#     return db_vendor

# def verify_vendor_otp(db: Session, email: str, otp: str) -> Tuple[VendorResponse, str]:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         return None, "Vendor not found"
    
#     if vendor.otp_attempts >= MAX_OTP_ATTEMPTS:
#         return None, "Maximum OTP attempts exceeded"
    
#     if vendor.otp != otp:
#         vendor.otp_attempts += 1
#         db.commit()
#         return None, "Invalid OTP"
    
#     if (datetime.utcnow() - vendor.otp_created_at) > timedelta(minutes=OTP_EXPIRY_MINUTES):
#         return None, "OTP expired"
    
#     vendor.otp_verified = True
#     vendor.otp_attempts = 0
#     vendor.status = 'pending'
#     vendor.last_login = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response, "OTP verified successfully"

# def resend_otp(db: Session, email: str) -> None:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         raise HTTPException(status_code=404, detail="Vendor not found")
    
#     if vendor.otp_last_sent_at and (datetime.utcnow() - vendor.otp_last_sent_at) < timedelta(minutes=OTP_RESEND_COOLDOWN_MINUTES):
#         raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")
    
#     if vendor.otp_attempts >= MAX_OTP_RESENDS:
#         raise HTTPException(status_code=429, detail="Maximum OTP resend attempts exceeded")
    
#     otp = generate_otp()
#     vendor.otp = otp
#     vendor.otp_created_at = datetime.utcnow()
#     vendor.otp_last_sent_at = datetime.utcnow()
#     vendor.otp_attempts = 0
#     send_email_otp(email, otp)
#     db.commit()

# def update_vendor_address(db: Session, vendor_id: int, update: AddressDetailsUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response

# def update_vendor_bank(db: Session, vendor_id: int, update: BankDetailsUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response

# def update_vendor_work(db: Session, vendor_id: int, update: WorkDetailsUpdate) -> VendorResponse:
#     logger.debug(f"Updating work details for vendor_id: {vendor_id}, update: {update.dict()}")
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         logger.error(f"Vendor with ID {vendor_id} not found")
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")

#     if not vendor.otp_verified:
#         logger.error(f"Vendor {vendor_id} not OTP verified")
#         raise HTTPException(status_code=403, detail="OTP verification required")

#     if not update.subcategory_charges:
#         logger.error("No subcategory charges provided")
#         raise HTTPException(status_code=400, detail="At least one subcategory charge is required")

#     category = get_category_by_id(db, update.category_id)
#     if not category:
#         logger.error(f"Category {update.category_id} not found")
#         raise HTTPException(status_code=404, detail=f"Category {update.category_id} not found")

#     try:
#         logger.debug(f"Setting category_id: {update.category_id}")
#         vendor.category_id = update.category_id

#         logger.debug(f"Deleting existing charges for vendor_id: {vendor_id}")
#         vendor.subcategory_charges.clear()

#         for charge in update.subcategory_charges:
#             logger.debug(f"Processing subcategory charge: {charge}")
#             if charge.service_charge < 0:
#                 logger.error(f"Negative service charge: {charge.service_charge}")
#                 raise HTTPException(status_code=400, detail="Service charge cannot be negative")
#             subcategory = get_subcategory_by_id(db, charge.subcategory_id)
#             if not subcategory:
#                 logger.error(f"Subcategory {charge.subcategory_id} not found")
#                 raise HTTPException(status_code=404, detail=f"Subcategory {charge.subcategory_id} not found")
#             if subcategory.category_id != update.category_id:
#                 logger.error(f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
#                 raise HTTPException(status_code=400, detail=f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
#             if subcategory.status not in [SubCategoryStatus.active, SubCategoryStatus.inactive]:
#                 logger.error(f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}")
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}"
#                 )

#             new_charge = VendorSubcategoryCharge(
#                 subcategory_id=charge.subcategory_id,
#                 category_id=update.category_id,
#                 service_charge=charge.service_charge,
#             )
#             logger.debug(f"Inserting charge: vendor_id={vendor_id}, subcategory_id={charge.subcategory_id}, service_charge={charge.service_charge}")
#             vendor.subcategory_charges.append(new_charge)

#         vendor.status = 'approved'
#         vendor.last_device_update = datetime.utcnow()
#         logger.debug(f"Committing changes for vendor_id: {vendor_id}")
#         db.commit()
#         db.refresh(vendor)
        
#         subcategory_charges = attach_subcategory_charges(db, vendor.id)
#         vendor_response = VendorResponse(
#             id=vendor.id,
#             full_name=vendor.full_name,
#             email=vendor.email,
#             phone=vendor.phone,
#             address=vendor.address,
#             state=vendor.state,
#             city=vendor.city,
#             pincode=vendor.pincode,
#             account_holder_name=vendor.account_holder_name,
#             account_number=vendor.account_number,
#             ifsc_code=vendor.ifsc_code,
#             upi_id=vendor.upi_id,
#             identity_doc_type=vendor.identity_doc_type,
#             identity_doc_number=vendor.identity_doc_number,
#             identity_doc_url=vendor.identity_doc_url,
#             bank_doc_type=vendor.bank_doc_type,
#             bank_doc_number=vendor.bank_doc_number,
#             bank_doc_url=vendor.bank_doc_url,
#             address_doc_type=vendor.address_doc_type,
#             address_doc_number=vendor.address_doc_number,
#             address_doc_url=vendor.address_doc_url,
#             category_id=vendor.category_id,
#             profile_pic=vendor.profile_pic,
#             status=vendor.admin_status,  # Map admin_status to status for frontend
#             admin_status=vendor.admin_status,
#             work_status=vendor.work_status,
#             subcategory_charges=subcategory_charges
#         )
#         logger.info(f"Vendor work details updated successfully: {vendor.id}")
#         return vendor_response
#     except HTTPException as e:
#         db.rollback()
#         logger.error(f"HTTPException in update_vendor_work: {str(e)}")
#         raise e
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"SQLAlchemyError in update_vendor_work: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in update_vendor_work: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def update_vendor_documents(db: Session, vendor_id: int, profile_pic: UploadFile | None, identity_doc: UploadFile, bank_doc: UploadFile, address_doc: UploadFile) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
#     max_file_size = 5 * 1024 * 1024  # 5MB
#     upload_base_dir = os.getenv("UPLOAD_DIR", "uploads")

#     def save_file(file: UploadFile, subdir: str, prefix: str) -> str:
#         try:
#             ext = file.filename.split(".")[-1].lower() if file.filename else ""
#             if ext not in allowed_extensions:
#                 logger.error(f"Invalid file type for {prefix}: {ext}")
#                 raise HTTPException(status_code=400, detail=f"Invalid {prefix} file type. Allowed: {', '.join(allowed_extensions)}")
#             if file.size > max_file_size:
#                 logger.error(f"{prefix} file too large: {file.size} bytes")
#                 raise HTTPException(status_code=400, detail=f"{prefix} file too large. Max size: {max_file_size} bytes")
            
#             file_path = Path(upload_base_dir) / subdir / f"{prefix}_{vendor_id}.{ext}"
#             file_path.parent.mkdir(parents=True, exist_ok=True)
#             with file_path.open("wb") as buffer:
#                 buffer.write(file.file.read())
#             logger.debug(f"Saved {prefix} file to {file_path}")
#             return str(file_path)
#         except Exception as e:
#             logger.error(f"Error saving {prefix} file: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Failed to save {prefix} file: {str(e)}")

#     try:
#         if profile_pic:
#             vendor.profile_pic = save_file(profile_pic, "profiles", "profile")
        
#         vendor.identity_doc_url = save_file(identity_doc, "documents", "identity")
#         vendor.bank_doc_url = save_file(bank_doc, "documents", "bank")
#         vendor.address_doc_url = save_file(address_doc, "documents", "address")
        
#         vendor.last_device_update = datetime.utcnow()
#         db.commit()
#         db.refresh(vendor)
        
#         subcategory_charges = attach_subcategory_charges(db, vendor.id)
#         vendor_response = VendorResponse(
#             id=vendor.id,
#             full_name=vendor.full_name,
#             email=vendor.email,
#             phone=vendor.phone,
#             address=vendor.address,
#             state=vendor.state,
#             city=vendor.city,
#             pincode=vendor.pincode,
#             account_holder_name=vendor.account_holder_name,
#             account_number=vendor.account_number,
#             ifsc_code=vendor.ifsc_code,
#             upi_id=vendor.upi_id,
#             identity_doc_type=vendor.identity_doc_type,
#             identity_doc_number=vendor.identity_doc_number,
#             identity_doc_url=vendor.identity_doc_url,
#             bank_doc_type=vendor.bank_doc_type,
#             bank_doc_number=vendor.bank_doc_number,
#             bank_doc_url=vendor.bank_doc_url,
#             address_doc_type=vendor.address_doc_type,
#             address_doc_number=vendor.address_doc_number,
#             address_doc_url=vendor.address_doc_url,
#             category_id=vendor.category_id,
#             profile_pic=vendor.profile_pic,
#             status=vendor.admin_status,  # Map admin_status to status for frontend
#             admin_status=vendor.admin_status,
#             work_status=vendor.work_status,
#             subcategory_charges=subcategory_charges
#         )
#         logger.info(f"Documents updated successfully for vendor_id: {vendor_id}")
#         return vendor_response
#     except HTTPException as e:
#         db.rollback()
#         logger.error(f"HTTPException in update_vendor_documents: {str(e)}")
#         raise e
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"SQLAlchemyError in update_vendor_documents: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in update_vendor_documents: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def update_vendor_device(db: Session, vendor_id: int, update: VendorDeviceUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response

# def change_vendor_admin_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if status not in ['active', 'inactive']:
#         raise HTTPException(status_code=400, detail="Invalid admin status")
    
#     vendor.admin_status = status
#     db.commit()
#     db.refresh(vendor)
#     if vendor.fcm_token:
#         send_push_notification(
#             token=vendor.fcm_token,
#             title="Status Update",
#             body=f"Your account status has been updated to {new_status}"
#         )

#     # return build_vendor_response(vendor, db)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response

# def change_vendor_work_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     if vendor.admin_status != 'active':
#         raise HTTPException(status_code=403, detail="Vendor must be active to change work status")
    
#     if status not in ['work_on', 'work_off']:
#         raise HTTPException(status_code=400, detail="Invalid work status")
    
#     vendor.work_status = status
#     db.commit()
#     db.refresh(vendor)
    
#     subcategory_charges = attach_subcategory_charges(db, vendor.id)
#     vendor_response = VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         profile_pic=vendor.profile_pic,
#         status=vendor.admin_status,  # Map admin_status to status for frontend
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )
#     return vendor_response


from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from passlib.context import CryptContext
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.utils.otp_utils import generate_otp, send_email_otp, send_email
from app.core.security import get_password_hash
from app.models.service_provider_model import ServiceProvider
from app.models.vendor_subcategory_charge import VendorSubcategoryCharge
from app.models.sub_category import SubCategory
from app.models.category import Category
from app.schemas.service_provider_schema import (
    VendorCreate, VendorDeviceUpdate, AddressDetailsUpdate, 
    BankDetailsUpdate, WorkDetailsUpdate, SubCategoryCharge, VendorResponse
)
from app.schemas.sub_category_schema import SubCategoryStatus
from app.utils.notification_utils import send_notification, NotificationType
import logging
from typing import List, Tuple
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
MAX_OTP_RESENDS = 3
OTP_RESEND_COOLDOWN_MINUTES = 1

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
    return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

def get_vendor_by_id(db: Session, vendor_id: int) -> ServiceProvider:
    return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()

def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
    return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

def get_category_by_id(db: Session, category_id: int) -> Category:
    return db.query(Category).filter(Category.id == category_id).first()

def attach_subcategory_charges(db: Session, vendor_id: int) -> List[SubCategoryCharge]:
    charges = db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).all()
    return [
        SubCategoryCharge(
            subcategory_id=charge.subcategory_id,
            subcategory_name=get_subcategory_by_id(db, charge.subcategory_id).name if get_subcategory_by_id(db, charge.subcategory_id) else None,
            service_charge=charge.service_charge
        )
        for charge in charges
    ]

def build_vendor_response(db: Session, vendor: ServiceProvider) -> VendorResponse:
    # Get Category Name
    category_name = None
    if vendor.category_id:
        category = db.query(Category).filter(Category.id == vendor.category_id).first()
        category_name = category.name if category else None

    # Get SubCategory Names + Charges
    subcategory_charges = attach_subcategory_charges(db, vendor.id)

    return VendorResponse(
        id=vendor.id,
        full_name=vendor.full_name,
        email=vendor.email,
        phone=vendor.phone,
        address=vendor.address,
        state=vendor.state,
        city=vendor.city,
        pincode=vendor.pincode,
        account_holder_name=vendor.account_holder_name,
        account_number=vendor.account_number,
        ifsc_code=vendor.ifsc_code,
        upi_id=vendor.upi_id,
        identity_doc_type=vendor.identity_doc_type,
        identity_doc_number=vendor.identity_doc_number,
        identity_doc_url=vendor.identity_doc_url,
        bank_doc_type=vendor.bank_doc_type,
        bank_doc_number=vendor.bank_doc_number,
        bank_doc_url=vendor.bank_doc_url,
        address_doc_type=vendor.address_doc_type,
        address_doc_number=vendor.address_doc_number,
        address_doc_url=vendor.address_doc_url,
        category_id=vendor.category_id,
        category_name=category_name,
        profile_pic=vendor.profile_pic,
        step=vendor.step,
        status=vendor.status,
        admin_status=vendor.admin_status,
        work_status=vendor.work_status,
        subcategory_charges=subcategory_charges
    )

def get_all_vendors(db: Session, page: int = 1, limit: int = 10):
    try:
        offset = (page - 1) * limit
        query = (
            db.query(ServiceProvider)
            .options(
                joinedload(ServiceProvider.category),
                joinedload(ServiceProvider.subcategory_charges).joinedload(VendorSubcategoryCharge.subcategory)
            )
        )

        total = query.count()
        vendors = query.offset(offset).limit(limit).all()

        vendor_responses = []
        for vendor in vendors:
            vendor_responses.append(build_vendor_response(db, vendor))

        return vendor_responses, total
    except Exception as e:
        logger.error(f"Error fetching vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def delete_vendor(db: Session, vendor_id: int) -> None:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        logger.error(f"Vendor not found for ID {vendor_id}")
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    try:
        db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).delete()
        db.delete(vendor)
        db.commit()
        logger.info(f"Vendor deleted successfully: ID {vendor_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in delete_vendor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def vendor_login(db: Session, email: str, password: str) -> Tuple[VendorResponse, str]:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    if not verify_password(password, vendor.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    vendor.last_login = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    vendor_response = build_vendor_response(db, vendor)
    return vendor_response, "Login successful"

def create_vendor(db: Session, vendor: VendorCreate) -> ServiceProvider:
    existing = get_vendor_by_email(db, email=vendor.email)
    if existing and existing.otp_verified:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if existing and not existing.otp_verified:
        existing.full_name = vendor.full_name
        existing.phone = vendor.phone
        existing.password = get_password_hash(vendor.password)
        existing.terms_accepted = vendor.terms_accepted
        existing.identity_doc_type = vendor.identity_doc_type
        existing.identity_doc_number = vendor.identity_doc_number
        existing.new_fcm_token = vendor.new_fcm_token
        existing.old_fcm_token = vendor.old_fcm_token
        existing.latitude = vendor.latitude
        existing.longitude = vendor.longitude
        existing.device_name = vendor.device_name
        existing.step = 0
        existing.otp = generate_otp()
        existing.otp_created_at = datetime.utcnow()
        existing.otp_last_sent_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        send_email_otp(vendor.email, existing.otp)
        return existing
    
    hashed_password = get_password_hash(vendor.password)
    otp = generate_otp()
    now = datetime.utcnow()
    
    db_vendor = ServiceProvider(
        full_name=vendor.full_name,
        email=vendor.email,
        phone=vendor.phone,
        password=hashed_password,
        terms_accepted=vendor.terms_accepted,
        identity_doc_type=vendor.identity_doc_type,
        identity_doc_number=vendor.identity_doc_number,
        new_fcm_token=vendor.new_fcm_token,
        old_fcm_token=vendor.old_fcm_token,
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        device_name=vendor.device_name,
        step=0,
        otp=otp,
        otp_created_at=now,
        otp_last_sent_at=now,
        otp_verified=False,
        last_login=now,
        last_device_update=now,
        status='pending',
        admin_status='inactive',
        work_status='work_on'
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    send_email_otp(vendor.email, otp)
    return db_vendor

def verify_vendor_otp(db: Session, email: str, otp: str) -> Tuple[VendorResponse, str]:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        return None, "Vendor not found"
    
    if vendor.otp_attempts >= MAX_OTP_ATTEMPTS:
        return None, "Maximum OTP attempts exceeded"
    
    if vendor.otp != otp:
        vendor.otp_attempts += 1
        db.commit()
        return None, "Invalid OTP"
    
    if (datetime.utcnow() - vendor.otp_created_at) > timedelta(minutes=OTP_EXPIRY_MINUTES):
        return None, "OTP expired"
    
    vendor.otp_verified = True
    vendor.otp_attempts = 0
    vendor.status = 'pending'
    vendor.step = 1
    vendor.last_login = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    # Send welcome email
    try:
        send_email(
            recipient=vendor.email,
            template_name="welcome",
            context={"name": vendor.full_name}
        )
        send_notification(
            recipient=vendor.email,
            notification_type=NotificationType.vendor_welcome,
            message=f"Welcome, {vendor.full_name}! Your account has been successfully verified.",
            recipient_id=vendor.id,
            fcm_token=vendor.new_fcm_token or vendor.old_fcm_token
        )
        logger.info(f"Welcome email and notification sent to vendor {vendor.id}")
    except Exception as e:
        logger.warning(f"Failed to send welcome email/notification to vendor {vendor.id}: {str(e)}")
    
    vendor_response = build_vendor_response(db, vendor)
    return vendor_response, "OTP verified successfully"

def resend_otp(db: Session, email: str) -> None:
    vendor = get_vendor_by_email(db, email)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if vendor.otp_last_sent_at and (datetime.utcnow() - vendor.otp_last_sent_at) < timedelta(minutes=OTP_RESEND_COOLDOWN_MINUTES):
        raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")
    
    if vendor.otp_attempts >= MAX_OTP_RESENDS:
        raise HTTPException(status_code=429, detail="Maximum OTP resend attempts exceeded")
    
    otp = generate_otp()
    vendor.otp = otp
    vendor.otp_created_at = datetime.utcnow()
    vendor.otp_last_sent_at = datetime.utcnow()
    vendor.otp_attempts = 0
    send_email_otp(email, otp)
    db.commit()

def update_vendor_address(db: Session, vendor_id: int, update: AddressDetailsUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    if vendor.step == 0:
        vendor.step = 2
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)

def update_vendor_bank(db: Session, vendor_id: int, update: BankDetailsUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    if vendor.step == 1:
        vendor.step = 3
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)

def update_vendor_work(db: Session, vendor_id: int, update: WorkDetailsUpdate) -> VendorResponse:
    logger.debug(f"Updating work details for vendor_id: {vendor_id}, update: {update.dict()}")
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        logger.error(f"Vendor with ID {vendor_id} not found")
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")

    if not vendor.otp_verified:
        logger.error(f"Vendor {vendor_id} not OTP verified")
        raise HTTPException(status_code=403, detail="OTP verification required")

    if not update.subcategory_charges:
        logger.error("No subcategory charges provided")
        raise HTTPException(status_code=400, detail="At least one subcategory charge is required")

    category = get_category_by_id(db, update.category_id)
    if not category:
        logger.error(f"Category {update.category_id} not found")
        raise HTTPException(status_code=404, detail=f"Category {update.category_id} not found")

    try:
        logger.debug(f"Setting category_id: {update.category_id}")
        vendor.category_id = update.category_id
        vendor.subcategory_charges.clear()

        for charge in update.subcategory_charges:
            logger.debug(f"Processing subcategory charge: {charge}")
            if charge.service_charge < 0:
                logger.error(f"Negative service charge: {charge.service_charge}")
                raise HTTPException(status_code=400, detail="Service charge cannot be negative")
            subcategory = get_subcategory_by_id(db, charge.subcategory_id)
            if not subcategory:
                logger.error(f"Subcategory {charge.subcategory_id} not found")
                raise HTTPException(status_code=404, detail=f"Subcategory {charge.subcategory_id} not found")
            if subcategory.category_id != update.category_id:
                logger.error(f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
                raise HTTPException(status_code=400, detail=f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
            if subcategory.status not in [SubCategoryStatus.active, SubCategoryStatus.inactive]:
                logger.error(f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}"
                )

            new_charge = VendorSubcategoryCharge(
                subcategory_id=charge.subcategory_id,
                category_id=update.category_id,
                service_charge=charge.service_charge,
            )
            logger.debug(f"Inserting charge: vendor_id={vendor_id}, subcategory_id={charge.subcategory_id}, service_charge={charge.service_charge}")
            vendor.subcategory_charges.append(new_charge)

        if vendor.step == 2:
            vendor.step = 4
        vendor.status = 'approved'
        vendor.last_device_update = datetime.utcnow()
        logger.debug(f"Committing changes for vendor_id: {vendor_id}")
        db.commit()
        db.refresh(vendor)
        
        logger.info(f"Vendor work details updated successfully: {vendor.id}")
        return build_vendor_response(db, vendor)
    except HTTPException as e:
        db.rollback()
        logger.error(f"HTTPException in update_vendor_work: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError in update_vendor_work: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in update_vendor_work: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def update_vendor_documents(db: Session, vendor_id: int, profile_pic: UploadFile | None, identity_doc: UploadFile, bank_doc: UploadFile, address_doc: UploadFile) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
    max_file_size = 5 * 1024 * 1024
    upload_base_dir = os.getenv("UPLOAD_DIR", "uploads")

    def save_file(file: UploadFile, subdir: str, prefix: str) -> str:
        try:
            ext = file.filename.split(".")[-1].lower() if file.filename else ""
            if ext not in allowed_extensions:
                logger.error(f"Invalid file type for {prefix}: {ext}")
                raise HTTPException(status_code=400, detail=f"Invalid {prefix} file type. Allowed: {', '.join(allowed_extensions)}")
            if file.size > max_file_size:
                logger.error(f"{prefix} file too large: {file.size} bytes")
                raise HTTPException(status_code=400, detail=f"{prefix} file too large. Max size: {max_file_size} bytes")
            
            file_path = Path(upload_base_dir) / subdir / f"{prefix}_{vendor_id}.{ext}"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("wb") as buffer:
                buffer.write(file.file.read())
            logger.debug(f"Saved {prefix} file to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving {prefix} file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save {prefix} file: {str(e)}")

    try:
        if profile_pic:
            vendor.profile_pic = save_file(profile_pic, "profiles", "profile")
        
        vendor.identity_doc_url = save_file(identity_doc, "documents", "identity")
        vendor.bank_doc_url = save_file(bank_doc, "documents", "bank")
        vendor.address_doc_url = save_file(address_doc, "documents", "address")
        
        if vendor.step == 3:
            vendor.step = 5
        vendor.last_device_update = datetime.utcnow()
        db.commit()
        db.refresh(vendor)
        
        logger.info(f"Documents updated successfully for vendor_id: {vendor_id}")
        return build_vendor_response(db, vendor)
    except HTTPException as e:
        db.rollback()
        logger.error(f"HTTPException in update_vendor_documents: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError in update_vendor_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in update_vendor_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def update_vendor_device(db: Session, vendor_id: int, update: VendorDeviceUpdate) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    vendor.last_device_update = datetime.utcnow()
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)

def change_vendor_admin_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if status not in ['active', 'inactive']:
        raise HTTPException(status_code=400, detail="Invalid admin status")
    
    vendor.admin_status = status
    db.commit()
    db.refresh(vendor)
    
    fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
    if fcm_token:
        try:
            send_notification(
                recipient=vendor.email,
                notification_type=NotificationType.admin_status_updated,
                message=f"Your account status has been updated to {status}",
                recipient_id=vendor.id,
                fcm_token=fcm_token
            )
            logger.info(f"Admin status notification sent to vendor {vendor_id}")
        except Exception as e:
            logger.warning(f"Failed to send admin status notification to vendor {vendor_id}: {str(e)}")
    
    return build_vendor_response(db, vendor)

def change_vendor_work_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    if not vendor.otp_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")
    
    if vendor.admin_status != 'active':
        raise HTTPException(status_code=403, detail="Vendor must be active to change work status")
    
    if status not in ['work_on', 'work_off']:
        raise HTTPException(status_code=400, detail="Invalid work status")
    
    vendor.work_status = status
    db.commit()
    db.refresh(vendor)
    
    return build_vendor_response(db, vendor)


# from datetime import datetime, timedelta
# from fastapi import HTTPException, UploadFile
# from passlib.context import CryptContext
# from sqlalchemy.orm import joinedload
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from app.utils.otp_utils import generate_otp, send_email_otp
# from app.core.security import get_password_hash
# from app.models.service_provider_model import ServiceProvider
# from app.models.vendor_subcategory_charge import VendorSubcategoryCharge
# from app.models.sub_category import SubCategory
# from app.models.category import Category
# from app.schemas.service_provider_schema import (
#     VendorCreate, VendorDeviceUpdate, AddressDetailsUpdate, 
#     BankDetailsUpdate, WorkDetailsUpdate, SubCategoryCharge, VendorResponse
# )
# from app.schemas.sub_category_schema import SubCategoryStatus
# import logging
# from typing import List, Tuple
# import os
# from pathlib import Path

# from app.utils.fcm import send_push_notification  
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OTP_EXPIRY_MINUTES = 5
# MAX_OTP_ATTEMPTS = 3
# MAX_OTP_RESENDS = 3
# OTP_RESEND_COOLDOWN_MINUTES = 1

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def get_vendor_by_email(db: Session, email: str) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.email == email).first()

# def get_vendor_by_id(db: Session, vendor_id: int) -> ServiceProvider:
#     return db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()

# def get_subcategory_by_id(db: Session, subcategory_id: int) -> SubCategory:
#     return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

# def get_category_by_id(db: Session, category_id: int) -> Category:
#     return db.query(Category).filter(Category.id == category_id).first()

# def attach_subcategory_charges(db: Session, vendor_id: int) -> List[SubCategoryCharge]:
#     charges = db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).all()
#     return [
#         SubCategoryCharge(subcategory_id=charge.subcategory_id, service_charge=charge.service_charge)
#         for charge in charges
#     ]

# # def build_vendor_response(db: Session, vendor: ServiceProvider) -> VendorResponse:
# #     """Common function to build VendorResponse object"""
# #     subcategory_charges = attach_subcategory_charges(db, vendor.id)
# #     return VendorResponse(
# #         id=vendor.id,
# #         full_name=vendor.full_name,
# #         email=vendor.email,
# #         phone=vendor.phone,
# #         address=vendor.address,
# #         state=vendor.state,
# #         city=vendor.city,
# #         pincode=vendor.pincode,
# #         account_holder_name=vendor.account_holder_name,
# #         account_number=vendor.account_number,
# #         ifsc_code=vendor.ifsc_code,
# #         upi_id=vendor.upi_id,
# #         identity_doc_type=vendor.identity_doc_type,
# #         identity_doc_number=vendor.identity_doc_number,
# #         identity_doc_url=vendor.identity_doc_url,
# #         bank_doc_type=vendor.bank_doc_type,
# #         bank_doc_number=vendor.bank_doc_number,
# #         bank_doc_url=vendor.bank_doc_url,
# #         address_doc_type=vendor.address_doc_type,
# #         address_doc_number=vendor.address_doc_number,
# #         address_doc_url=vendor.address_doc_url,
# #         category_id=vendor.category_id,
# #         profile_pic=vendor.profile_pic,
# #         step=vendor.step,  # Include step
# #         status=vendor.status,  # Map admin_status to status for frontend
# #         admin_status=vendor.admin_status,
# #         work_status=vendor.work_status,
# #         subcategory_charges=subcategory_charges
# #     )

# def build_vendor_response(db: Session, vendor: ServiceProvider) -> VendorResponse:
#     # Get Category Name
#     category_name = None
#     if vendor.category_id:
#         category = db.query(Category).filter(Category.id == vendor.category_id).first()
#         category_name = category.name if category else None

#     # Get SubCategory Names + Charges
#     subcategory_charges = []
#     charges = db.query(VendorSubcategoryCharge).filter(
#         VendorSubcategoryCharge.vendor_id == vendor.id
#     ).all()

#     for charge in charges:
#         subcat = db.query(SubCategory).filter(SubCategory.id == charge.subcategory_id).first()
#         subcategory_charges.append({
#             "subcategory_id": charge.subcategory_id,
#             "subcategory_name": subcat.name if subcat else None,
#             "service_charge": charge.service_charge,
#         })

#     return VendorResponse(
#         id=vendor.id,
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         address=vendor.address,
#         state=vendor.state,
#         city=vendor.city,
#         pincode=vendor.pincode,
#         account_holder_name=vendor.account_holder_name,
#         account_number=vendor.account_number,
#         ifsc_code=vendor.ifsc_code,
#         upi_id=vendor.upi_id,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         identity_doc_url=vendor.identity_doc_url,
#         bank_doc_type=vendor.bank_doc_type,
#         bank_doc_number=vendor.bank_doc_number,
#         bank_doc_url=vendor.bank_doc_url,
#         address_doc_type=vendor.address_doc_type,
#         address_doc_number=vendor.address_doc_number,
#         address_doc_url=vendor.address_doc_url,
#         category_id=vendor.category_id,
#         category_name=category_name,  # 👈 Name instead of just ID
#         profile_pic=vendor.profile_pic,
#         step=vendor.step,
#         status=vendor.status,
#         admin_status=vendor.admin_status,
#         work_status=vendor.work_status,
#         subcategory_charges=subcategory_charges
#     )


# def get_all_vendors(db: Session, page: int = 1, limit: int = 10):
#     """Retrieve all vendors with pagination and category/subcategory names efficiently."""
#     try:
#         offset = (page - 1) * limit

#         # Eager load category and subcategory charges with subcategory
#         query = (
#             db.query(ServiceProvider)
#             .options(
#                 joinedload(ServiceProvider.category),  # load Category
#                 joinedload(ServiceProvider.subcategory_charges).joinedload(VendorSubcategoryCharge.subcategory)  # load SubCategory
#             )
#         )

#         total = query.count()
#         vendors = query.offset(offset).limit(limit).all()

#         vendor_responses = []
#         for vendor in vendors:
#             # Category Name
#             category_name = vendor.category.name if vendor.category else None

#             # Subcategory names
#             subcategory_charges = []
#             for charge in vendor.subcategory_charges:
#                 subcategory_name = charge.subcategory.name if charge.subcategory else None
#                 subcategory_charges.append({
#                     "subcategory_id": charge.subcategory_id,
#                     "subcategory_name": subcategory_name,
#                     "service_charge": charge.service_charge
#                 })

#             vendor_responses.append(
#                 VendorResponse(
#                     id=vendor.id,
#                     full_name=vendor.full_name,
#                     email=vendor.email,
#                     phone=vendor.phone,
#                     address=vendor.address,
#                     state=vendor.state,
#                     city=vendor.city,
#                     pincode=vendor.pincode,
#                     account_holder_name=vendor.account_holder_name,
#                     account_number=vendor.account_number,
#                     ifsc_code=vendor.ifsc_code,
#                     upi_id=vendor.upi_id,
#                     identity_doc_type=vendor.identity_doc_type,
#                     identity_doc_number=vendor.identity_doc_number,
#                     identity_doc_url=vendor.identity_doc_url,
#                     bank_doc_type=vendor.bank_doc_type,
#                     bank_doc_number=vendor.bank_doc_number,
#                     bank_doc_url=vendor.bank_doc_url,
#                     address_doc_type=vendor.address_doc_type,
#                     address_doc_number=vendor.address_doc_number,
#                     address_doc_url=vendor.address_doc_url,
#                     category_id=vendor.category_id,
#                     category_name=category_name,
#                     profile_pic=vendor.profile_pic,
#                     step=vendor.step,
#                     status=vendor.status,
#                     admin_status=vendor.admin_status,
#                     work_status=vendor.work_status,
#                     subcategory_charges=subcategory_charges
#                 )
#             )

#         return vendor_responses, total

#     except Exception as e:
#         logger.error(f"Error fetching vendors: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")



# def delete_vendor(db: Session, vendor_id: int) -> None:
#     """Delete a vendor by ID."""
#     vendor = get_vendor_by_id(db, vendor_id)
#     if not vendor:
#         logger.error(f"Vendor not found for ID {vendor_id}")
#         raise HTTPException(status_code=404, detail="Vendor not found")
    
#     try:
#         db.query(VendorSubcategoryCharge).filter(VendorSubcategoryCharge.vendor_id == vendor_id).delete()
#         db.delete(vendor)
#         db.commit()
#         logger.info(f"Vendor deleted successfully: ID {vendor_id}")
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"Database error in delete_vendor: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in delete_vendor: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def vendor_login(db: Session, email: str, password: str) -> Tuple[VendorResponse, str]:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     if not verify_password(password, vendor.password):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     vendor.last_login = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     vendor_response = build_vendor_response(db, vendor)
#     return vendor_response, "Login successful"

# def create_vendor(db: Session, vendor: VendorCreate) -> ServiceProvider:
#     existing = get_vendor_by_email(db, email=vendor.email)
#     if existing and existing.otp_verified:
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     if existing and not existing.otp_verified:
#         existing.full_name = vendor.full_name
#         existing.phone = vendor.phone
#         existing.password = get_password_hash(vendor.password)
#         existing.terms_accepted = vendor.terms_accepted
#         existing.identity_doc_type = vendor.identity_doc_type
#         existing.identity_doc_number = vendor.identity_doc_number
#         existing.fcm_token = vendor.fcm_token
#         existing.latitude = vendor.latitude
#         existing.longitude = vendor.longitude
#         existing.device_name = vendor.device_name
#         existing.step = 0  # Initial step 0
#         existing.otp = generate_otp()
#         existing.otp_created_at = datetime.utcnow()
#         existing.otp_last_sent_at = datetime.utcnow()
#         db.commit()
#         db.refresh(existing)
#         send_email_otp(vendor.email, existing.otp)
#         return existing
    
#     hashed_password = get_password_hash(vendor.password)
#     otp = generate_otp()
#     now = datetime.utcnow()
    
#     db_vendor = ServiceProvider(
#         full_name=vendor.full_name,
#         email=vendor.email,
#         phone=vendor.phone,
#         password=hashed_password,
#         terms_accepted=vendor.terms_accepted,
#         identity_doc_type=vendor.identity_doc_type,
#         identity_doc_number=vendor.identity_doc_number,
#         fcm_token=vendor.fcm_token,
#         latitude=vendor.latitude,
#         longitude=vendor.longitude,
#         device_name=vendor.device_name,
#         step=0,  # Initial step 0
#         otp=otp,
#         otp_created_at=now,
#         otp_last_sent_at=now,
#         otp_verified=False,
#         last_login=now,
#         last_device_update=now,
#         status='pending',
#         admin_status='inactive',
#         work_status='work_on'
#     )
#     db.add(db_vendor)
#     db.commit()
#     db.refresh(db_vendor)
    
#     send_email_otp(vendor.email, otp)
#     return db_vendor

# def verify_vendor_otp(db: Session, email: str, otp: str) -> Tuple[VendorResponse, str]:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         return None, "Vendor not found"
    
#     if vendor.otp_attempts >= MAX_OTP_ATTEMPTS:
#         return None, "Maximum OTP attempts exceeded"
    
#     if vendor.otp != otp:
#         vendor.otp_attempts += 1
#         db.commit()
#         return None, "Invalid OTP"
    
#     if (datetime.utcnow() - vendor.otp_created_at) > timedelta(minutes=OTP_EXPIRY_MINUTES):
#         return None, "OTP expired"
    
#     vendor.otp_verified = True
#     vendor.otp_attempts = 0
#     vendor.status = 'pending'
#     vendor.step = 1  # Step 1 after OTP verify (address)
#     vendor.last_login = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     vendor_response = build_vendor_response(db, vendor)
#     return vendor_response, "OTP verified successfully"

# def resend_otp(db: Session, email: str) -> None:
#     vendor = get_vendor_by_email(db, email)
#     if not vendor:
#         raise HTTPException(status_code=404, detail="Vendor not found")
    
#     if vendor.otp_last_sent_at and (datetime.utcnow() - vendor.otp_last_sent_at) < timedelta(minutes=OTP_RESEND_COOLDOWN_MINUTES):
#         raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")
    
#     if vendor.otp_attempts >= MAX_OTP_RESENDS:
#         raise HTTPException(status_code=429, detail="Maximum OTP resend attempts exceeded")
    
#     otp = generate_otp()
#     vendor.otp = otp
#     vendor.otp_created_at = datetime.utcnow()
#     vendor.otp_last_sent_at = datetime.utcnow()
#     vendor.otp_attempts = 0
#     send_email_otp(email, otp)
#     db.commit()

# def update_vendor_address(db: Session, vendor_id: int, update: AddressDetailsUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     # Step update: Only if initial registration (step == 0)
#     if vendor.step == 0:
#         vendor.step = 2  # Address complete -> step 2 (bank)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     return build_vendor_response(db, vendor)

# def update_vendor_bank(db: Session, vendor_id: int, update: BankDetailsUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     # Step update: Only if initial (step == 1)
#     if vendor.step == 1:
#         vendor.step = 3  # Bank complete -> step 3 (work)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     return build_vendor_response(db, vendor)

# def update_vendor_work(db: Session, vendor_id: int, update: WorkDetailsUpdate) -> VendorResponse:
#     logger.debug(f"Updating work details for vendor_id: {vendor_id}, update: {update.dict()}")
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         logger.error(f"Vendor with ID {vendor_id} not found")
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")

#     if not vendor.otp_verified:
#         logger.error(f"Vendor {vendor_id} not OTP verified")
#         raise HTTPException(status_code=403, detail="OTP verification required")

#     if not update.subcategory_charges:
#         logger.error("No subcategory charges provided")
#         raise HTTPException(status_code=400, detail="At least one subcategory charge is required")

#     category = get_category_by_id(db, update.category_id)
#     if not category:
#         logger.error(f"Category {update.category_id} not found")
#         raise HTTPException(status_code=404, detail=f"Category {update.category_id} not found")

#     try:
#         logger.debug(f"Setting category_id: {update.category_id}")
#         vendor.category_id = update.category_id

#         logger.debug(f"Deleting existing charges for vendor_id: {vendor_id}")
#         vendor.subcategory_charges.clear()

#         for charge in update.subcategory_charges:
#             logger.debug(f"Processing subcategory charge: {charge}")
#             if charge.service_charge < 0:
#                 logger.error(f"Negative service charge: {charge.service_charge}")
#                 raise HTTPException(status_code=400, detail="Service charge cannot be negative")
#             subcategory = get_subcategory_by_id(db, charge.subcategory_id)
#             if not subcategory:
#                 logger.error(f"Subcategory {charge.subcategory_id} not found")
#                 raise HTTPException(status_code=404, detail=f"Subcategory {charge.subcategory_id} not found")
#             if subcategory.category_id != update.category_id:
#                 logger.error(f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
#                 raise HTTPException(status_code=400, detail=f"Subcategory {charge.subcategory_id} does not belong to category {update.category_id}")
#             if subcategory.status not in [SubCategoryStatus.active, SubCategoryStatus.inactive]:
#                 logger.error(f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}")
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Invalid status for subcategory {charge.subcategory_id}: {subcategory.status}"
#                 )

#             new_charge = VendorSubcategoryCharge(
#                 subcategory_id=charge.subcategory_id,
#                 category_id=update.category_id,
#                 service_charge=charge.service_charge,
#             )
#             logger.debug(f"Inserting charge: vendor_id={vendor_id}, subcategory_id={charge.subcategory_id}, service_charge={charge.service_charge}")
#             vendor.subcategory_charges.append(new_charge)

#         # Step update: Only if initial (step == 2)
#         if vendor.step == 2:
#             vendor.step = 4  # Work complete -> step 4 (document)
        
#         vendor.status = 'approved'
#         vendor.last_device_update = datetime.utcnow()
#         logger.debug(f"Committing changes for vendor_id: {vendor_id}")
#         db.commit()
#         db.refresh(vendor)
        
#         logger.info(f"Vendor work details updated successfully: {vendor.id}")
#         return build_vendor_response(db, vendor)
#     except HTTPException as e:
#         db.rollback()
#         logger.error(f"HTTPException in update_vendor_work: {str(e)}")
#         raise e
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"SQLAlchemyError in update_vendor_work: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in update_vendor_work: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def update_vendor_documents(db: Session, vendor_id: int, profile_pic: UploadFile | None, identity_doc: UploadFile, bank_doc: UploadFile, address_doc: UploadFile) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
#     max_file_size = 5 * 1024 * 1024  # 5MB
#     upload_base_dir = os.getenv("UPLOAD_DIR", "uploads")

#     def save_file(file: UploadFile, subdir: str, prefix: str) -> str:
#         try:
#             ext = file.filename.split(".")[-1].lower() if file.filename else ""
#             if ext not in allowed_extensions:
#                 logger.error(f"Invalid file type for {prefix}: {ext}")
#                 raise HTTPException(status_code=400, detail=f"Invalid {prefix} file type. Allowed: {', '.join(allowed_extensions)}")
#             if file.size > max_file_size:
#                 logger.error(f"{prefix} file too large: {file.size} bytes")
#                 raise HTTPException(status_code=400, detail=f"{prefix} file too large. Max size: {max_file_size} bytes")
            
#             file_path = Path(upload_base_dir) / subdir / f"{prefix}_{vendor_id}.{ext}"
#             file_path.parent.mkdir(parents=True, exist_ok=True)
#             with file_path.open("wb") as buffer:
#                 buffer.write(file.file.read())
#             logger.debug(f"Saved {prefix} file to {file_path}")
#             return str(file_path)
#         except Exception as e:
#             logger.error(f"Error saving {prefix} file: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Failed to save {prefix} file: {str(e)}")

#     try:
#         if profile_pic:
#             vendor.profile_pic = save_file(profile_pic, "profiles", "profile")
        
#         vendor.identity_doc_url = save_file(identity_doc, "documents", "identity")
#         vendor.bank_doc_url = save_file(bank_doc, "documents", "bank")
#         vendor.address_doc_url = save_file(address_doc, "documents", "address")
        
#         # Step update: Only if initial (step == 3)
#         if vendor.step == 3:
#             vendor.step = 5  # Documents complete -> step 5 (complete)
        
#         vendor.last_device_update = datetime.utcnow()
#         db.commit()
#         db.refresh(vendor)
        
#         logger.info(f"Documents updated successfully for vendor_id: {vendor_id}")
#         return build_vendor_response(db, vendor)
#     except HTTPException as e:
#         db.rollback()
#         logger.error(f"HTTPException in update_vendor_documents: {str(e)}")
#         raise e
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"SQLAlchemyError in update_vendor_documents: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error in update_vendor_documents: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# def update_vendor_device(db: Session, vendor_id: int, update: VendorDeviceUpdate) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     for field, value in update.dict(exclude_unset=True).items():
#         setattr(vendor, field, value)
    
#     vendor.last_device_update = datetime.utcnow()
#     db.commit()
#     db.refresh(vendor)
    
#     return build_vendor_response(db, vendor)

# def change_vendor_admin_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if status not in ['active', 'inactive']:
#         raise HTTPException(status_code=400, detail="Invalid admin status")
    
#     vendor.admin_status = status
#     db.commit()
#     db.refresh(vendor)
#     if vendor.fcm_token:
#         try:
#             send_push_notification(
#                 token=vendor.fcm_token,
#                 title="Status Update",
#                 body=f"Your account status has been updated to {status}"
#             )
#         except Exception as e:
#             logger.warning(f"FCM notification failed for vendor {vendor_id}: {str(e)}")


#     return build_vendor_response(db, vendor)

# def change_vendor_work_status(db: Session, vendor_id: int, status: str) -> VendorResponse:
#     vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
#     if not vendor:
#         raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
#     if not vendor.otp_verified:
#         raise HTTPException(status_code=403, detail="OTP verification required")
    
#     if vendor.admin_status != 'active':
#         raise HTTPException(status_code=403, detail="Vendor must be active to change work status")
    
#     if status not in ['work_on', 'work_off']:
#         raise HTTPException(status_code=400, detail="Invalid work status")
    
#     vendor.work_status = status
#     db.commit()
#     db.refresh(vendor)
    
#     return build_vendor_response(db, vendor)