
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class VendorSubcategoryCharge(Base):
    __tablename__ = "vendor_subcategory_charges"

    vendor_id = Column(Integer, ForeignKey("service_providers.id"), primary_key=True)
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    service_charge = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # ORM relationships
    vendor = relationship("ServiceProvider", back_populates="subcategory_charges")
    subcategory = relationship("SubCategory", back_populates="vendors_association")
    # category = relationship("Category", back_populates="category")
