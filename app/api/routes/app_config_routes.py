from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.encoders import jsonable_encoder

from app.core.security import get_db, get_current_admin
from app.crud.app_config_crud import AppConfigCRUD
from app.schemas.app_config_schema import AppConfigResponse, AppConfigUpdate
from app.core.redis import get_cache, set_cache, delete_cache_pattern

router = APIRouter()

@router.get("/app-config", response_model=AppConfigResponse, tags=["App Config"])
async def get_app_config(
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db)
):
    """Public endpoint for mobile apps to fetch latest version and force update configuration."""
    cache_key = f"app_config:{platform}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    crud = AppConfigCRUD(db)
    config = crud.get_config(platform=platform)
    if config:
        config_data = jsonable_encoder(config)
        await set_cache(cache_key, config_data, ttl_seconds=3600)  # Cache for 1 hour
    return config

@router.get("/admin/app-config", response_model=AppConfigResponse, tags=["App Config Admin"])
async def get_admin_app_config(
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to fetch current app configuration."""
    cache_key = f"app_config:{platform}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    crud = AppConfigCRUD(db)
    config = crud.get_config(platform=platform)
    if config:
        config_data = jsonable_encoder(config)
        await set_cache(cache_key, config_data, ttl_seconds=3600)
    return config

@router.put("/admin/app-config", response_model=AppConfigResponse, tags=["App Config Admin"])
async def update_admin_app_config(
    config_update: AppConfigUpdate,
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to update app configuration (version numbers, force update, Play Store link, etc.)."""
    crud = AppConfigCRUD(db)
    update_data = config_update.model_dump(exclude_unset=True) if hasattr(config_update, 'model_dump') else config_update.dict(exclude_unset=True)
    updated_config = crud.create_or_update_config(update_data, platform=platform)
    
    # Invalidate cached app_config for all platforms
    await delete_cache_pattern("app_config:*")
    return updated_config

