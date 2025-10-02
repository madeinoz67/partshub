"""
API Token management service for PartsHub.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..models import APIToken, User


def create_api_token(
    db: Session,
    user_id: str,
    name: str,
    description: str | None = None,
    expires_in_days: int | None = None,
) -> tuple[str, APIToken]:
    """
    Create a new API token for a user.

    Args:
        db: Database session
        user_id: ID of the user creating the token
        name: Human-readable name for the token
        description: Optional description
        expires_in_days: Optional expiration in days (None = no expiration)

    Returns:
        tuple: (raw_token, api_token_model)

    Raises:
        ValueError: If user not found or invalid parameters
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")

    if not user.is_active:
        raise ValueError("Cannot create token for inactive user")

    # Generate the token
    raw_token, api_token = APIToken.generate_token(
        user_id=user_id,
        name=name,
        description=description,
        expires_in_days=expires_in_days,
    )

    # Save to database
    db.add(api_token)
    db.commit()
    db.refresh(api_token)

    return raw_token, api_token


def verify_api_token(raw_token: str, db: Session) -> User | None:
    """
    Verify an API token and return the associated user.

    Args:
        raw_token: The raw API token string
        db: Database session

    Returns:
        User object if token is valid, None otherwise
    """
    if not raw_token or len(raw_token) < 8:
        return None

    # Extract prefix from token
    prefix = raw_token[:8]

    # Find token by prefix
    api_token = db.query(APIToken).filter(APIToken.prefix == prefix).first()
    if not api_token:
        return None

    # Verify the full token
    if not api_token.verify_token(raw_token):
        return None

    # Get the user
    user = db.query(User).filter(User.id == api_token.user_id).first()
    if not user or not user.is_active:
        return None

    # Update last used timestamp
    api_token.update_last_used()
    db.commit()

    return user


def list_user_tokens(
    db: Session, user_id: str, include_inactive: bool = False
) -> list[APIToken]:
    """
    List all API tokens for a user.

    Args:
        db: Database session
        user_id: User ID to list tokens for
        include_inactive: Whether to include inactive/expired tokens

    Returns:
        List of APIToken objects
    """
    query = db.query(APIToken).filter(APIToken.user_id == user_id)

    if not include_inactive:
        now = datetime.now(UTC)
        query = query.filter(
            APIToken.is_active is True,
            (APIToken.expires_at.is_(None) | (APIToken.expires_at > now)),
        )

    return query.order_by(APIToken.created_at.desc()).all()


def get_api_token(
    db: Session, token_id: str, user_id: str | None = None
) -> APIToken | None:
    """
    Get an API token by ID.

    Args:
        db: Database session
        token_id: Token ID to retrieve
        user_id: Optional user ID to filter by (for security)

    Returns:
        APIToken object if found, None otherwise
    """
    query = db.query(APIToken).filter(APIToken.id == token_id)

    if user_id:
        query = query.filter(APIToken.user_id == user_id)

    return query.first()


def revoke_api_token(db: Session, token_id: str, user_id: str | None = None) -> bool:
    """
    Revoke (deactivate) an API token.

    Args:
        db: Database session
        token_id: Token ID to revoke
        user_id: Optional user ID to filter by (for security)

    Returns:
        True if token was revoked, False if not found
    """
    query = db.query(APIToken).filter(APIToken.id == token_id)

    if user_id:
        query = query.filter(APIToken.user_id == user_id)

    api_token = query.first()
    if not api_token:
        return False

    api_token.deactivate()
    db.commit()
    return True


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired API tokens by marking them as inactive.

    Args:
        db: Database session

    Returns:
        Number of tokens that were cleaned up
    """
    now = datetime.now(UTC)

    expired_tokens = (
        db.query(APIToken)
        .filter(
            APIToken.is_active is True,
            APIToken.expires_at.isnot(None),
            APIToken.expires_at <= now,
        )
        .all()
    )

    count = 0
    for token in expired_tokens:
        token.deactivate()
        count += 1

    if count > 0:
        db.commit()

    return count
