"""
JWT authentication utilities for PartsHub.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os

from jose import JWTError, jwt
from fastapi import HTTPException, status


# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Token expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token has expired
        exp = payload.get("exp")
        if exp is None:
            return None

        # Convert exp timestamp to datetime
        if datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None

        return payload

    except JWTError:
        return None


def get_current_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None

    return payload.get("sub")  # 'sub' is the standard claim for user ID


def create_user_token(user_id: str, username: str, is_admin: bool = False,
                     expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token for a user.

    Args:
        user_id: User's unique identifier
        username: User's username
        is_admin: Whether the user has admin privileges
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    token_data = {
        "sub": user_id,  # Standard JWT claim for subject (user ID)
        "username": username,
        "is_admin": is_admin,
        "token_type": "access"
    }

    return create_access_token(token_data, expires_delta)


def get_current_user(token: str) -> Dict[str, Any]:
    """
    Get current user data from JWT token, raising exception if invalid.

    Args:
        token: JWT token string

    Returns:
        User data from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "is_admin": payload.get("is_admin", False),
    }