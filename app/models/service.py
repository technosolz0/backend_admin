# # NEW_NAME: service_model.py
# from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, Integer, String, Boolean, JSON, Enum as SAEnum
# from sqlalchemy.orm import relationship
# from app.database import Base
# # from app.models.service_provider_model import provider_services  # Ensure this exists and is imported

# class Service(Base):
#     __tablename__ = 'services'

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     description = Column(String, nullable=True)
#     price = Column(Integer, nullable=True)
#     image = Column(String, nullable=True)
#     status = Column(String, default='Active')

#     category_id = Column(Integer, ForeignKey('categories.id'))
#     sub_category_id = Column(Integer, ForeignKey('sub_categories.id'))

#     category = relationship("Category", back_populates="services")
#     sub_category = relationship("SubCategory", back_populates="services")

#     # ✅ Add this reverse many-to-many relationship
#     # providers = relationship(
#     #     "ServiceProvider",
#     #     secondary=provider_services,
#     #     back_populates="services"
#     # )
