from sqlalchemy.orm import Session
from app.models.referral_config_model import ReferralConfig
from app.schemas.referral_config_schema import ReferralConfigUpdate

def get_referral_config(db: Session) -> ReferralConfig:
    """Get the active referral configuration or create a default record if missing."""
    config = db.query(ReferralConfig).first()
    if not config:
        config = ReferralConfig(
            referrer_reward_amount=100.0,
            referred_vendor_reward_amount=50.0,
            user_referrer_reward_amount=50.0,
            user_referred_reward_amount=50.0,
            min_referral_reward=5.0,
            max_referral_reward=40.0,
            is_random_referral_reward=False,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def update_referral_config(db: Session, update_data: ReferralConfigUpdate) -> ReferralConfig:
    """Update referral configuration values."""
    config = get_referral_config(db)
    data = update_data.model_dump(exclude_unset=True) if hasattr(update_data, 'model_dump') else update_data.dict(exclude_unset=True)

    for field, value in data.items():
        if value is not None:
            setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config
