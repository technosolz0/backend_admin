# from datetime import datetime, timedelta, timezone
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# import os

# from app.database import SessionLocal
# from app.models.user import User
# from app.models.service_provider_model import ServiceProvider  # ✅ Add this

# # 🔐 Security Setup
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")

# # 🔐 OAuth2 Password Bearers
# oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/auth/login")
# oauth2_scheme_vendor = OAuth2PasswordBearer(tokenUrl="/vendors/login")  # ✅ For vendors

# # ✅ Password hashing & verification
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password):
#     return pwd_context.hash(password)

# # ✅ JWT creation
# # def create_access_token(data: dict, expires_delta: timedelta = None):
# #     to_encode = data.copy()
# #     expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
# #     to_encode.update({"exp": expire})
# #     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
# #     return encoded_jwt

# def create_access_token(data: dict, expires_delta: timedelta = None, token_type: str = "access"):
#     """
#     Create JWT access or refresh tokens.
#     - Access token: short-lived (default 30 minutes)
#     - Refresh token: long-lived (default 30 days)
#     """
#     to_encode = data.copy()

#     if token_type == "refresh":
#         expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=30))
#     else:  # access token
#         expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))

#     to_encode.update({
#         "exp": expire,
#         "type": token_type
#     })

#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# # ✅ DB session dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ✅ JWT Auth Dependency (User)
# def get_current_user(
#     token: str = Depends(oauth2_scheme_user),
#     db: Session = Depends(get_db),
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate user credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception

#     user = db.query(User).filter(User.email == email).first()
#     if user is None:
#         raise credentials_exception
#     return user

# # ✅ JWT Auth Dependency (Vendor)
# def get_current_vendor(
#     token: str = Depends(oauth2_scheme_vendor),
#     db: Session = Depends(get_db),
# ) -> ServiceProvider:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate vendor credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception

#     vendor = db.query(ServiceProvider).filter(ServiceProvider.email == email).first()
#     if vendor is None:
#         raise credentials_exception
#     return vendor






# app/core/security.py - Updated with role in token and unified schemes
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from app.database import SessionLocal
from app.models.user import User
from app.models.service_provider_model import ServiceProvider

# 🔐 Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# 🔐 Unified OAuth2 Bearer (shared for user/vendor)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Use one scheme for simplicity

# ✅ Password hashing & verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ✅ JWT creation - Updated to include 'role'
def create_access_token(data: dict, expires_delta: timedelta = None, token_type: str = "access", role: str = "user"):
    """
    Create JWT access or refresh tokens with role.
    - role: 'user' or 'vendor'
    """
    to_encode = data.copy()

    if token_type == "refresh":
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=30))
    else:  # access token
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))

    to_encode.update({
        "exp": expire,
        "type": token_type,
        "role": role  # ✅ Add role
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ✅ DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Unified JWT Auth Dependency (User or Vendor)
def get_current_identity(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")  # 'user' or 'vendor'
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch based on role
    if role == 'vendor':
        vendor = db.query(ServiceProvider).filter(ServiceProvider.email == email).first()
        if vendor is None:
            raise credentials_exception
        return vendor
    else:  # default to user
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user

# Legacy: get_current_user (for user-only routes)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    identity = get_current_identity(token=token, db=db)
    if not isinstance(identity, User):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity

# Legacy: get_current_vendor (for vendor-only routes)
def get_current_vendor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ServiceProvider:
    identity = get_current_identity(token=token, db=db)
    if not isinstance(identity, ServiceProvider):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate vendor credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity