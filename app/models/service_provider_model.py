from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    profile_pic = Column(String)
    address = Column(String)
    state = Column(String)
    city = Column(String)
    pincode = Column(String)
    terms_accepted = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    account_holder_name = Column(String)
    account_number = Column(String)
    ifsc_code = Column(String)
    upi_id = Column(String)
    identity_doc_type = Column(String)
    identity_doc_number = Column(String)
    identity_doc_url = Column(String)
    bank_doc_type = Column(String)
    bank_doc_number = Column(String)
    bank_doc_url = Column(String)
    address_doc_type = Column(String)
    address_doc_number = Column(String)
    address_doc_url = Column(String)
    new_fcm_token = Column(String)  # Updated from fcm_token
    old_fcm_token = Column(String)  # Added for fallback
    last_login = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    device_name = Column(String)
    last_device_update = Column(DateTime)
    step = Column(Integer, default=0, nullable=False)  # Registration step (0-5)

    status = Column(SAEnum('pending', 'approved', 'rejected', 'inactive', name='vendor_status'), default='approved')
    admin_status = Column(SAEnum('active', 'inactive', name='admin_status'), default='inactive')
    work_status = Column(SAEnum('work_on', 'work_off', name='work_status'), default='work_on')

    otp = Column(String)
    otp_created_at = Column(DateTime)
    otp_verified = Column(Boolean, default=False)
    otp_attempts = Column(Integer, default=0)
    otp_last_sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="vendors")

    # Link to VendorSubcategoryCharge table
    subcategory_charges = relationship(
        "VendorSubcategoryCharge",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )

    # Shortcut to get subcategories directly
    subcategories = relationship(
        "SubCategory",
        secondary="vendor_subcategory_charges",
        viewonly=True
    )
    bank_accounts = relationship(
        "VendorBankAccount",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )