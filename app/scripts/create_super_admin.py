from app.database import SessionLocal
from app.models.user import User, UserStatus
from app.core.security import get_password_hash

def create_super_admin():
    db = SessionLocal()

    email = "admin@servex.com"
    password = "SuperSecure@123"
    name = "Servex Admin"
    mobile = "9999999999"  # <-- Add mobile here

    if db.query(User).filter(User.email == email).first():
        print("Super admin already exists.")
        return

    user = User(
        name=name,
        email=email,
        mobile=mobile,  # <-- Assign mobile here
        hashed_password=get_password_hash(password),
        status=UserStatus.active,
        is_superuser=True,
        is_verified=True
    )

    db.add(user)
    db.commit()
    print(f"✅ Super admin created successfully: {email}")

if __name__ == "__main__":
    create_super_admin()
