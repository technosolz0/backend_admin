# app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.models.user import User

def get_super_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions (admin only)",
        )
    return current_user
