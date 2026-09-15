from sqlalchemy.orm import Session
from app.models.app_config_model import AppConfig
from app.schemas.app_config_schema import AppConfigUpdate, AppConfigCreate

class AppConfigCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_config(self, platform: str = "android") -> AppConfig:
        """Fetch the app configuration for the given platform (or default). Creates default row if missing."""
        config = self.db.query(AppConfig).filter(AppConfig.platform == platform).first()
        if not config:
            # Fallback to first available config or create default
            config = self.db.query(AppConfig).first()
        
        if not config:
            config = AppConfig(
                platform=platform,
                latest_version="1.0.0",
                min_supported_version="1.0.0",
                force_update=False,
                play_store_url="https://play.google.com/store/apps/details?id=com.serwex.partner",
                update_message="A new version of Serwex is available. Please update to continue.",
                referrer_reward_amount=100.0,
                referred_vendor_reward_amount=50.0,
                user_referrer_reward_amount=50.0,
                user_referred_reward_amount=50.0,
                min_referral_reward=5.0,
                max_referral_reward=40.0,
                is_random_referral_reward=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        else:
            updated = False
            if config.referrer_reward_amount is None:
                config.referrer_reward_amount = 100.0
                updated = True
            if config.referred_vendor_reward_amount is None:
                config.referred_vendor_reward_amount = 50.0
                updated = True
            if config.user_referrer_reward_amount is None:
                config.user_referrer_reward_amount = 50.0
                updated = True
            if config.user_referred_reward_amount is None:
                config.user_referred_reward_amount = 50.0
                updated = True
            if config.min_referral_reward is None:
                config.min_referral_reward = 5.0
                updated = True
            if config.max_referral_reward is None:
                config.max_referral_reward = 40.0
                updated = True
            if config.is_random_referral_reward is None:
                config.is_random_referral_reward = True
                updated = True
            if updated:
                self.db.commit()
                self.db.refresh(config)

        return config

    def create_or_update_config(self, config_data: dict, platform: str = "android") -> AppConfig:
        """Create or update app configuration (admin)."""
        config = self.db.query(AppConfig).filter(AppConfig.platform == platform).first()
        if not config:
            config = self.db.query(AppConfig).first()

        if config:
            for key, value in config_data.items():
                if value is not None and hasattr(config, key):
                    setattr(config, key, value)
            self.db.commit()
            self.db.refresh(config)
        else:
            config = AppConfig(**config_data)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config
