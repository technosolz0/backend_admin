from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password, create_access_token, get_current_user
from app.schemas.admin_schema import AdminLoginSchema

router = APIRouter(prefix="/admin", tags=["Admin Authentication"])

# 🔌 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Superadmin-only Dependency
def get_super_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions (Admin only)",
        )
    return current_user

# 🔐 POST /admin/login
@router.post("/login")
def admin_login(credentials: AdminLoginSchema, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.email == credentials.email).first()

    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not admin.is_superuser:
        raise HTTPException(status_code=403, detail="You are not authorized as an admin")

    token = create_access_token(data={"sub": admin.email}, role="admin")
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
            "is_superuser": admin.is_superuser
        }
    }

# ✅ Example protected admin-only route
@router.get("/dashboard", dependencies=[Depends(get_super_admin)])
def admin_dashboard():
    return {"message": "Welcome to the Admin Dashboard!"}
