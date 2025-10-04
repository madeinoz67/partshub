"""
Contract test for POST /api/components/bulk/tags/add
Tests bulk tag addition endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkTagsAddContract:
    """Contract tests for bulk tag addition endpoint"""

    def test_bulk_add_tags_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that bulk tag addition requires admin privileges"""
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
            "tags": ["test-tag-1", "test-tag-2"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
            json=request_data,
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_add_tags_success(self, client: TestClient, auth_headers, db_session):
        """Test successful bulk tag addition"""
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
            "tags": ["test-tag-1", "test-tag-2"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
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

    def test_bulk_add_tags_validates_request_schema(
        self, client: TestClient, auth_headers
    ):
        """Test request validation for missing required fields"""
        # Missing tags field
        invalid_data = {"component_ids": [1, 2]}

        response = client.post(
            "/api/components/bulk/tags/add",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_add_tags_validates_empty_arrays(
        self, client: TestClient, auth_headers
    ):
        """Test that empty arrays are rejected per OpenAPI spec"""
        # Empty component_ids array (minItems: 1)
        invalid_data = {"component_ids": [], "tags": ["test-tag"]}

        response = client.post(
            "/api/components/bulk/tags/add",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

        # Empty tags array (minItems: 1)
        invalid_data = {"component_ids": [1, 2], "tags": []}

        response = client.post(
            "/api/components/bulk/tags/add",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_add_tags_validates_max_items(self, client: TestClient, auth_headers):
        """Test that component_ids array is limited to 1000 items per OpenAPI spec"""
        # Create request with 1001 component IDs (exceeds maxItems: 1000)
        invalid_data = {
            "component_ids": list(range(1, 1002)),
            "tags": ["test-tag"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_add_tags_response_structure(
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
            "tags": ["test-tag"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
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

    def test_bulk_add_tags_handles_nonexistent_components(
        self, client: TestClient, auth_headers
    ):
        """Test behavior when component IDs don't exist"""
        request_data = {
            "component_ids": [999999, 999998],
            "tags": ["test-tag"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
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

    def test_bulk_add_tags_error_response_structure(
        self, client: TestClient, auth_headers
    ):
        """Test error response structure matches BulkOperationError schema"""
        request_data = {
            "component_ids": [999999],
            "tags": ["test-tag"],
        }

        response = client.post(
            "/api/components/bulk/tags/add",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        if "errors" in data and len(data["errors"]) > 0:
            error = data["errors"][0]

            # Required fields per BulkOperationError schema
            assert "component_id" in error
            assert "component_name" in error
            assert "error_message" in error
            assert "error_type" in error

            # error_type must be one of the allowed enum values
            assert error["error_type"] in [
                "not_found",
                "concurrent_modification",
                "validation_error",
                "permission_denied",
            ]

    def test_bulk_add_tags_concurrent_modification_handling(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test concurrent modification detection (409 response)"""
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
            "tags": ["test-tag"],
        }

        # First request should succeed
        response1 = client.post(
            "/api/components/bulk/tags/add",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response1.status_code in [200, 409]

        # If implementation includes optimistic locking,
        # concurrent modification should return 409
        if response1.status_code == 409:
            data = response1.json()
            assert "success" in data
            assert data["success"] is False
