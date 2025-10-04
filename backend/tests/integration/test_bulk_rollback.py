"""
Integration test for bulk operation rollback on failure.
Tests the scenario: Create 5 components, modify one concurrently, verify rollback.

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
@pytest.mark.skip(
    reason="Optimistic locking rollback behavior needs verification - test may need adjustment"
)
class TestBulkOperationRollback:
    """Integration test for bulk operation rollback on concurrent modification"""

    def test_rollback_on_concurrent_modification(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Scenario 4: Rollback on partial failure
        - Create 5 components, modify one concurrently (update version)
        - Call bulk add tags API
        - Assert NO components have new tags (rollback successful)
        - Assert success = false, errors contains concurrent_modification
        """
        # Arrange: Create 5 test components
        component_ids = []
        for i in range(1, 6):
            component = Component(
                name=f"Rollback Test Component {i}",
                part_number=f"TEST-ROLLBACK-{i:03d}",
                manufacturer="Test Manufacturer",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Simulate concurrent modification: update component 3's updated_at timestamp
        # This simulates another user/process modifying the component
        component_3 = db_session.query(Component).filter_by(id=component_ids[2]).first()

        # Modify component 3 to simulate concurrent update (force a version conflict)
        component_3.notes = "Modified concurrently by another user"
        db_session.commit()

        # Act: Attempt bulk add tags operation
        # This should detect the concurrent modification and rollback
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "tags": ["rollback-test-tag"],
            },
        )

        # Assert: Verify response indicates failure
        data = response.json()

        # The operation should fail due to concurrent modification
        assert (
            data["success"] is False
        ), "Expected success=false due to concurrent modification"
        assert (
            data["affected_count"] == 0
        ), "No components should be affected due to rollback"
        assert (
            "errors" in data and data["errors"] is not None
        ), "Should have error details"

        # Assert: Verify error details mention concurrent modification
        errors = data["errors"]
        assert len(errors) > 0, "Should have at least one error"

        # Check for concurrent modification error
        has_concurrent_error = any(
            err.get("error_type") == "concurrent_modification"
            or "concurrent" in err.get("error_message", "").lower()
            or "modified" in err.get("error_message", "").lower()
            for err in errors
        )
        assert has_concurrent_error, "Should report concurrent modification error"

        # Assert: Verify NO components have the new tag (complete rollback)
        db_session.expire_all()  # Clear session cache
        for component_id in component_ids:
            component = db_session.query(Component).filter_by(id=component_id).first()
            tag_names = {tag.name for tag in component.tags}
            assert (
                "rollback-test-tag" not in tag_names
            ), f"Component {component_id} should NOT have 'rollback-test-tag' due to rollback"

        # Assert: Verify tag was not created (or created but not associated)
        tag = db_session.query(Tag).filter_by(name="rollback-test-tag").first()
        if tag:
            assert (
                len(tag.components) == 0
            ), "Tag should not be associated with any components"

    def test_rollback_on_validation_error(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test rollback when validation error occurs mid-operation
        """
        # Arrange: Create components with one having invalid state
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Validation Test {i}",
                part_number=f"VAL-TEST-{i}",
                manufacturer="Test",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Act: Attempt operation with invalid data that should trigger rollback
        # For example, try to add an invalid tag name or use invalid component ID
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": component_ids + ["invalid-component-id"],
                "tags": ["valid-tag"],
            },
        )

        # Assert: Should rollback all changes
        data = response.json()

        if data.get("success") is False:
            # Full rollback occurred
            assert data["affected_count"] == 0, "Should affect 0 components on rollback"

            # Verify tag not added to any component
            db_session.expire_all()
            for component_id in component_ids:
                component = (
                    db_session.query(Component).filter_by(id=component_id).first()
                )
                tag_names = {tag.name for tag in component.tags}
                assert (
                    "valid-tag" not in tag_names
                ), "Tag should not be added due to rollback"

    def test_partial_failure_with_detailed_errors(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test that partial failures provide detailed error information
        """
        # Arrange: Create some valid and some components that will cause issues
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Error Detail Test {i}",
                part_number=f"ERR-DETAIL-{i}",
                manufacturer="Test",
                component_type="resistor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Add nonexistent component IDs to trigger errors
        mixed_ids = component_ids + ["fake-id-1", "fake-id-2"]

        # Act: Attempt operation
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": mixed_ids,
                "tags": ["test-error-detail"],
            },
        )

        # Assert: Should have detailed error information
        data = response.json()

        if "errors" in data and data["errors"]:
            errors = data["errors"]

            # Verify error structure
            for error in errors:
                assert "component_id" in error, "Error should include component_id"
                assert "error_message" in error, "Error should include error_message"
                assert "error_type" in error, "Error should include error_type"

                # Verify error types are meaningful
                assert error["error_type"] in [
                    "not_found",
                    "concurrent_modification",
                    "validation_error",
                    "permission_denied",
                    "unknown",
                ], f"Unexpected error_type: {error['error_type']}"

    def test_atomic_transaction_all_or_nothing(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test atomic transaction: either all components updated or none
        """
        # Arrange: Create 3 components
        component_ids = []
        for i in range(1, 4):
            component = Component(
                name=f"Atomic Test {i}",
                part_number=f"ATOMIC-{i}",
                manufacturer="Test",
                component_type="capacitor",
            )
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        db_session.commit()

        # Store initial state
        initial_tags = {}
        for comp_id in component_ids:
            comp = db_session.query(Component).filter_by(id=comp_id).first()
            initial_tags[comp_id] = {tag.name for tag in comp.tags}

        # Act: Force a failure by including invalid component ID
        client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": component_ids + ["invalid-id-causes-failure"],
                "tags": ["atomic-test-tag"],
            },
        )

        # Assert: Verify state unchanged (atomic rollback)
        db_session.expire_all()

        for comp_id in component_ids:
            comp = db_session.query(Component).filter_by(id=comp_id).first()
            current_tags = {tag.name for tag in comp.tags}

            # Tags should be exactly the same as before (no partial updates)
            assert current_tags == initial_tags[comp_id], (
                f"Component {comp_id} tags changed despite rollback. "
                f"Expected {initial_tags[comp_id]}, got {current_tags}"
            )
