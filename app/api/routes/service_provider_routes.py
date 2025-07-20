from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from app.core.security import get_db
from app.models.service_provider_model import ServiceProvider
from app.schemas.service_provider_schema import ServiceProviderOut, ServiceProviderCreate
import os
import shutil
from uuid import uuid4

router = APIRouter(prefix="/serviceproviders", tags=["ServiceProviders"])

# POST: Register new service provider
@router.post("/", response_model=ServiceProviderOut, status_code=status.HTTP_201_CREATED)
def create_service_provider(
    user_id: int = Form(...),
    category: str = Form(...),
    service_locations: str = Form(...),
    address: str = Form(...),
    road: str = Form(None),
    landmark: str = Form(None),
    pin_code: str = Form(None),
    experience_years: int = Form(None),
    about: str = Form(None),
    bank_name: str = Form(...),
    account_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    profile_pic: UploadFile = File(...),
    address_proof: UploadFile = File(...),
    bank_statement: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    def save_file(upload: UploadFile, folder="static/uploads"):
        filename = f"{uuid4().hex}_{upload.filename}"
        file_path = os.path.join(folder, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return f"/{file_path}"

    profile_pic_path = save_file(profile_pic)
    address_proof_path = save_file(address_proof)
    bank_statement_path = save_file(bank_statement)

    new_provider = ServiceProvider(
        user_id=user_id,
        category=category,
        service_locations=service_locations,
        address=address,
        road=road,
        landmark=landmark,
        pin_code=pin_code,
        experience_years=experience_years,
        about=about,
        bank_name=bank_name,
        account_name=account_name,
        account_number=account_number,
        ifsc_code=ifsc_code,
        profile_pic_path=profile_pic_path,
        address_proof_path=address_proof_path,
        bank_statement_path=bank_statement_path,
    )
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return new_provider


# GET: List all service providers
@router.get("/", response_model=list[ServiceProviderOut])
def list_service_providers(db: Session = Depends(get_db)):
    return db.query(ServiceProvider).all()


# GET: Get a service provider by ID
@router.get("/{provider_id}", response_model=ServiceProviderOut)
def get_service_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(ServiceProvider).filter(ServiceProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Service provider not found")
    return provider


# DELETE: Delete a service provider
@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(ServiceProvider).filter(ServiceProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Service provider not found")
    db.delete(provider)
    db.commit()
