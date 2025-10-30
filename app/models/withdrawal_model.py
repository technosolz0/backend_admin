# app/models/withdrawal_model.py

from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class WithdrawalStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount requested (net after commission)
    gross_amount = Column(Float, nullable=False)  # Original amount before commission
    commission_amount = Column(Float, nullable=False)  # Commission deducted (10%)
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING, nullable=False)
    bank_account = Column(String(255), nullable=True)  # Bank account identifier
    notes = Column(Text, nullable=True)  # Vendor's notes
    admin_message = Column(Text, nullable=True)  # Admin's custom message
    admin_id = Column(Integer, nullable=True)  # Admin who processed it
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)  # When admin processed
    completed_at = Column(DateTime, nullable=True)  # When money transferred
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("ServiceProvider", backref="withdrawals")

    def __repr__(self):
        return f"<Withdrawal(id={self.id}, vendor_id={self.vendor_id}, amount={self.amount}, status={self.status})>"