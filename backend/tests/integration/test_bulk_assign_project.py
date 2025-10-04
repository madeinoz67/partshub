"""
Integration test for bulk project assignment operation.
Tests the scenario: Create project + 5 components, bulk assign, verify associations.

Following TDD principles:
- This test MUST FAIL initially (implementation not done yet)
- Tests isolated database (in-memory SQLite)
- Each test is independent and can run in any order
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.src.models import Component, Project, ProjectComponent


@pytest.mark.integration
class TestBulkAssignProjectIntegration:
    """Integration test for bulk project assignment functionality"""

    def test_bulk_assign_five_components_to_project(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Scenario 2: Bulk assign to project (5 components)
        - Create test project and 5 components
        - Call bulk assign API with quantities
        - Assert all 5 components linked to project
        - Assert ProjectComponent records created with correct quantities
        """
        # Arrange: Create test project
        project = Project(
            name="Test Bulk Assignment Project",
            description="For testing bulk operations",
        )
        db_session.add(project)
        db_session.flush()
        project_id = project.id

        # Arrange: Create 5 test components
        component_ids = []
        for i in range(1, 6):
            component = Component(
                name=f"Component {i}",
                part_number=f"TEST-PROJECT-{i}",
                manufacturer="Test Mfg",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Arrange: Prepare quantities mapping
        quantities = {comp_id: i for i, comp_id in enumerate(component_ids, 1)}

        # Act: Call bulk assign API
        response = client.post(
            "/api/components/bulk/projects/assign",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "project_id": project_id,
                "quantities": quantities,
            },
        )

        # Assert: Verify response
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["success"] is True, "Expected success=true"
        assert (
            data["affected_count"] == 5
        ), f"Expected affected_count=5, got {data['affected_count']}"
        assert (
            data.get("errors") is None or data.get("errors") == []
        ), "Expected no errors"

        # Assert: Verify ProjectComponent records created
        db_session.expire_all()  # Clear session cache
        project = db_session.query(Project).filter_by(id=project_id).first()
        assert len(project.project_components) == 5, "Expected 5 project components"

        # Assert: Verify correct quantities assigned
        for i, component_id in enumerate(component_ids, 1):
            pc = (
                db_session.query(ProjectComponent)
                .filter_by(project_id=project_id, component_id=component_id)
                .first()
            )
            assert pc is not None, f"ProjectComponent for {component_id} not found"
            assert (
                pc.quantity_allocated == i
            ), f"Expected quantity {i}, got {pc.quantity_allocated}"

    def test_bulk_assign_with_default_quantity_one(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk assign with no quantities specified defaults to 1 for each
        """
        # Arrange: Create project and components
        project = Project(name="Default Quantity Project")
        db_session.add(project)
        db_session.flush()

        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Component {i}",
                part_number=f"DEFAULT-QTY-{i}",
                manufacturer="Test",
                component_type="capacitor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Act: Assign without quantities field (should default to 1)
        response = client.post(
            "/api/components/bulk/projects/assign",
            headers=auth_headers,
            json={"component_ids": component_ids, "project_id": project.id},
        )

        # Assert: All should have quantity 1
        assert response.status_code == 200
        data = response.json()
        assert data["affected_count"] == 3

        for component_id in component_ids:
            pc = (
                db_session.query(ProjectComponent)
                .filter_by(project_id=project.id, component_id=component_id)
                .first()
            )
            assert pc is not None
            assert pc.quantity_allocated == 1, "Default quantity should be 1"

    def test_bulk_assign_to_nonexistent_project(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk assign to nonexistent project returns error
        """
        # Arrange: Create components but no project
        component_ids = []
        for i in range(1, 3):
            component = Component(
                name=f"Component {i}",
                part_number=f"NO-PROJECT-{i}",
                manufacturer="Test",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Act: Try to assign to nonexistent project
        response = client.post(
            "/api/components/bulk/projects/assign",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "project_id": "nonexistent-project-id-12345",
            },
        )

        # Assert: Should return error (404 or 400)
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400 or 404, got {response.status_code}"

        # Verify no ProjectComponent records created
        pc_count = db_session.query(ProjectComponent).count()
        assert pc_count == 0, "No ProjectComponent records should be created"

    def test_bulk_assign_updates_existing_assignment(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test that assigning already-assigned component updates the quantity
        """
        # Arrange: Create project and component
        project = Project(name="Update Test Project")
        component = Component(
            name="Update Component",
            part_number="UPDATE-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(project)
        db_session.add(component)
        db_session.flush()

        # Create initial assignment with quantity 5
        initial_pc = ProjectComponent(
            project_id=project.id, component_id=component.id, quantity_allocated=5
        )
        db_session.add(initial_pc)
        db_session.commit()

        # Act: Reassign with quantity 10
        response = client.post(
            "/api/components/bulk/projects/assign",
            headers=auth_headers,
            json={
                "component_ids": [component.id],
                "project_id": project.id,
                "quantities": {component.id: 10},
            },
        )

        # Assert: Quantity should be updated
        assert response.status_code == 200
        db_session.expire_all()

        pc = (
            db_session.query(ProjectComponent)
            .filter_by(project_id=project.id, component_id=component.id)
            .first()
        )
        assert pc is not None
        assert pc.quantity_allocated == 10, "Quantity should be updated to 10"

    def test_bulk_assign_with_invalid_quantity(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk assign with negative or zero quantity returns validation error
        """
        # Arrange: Create project and component
        project = Project(name="Invalid Quantity Project")
        component = Component(
            name="Component",
            part_number="INVALID-QTY-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(project)
        db_session.add(component)
        db_session.commit()

        # Act: Try to assign with invalid quantity
        response = client.post(
            "/api/components/bulk/projects/assign",
            headers=auth_headers,
            json={
                "component_ids": [component.id],
                "project_id": project.id,
                "quantities": {component.id: -5},  # Invalid negative quantity
            },
        )

        # Assert: Should return validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
