# NEW_NAME: user_address_model.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class UserAddress(Base):
    __tablename__ = "user_addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Full address details
    name = Column(String, nullable=False)  # Person name
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    country = Column(String, nullable=False, default="India")

    # Delivery type (Home/Work/Other)
    address_type = Column(String, default="Home")

    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")
