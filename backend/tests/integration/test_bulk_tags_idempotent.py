"""
Integration test for bulk tag operation idempotency.
Tests the scenario: Create 3 components (2 with tag), verify idempotent behavior.

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
class TestBulkTagsIdempotent:
    """Integration test for bulk tag operation idempotency"""

    def test_duplicate_tags_handled_idempotently(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Scenario 5: Duplicate tags handled idempotently
        - Create 3 components, 2 already have "resistor" tag
        - Call bulk add tags with ["resistor"]
        - Assert tag added only to component without it
        - Assert no duplicate tags created
        """
        # Arrange: Create tag
        resistor_tag = Tag(name="resistor")
        db_session.add(resistor_tag)
        db_session.flush()

        # Arrange: Create 3 components, 2 with tag already
        component_ids = []

        # Components 1 and 2 already have the tag
        for i in range(1, 3):
            component = Component(
                name=f"Tagged Component {i}",
                part_number=f"TAGGED-{i}",
                manufacturer="Test Mfg",
                component_type="resistor",
            )
            component.tags.append(resistor_tag)
            db_session.add(component)
            db_session.flush()
            component_ids.append(component.id)

        # Component 3 does NOT have the tag
        component_3 = Component(
            name="Untagged Component 3",
            part_number="UNTAGGED-3",
            manufacturer="Test Mfg",
            component_type="resistor",
        )
        db_session.add(component_3)
        db_session.flush()
        component_ids.append(component_3.id)

        db_session.commit()

        # Verify initial state
        comp1 = db_session.query(Component).filter_by(id=component_ids[0]).first()
        comp2 = db_session.query(Component).filter_by(id=component_ids[1]).first()
        comp3 = db_session.query(Component).filter_by(id=component_ids[2]).first()

        assert len(comp1.tags) == 1 and comp1.tags[0].name == "resistor"
        assert len(comp2.tags) == 1 and comp2.tags[0].name == "resistor"
        assert len(comp3.tags) == 0, "Component 3 should have no tags initially"

        # Act: Add "resistor" tag to all 3 components
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "tags": ["resistor"],
            },
        )

        # Assert: Verify response
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["success"] is True, "Expected success=true"

        # affected_count could be 1 (only component 3) or 3 (all processed idempotently)
        # Both are valid idempotent behaviors
        assert (
            data["affected_count"] in [1, 3]
        ), f"Expected affected_count 1 (only new) or 3 (all processed), got {data['affected_count']}"

        # Assert: Verify no duplicate tags created
        db_session.expire_all()

        comp1 = db_session.query(Component).filter_by(id=component_ids[0]).first()
        comp2 = db_session.query(Component).filter_by(id=component_ids[1]).first()
        comp3 = db_session.query(Component).filter_by(id=component_ids[2]).first()

        # Each component should have exactly 1 "resistor" tag (no duplicates)
        comp1_resistor_count = sum(1 for tag in comp1.tags if tag.name == "resistor")
        comp2_resistor_count = sum(1 for tag in comp2.tags if tag.name == "resistor")
        comp3_resistor_count = sum(1 for tag in comp3.tags if tag.name == "resistor")

        assert (
            comp1_resistor_count == 1
        ), "Component 1 should have exactly 1 'resistor' tag"
        assert (
            comp2_resistor_count == 1
        ), "Component 2 should have exactly 1 'resistor' tag"
        assert comp3_resistor_count == 1, "Component 3 should now have 1 'resistor' tag"

        # Assert: Verify total tag count (should still be 1 tag in database)
        total_tags = db_session.query(Tag).filter_by(name="resistor").count()
        assert (
            total_tags == 1
        ), "Should have exactly 1 'resistor' tag in database (no duplicates)"

    def test_multiple_tags_idempotent_partial_overlap(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test idempotency with multiple tags where components have partial overlap
        """
        # Arrange: Create tags
        tag_smd = Tag(name="SMD")
        tag_0805 = Tag(name="0805")
        db_session.add(tag_smd)
        db_session.add(tag_0805)
        db_session.flush()

        # Arrange: Create components with different tag combinations
        component_ids = []

        # Component 1: has SMD only
        comp1 = Component(
            name="Component 1",
            part_number="OVERLAP-1",
            manufacturer="Test",
            component_type="resistor",
        )
        comp1.tags.append(tag_smd)
        db_session.add(comp1)
        db_session.flush()
        component_ids.append(comp1.id)

        # Component 2: has 0805 only
        comp2 = Component(
            name="Component 2",
            part_number="OVERLAP-2",
            manufacturer="Test",
            component_type="resistor",
        )
        comp2.tags.append(tag_0805)
        db_session.add(comp2)
        db_session.flush()
        component_ids.append(comp2.id)

        # Component 3: has both SMD and 0805
        comp3 = Component(
            name="Component 3",
            part_number="OVERLAP-3",
            manufacturer="Test",
            component_type="resistor",
        )
        comp3.tags.append(tag_smd)
        comp3.tags.append(tag_0805)
        db_session.add(comp3)
        db_session.flush()
        component_ids.append(comp3.id)

        db_session.commit()

        # Act: Add both tags to all components (idempotent)
        response = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "tags": ["SMD", "0805"],
            },
        )

        # Assert: Success
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert: Verify each component has both tags exactly once
        db_session.expire_all()

        for comp_id in component_ids:
            comp = db_session.query(Component).filter_by(id=comp_id).first()

            smd_count = sum(1 for tag in comp.tags if tag.name == "SMD")
            tag_0805_count = sum(1 for tag in comp.tags if tag.name == "0805")

            assert (
                smd_count == 1
            ), f"Component {comp_id} should have exactly 1 'SMD' tag"
            assert (
                tag_0805_count == 1
            ), f"Component {comp_id} should have exactly 1 '0805' tag"
            assert (
                len(comp.tags) == 2
            ), f"Component {comp_id} should have exactly 2 tags total"

    def test_idempotent_tag_removal(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test idempotent tag removal (removing tag that some components don't have)
        """
        # Arrange: Create tag
        remove_tag = Tag(name="remove-me")
        db_session.add(remove_tag)
        db_session.flush()

        # Arrange: Create components, only some have the tag
        component_ids = []

        # Component 1 has the tag
        comp1 = Component(
            name="Has Tag",
            part_number="REMOVE-1",
            manufacturer="Test",
            component_type="resistor",
        )
        comp1.tags.append(remove_tag)
        db_session.add(comp1)
        db_session.flush()
        component_ids.append(comp1.id)

        # Component 2 does NOT have the tag
        comp2 = Component(
            name="No Tag",
            part_number="REMOVE-2",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(comp2)
        db_session.flush()
        component_ids.append(comp2.id)

        db_session.commit()

        # Act: Remove tag from both components (idempotent - should not fail on comp2)
        response = client.post(
            "/api/v1/components/bulk/tags/remove",
            headers=auth_headers,
            json={
                "component_ids": component_ids,
                "tags": ["remove-me"],
            },
        )

        # Assert: Success (idempotent removal)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Assert: Both components have no "remove-me" tag
        db_session.expire_all()

        comp1 = db_session.query(Component).filter_by(id=component_ids[0]).first()
        comp2 = db_session.query(Component).filter_by(id=component_ids[1]).first()

        assert len([t for t in comp1.tags if t.name == "remove-me"]) == 0
        assert len([t for t in comp2.tags if t.name == "remove-me"]) == 0

    def test_adding_same_tag_twice_sequential(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """
        Test adding same tag twice in sequential operations is idempotent
        """
        # Arrange: Create component
        component = Component(
            name="Sequential Test",
            part_number="SEQ-001",
            manufacturer="Test",
            component_type="capacitor",
        )
        db_session.add(component)
        db_session.commit()

        # Act: Add tag first time
        response1 = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": [component.id],
                "tags": ["sequential-tag"],
            },
        )

        # Act: Add same tag second time
        response2 = client.post(
            "/api/v1/components/bulk/tags/add",
            headers=auth_headers,
            json={
                "component_ids": [component.id],
                "tags": ["sequential-tag"],
            },
        )

        # Assert: Both operations succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Assert: Component has tag exactly once
        db_session.expire_all()
        comp = db_session.query(Component).filter_by(id=component.id).first()

        sequential_tag_count = sum(
            1 for tag in comp.tags if tag.name == "sequential-tag"
        )
        assert (
            sequential_tag_count == 1
        ), "Should have exactly 1 'sequential-tag' after two additions"
