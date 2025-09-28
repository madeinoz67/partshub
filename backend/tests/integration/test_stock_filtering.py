"""
Integration tests for stock filtering functionality.
Tests the stock filtering API endpoints and parameter validation.
"""

import pytest


@pytest.mark.integration
def test_stock_status_parameter_validation(client, auth_headers):
    """Test that stock status parameter validation works correctly."""
    # Test valid stock status parameters
    valid_statuses = ["out", "low", "available"]
    for status in valid_statuses:
        response = client.get(
            f"/api/v1/components?stock_status={status}&limit=1", headers=auth_headers
        )
        # Even if there's no data, the endpoint should return 200 with proper structure
        assert response.status_code == 200, f"Valid status {status} should return 200"
        data = response.json()
        assert "components" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    # Test invalid stock status parameter
    response = client.get(
        "/api/v1/components?stock_status=invalid", headers=auth_headers
    )
    assert response.status_code == 422  # Validation error for invalid parameter


@pytest.mark.integration
def test_stock_filtering_api_structure(client, auth_headers):
    """Test that the stock filtering API returns the expected response structure."""
    # Test basic components endpoint works
    response = client.get("/api/v1/components?limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure matches expected format
    required_fields = ["components", "total", "limit", "offset"]
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from response"

    # Verify data types
    assert isinstance(data["total"], int)
    assert isinstance(data["limit"], int)
    assert isinstance(data["offset"], int)
    assert isinstance(data["components"], list)

    # Test with stock status filter - should maintain same structure
    response = client.get("/api/v1/components?stock_status=available&limit=5", headers=auth_headers)
    assert response.status_code == 200
    filtered_data = response.json()

    # Same structure should be maintained
    for field in required_fields:
        assert field in filtered_data, f"Required field '{field}' missing from filtered response"