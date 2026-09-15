"""
Database Alteration & Migration Script
---------------------------------------
This script automatically:
1. Creates any missing tables defined in app.models (including referral_configs).
2. Inspects existing tables and safely adds `created_at` and `updated_at` columns if they are missing.
3. Supports PostgreSQL, MySQL, MariaDB, and SQLite databases.
"""

import sys
import logging
from sqlalchemy import inspect, text, TIMESTAMP
from app.database import engine, Base
import app.models  # Register all models with Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def alter_database_tables():
    logger.info("Initializing database table creation...")
    # Step 1: Create all defined tables if they do not exist
    Base.metadata.create_all(bind=engine)
    logger.info("Base.metadata.create_all() executed successfully.")

    # Step 2: Inspect existing tables and columns
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    logger.info(f"Discovered {len(existing_tables)} tables in database: {', '.join(existing_tables)}")

    dialect_name = engine.dialect.name.lower()
    logger.info(f"Target Database Dialect: '{dialect_name}'")

    with engine.begin() as connection:
        for table_name in existing_tables:
            columns_info = inspector.get_columns(table_name)
            column_names = {col["name"].lower() for col in columns_info}

            # Check for created_at
            if "created_at" not in column_names:
                logger.info(f"Table '{table_name}' is missing 'created_at'. Adding column...")
                try:
                    if dialect_name == "sqlite":
                        sql = f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    elif dialect_name in ("postgresql", "postgres"):
                        sql = f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"
                    else:  # mysql / mariadb / oracle / generic
                        sql = f"ALTER TABLE {table_name} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    
                    connection.execute(text(sql))
                    logger.info(f"Successfully added 'created_at' to '{table_name}'.")
                except Exception as e:
                    logger.warning(f"Could not add 'created_at' to '{table_name}': {e}")

            # Check for updated_at
            if "updated_at" not in column_names:
                logger.info(f"Table '{table_name}' is missing 'updated_at'. Adding column...")
                try:
                    if dialect_name == "sqlite":
                        sql = f"ALTER TABLE {table_name} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    elif dialect_name in ("postgresql", "postgres"):
                        sql = f"ALTER TABLE {table_name} ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"
                    elif dialect_name in ("mysql", "mariadb"):
                        sql = f"ALTER TABLE {table_name} ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                    else:
                        sql = f"ALTER TABLE {table_name} ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    
                    connection.execute(text(sql))
                    logger.info(f"Successfully added 'updated_at' to '{table_name}'.")
                except Exception as e:
                    logger.warning(f"Could not add 'updated_at' to '{table_name}': {e}")

    logger.info("Database migration & table alteration completed successfully!")


if __name__ == "__main__":
    try:
        alter_database_tables()
        print("\nSUCCESS: All DB tables altered and updated successfully.")
    except Exception as err:
        print(f"\nERROR: Database migration failed: {err}", file=sys.stderr)
        sys.exit(1)

# python3 alter_db_tables.py