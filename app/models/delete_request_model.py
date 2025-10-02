# app/models/delete_request_model.py
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class DeleteRequest(Base):
    __tablename__ = "delete_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)       # अगर user से request है
    vendor_id = Column(Integer, nullable=True)     # अगर vendor से request है
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    role = Column(String, nullable=False)          # "user" or "vendor"
    request_date = Column(DateTime(timezone=True), server_default=func.now())
