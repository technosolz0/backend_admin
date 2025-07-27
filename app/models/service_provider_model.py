from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Table
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base

# Enums for status
class VendorStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"

class WorkStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"

# Many-to-many for services
provider_services = Table(
    "provider_services",
    Base.metadata,
    Column("provider_id", Integer, ForeignKey("service_providers.id")),
    Column("service_id", Integer, ForeignKey("services.id"))
)

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    status = Column(String, default=VendorStatus.PENDING)
    work_status = Column(String, default=WorkStatus.OFFLINE)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sub_category_id = Column(Integer, ForeignKey("sub_categories.id"), nullable=True)

    service_locations = Column(JSONB, nullable=False)
    address = Column(String, nullable=True)
    road = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    about = Column(String, nullable=True)

    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)

    profile_pic_path = Column(String, nullable=True)
    address_proof_path = Column(String, nullable=True)
    bank_statement_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=func.now())

    category = relationship("Category", back_populates="providers")
    sub_category = relationship("SubCategory", back_populates="providers")

    services = relationship("Service", secondary=provider_services, back_populates="providers")

    def __repr__(self):
        return f"<ServiceProvider(id={self.id}, email='{self.email}', phone='{self.phone}')>"
