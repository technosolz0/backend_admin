# app/models/delete_request_model.py
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class DeleteRequest(Base):
    __tablename__ = "delete_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)       # अगर user से request है
    vendor_id = Column(Integer, ForeignKey("service_providers.id"), nullable=True)     # अगर vendor से request है
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    role = Column(String, nullable=False)          # "user" or "vendor"
    request_date = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure delete request is from either user OR vendor, but not both or neither
    __table_args__ = (
        CheckConstraint(
            '(user_id IS NOT NULL AND vendor_id IS NULL) OR (user_id IS NULL AND vendor_id IS NOT NULL)',
            name='delete_request_xor_constraint'
        ),
    )

    user = relationship("User", backref="delete_requests")
    vendor = relationship("ServiceProvider", backref="delete_requests")
