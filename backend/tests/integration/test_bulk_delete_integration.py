"""
Integration test for bulk delete operation.
Tests the scenario: Create 8 components, bulk delete, verify all removed.

Following TDD principles:
- This test MUST FAIL initially (implementation not done yet)
- Tests isolated database (in-memory SQLite)
- Each test is independent and can run in any order
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.src.models import Component, Project, ProjectComponent, Tag


@pytest.mark.integration
class TestBulkDeleteIntegration:
    """Integration test for bulk component deletion functionality"""

    def test_bulk_delete_eight_components(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Scenario 3: Bulk delete (8 components)
        - Create 8 test components
        - Call bulk delete API
        - Assert all 8 components removed from DB
        - Assert affected_count = 8, success = true
        """
        # Arrange: Create 8 test components
        component_ids = []
        for i in range(1, 9):
            component = Component(
                name=f"Delete Test Component {i}",
                part_number=f"TEST-DELETE-{i:03d}",
                manufacturer="Test Manufacturer",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Verify components exist before deletion
        count_before = (
            db_session.query(Component).filter(Component.id.in_(component_ids)).count()
        )
        assert count_before == 8, "Should have 8 components before deletion"

        # Act: Call bulk delete API
        response = client.post(
            "/api/components/bulk/delete",
            headers=auth_headers,
            json={"component_ids": component_ids},
        )

        # Assert: Verify response
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["success"] is True, "Expected success=true"
        assert (
            data["affected_count"] == 8
        ), f"Expected affected_count=8, got {data['affected_count']}"
        assert (
            data.get("errors") is None or data.get("errors") == []
        ), "Expected no errors"

        # Assert: Verify all components removed from database
        db_session.expire_all()  # Clear session cache
        count_after = (
            db_session.query(Component).filter(Component.id.in_(component_ids)).count()
        )
        assert count_after == 0, "All 8 components should be deleted"

    def test_bulk_delete_with_related_tags(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk delete removes component-tag associations but preserves tags
        """
        # Arrange: Create tag
        tag = Tag(name="test-tag-preserve")
        db_session.add(tag)
        db_session.flush()

        # Arrange: Create components with tags
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Tagged Component {i}",
                part_number=f"TAGGED-{i}",
                manufacturer="Test",
                component_type="resistor",
            )
            component.tags.append(tag)
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Verify tag exists and has 3 components
        tag = db_session.query(Tag).filter_by(name="test-tag-preserve").first()
        assert len(tag.components) == 3, "Tag should have 3 components"

        # Act: Delete components
        response = client.post(
            "/api/components/bulk/delete",
            headers=auth_headers,
            json={"component_ids": component_ids},
        )

        # Assert: Components deleted
        assert response.status_code == 200
        assert response.json()["affected_count"] == 3

        # Assert: Tag still exists but has no components
        db_session.expire_all()
        tag = db_session.query(Tag).filter_by(name="test-tag-preserve").first()
        assert tag is not None, "Tag should still exist"
        assert len(tag.components) == 0, "Tag should have no components after deletion"

    def test_bulk_delete_with_project_assignments(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk delete cascades to ProjectComponent assignments
        """
        # Arrange: Create project
        project = Project(name="Delete Cascade Test Project")
        db_session.add(project)
        db_session.flush()

        # Arrange: Create components assigned to project
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Project Component {i}",
                part_number=f"PROJ-DEL-{i}",
                manufacturer="Test",
                component_type="capacitor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

            # Assign to project
            pc = ProjectComponent(
                project_id=project.id,
                component_id=component.id,
                quantity_allocated=10,
            )
            db_session.add(pc)

        db_session.commit()

        # Verify project has 3 components
        assert len(project.project_components) == 3, "Project should have 3 components"

        # Act: Delete components
        response = client.post(
            "/api/components/bulk/delete",
            headers=auth_headers,
            json={"component_ids": component_ids},
        )

        # Assert: Components deleted
        assert response.status_code == 200
        assert response.json()["affected_count"] == 3

        # Assert: ProjectComponent records also deleted (cascade)
        db_session.expire_all()
        pc_count = (
            db_session.query(ProjectComponent)
            .filter(ProjectComponent.component_id.in_(component_ids))
            .count()
        )
        assert pc_count == 0, "ProjectComponent records should be cascade deleted"

        # Assert: Project still exists
        project = db_session.query(Project).filter_by(id=project.id).first()
        assert project is not None, "Project should still exist"
        assert len(project.project_components) == 0, "Project should have no components"

    def test_bulk_delete_empty_list(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk delete with empty component list
        """
        # Act: Call with empty list
        response = client.post(
            "/api/components/bulk/delete",
            headers=auth_headers,
            json={"component_ids": []},
        )

        # Assert: Should return success with 0 affected
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 0

    def test_bulk_delete_nonexistent_component(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk delete with nonexistent component ID
        """
        # Arrange: Create one valid component
        component = Component(
            name="Valid Component",
            part_number="VALID-DELETE-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Try to delete valid + nonexistent
        response = client.post(
            "/api/components/bulk/delete",
            headers=auth_headers,
            json={"component_ids": [component.id, "nonexistent-id-12345"]},
        )

        # Assert: Should handle gracefully
        # Either skip nonexistent (partial success) or full rollback
        data = response.json()

        if data.get("success") is True:
            # Partial success - only valid deleted
            assert data["affected_count"] == 1
            assert data.get("errors") is not None  # Should report nonexistent
        else:
            # Full rollback
            assert data["affected_count"] == 0
            assert "errors" in data

            # Verify valid component not deleted
            db_session.expire_all()
            comp = db_session.query(Component).filter_by(id=component.id).first()
            assert comp is not None, "Valid component should not be deleted on rollback"

    def test_bulk_delete_requires_admin(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Test bulk delete requires admin privileges (quick check, full test in test_bulk_admin_only.py)
        """
        # Arrange: Create component
        component = Component(
            name="Admin Only Delete",
            part_number="ADMIN-DEL-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Try to delete as non-admin user
        response = client.post(
            "/api/components/bulk/delete",
            headers=user_auth_headers,  # Non-admin user
            json={"component_ids": [component.id]},
        )

        # Assert: Should return 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

        # Verify component not deleted
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()
        assert comp is not None, "Component should not be deleted by non-admin"
