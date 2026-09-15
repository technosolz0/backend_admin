from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReferralConfigBase(BaseModel):
    referrer_reward_amount: float = 100.0
    referred_vendor_reward_amount: float = 50.0
    user_referrer_reward_amount: float = 50.0
    user_referred_reward_amount: float = 50.0
    min_referral_reward: float = 5.0
    max_referral_reward: float = 40.0
    is_random_referral_reward: bool = False

class ReferralConfigCreate(ReferralConfigBase):
    pass

class ReferralConfigUpdate(BaseModel):
    referrer_reward_amount: Optional[float] = None
    referred_vendor_reward_amount: Optional[float] = None
    user_referrer_reward_amount: Optional[float] = None
    user_referred_reward_amount: Optional[float] = None
    min_referral_reward: Optional[float] = None
    max_referral_reward: Optional[float] = None
    is_random_referral_reward: Optional[bool] = None

class ReferralConfigOut(ReferralConfigBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
