#!/usr/bin/env python3
"""
Debug the exact production authentication flow step by step
"""

import os

os.environ["TESTING"] = "1"

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.auth.jwt_auth import create_access_token, get_current_user
from src.database.connection import get_db
from src.models import Base, User

from tests.conftest import TestingSessionLocal, test_engine

# Create test app with exact production patterns
app = FastAPI()
security = HTTPBearer(auto_error=False)

# Recreate the production dependency chain with debug logging
async def debug_get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    print("DEBUG: get_optional_user called")
    print(f"DEBUG: credentials = {credentials is not None}")
    if credentials:
        print(f"DEBUG: token length = {len(credentials.credentials)}")

    if not credentials:
        print("DEBUG: No credentials, returning None")
        return None

    token = credentials.credentials
    print(f"DEBUG: Attempting JWT verification for token: {token[:20]}...")

    try:
        user_data = get_current_user(token)
        print(f"DEBUG: get_current_user succeeded: {user_data}")

        # Verify user exists in database
        user = db.query(User).filter(User.id == user_data["user_id"]).first()
        print(f"DEBUG: Database user lookup: {user is not None}")

        if user and user.is_active:
            print(f"DEBUG: User found and active: {user.username}")
            return {
                "user_id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
                "auth_type": "jwt"
            }
        else:
            print("DEBUG: User not found or inactive")
    except Exception as e:
        print(f"DEBUG: JWT verification failed: {e}")
        import traceback
        traceback.print_exc()

    print("DEBUG: Authentication failed, returning None")
    return None

async def debug_require_auth(current_user = Depends(debug_get_optional_user)):
    print(f"DEBUG: require_auth called with current_user = {current_user}")
    if not current_user:
        print("DEBUG: require_auth raising 401")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("DEBUG: require_auth returning user")
    return current_user

@app.post("/debug-auth")
async def debug_auth_endpoint(current_user: dict = Depends(debug_require_auth)):
    print(f"DEBUG: Endpoint reached with user: {current_user}")
    return {"authenticated": True, "user": current_user}

def test_production_debug():
    """Test the exact production authentication flow with debugging"""

    # Setup
    Base.metadata.create_all(bind=test_engine)
    shared_session = TestingSessionLocal()

    def override_get_db():
        print("DEBUG: override_get_db called")
        yield shared_session

    app.dependency_overrides[get_db] = override_get_db

    # Create user
    user = User(username='debug_user', full_name='Debug User', is_admin=True, is_active=True)
    user.set_password('test123')
    shared_session.add(user)
    shared_session.commit()
    shared_session.refresh(user)

    # Create token
    token = create_access_token({
        'sub': user.id,
        'user_id': user.id,
        'username': user.username,
        'is_admin': user.is_admin
    })

    print(f"Setup complete. User ID: {user.id}")
    print(f"Token created: {len(token)} chars")

    # Test
    with TestClient(app) as client:
        print("\\n=== Testing production authentication flow ===")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/debug-auth", json={}, headers=headers)
        print(f"\\nFinal response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print(f"Success response: {response.json()}")

    shared_session.close()
    app.dependency_overrides.clear()

if __name__ == "__main__":
    test_production_debug()
