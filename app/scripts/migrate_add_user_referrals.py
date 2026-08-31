import logging
from sqlalchemy import text
from app.database import engine, Base
from app.models.user_referral_model import UserReferral

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting database migration for User Referrals...")
    
    with engine.begin() as conn:
        # 1. Add columns to users table if they don't exist
        user_cols = [
            ("referral_code", "VARCHAR"),
            ("referred_by_id", "INTEGER REFERENCES users(id)"),
            ("applied_referral_code", "VARCHAR"),
            ("referral_type", "VARCHAR")
        ]
        for col_name, col_type in user_cols:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                logger.info(f"Added column '{col_name}' to users table.")
            except Exception as e:
                logger.info(f"Column '{col_name}' on users table skipped/exists: {e}")

        # Add index on users(referral_code)
        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_users_referral_code ON users (referral_code);"))
            logger.info("Created unique index ix_users_referral_code.")
        except Exception as e:
            logger.info(f"Index ix_users_referral_code skipped/exists: {e}")

        # 2. Add columns to app_configs table if they don't exist
        config_cols = [
            ("user_referrer_reward_amount", "FLOAT DEFAULT 50.0 NOT NULL"),
            ("user_referred_reward_amount", "FLOAT DEFAULT 50.0 NOT NULL"),
            ("min_referral_reward", "FLOAT DEFAULT 5.0 NOT NULL"),
            ("max_referral_reward", "FLOAT DEFAULT 40.0 NOT NULL"),
            ("is_random_referral_reward", "BOOLEAN DEFAULT TRUE NOT NULL")
        ]
        for col_name, col_type in config_cols:
            try:
                conn.execute(text(f"ALTER TABLE app_configs ADD COLUMN {col_name} {col_type};"))
                logger.info(f"Added column '{col_name}' to app_configs table.")
            except Exception as e:
                logger.info(f"Column '{col_name}' on app_configs table skipped/exists: {e}")

        # 3. Add user_referral_id column to wallet_transactions table
        try:
            conn.execute(text("ALTER TABLE wallet_transactions ADD COLUMN user_referral_id INTEGER REFERENCES user_referrals(id);"))
            logger.info("Added column 'user_referral_id' to wallet_transactions table.")
        except Exception as e:
            logger.info(f"Column 'user_referral_id' on wallet_transactions table skipped/exists: {e}")

    # 4. Create user_referrals table using SQLAlchemy metadata
    try:
        UserReferral.__table__.create(bind=engine, checkfirst=True)
        logger.info("Created or validated user_referrals table.")
    except Exception as e:
        logger.error(f"Error creating user_referrals table: {e}")

    logger.info("User Referrals database migration finished successfully!")

if __name__ == "__main__":
    migrate()
