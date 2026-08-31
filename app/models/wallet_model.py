from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Ensure wallet belongs to either user OR vendor, but not both or neither
    __table_args__ = (
        CheckConstraint(
            '(user_id IS NOT NULL AND vendor_id IS NULL) OR (user_id IS NULL AND vendor_id IS NOT NULL)',
            name='wallet_xor_constraint'
        ),
    )

    user = relationship("User", backref="wallets")
    vendor = relationship("Vendor", backref="wallets")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referral_id = Column(Integer, ForeignKey("vendor_referrals.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # REFERRAL_BONUS_REFERRER, REFERRAL_BONUS_NEW_VENDOR, EARNING, WITHDRAWAL
    description = Column(String, nullable=True)
    status = Column(String, default="COMPLETED", nullable=False)
    reference_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="transactions")
    vendor = relationship("Vendor", backref="wallet_transactions")
    referral = relationship("VendorReferral", backref="wallet_transactions")


