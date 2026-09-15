# NEW_NAME: category_model.py
from sqlalchemy import Column, Enum, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.category_schema import CategoryStatus

class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    status = Column(Enum(CategoryStatus), default=CategoryStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sub_categories = relationship("SubCategory", back_populates="category", cascade="all, delete")
    vendors = relationship("Vendor", back_populates="category")

    # vendor_subcategory_charges = relationship("VendorSubcategoryCharge", back_populates="category")
