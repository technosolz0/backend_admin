
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Union
import os

from app.database import SessionLocal
from app.models.user import User
from app.models.service_provider_model import ServiceProvider

# 🔐 Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# 🔐 Unified OAuth2 Bearer (shared for user/vendor)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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

# ✅ FIXED: Unified JWT Auth Dependency (User or Vendor)
def get_current_identity(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Union[User, ServiceProvider]:  # ✅ FIXED: Return type is Union, not dict
    """
    Unified authentication that returns either a User or ServiceProvider object.
    """
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
            
    except JWTError as e:
        # Add logging for debugging
        print(f"JWT decode error: {str(e)}")
        raise credentials_exception

    # Fetch based on role
    if role == 'vendor':
        vendor = db.query(ServiceProvider).filter(ServiceProvider.email == email).first()
        if vendor is None:
            print(f"Vendor not found for email: {email}")
            raise credentials_exception
        return vendor
    else:  # default to user (role == 'user' or None)
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"User not found for email: {email}")
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

# Admin: get_current_admin (for admin-only routes)
def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    identity = get_current_identity(token=token, db=db)
    if not isinstance(identity, User) or not identity.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity
