from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    category = Column(String)
    service_locations = Column(String)
    address = Column(String)
    road = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    about = Column(String, nullable=True)

    bank_name = Column(String)
    account_name = Column(String)
    account_number = Column(String)
    ifsc_code = Column(String)

    profile_pic_path = Column(String)
    address_proof_path = Column(String)
    bank_statement_path = Column(String)

    user = relationship("User")  # assuming you have a User model
