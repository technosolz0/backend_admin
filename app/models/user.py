# from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
# from app.database import Base
# import enum
# from datetime import datetime
# from sqlalchemy.orm import relationship


# class UserStatus(str, enum.Enum):
#     active = "active"
#     blocked = "blocked"


# class LoginLog(Base):
#     __tablename__ = "login_logs"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     timestamp = Column(DateTime, default=datetime.utcnow)

#     user = relationship("User", back_populates="login_logs")


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     mobile = Column(String, unique=True, nullable=False)
#     hashed_password = Column(String, nullable=True)
#     status = Column(Enum(UserStatus), default=UserStatus.active)
#     is_superuser = Column(Boolean, default=False)
#     otp = Column(String, nullable=True)
#     otp_created_at = Column(DateTime, nullable=True)
#     is_verified = Column(Boolean, default=False)
#     fcm_token = Column(String, nullable=True)
#     last_login_at = Column(DateTime, nullable=True)
#     login_logs = relationship("LoginLog", back_populates="user", lazy='joined')
#     addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
#     bookings = relationship("Booking", back_populates="user")

from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime


class UserStatus(str, enum.Enum):
    active = "active"
    blocked = "blocked"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mobile = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.active)
    is_superuser = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    profile_pic = Column(String, nullable=True)  # URL or path to profile picture
    old_fcm_token = Column(String, nullable=True)  # Previous FCM token
    new_fcm_token = Column(String, nullable=True)  # Latest FCM token
    device_id = Column(String, nullable=True)  # Device identifier for new_fcm_token
    device_type = Column(String, nullable=True)  # e.g., iOS, Android
    os_version = Column(String, nullable=True)  # e.g., iOS 16.0, Android 13
    app_version = Column(String, nullable=True)  # e.g., 1.0.0
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)
    addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user")