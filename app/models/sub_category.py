# app/models/sub_category.py
# NEW_NAME: sub_category_model.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.sub_category_schema import SubCategoryStatus

class SubCategory(Base):
    __tablename__ = 'sub_categories'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    status = Column(Enum(SubCategoryStatus), default=SubCategoryStatus.active)

    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship("Category", back_populates="sub_categories")

    # Vendors linked through the association table (view only)
    vendors = relationship(
        "ServiceProvider",
        secondary="vendor_subcategory_charges",
        viewonly=True
    )

    # Association table ORM link
    vendors_association = relationship(
        "VendorSubcategoryCharge", 
        back_populates="subcategory"
    )
