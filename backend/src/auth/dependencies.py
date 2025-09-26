"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .jwt_auth import get_current_user as get_user_from_token
from .api_tokens import verify_api_token
from ..database import get_db
from ..models import User, APIToken


# Security scheme for bearer tokens
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Supports both JWT tokens and API tokens.
    Used for anonymous read access with optional authentication.
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Try JWT authentication first
    try:
        user_data = get_user_from_token(token)

        # Verify user exists in database
        user = db.query(User).filter(User.id == user_data["user_id"]).first()
        if user and user.is_active:
            user.update_last_login()
            db.commit()
            return {
                "user_id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
                "auth_type": "jwt"
            }
    except HTTPException:
        pass

    # Try API token authentication
    user = verify_api_token(token, db)
    if user:
        return {
            "user_id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
            "auth_type": "api_token"
        }

    # Invalid token but don't raise error (optional auth)
    return None


async def require_auth(
    current_user: Optional[dict] = Depends(get_optional_user)
) -> dict:
    """
    Require authentication. Raises 401 if not authenticated.
    Supports both JWT tokens and API tokens.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


async def require_admin(
    current_user: dict = Depends(require_auth)
) -> dict:
    """
    Require admin authentication. Raises 403 if not admin.
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user


# Legacy compatibility functions (used by existing mock auth in components.py)
def get_current_user():
    """Mock authentication - always returns None for anonymous access."""
    return None


def require_auth_legacy():
    """Mock authentication requirement - allows mock tokens for testing."""
    # For MVP testing, allow mock JWT tokens and API keys
    # In production, this would validate real tokens
    return {"user_id": "test_user", "username": "test"}  # Mock user