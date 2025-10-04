"""
Contract test for POST /api/components/bulk/tags/remove
Tests bulk tag removal endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkTagsRemoveContract:
    """Contract tests for bulk tag removal endpoint"""

    def test_bulk_remove_tags_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that bulk tag removal requires admin privileges"""
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
            "tags": ["test-tag-1"],
        }

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=request_data,
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_remove_tags_success(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test successful bulk tag removal"""
        from backend.src.models.component import Component

        # Create test components with tags
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
            "/api/components/bulk/tags/remove",
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

    def test_bulk_remove_tags_validates_request_schema(
        self, client: TestClient, auth_headers
    ):
        """Test request validation for missing required fields"""
        # Missing tags field
        invalid_data = {"component_ids": [1, 2]}

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_remove_tags_validates_empty_arrays(
        self, client: TestClient, auth_headers
    ):
        """Test that empty arrays are rejected per OpenAPI spec"""
        # Empty component_ids array (minItems: 1)
        invalid_data = {"component_ids": [], "tags": ["test-tag"]}

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

        # Empty tags array (minItems: 1)
        invalid_data = {"component_ids": [1, 2], "tags": []}

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_remove_tags_validates_max_items(
        self, client: TestClient, auth_headers
    ):
        """Test that component_ids array is limited to 1000 items per OpenAPI spec"""
        # Create request with 1001 component IDs (exceeds maxItems: 1000)
        invalid_data = {
            "component_ids": list(range(1, 1002)),
            "tags": ["test-tag"],
        }

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_remove_tags_response_structure(
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
            "/api/components/bulk/tags/remove",
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

    def test_bulk_remove_tags_concurrent_modification_handling(
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

        response = client.post(
            "/api/components/bulk/tags/remove",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 409]

        # If implementation includes optimistic locking,
        # concurrent modification should return 409
        if response.status_code == 409:
            data = response.json()
            assert "success" in data
            assert data["success"] is False
