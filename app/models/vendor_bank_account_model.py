# app/models/vendor_bank_account_model.py (NEW FILE)

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class VendorBankAccount(Base):
    __tablename__ = "vendor_bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    account_holder_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=False)
    ifsc_code = Column(String(20), nullable=False)
    bank_name = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    upi_id = Column(String(100), nullable=True)
    
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Documents
    bank_doc_type = Column(String(50), nullable=True)
    bank_doc_number = Column(String(100), nullable=True)
    bank_doc_url = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    vendor = relationship("ServiceProvider", back_populates="bank_accounts")