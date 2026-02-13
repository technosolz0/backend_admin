from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.service_provider_model import ServiceProvider
from app.database import SQLALCHEMY_DATABASE_URL

# Setup DB connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check Vendor ID 1 (or allow input)
    vendor_id = 1 
    vendor = db.query(ServiceProvider).filter(ServiceProvider.id == vendor_id).first()
    
    if vendor:
        print(f"Vendor ID: {vendor.id}")
        print(f"Full Name: '{vendor.full_name}'") # Quote to see empties
        print(f"Email: {vendor.email}")
        
        if vendor.full_name is None:
            print("ALERT: full_name is None!")
        elif vendor.full_name == "":
            print("ALERT: full_name is empty string!")
    else:
        print(f"Vendor with ID {vendor_id} not found.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
