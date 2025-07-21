from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Table
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base

# Association table for many-to-many relationship between providers and services
provider_services = Table(
    "provider_services",
    Base.metadata,
    Column("provider_id", Integer, ForeignKey("service_providers.id")),
    Column("service_id", Integer, ForeignKey("services.id"))
)


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    # Verification
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)

    # Admin Status Control
    last_login = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, suspended, etc.

    # Service Details
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sub_category_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    service_locations = Column(JSONB, nullable=False)  # List[str]
    address = Column(String, nullable=True)
    road = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    about = Column(String, nullable=True)

    # Bank Details
    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)

    # Documents
    profile_pic_path = Column(String, nullable=True)
    address_proof_path = Column(String, nullable=True)
    bank_statement_path = Column(String, nullable=True)

    # System Info
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="providers")
    sub_category = relationship("SubCategory", back_populates="providers")
    services = relationship("Service", secondary=provider_services, back_populates="providers")

    def __repr__(self):
        return f"<ServiceProvider(id={self.id}, email='{self.email}', phone='{self.phone}')>"
