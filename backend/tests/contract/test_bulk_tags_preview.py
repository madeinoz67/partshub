"""
Contract test for GET /api/v1/components/bulk/tags/preview
Tests tag preview endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkTagsPreviewContract:
    """Contract tests for tag preview endpoint"""

    def test_bulk_tags_preview_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that tag preview requires admin privileges"""
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

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component.id}&add_tags=test-tag",
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_tags_preview_success(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test successful tag preview generation"""
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

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component1.id},{component2.id}&add_tags=tag1,tag2",
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert isinstance(data["components"], list)
        assert len(data["components"]) == 2

    def test_bulk_tags_preview_requires_component_ids(
        self, client: TestClient, auth_headers
    ):
        """Test that component_ids parameter is required"""
        # Missing component_ids parameter
        response = client.get(
            "/api/v1/components/bulk/tags/preview?add_tags=test-tag",
            headers=auth_headers,
        )

        # Should return 422 for missing required parameter
        assert response.status_code == 422

    def test_bulk_tags_preview_response_structure(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches TagPreviewResponse schema"""
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

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component.id}&add_tags=test-tag",
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()

        # Required field per TagPreviewResponse schema
        assert "components" in data
        assert isinstance(data["components"], list)

        if len(data["components"]) > 0:
            preview = data["components"][0]

            # Required fields per ComponentTagPreview schema
            required_fields = [
                "component_id",
                "component_name",
                "current_tags",
                "resulting_tags",
            ]

            for field in required_fields:
                assert field in preview

            # All tag fields should be arrays
            assert isinstance(preview["current_tags"], list)
            assert isinstance(preview["resulting_tags"], list)

    def test_bulk_tags_preview_with_add_and_remove(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test preview with both add_tags and remove_tags parameters"""
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

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component.id}&add_tags=new-tag&remove_tags=old-tag",
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert len(data["components"]) == 1

    def test_bulk_tags_preview_with_only_remove(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test preview with only remove_tags parameter"""
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

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component.id}&remove_tags=old-tag",
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "components" in data

    def test_bulk_tags_preview_with_multiple_components(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test preview with multiple component IDs in query parameter"""
        from backend.src.models.component import Component

        # Create test components
        components = []
        for i in range(3):
            component = Component(
                name=f"Test Component {i+1}",
                part_number=f"TEST-00{i+1}",
                manufacturer="Test Mfg",
                component_type="resistor",
                value="10k",
                package="0805",
            )
            components.append(component)

        db_session.add_all(components)
        db_session.commit()

        component_ids = ",".join(str(c.id) for c in components)

        response = client.get(
            f"/api/v1/components/bulk/tags/preview?component_ids={component_ids}&add_tags=test-tag",
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert len(data["components"]) == 3
