#!/usr/bin/env python3
"""
Debug HTTPBearer dependency specifically in TestClient
"""

import os

os.environ["TESTING"] = "1"

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

# Create test app
app = FastAPI()
security = HTTPBearer(auto_error=False)

@app.get("/test-bearer")
async def test_bearer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        return {
            "has_credentials": True,
            "scheme": credentials.scheme,
            "token_length": len(credentials.credentials),
            "token_start": credentials.credentials[:20] + "..."
        }
    else:
        return {"has_credentials": False}

def test_bearer_dependency():
    """Test if HTTPBearer dependency receives credentials in TestClient"""

    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_payload"

    with TestClient(app) as client:
        # Test without token
        response = client.get("/test-bearer")
        print(f"No token: {response.status_code} - {response.json()}")

        # Test with token
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get("/test-bearer", headers=headers)
        print(f"With token: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    test_bearer_dependency()
