from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class AppConfigBase(BaseModel):
    platform: str = "android"
    latest_version: str = "1.0.0"
    min_supported_version: str = "1.0.0"
    force_update: bool = False
    play_store_url: Optional[str] = "https://play.google.com/store/apps/details?id=com.serwex.partner"
    app_store_url: Optional[str] = None
    update_message: Optional[str] = "A new version of Serwex is available. Please update to continue."
    referrer_reward_amount: float = 100.0
    referred_vendor_reward_amount: float = 50.0
    user_referrer_reward_amount: float = 50.0
    user_referred_reward_amount: float = 50.0
    min_referral_reward: float = 5.0
    max_referral_reward: float = 40.0
    is_random_referral_reward: bool = True

    @field_validator(
        "referrer_reward_amount",
        "referred_vendor_reward_amount",
        "user_referrer_reward_amount",
        "user_referred_reward_amount",
        "min_referral_reward",
        "max_referral_reward",
        mode="before"
    )
    @classmethod
    def default_float_if_none(cls, v, info):
        if v is None:
            defaults = {
                "referrer_reward_amount": 100.0,
                "referred_vendor_reward_amount": 50.0,
                "user_referrer_reward_amount": 50.0,
                "user_referred_reward_amount": 50.0,
                "min_referral_reward": 5.0,
                "max_referral_reward": 40.0,
            }
            return defaults.get(info.field_name, 0.0)
        return v

    @field_validator("is_random_referral_reward", mode="before")
    @classmethod
    def default_bool_if_none(cls, v):
        if v is None:
            return True
        return v

class AppConfigCreate(AppConfigBase):
    pass

class AppConfigUpdate(BaseModel):
    platform: Optional[str] = None
    latest_version: Optional[str] = None
    min_supported_version: Optional[str] = None
    force_update: Optional[bool] = None
    play_store_url: Optional[str] = None
    app_store_url: Optional[str] = None
    update_message: Optional[str] = None
    referrer_reward_amount: Optional[float] = None
    referred_vendor_reward_amount: Optional[float] = None
    user_referrer_reward_amount: Optional[float] = None
    user_referred_reward_amount: Optional[float] = None
    min_referral_reward: Optional[float] = None
    max_referral_reward: Optional[float] = None
    is_random_referral_reward: Optional[bool] = None

class AppConfigResponse(AppConfigBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

