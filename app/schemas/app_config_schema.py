from pydantic import BaseModel
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

class AppConfigResponse(AppConfigBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
