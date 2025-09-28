#!/usr/bin/env python3
"""
Test runner script that ensures complete isolation from production environment.
"""

import os
import subprocess
import sys


def main():
    """Run tests with proper environment isolation."""

    # Set environment variables for test isolation
    test_env = os.environ.copy()
    test_env.update({
        "TESTING": "1",
        "DATABASE_URL": "sqlite:///:memory:",  # In-memory database
        "PORT": "8001",  # Different port from production (8000)
        "SECRET_KEY": "test-secret-key-not-for-production",
    })

    print("🧪 Running tests with isolated environment:")
    print(f"   - Database: {test_env['DATABASE_URL']}")
    print(f"   - Port: {test_env['PORT']}")
    print(f"   - Testing mode: {test_env['TESTING']}")
    print()

    # Run pytest with the test environment using uv
    try:
        result = subprocess.run([
            "uv", "run", "pytest"
        ] + sys.argv[1:], env=test_env, check=False)

        return result.returncode

    except KeyboardInterrupt:
        print("\n🚫 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
