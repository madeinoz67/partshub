#!/usr/bin/env python3
"""
Debug authentication dependency chain issue.
Isolate the FastAPI + TestClient + JWT authentication problem.
"""

import os

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from src.auth.jwt_auth import create_access_token, get_current_user
from src.database import get_db
from src.models import Base, User

# Create test database
test_engine = create_engine(
    "sqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)

# Create minimal app for testing
debug_app = FastAPI()
security = HTTPBearer(auto_error=False)

# Test endpoints
@debug_app.get("/test-no-auth")
def test_no_auth():
    return {"status": "no auth required"}

@debug_app.get("/test-optional-auth")
async def test_optional_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials:
        return {"status": "no credentials"}

    try:
        user_data = get_current_user(credentials.credentials)
        return {"status": "authenticated", "user": user_data}
    except Exception as e:
        return {"status": "auth failed", "error": str(e)}

@debug_app.get("/test-required-auth")
async def test_required_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_data = get_current_user(credentials.credentials)
    return {"status": "authenticated", "user": user_data}

def test_authentication_debug():
    """Debug the authentication dependency chain step by step."""

    # Setup shared session
    shared_session = TestingSessionLocal()

    def override_get_db():
        yield shared_session

    debug_app.dependency_overrides[get_db] = override_get_db

    # Create test user
    user = User(
        username="debug_user",
        full_name="Debug User",
        is_admin=True,
        is_active=True
    )
    user.set_password("test123")
    shared_session.add(user)
    shared_session.commit()
    shared_session.refresh(user)

    # Create token
    token = create_access_token({
        "sub": user.id,
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    })

    print(f"Created user: {user.id}")
    print(f"Token created: {len(token)} chars")

    # Test with TestClient
    with TestClient(debug_app) as client:
        # Test 1: No auth endpoint
        response = client.get("/test-no-auth")
        print(f"No auth test: {response.status_code} - {response.json()}")

        # Test 2: Optional auth without token
        response = client.get("/test-optional-auth")
        print(f"Optional auth (no token): {response.status_code} - {response.json()}")

        # Test 3: Optional auth with token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/test-optional-auth", headers=headers)
        print(f"Optional auth (with token): {response.status_code} - {response.json()}")

        # Test 4: Required auth with token
        response = client.get("/test-required-auth", headers=headers)
        print(f"Required auth (with token): {response.status_code} - {response.json()}")

    shared_session.close()
    debug_app.dependency_overrides.clear()

if __name__ == "__main__":
    test_authentication_debug()
