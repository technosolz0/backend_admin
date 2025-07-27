from app.database import engine, Base

# Import all models here to register them with SQLAlchemy's Base
from app.models import (
    user,
    service_provider_model,
    category,
    sub_category,
    service,
    booking_model,          # <-- NEW: Booking model
)

print("✅ Creating all tables in the database...")
Base.metadata.create_all(bind=engine)
print("🎉 Done creating tables.")
