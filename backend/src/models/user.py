"""
User model for authentication and authorization.
"""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from ..database import Base

if TYPE_CHECKING:
    from .api_token import APIToken


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication and access control."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    api_tokens = relationship(
        "APIToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the user's hashed password."""
        return pwd_context.verify(password, self.hashed_password)

    def update_last_login(self) -> None:
        """Update the user's last login timestamp."""
        self.last_login = datetime.now(timezone.utc)

    @property
    def requires_password_change(self) -> bool:
        """Check if user must change password on next login."""
        return self.must_change_password

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}', is_admin={self.is_admin})>"