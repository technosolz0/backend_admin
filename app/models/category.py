from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    status = Column(String, default='Active')

    sub_categories = relationship("SubCategory", back_populates="category", cascade="all, delete")
    providers = relationship("ServiceProvider", back_populates="category")
