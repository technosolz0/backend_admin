# from sqlalchemy.orm import Session
# from typing import Optional
# from app.models.user import User, UserStatus
# from app.schemas.user_schema import UserCreate, UserUpdate
# from app.core.security import get_password_hash

# def get_user_by_email(db: Session, email: str):
#     return db.query(User).filter(User.email == email).first()

# def create_user(db: Session, user: UserCreate):
#     hashed_password = get_password_hash(user.password)
#     db_user = User(
#         name=user.name,
#         email=user.email,
#         hashed_password=hashed_password,
#         status=UserStatus.active
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_users(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(User).offset(skip).limit(limit).all()

# def delete_user(db: Session, user_id: int) -> bool:
#     user = db.query(User).get(user_id)
#     if not user:
#         return False
#     db.delete(user)
#     db.commit()
#     return True

# def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
#     user = db.query(User).get(user_id)
#     if not user:
#         return None
#     if data.name is not None:
#         user.name = data.name
#     if data.email is not None:
#         user.email = data.email
#     if data.password is not None:
#         user.hashed_password = get_password_hash(data.password)
#     if data.status is not None:
#         user.status = data.status
#     db.commit()
#     db.refresh(user)
#     return user

# def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
#     user = db.query(User).get(user_id)
#     if not user:
#         return None
#     user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
#     db.commit()
#     db.refresh(user)
#     return user


from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User, UserStatus
from app.schemas import user_schema
from app.utils.otp_utils import generate_otp
from app.utils.email_utils import send_email_otp
from datetime import datetime, timedelta
from app.core.security import get_password_hash


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user_with_otp(db: Session, user: user_schema.UserCreate):
    otp = generate_otp()
    db_user = User(
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        status=UserStatus.active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    send_email_otp(user.email, otp)
    return db_user, otp


def verify_otp(db: Session, email: str, otp: str):
    user = get_user_by_email(db, email)
    if not user or user.otp != otp:
        return None

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        return "expired"

    user.is_verified = True
    user.otp = None
    user.otp_created_at = None
    db.commit()
    db.refresh(user)
    return user


def resend_otp(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        return None

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    send_email_otp(user.email, otp)
    return otp


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def update_user(db: Session, user_id: int, data: user_schema.UserUpdate) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.mobile is not None:
        user.mobile = data.mobile
    if data.password is not None:
        user.hashed_password = get_password_hash(data.password)
    if data.status is not None:
        user.status = data.status
    db.commit()
    db.refresh(user)
    return user


def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.status = UserStatus.blocked if user.status == UserStatus.active else UserStatus.active
    db.commit()
    db.refresh(user)
    return user

def create_login_otp(db, email: str):
    user = db.query(User).filter(User.email == email, User.is_verified == True).first()
    if not user:
        return None

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    send_email_otp(email, otp)
    return otp

def verify_login_otp(db, email: str, otp: str):
    user = db.query(User).filter(User.email == email, User.is_verified == True).first()
    if not user:
        return None
    if user.otp != otp:
        return "invalid"

    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if datetime.utcnow() > expiry_time:
        return "expired"

    # ✅ clear OTP
    user.otp = None
    user.otp_created_at = None

    # ✅ update last login time
    user.last_login_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user