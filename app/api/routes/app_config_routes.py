from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import get_db, get_current_admin
from app.crud.app_config_crud import AppConfigCRUD
from app.schemas.app_config_schema import AppConfigResponse, AppConfigUpdate

router = APIRouter()

@router.get("/app-config", response_model=AppConfigResponse, tags=["App Config"])
def get_app_config(
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db)
):
    """Public endpoint for mobile apps to fetch latest version and force update configuration."""
    crud = AppConfigCRUD(db)
    return crud.get_config(platform=platform)

@router.get("/admin/app-config", response_model=AppConfigResponse, tags=["App Config Admin"])
def get_admin_app_config(
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to fetch current app configuration."""
    crud = AppConfigCRUD(db)
    return crud.get_config(platform=platform)

@router.put("/admin/app-config", response_model=AppConfigResponse, tags=["App Config Admin"])
def update_admin_app_config(
    config_update: AppConfigUpdate,
    platform: str = Query("android", description="Platform: android or ios"),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Admin endpoint to update app configuration (version numbers, force update, Play Store link, etc.)."""
    crud = AppConfigCRUD(db)
    update_data = config_update.model_dump(exclude_unset=True) if hasattr(config_update, 'model_dump') else config_update.dict(exclude_unset=True)
    return crud.create_or_update_config(update_data, platform=platform)
