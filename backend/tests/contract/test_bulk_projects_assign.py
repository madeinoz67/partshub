"""
Contract test for POST /api/components/bulk/projects/assign
Tests bulk project assignment endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestBulkProjectsAssignContract:
    """Contract tests for bulk project assignment endpoint"""

    def test_bulk_assign_project_requires_admin(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that bulk project assignment requires admin privileges"""
        from backend.src.models.component import Component
        from backend.src.models.project import Project

        # Create test project
        project = Project(
            name="Test Project",
            description="Test project for assignment",
        )
        db_session.add(project)

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
            "project_id": project.id,
            "quantities": {str(component1.id): 5},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=request_data,
            headers=user_auth_headers,
        )

        # Should return 403 Forbidden for non-admin users
        assert response.status_code == 403

    def test_bulk_assign_project_success(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test successful bulk project assignment"""
        from backend.src.models.component import Component
        from backend.src.models.project import Project

        # Create test project
        project = Project(
            name="Test Project",
            description="Test project for assignment",
        )
        db_session.add(project)

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
            "project_id": project.id,
            "quantities": {str(component1.id): 5, str(component2.id): 10},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
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

    def test_bulk_assign_project_validates_request_schema(
        self, client: TestClient, auth_headers
    ):
        """Test request validation for missing required fields"""
        # Missing project_id field
        invalid_data = {
            "component_ids": [1, 2],
            "quantities": {"1": 5, "2": 10},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should return 422 for validation error
        assert response.status_code == 422

        # Missing quantities field
        invalid_data = {
            "component_ids": [1, 2],
            "project_id": 1,
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_assign_project_validates_empty_arrays(
        self, client: TestClient, auth_headers
    ):
        """Test that empty component_ids array is rejected per OpenAPI spec"""
        # Empty component_ids array (minItems: 1)
        invalid_data = {
            "component_ids": [],
            "project_id": 1,
            "quantities": {},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_assign_project_validates_max_items(
        self, client: TestClient, auth_headers
    ):
        """Test that component_ids array is limited to 1000 items per OpenAPI spec"""
        # Create request with 1001 component IDs (exceeds maxItems: 1000)
        component_ids = list(range(1, 1002))
        quantities = {str(i): 1 for i in component_ids}

        invalid_data = {
            "component_ids": component_ids,
            "project_id": 1,
            "quantities": quantities,
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=invalid_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_bulk_assign_project_handles_nonexistent_project(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test 404 response when project doesn't exist"""
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
            "project_id": 999999,  # Nonexistent project
            "quantities": {str(component.id): 5},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
            json=request_data,
            headers=auth_headers,
        )

        # This will fail until endpoint is implemented
        # Should return 404 for nonexistent project per OpenAPI spec
        assert response.status_code == 404

    def test_bulk_assign_project_response_structure(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches BulkOperationResponse schema"""
        from backend.src.models.component import Component
        from backend.src.models.project import Project

        # Create test project
        project = Project(
            name="Test Project",
            description="Test project for assignment",
        )
        db_session.add(project)

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
            "project_id": project.id,
            "quantities": {str(component.id): 5},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
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

    def test_bulk_assign_project_concurrent_modification_handling(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test concurrent modification detection (409 response)"""
        from backend.src.models.component import Component
        from backend.src.models.project import Project

        # Create test project
        project = Project(
            name="Test Project",
            description="Test project for assignment",
        )
        db_session.add(project)

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
            "project_id": project.id,
            "quantities": {str(component.id): 5},
        }

        response = client.post(
            "/api/components/bulk/projects/assign",
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
