"""
Admin user management for PartsHub.
"""

import secrets
import stat
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import User


def _write_credentials_file(username: str, password: str) -> Path:
    """
    Write admin credentials to a secure file.

    Args:
        username: Admin username
        password: Admin password

    Returns:
        Path to the credentials file
    """
    # Determine credentials file path (in root data directory for Docker compatibility)
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    credentials_file = data_dir / ".admin_credentials.txt"

    # Write credentials with warning banner
    content = f"""
{'=' * 70}
    PARTSHUB ADMIN CREDENTIALS - FIRST TIME SETUP
{'=' * 70}

Username: {username}
Password: {password}

IMPORTANT SECURITY NOTICES:
- This file was automatically created during first-time setup
- DELETE THIS FILE immediately after reading the credentials
- Change the admin password after your first login
- Never commit this file to version control (.gitignore should exclude it)

To manually delete this file, run:
    rm {credentials_file}

{'=' * 70}
"""

    credentials_file.write_text(content)

    # Set restrictive permissions (owner read/write only)
    try:
        credentials_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
    except (OSError, NotImplementedError):
        # Windows or permission error - file permissions not supported on this platform
        pass

    return credentials_file


def create_default_admin(db: Session, username: str = "admin") -> tuple[User, str]:
    """
    Create a default admin user with a randomly generated password.

    Args:
        db: Database session
        username: Admin username (default: "admin")

    Returns:
        tuple: (user, temporary_password)

    Raises:
        ValueError: If user with same username already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        raise ValueError(f"User with username '{username}' already exists")

    # Generate a secure temporary password
    temporary_password = secrets.token_urlsafe(16)  # 22 characters

    # Create the admin user
    admin_user = User(
        id=str(uuid.uuid4()),
        username=username,
        full_name="Default Administrator",
        is_active=True,
        is_admin=True,
        must_change_password=True,  # Force password change on first login
    )

    admin_user.set_password(temporary_password)

    # Save to database
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Write credentials to secure file
    try:
        credentials_file = _write_credentials_file(username, temporary_password)
        print(f"\n📄 Credentials also saved to: {credentials_file}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not write credentials file: {e}")

    return admin_user, temporary_password


def ensure_admin_exists(db: Session) -> tuple[User, str] | None:
    """
    Ensure at least one admin user exists, creating one if necessary.

    Args:
        db: Database session

    Returns:
        tuple: (user, temporary_password) if admin was created, None if admin already exists
    """
    # Check if any admin user exists
    admin_exists = (
        db.query(User).filter(User.is_admin is True, User.is_active is True).first()
    )

    if admin_exists:
        return None

    # No admin exists, create default admin
    return create_default_admin(db)


def create_user(
    db: Session,
    username: str,
    password: str,
    full_name: str | None = None,
    is_admin: bool = False,
    force_password_change: bool = False,
) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        username: User's username
        password: User's password
        full_name: Optional full name
        is_admin: Whether user should have admin privileges
        force_password_change: Whether to force password change on next login

    Returns:
        Created User object

    Raises:
        ValueError: If user with same username already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        raise ValueError(f"User with username '{username}' already exists")

    # Create the user
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        full_name=full_name,
        is_active=True,
        is_admin=is_admin,
        must_change_password=force_password_change,
    )

    user.set_password(password)

    # Save to database
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def change_password(db: Session, user_id: str, new_password: str) -> bool:
    """
    Change a user's password.

    Args:
        db: Database session
        user_id: User ID
        new_password: New password

    Returns:
        True if password was changed, False if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    user.set_password(new_password)
    user.must_change_password = False  # Clear force password change flag
    db.commit()

    return True


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username
        password: Password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    if not user.is_active:
        return None

    if not user.verify_password(password):
        return None

    # Update last login
    user.update_last_login()
    db.commit()

    return user


def reset_admin_password(db: Session, username: str = "admin") -> tuple[User, str]:
    """
    Reset admin user password to a new random password.

    Args:
        db: Database session
        username: Admin username to reset (default: "admin")

    Returns:
        tuple: (user, new_password)

    Raises:
        ValueError: If user not found or is not an admin
    """
    # Find the admin user
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise ValueError(f"User '{username}' not found")

    if not user.is_admin:
        raise ValueError(f"User '{username}' is not an admin")

    # Generate new random password
    new_password = secrets.token_urlsafe(16)

    # Update password and force change on next login
    user.set_password(new_password)
    user.must_change_password = True
    db.commit()
    db.refresh(user)

    # Write to credentials file
    try:
        credentials_file = _write_credentials_file(username, new_password)
        print(f"\n📄 Credentials saved to: {credentials_file}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not write credentials file: {e}")

    return user, new_password
