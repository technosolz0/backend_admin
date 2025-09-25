# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from dotenv import load_dotenv
# import os

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
# Base = declarative_base()


# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Logs all SQL queries (optional, useful for debugging)
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base for models
Base = declarative_base()

def init_db():
    """
    Call this function to automatically create/update all tables based on models.
    Note: This won't handle column type changes or drops.
    For production-safe migrations, use Alembic.
    """
    import app.models  # Import all models to register them with Base
    Base.metadata.create_all(bind=engine)
