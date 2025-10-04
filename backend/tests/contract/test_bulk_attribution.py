"""
Contract test for POST /api/components/bulk/attribution/set
Tests bulk attribution setting endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkAttributionContract:
    """Contract tests for bulk attribution setting endpoint"""

    def test_bulk_set_attribution_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that bulk attribution setting requires admin privileges"""
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
            "attribution_data": {"source": "DigiKey", "order_id": "12345"},
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=request_data,
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_set_attribution_success(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test successful bulk attribution setting"""
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
            "attribution_data": {
                "source": "DigiKey",
                "order_id": "12345",
                "batch": "2024-01",
            },
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
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

    def test_bulk_set_attribution_validates_request_schema(
        self, client: TestClient, auth_headers
    ):
        """Test request validation for missing required fields"""
        # Missing attribution_data field
        invalid_data = {"component_ids": [1, 2]}

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

        # Missing component_ids field
        invalid_data = {"attribution_data": {"source": "DigiKey"}}

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_attribution_validates_empty_arrays(
        self, client: TestClient, auth_headers
    ):
        """Test that empty component_ids array is rejected per OpenAPI spec"""
        # Empty component_ids array (minItems: 1)
        invalid_data = {
            "component_ids": [],
            "attribution_data": {"source": "DigiKey"},
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_attribution_validates_max_items(
        self, client: TestClient, auth_headers
    ):
        """Test that component_ids array is limited to 1000 items per OpenAPI spec"""
        # Create request with 1001 component IDs (exceeds maxItems: 1000)
        invalid_data = {
            "component_ids": list(range(1, 1002)),
            "attribution_data": {"source": "DigiKey"},
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_set_attribution_accepts_empty_object(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that empty attribution_data object is accepted (clears attribution)"""
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
            "attribution_data": {},  # Empty object should clear attribution
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        # Empty object should be accepted
        assert response.status_code == 200

    def test_bulk_set_attribution_accepts_arbitrary_keys(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that attribution_data accepts arbitrary key-value pairs"""
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
            "attribution_data": {
                "custom_field_1": "value1",
                "custom_field_2": "value2",
                "another_field": "value3",
            },
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        # Arbitrary keys should be accepted (additionalProperties in schema)
        assert response.status_code == 200

    def test_bulk_set_attribution_response_structure(
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
            "attribution_data": {"source": "DigiKey"},
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
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

    def test_bulk_set_attribution_handles_nonexistent_components(
        self, client: TestClient, auth_headers
    ):
        """Test behavior when component IDs don't exist"""
        request_data = {
            "component_ids": [999999, 999998],
            "attribution_data": {"source": "DigiKey"},
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
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

    def test_bulk_set_attribution_validates_value_types(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that attribution_data values must be strings per OpenAPI spec"""
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

        # Non-string values in attribution_data
        invalid_data = {
            "component_ids": [component.id],
            "attribution_data": {
                "source": "DigiKey",
                "order_id": 12345,  # Should be string, not integer
            },
        }

        response = client.post(
            "/api/components/bulk/attribution/set",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for type validation error
        assert response.status_code == 422
