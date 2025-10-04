"""
Integration test for bulk operation admin-only access control.
Tests the scenario: Verify non-admin gets 403 Forbidden.

Following TDD principles:
- This test MUST FAIL initially (implementation not done yet)
- Tests isolated database (in-memory SQLite)
- Each test is independent and can run in any order
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.src.models import Component, Project


@pytest.mark.integration
class TestBulkAdminOnly:
    """Integration test for bulk operation admin-only access enforcement"""

    def test_bulk_add_tags_non_admin_forbidden(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Scenario 6: Admin-only access enforcement
        - Create non-admin user token
        - Call any bulk operation endpoint
        - Assert 403 Forbidden response
        - Assert detail = "Admin privileges required"
        """
        # Arrange: Create test component
        component = Component(
            name="Admin Only Component",
            part_number="ADMIN-TAG-001",
            manufacturer="Test Mfg",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Try to bulk add tags as non-admin user
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=user_auth_headers,  # Non-admin user
            json={
                "component_ids": [component.id],
                "tags": ["unauthorized-tag"],
            },
        )

        # Assert: Verify 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

        data = response.json()
        assert "detail" in data, "Response should have 'detail' field"

        # Check for admin privileges message
        detail = data["detail"].lower()
        assert (
            "admin" in detail or "privilege" in detail or "forbidden" in detail
        ), f"Expected admin/privilege message, got: {data['detail']}"

        # Verify tag was NOT added
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()
        tag_names = {tag.name for tag in comp.tags}
        assert (
            "unauthorized-tag" not in tag_names
        ), "Tag should not be added by non-admin"

    def test_bulk_assign_project_non_admin_forbidden(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Test bulk project assignment requires admin privileges
        """
        # Arrange: Create project and component
        project = Project(name="Admin Only Project")
        component = Component(
            name="Component",
            part_number="ADMIN-PROJ-001",
            manufacturer="Test",
            component_type="capacitor",
        )
        db_session.add(project)
        db_session.add(component)
        db_session.commit()

        # Act: Try to bulk assign as non-admin
        response = client.post(
            "/api/v1/components/bulk/projects/assign",
            headers=user_auth_headers,
            json={
                "component_ids": [component.id],
                "project_id": project.id,
            },
        )

        # Assert: 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

        # Verify no assignment created
        db_session.expire_all()
        project = db_session.query(Project).filter_by(id=project.id).first()
        assert (
            len(project.project_components) == 0
        ), "No assignment should be created by non-admin"

    def test_bulk_delete_non_admin_forbidden(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Test bulk delete requires admin privileges
        """
        # Arrange: Create component
        component = Component(
            name="Protected Component",
            part_number="ADMIN-DEL-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Try to bulk delete as non-admin
        response = client.post(
            "/api/v1/components/bulk/delete",
            headers=user_auth_headers,
            json={
                "component_ids": [component.id],
            },
        )

        # Assert: 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

        # Verify component NOT deleted
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()
        assert comp is not None, "Component should not be deleted by non-admin"

    def test_bulk_remove_tags_non_admin_forbidden(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Test bulk tag removal requires admin privileges
        """
        # Arrange: Create component with tag
        from backend.src.models import Tag

        tag = Tag(name="protected-tag")
        component = Component(
            name="Tagged Component",
            part_number="ADMIN-RMTAG-001",
            manufacturer="Test",
            component_type="resistor",
        )
        component.tags.append(tag)
        db_session.add(component)
        db_session.commit()

        # Act: Try to remove tag as non-admin
        response = client.post(
            "/api/v1/components/bulk/tags/remove",
            headers=user_auth_headers,
            json={
                "component_ids": [component.id],
                "tags": ["protected-tag"],
            },
        )

        # Assert: 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

        # Verify tag still present
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()
        tag_names = {tag.name for tag in comp.tags}
        assert "protected-tag" in tag_names, "Tag should not be removed by non-admin"

    def test_admin_user_can_perform_bulk_operations(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test that admin users CAN perform bulk operations (positive case)
        """
        # Arrange: Create component
        component = Component(
            name="Admin Test Component",
            part_number="ADMIN-OK-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Add tag as admin user
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,  # Admin user
            json={
                "component_ids": [component.id],
                "tags": ["admin-allowed"],
            },
        )

        # Assert: Success (200 or 201)
        assert response.status_code in [
            200,
            201,
        ], f"Admin should be able to bulk add tags, got {response.status_code}"

        data = response.json()
        assert data.get("success") is True, "Admin operation should succeed"

        # Verify tag added
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()
        tag_names = {tag.name for tag in comp.tags}
        assert "admin-allowed" in tag_names, "Admin should be able to add tags"

    def test_unauthenticated_user_gets_401(
        self, client: TestClient, db_session: Session
    ):
        """
        Test that unauthenticated requests get 401 Unauthorized (not 403)
        """
        # Arrange: Create component
        component = Component(
            name="Unauth Test",
            part_number="UNAUTH-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Try bulk operation without auth headers
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            # No headers = no authentication
            json={
                "component_ids": [component.id],
                "tags": ["test"],
            },
        )

        # Assert: 401 Unauthorized (not 403)
        assert (
            response.status_code == 401
        ), f"Unauthenticated request should get 401, got {response.status_code}"

    def test_expired_token_gets_401(self, client: TestClient, db_session: Session):
        """
        Test that expired/invalid tokens get 401 Unauthorized
        """
        # Arrange: Create component
        component = Component(
            name="Expired Token Test",
            part_number="EXPIRED-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Use invalid token
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers={"Authorization": "Bearer invalid-expired-token-12345"},
            json={
                "component_ids": [component.id],
                "tags": ["test"],
            },
        )

        # Assert: 401 Unauthorized
        assert (
            response.status_code == 401
        ), f"Invalid token should get 401, got {response.status_code}"

    def test_consistent_403_message_across_endpoints(
        self, client: TestClient, db_session: Session, user_auth_headers: dict
    ):
        """
        Test that all bulk endpoints return consistent 403 error messages
        """
        # Arrange: Create test data
        component = Component(
            name="Consistency Test",
            part_number="CONSIST-001",
            manufacturer="Test",
            component_type="resistor",
        )
        project = Project(name="Test Project")
        db_session.add(component)
        db_session.add(project)
        db_session.commit()

        # Test all bulk endpoints
        endpoints = [
            (
                "/api/v1/components/bulk/tags/add",
                {"component_ids": [component.id], "tags": ["test"]},
            ),
            (
                "/api/v1/components/bulk/tags/remove",
                {"component_ids": [component.id], "tags": ["test"]},
            ),
            (
                "/api/v1/components/bulk/projects/assign",
                {"component_ids": [component.id], "project_id": project.id},
            ),
            ("/api/v1/components/bulk/delete", {"component_ids": [component.id]}),
        ]

        for endpoint, payload in endpoints:
            response = client.post(
                endpoint,
                headers=user_auth_headers,
                json=payload,
            )

            # All should return 403
            assert (
                response.status_code == 403
            ), f"Endpoint {endpoint} should return 403, got {response.status_code}"

            # All should have detail field with admin message
            data = response.json()
            assert "detail" in data, f"Endpoint {endpoint} missing 'detail' field"

            detail = data["detail"].lower()
            assert (
                "admin" in detail or "privilege" in detail or "forbidden" in detail
            ), f"Endpoint {endpoint} has inconsistent error message: {data['detail']}"
