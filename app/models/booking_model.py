# # app/models/booking_model.py
# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
# from sqlalchemy.orm import relationship
# from datetime import datetime
# import enum
# from app.database import Base


# class BookingStatus(str, enum.Enum):
#     pending = "pending"
#     accepted = "accepted"
#     cancelled = "cancelled"
#     completed = "completed"


# class Booking(Base):
#     __tablename__ = "bookings"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     serviceprovider_id = Column(Integer, ForeignKey("service_providers.id"))

#     category_id = Column(Integer, ForeignKey("categories.id"))
#     subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))
#     # service_id = Column(Integer, ForeignKey("services.id"))

#     scheduled_time = Column(DateTime, nullable=True)
#     status = Column(Enum(BookingStatus), default=BookingStatus.pending)

#     created_at = Column(DateTime, default=datetime.utcnow)

#     otp = Column(String, nullable=True)
#     otp_created_at = Column(DateTime, nullable=True)

#     # Optional: relationships
#     user = relationship("User", backref="bookings")
#     service_provider = relationship("ServiceProvider", backref="bookings")
# app/models/booking_model.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    cancelled = "cancelled"
    completed = "completed"


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    cancelled = "cancelled"
    completed = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    serviceprovider_id = Column(Integer, ForeignKey("service_providers.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"))
    scheduled_time = Column(DateTime, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="bookings")
    service_provider = relationship("ServiceProvider", backref="bookings")
    category = relationship("Category", backref="bookings")
    subcategory = relationship("SubCategory", backref="bookings")