"""
Contract test for POST /api/components/bulk/low-stock/set
Tests bulk low-stock threshold setting endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkLowStockContract:
    """Contract tests for bulk low-stock threshold setting endpoint"""

    def test_bulk_set_low_stock_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that bulk low-stock setting requires admin privileges"""
        from backend.src.models.component import Component

        # Create test components
        component1 = Component(
            name="Test Component 1",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        db_session.add(component1)
        db_session.commit()

        request_data = {
            "component_ids": [component1.id],
            "threshold": 10,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_set_low_stock_success(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test successful bulk low-stock threshold setting"""
        from backend.src.models.component import Component

        # Create test components
        component1 = Component(
            name="Test Component 1",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        component2 = Component(
            name="Test Component 2",
            part_number="TEST-002",
            manufacturer="Test Mfg",
            component_type="capacitor",
            value="100nF",
            package="0805",
        )
        db_session.add_all([component1, component2])
        db_session.commit()

        request_data = {
            "component_ids": [component1.id, component2.id],
            "threshold": 20,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "affected_count" in data
        assert data["success"] is True
        assert data["affected_count"] == 2

    def test_bulk_set_low_stock_validates_request_schema(
        self, client: TestClient, auth_headers
    ):
        """Test request validation for missing required fields"""
        # Missing threshold field
        invalid_data = {"component_ids": [1, 2]}

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

        # Missing component_ids field
        invalid_data = {"threshold": 10}

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_low_stock_validates_empty_arrays(
        self, client: TestClient, auth_headers
    ):
        """Test that empty component_ids array is rejected per OpenAPI spec"""
        # Empty component_ids array (minItems: 1)
        invalid_data = {
            "component_ids": [],
            "threshold": 10,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_low_stock_validates_max_items(
        self, client: TestClient, auth_headers
    ):
        """Test that component_ids array is limited to 1000 items per OpenAPI spec"""
        # Create request with 1001 component IDs (exceeds maxItems: 1000)
        invalid_data = {
            "component_ids": list(range(1, 1002)),
            "threshold": 10,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_low_stock_validates_threshold_minimum(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that threshold must be >= 0 per OpenAPI spec"""
        from backend.src.models.component import Component

        # Create test component
        component = Component(
            name="Test Component",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        db_session.add(component)
        db_session.commit()

        # Negative threshold (violates minimum: 0 constraint)
        invalid_data = {
            "component_ids": [component.id],
            "threshold": -1,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_set_low_stock_accepts_zero_threshold(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that threshold of 0 is accepted per OpenAPI spec (minimum: 0)"""
        from backend.src.models.component import Component

        # Create test component
        component = Component(
            name="Test Component",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        db_session.add(component)
        db_session.commit()

        request_data = {
            "component_ids": [component.id],
            "threshold": 0,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        # Should accept threshold of 0
        assert response.status_code == 200

    def test_bulk_set_low_stock_response_structure(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches BulkOperationResponse schema"""
        from backend.src.models.component import Component

        # Create test component
        component = Component(
            name="Test Component",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        db_session.add(component)
        db_session.commit()

        request_data = {
            "component_ids": [component.id],
            "threshold": 10,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()

        # Required fields per BulkOperationResponse schema
        assert "success" in data
        assert "affected_count" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["affected_count"], int)

        # Optional errors field should be array if present
        if "errors" in data:
            assert isinstance(data["errors"], list)

    def test_bulk_set_low_stock_handles_nonexistent_components(
        self, client: TestClient, auth_headers
    ):
        """Test behavior when component IDs don't exist"""
        request_data = {
            "component_ids": [999999, 999998],
            "threshold": 10,
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        # Should return 200 with errors in response
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert data["affected_count"] == 0
        assert "errors" in data
        assert len(data["errors"]) > 0

    def test_bulk_set_low_stock_validates_threshold_type(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that threshold must be an integer"""
        from backend.src.models.component import Component

        # Create test component
        component = Component(
            name="Test Component",
            part_number="TEST-001",
            manufacturer="Test Mfg",
            component_type="resistor",
            value="10k",
            package="0805",
        )
        db_session.add(component)
        db_session.commit()

        request_data = {
            "component_ids": [component.id],
            "threshold": "not-an-integer",
        }

        response = client.post(
            "/api/components/bulk/low-stock/set",
            json=request_data,
            headers=auth_headers,
        )

        # Should return 422 for type validation error
        assert response.status_code == 422
