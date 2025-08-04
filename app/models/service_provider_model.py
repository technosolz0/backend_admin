from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Table, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

# Association table for many-to-many: ServiceProvider <-> SubCategory
vendor_subcategory_charges = Table(
    'vendor_subcategory_charges',
    Base.metadata,
    Column('vendor_id', Integer, ForeignKey('service_providers.id'), primary_key=True),
    Column('subcategory_id', Integer, ForeignKey('sub_categories.id'), primary_key=True),
    Column('service_charge', Float, nullable=False),
    extend_existing=True
)

# Enums
class VendorStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class WorkStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"

# Main Model
class ServiceProvider(Base):
    __tablename__ = "service_providers"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    
    profile_pic = Column(String, nullable=True)
    address = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    terms_accepted = Column(Boolean, default=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Bank Details
    account_holder_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)

    # KYC
    document_type = Column(String, nullable=True)
    document_number = Column(String, nullable=True)
    document_image = Column(String, nullable=True)

    # Device Info
    fcm_token = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    device_name = Column(String, nullable=True)
    last_device_update = Column(DateTime, nullable=True)

    # Status / OTP
    status = Column(Enum(VendorStatus), default=VendorStatus.PENDING)
    work_status = Column(Enum(WorkStatus), default=WorkStatus.OFFLINE)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    otp_verified = Column(Boolean, default=False)
    otp_attempts = Column(Integer, default=0)
    otp_last_sent = Column(DateTime, nullable=True)
    otp_last_sent_at = Column(DateTime, nullable=True)


    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subcategories = relationship(
        "SubCategory",
        secondary=vendor_subcategory_charges,
        back_populates="providers"
    )
    category = relationship("Category", back_populates="providers")
