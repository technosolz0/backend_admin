"""
Database Migration Script: Rename service_provider / service_providers to vendor / vendors.

This script safely renames:
1. Table 'service_providers' -> 'vendors'
2. Sequence 'service_providers_id_seq' -> 'vendors_id_seq'
3. Columns in related tables:
   - 'bookings.serviceprovider_id' or 'bookings.service_provider_id' -> 'bookings.vendor_id'
   - 'reviews.service_provider_id' -> 'reviews.vendor_id'
"""

import sys
import logging
from sqlalchemy import inspect, text
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def migrate_database():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Existing database tables: {tables}")

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Rename table service_providers -> vendors
            if "service_providers" in tables and "vendors" not in tables:
                logger.info("Renaming table 'service_providers' to 'vendors'...")
                conn.execute(text("ALTER TABLE service_providers RENAME TO vendors;"))
                logger.info("✅ Table 'service_providers' successfully renamed to 'vendors'.")
                
                # PostgreSQL sequence update
                if engine.dialect.name == "postgresql":
                    logger.info("Updating PostgreSQL sequence name if present...")
                    conn.execute(text("ALTER SEQUENCE IF EXISTS service_providers_id_seq RENAME TO vendors_id_seq;"))
            elif "vendors" in tables:
                logger.info("Table 'vendors' already exists.")

            # Refresh inspector after table rename
            inspector = inspect(engine)
            
            # 2. Update columns in 'bookings' table
            if "bookings" in tables:
                booking_cols = [col["name"] for col in inspector.get_columns("bookings")]
                if "serviceprovider_id" in booking_cols and "vendor_id" not in booking_cols:
                    logger.info("Renaming column 'bookings.serviceprovider_id' to 'vendor_id'...")
                    conn.execute(text("ALTER TABLE bookings RENAME COLUMN serviceprovider_id TO vendor_id;"))
                    logger.info("✅ Column 'bookings.serviceprovider_id' renamed to 'vendor_id'.")
                elif "service_provider_id" in booking_cols and "vendor_id" not in booking_cols:
                    logger.info("Renaming column 'bookings.service_provider_id' to 'vendor_id'...")
                    conn.execute(text("ALTER TABLE bookings RENAME COLUMN service_provider_id TO vendor_id;"))
                    logger.info("✅ Column 'bookings.service_provider_id' renamed to 'vendor_id'.")

            # 3. Update columns in 'reviews' table
            if "reviews" in tables:
                review_cols = [col["name"] for col in inspector.get_columns("reviews")]
                if "service_provider_id" in review_cols and "vendor_id" not in review_cols:
                    logger.info("Renaming column 'reviews.service_provider_id' to 'vendor_id'...")
                    conn.execute(text("ALTER TABLE reviews RENAME COLUMN service_provider_id TO vendor_id;"))
                    logger.info("✅ Column 'reviews.service_provider_id' renamed to 'vendor_id'.")

            trans.commit()
            logger.info("🎉 Database migration completed successfully!")
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            raise e

if __name__ == "__main__":
    migrate_database()
