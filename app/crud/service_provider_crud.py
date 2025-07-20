from sqlalchemy.orm import Session
from app import models, schemas

def create_service_provider(db: Session, user_id: int, data: schemas.ServiceProviderCreate,
                            profile_pic_path: str, address_proof_path: str, bank_statement_path: str):
    service_provider = models.ServiceProvider(
        user_id=user_id,
        category=data.category,
        service_locations=",".join(data.service_locations),
        address=data.address,
        road=data.road,
        landmark=data.landmark,
        pin_code=data.pin_code,
        experience_years=data.experience_years,
        about=data.about,
        bank_name=data.bank_name,
        account_name=data.account_name,
        account_number=data.account_number,
        ifsc_code=data.ifsc_code,
        profile_pic_path=profile_pic_path,
        address_proof_path=address_proof_path,
        bank_statement_path=bank_statement_path,
    )
    db.add(service_provider)
    db.commit()
    db.refresh(service_provider)
    return service_provider
