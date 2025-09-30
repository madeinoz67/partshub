#!/usr/bin/env python3
"""
CLI tool to reset admin password for PartsHub.

Usage:
    uv run --project .. python reset_admin_password.py [username]

If username is not provided, defaults to "admin".
"""

import sys
from pathlib import Path

from src.auth.admin import reset_admin_password
from src.database import SessionLocal


def main():
    """Reset admin password and display credentials."""
    # Get username from command line args or use default
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"

    print("\n🔐 PartsHub Admin Password Reset Tool")
    print("=" * 50)

    # Create database session
    db = SessionLocal()

    try:
        # Reset password
        user, new_password = reset_admin_password(db, username)

        print(f"\n✅ Password reset successful!")
        print("\n🔑 NEW ADMIN CREDENTIALS:")
        print(f"   Username: {user.username}")
        print(f"   Password: {new_password}")
        print("\n⚠️  IMPORTANT:")
        print("   - Save these credentials immediately")
        print("   - Change the password after first login")
        print("   - Delete the credentials file after reading it")
        print("\n" + "=" * 50 + "\n")

    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()