"""
API Token model for API-based authentication.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database import Base

if TYPE_CHECKING:
    pass


class APIToken(Base):
    """API Token model for programmatic access."""

    __tablename__ = "api_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # Human-readable token name
    description = Column(Text, nullable=True)
    hashed_token = Column(Text, nullable=False, unique=True)  # Hashed version for security
    prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = never expires
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="api_tokens")

    @classmethod
    def generate_token(cls, user_id: str, name: str, description: str | None = None,
                      expires_in_days: int | None = None) -> tuple[str, "APIToken"]:
        """
        Generate a new API token and return both the raw token and the model instance.

        Returns:
            tuple: (raw_token, api_token_model)
        """
        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)  # 43 characters

        # Create prefix (first 8 chars for identification)
        prefix = raw_token[:8]

        # Hash the token for storage
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        # Create the token instance
        token = cls(
            id=secrets.token_urlsafe(12),
            user_id=user_id,
            name=name,
            description=description,
            hashed_token=hashed_token,
            prefix=prefix,
            expires_at=expires_at
        )

        return raw_token, token

    def verify_token(self, raw_token: str) -> bool:
        """Verify a raw token against this token's hash."""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return token_hash == self.hashed_token

    def update_last_used(self) -> None:
        """Update the token's last used timestamp."""
        self.last_used_at = datetime.now(UTC)

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def masked_token(self) -> str:
        """Return a masked version of the token for display."""
        return f"{self.prefix}{'*' * 35}"

    def deactivate(self) -> None:
        """Deactivate the token."""
        self.is_active = False

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        if self.is_expired:
            status = "expired"
        return f"<APIToken(id='{self.id}', name='{self.name}', prefix='{self.prefix}', status='{status}')>"
