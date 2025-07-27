from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SubCategory(Base):
    __tablename__ = 'sub_categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    status = Column(String, default='Active')

    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship("Category", back_populates="sub_categories")
    services = relationship("Service", back_populates="sub_category")  # ✅ Add this
    providers = relationship("ServiceProvider", back_populates="sub_category")
