from app.database import Base, engine
from app.models import category  # make sure your category model is imported

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
