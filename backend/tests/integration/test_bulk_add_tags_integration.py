"""
Integration test for bulk add tags operation.
Tests the scenario: Create 3 components, bulk add tags, verify all have tags.

Following TDD principles:
- This test MUST FAIL initially (implementation not done yet)
- Tests isolated database (in-memory SQLite)
- Each test is independent and can run in any order
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.src.models import Component, Tag


@pytest.mark.integration
class TestBulkAddTagsIntegration:
    """Integration test for bulk tag addition functionality"""

    def test_bulk_add_tags_to_three_components(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Scenario 1: Bulk add tags (3 components)
        - Create 3 test components in isolated DB
        - Call bulk add tags API with ["resistor", "SMD"]
        - Assert all 3 components have both tags
        - Assert affected_count = 3, success = true
        """
        # Arrange: Create 3 test components
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Test Component {i}",
                part_number=f"TEST-BULK-TAG-{i}",
                manufacturer="Test Manufacturer",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Act: Call bulk add tags API
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={"component_ids": component_ids, "tags": ["resistor", "SMD"]},
        )

        # Assert: Verify response
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["success"] is True, "Expected success=true"
        assert (
            data["affected_count"] == 3
        ), f"Expected affected_count=3, got {data['affected_count']}"
        assert (
            data.get("errors") is None or data.get("errors") == []
        ), "Expected no errors"

        # Assert: Verify all 3 components have both tags
        for component_id in component_ids:
            component = db_session.query(Component).filter_by(id=component_id).first()
            tag_names = {tag.name for tag in component.tags}
            assert (
                "resistor" in tag_names
            ), f"Component {component_id} missing 'resistor' tag"
            assert "SMD" in tag_names, f"Component {component_id} missing 'SMD' tag"

    def test_bulk_add_tags_creates_new_tags(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test that bulk add tags creates new Tag records if they don't exist
        """
        # Arrange: Create components
        component_ids = []
        for i in range(1, 3):
            component = Component(
                name=f"Component {i}",
                part_number=f"TEST-NEW-TAG-{i}",
                manufacturer="Test Mfg",
                component_type="capacitor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Verify tags don't exist yet
        initial_tag_count = db_session.query(Tag).count()

        # Act: Add new tags via bulk operation
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={"component_ids": component_ids, "tags": ["new-tag-1", "new-tag-2"]},
        )

        # Assert: Tags were created
        assert response.status_code == 200
        final_tag_count = db_session.query(Tag).count()
        assert final_tag_count == initial_tag_count + 2, "Expected 2 new tags created"

        # Verify tags exist in database
        tag1 = db_session.query(Tag).filter_by(name="new-tag-1").first()
        tag2 = db_session.query(Tag).filter_by(name="new-tag-2").first()
        assert tag1 is not None, "Tag 'new-tag-1' should exist"
        assert tag2 is not None, "Tag 'new-tag-2' should exist"

    def test_bulk_add_tags_empty_component_list(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk add tags with empty component list returns appropriate response
        """
        # Act: Call with empty component list
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={"component_ids": [], "tags": ["test-tag"]},
        )

        # Assert: Should return success with 0 affected
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 0

    def test_bulk_add_tags_nonexistent_component(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test bulk add tags with nonexistent component ID returns error
        """
        # Arrange: Create one valid component
        component = Component(
            name="Valid Component",
            part_number="VALID-001",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Include nonexistent component ID
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": [component.id, "nonexistent-id-12345"],
                "tags": ["test-tag"],
            },
        )

        # Assert: Should fail or partially succeed with error details
        data = response.json()
        # Either full rollback (success=false) or partial with errors
        if data.get("success") is False:
            assert "errors" in data
            assert len(data["errors"]) > 0
            assert data["affected_count"] == 0  # Rollback
        else:
            # If partial success, should have error details
            assert "errors" in data and data["errors"] is not None
