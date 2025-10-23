from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("service_providers.id"), nullable=True)
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
    vendor = relationship("ServiceProvider", backref="wallets")
