"""
Authentication API endpoints.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.admin import authenticate_user, change_password, create_user
from ..auth.api_tokens import (
    create_api_token,
    list_user_tokens,
    revoke_api_token,
)
from ..auth.dependencies import require_admin, require_auth
from ..auth.jwt_auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_user_token
from ..database import get_db
from ..models import User


# Pydantic schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    is_admin: bool = False


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class APITokenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    expires_in_days: int | None = Field(None, gt=0, le=365)


class APITokenResponse(BaseModel):
    id: str
    name: str
    description: str | None
    prefix: str
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class APITokenCreated(APITokenResponse):
    token: str  # Only returned on creation


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_user_token(
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/change-password")
async def change_user_password(
    password_data: PasswordChange,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    # Verify current password
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user or not user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Change password
    success = change_password(db, user.id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )

    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get current user information."""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


# Admin-only endpoints
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    from ..models.user import User

    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)."""
    try:
        user = create_user(
            db=db,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            is_admin=user_data.is_admin,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# API Token Management
@router.post("/api-tokens", response_model=APITokenCreated)
async def create_user_api_token(
    token_data: APITokenCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new API token for the current user."""
    try:
        raw_token, api_token = create_api_token(
            db=db,
            user_id=current_user["user_id"],
            name=token_data.name,
            description=token_data.description,
            expires_in_days=token_data.expires_in_days,
        )

        return APITokenCreated(
            id=api_token.id,
            name=api_token.name,
            description=api_token.description,
            prefix=api_token.prefix,
            is_active=api_token.is_active,
            expires_at=api_token.expires_at,
            last_used_at=api_token.last_used_at,
            created_at=api_token.created_at,
            token=raw_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/api-tokens", response_model=list[APITokenResponse])
async def list_api_tokens(
    current_user: dict = Depends(require_auth), db: Session = Depends(get_db)
):
    """List API tokens for the current user."""
    tokens = list_user_tokens(db, current_user["user_id"])
    return [
        APITokenResponse(
            id=token.id,
            name=token.name,
            description=token.description,
            prefix=token.prefix,
            is_active=token.is_active,
            expires_at=token.expires_at,
            last_used_at=token.last_used_at,
            created_at=token.created_at,
        )
        for token in tokens
    ]


@router.delete("/api-tokens/{token_id}")
async def revoke_user_api_token(
    token_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Revoke an API token."""
    success = revoke_api_token(db, token_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API token not found"
        )

    return {"message": "API token revoked successfully"}
