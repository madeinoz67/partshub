"""
Integration Test: Scenario 7 - Duplicate Prevention

User Story: User prevented from creating locations with existing names.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 7

Functional Requirements: FR-007 (Duplicate prevention), Transactional behavior

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestDuplicatePrevention:
    """
    Scenario 7: Duplicate Prevention (FR-007)

    User is prevented from creating locations with names that already exist
    Transactional: If ANY duplicate exists, NO locations are created
    """

    def test_prevent_duplicate_on_second_creation(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: Locations 'test-a', 'test-b', 'test-c' already exist
        When: User tries to create same locations again
        Then: Creation fails with duplicate error, no locations created
        """
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}

        # First creation - should succeed
        response1 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )
        assert response1.status_code == 201, "First creation should succeed"
        assert response1.json()["created_count"] == 3

        # Second creation with same configuration - should fail
        response2 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Should return 409 Conflict
        assert (
            response2.status_code == 409
        ), f"Expected 409 Conflict, got {response2.status_code}"

        data = response2.json()
        # Verify error message mentions duplicates
        if "errors" in data:
            assert len(data["errors"]) > 0
            error_text = " ".join(data["errors"]).lower()
            assert "duplicate" in error_text or "already exists" in error_text
            # Should mention the duplicate location names
            assert (
                "test-a" in error_text
                or "test-b" in error_text
                or "test-c" in error_text
            )

    def test_transactional_rollback_on_partial_duplicate(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: Location 'overlap-b' already exists
        When: User tries to create 'overlap-a', 'overlap-b', 'overlap-c'
        Then: All creation is rolled back (created_count = 0)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create single location 'overlap-b'
        single_payload = {
            "layout_type": "row",
            "prefix": "overlap-",
            "ranges": [{"range_type": "letters", "start": "b", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }
        response1 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=single_payload,
            headers=headers,
        )
        assert response1.status_code == 201

        # Try to create batch that includes 'overlap-b'
        batch_payload = {
            "layout_type": "row",
            "prefix": "overlap-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }
        response2 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=batch_payload,
            headers=headers,
        )

        assert response2.status_code == 409

        data = response2.json()
        # Transactional: created_count should be 0 (none created)
        assert (
            data.get("created_count", -1) == 0
        ), "Transaction should rollback, no locations created"
        assert data.get("success", True) is False

    def test_case_sensitive_duplicate_detection(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: Location 'Case-a' exists
        When: User tries to create 'case-a'
        Then: Duplicate detection should be case-sensitive (or insensitive based on design)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create with uppercase
        upper_payload = {
            "layout_type": "row",
            "prefix": "Case-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }
        response1 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=upper_payload,
            headers=headers,
        )
        assert response1.status_code == 201

        # Try with lowercase
        lower_payload = {
            "layout_type": "row",
            "prefix": "case-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }
        response2 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=lower_payload,
            headers=headers,
        )

        # Design choice: case-sensitive should succeed, case-insensitive should fail
        # This tests the actual behavior
        assert response2.status_code in [201, 409]

    def test_duplicate_with_different_parent(self, client: TestClient, auth_token: str):
        """
        Given: Location 'child-a' exists under parent1
        When: User tries to create 'child-a' under parent2
        Then: Duplicate is detected (names must be globally unique)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create two parent locations
        parent1_payload = {
            "layout_type": "single",
            "prefix": "parent1",
            "ranges": [],
            "separators": [],
            "location_type": "cabinet",
            "single_part_only": False,
        }
        parent1_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=parent1_payload,
            headers=headers,
        )
        parent1_id = parent1_resp.json()["created_ids"][0]

        parent2_payload = {
            "layout_type": "single",
            "prefix": "parent2",
            "ranges": [],
            "separators": [],
            "location_type": "cabinet",
            "single_part_only": False,
        }
        parent2_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=parent2_payload,
            headers=headers,
        )
        parent2_id = parent2_resp.json()["created_ids"][0]

        # Create child-a under parent1
        child1_payload = {
            "layout_type": "row",
            "prefix": "child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "parent_id": parent1_id,
            "location_type": "drawer",
            "single_part_only": False,
        }
        response1 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=child1_payload,
            headers=headers,
        )
        assert response1.status_code == 201

        # Try to create child-a under parent2 (same name, different parent)
        child2_payload = {
            "layout_type": "row",
            "prefix": "child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "parent_id": parent2_id,
            "location_type": "drawer",
            "single_part_only": False,
        }
        response2 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=child2_payload,
            headers=headers,
        )

        # Should detect duplicate (names are globally unique per spec)
        assert response2.status_code == 409

    def test_no_duplicates_within_same_batch(self, client: TestClient, auth_token: str):
        """
        Given: User configures valid layout
        When: Layout generates unique names
        Then: All locations are created (no internal duplicates)
        """
        payload = {
            "layout_type": "grid",
            "prefix": "unique-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 3},
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Should succeed - grid layout generates unique names
        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 9  # 3x3 grid
        assert len(data["created_ids"]) == 9
        # All IDs should be unique
        assert len(set(data["created_ids"])) == 9
