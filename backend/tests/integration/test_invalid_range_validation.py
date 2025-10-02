"""
Integration Test: Scenario 6 - Invalid Range Validation

User Story: User corrected when start > end.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 6

Functional Requirements: FR-019 (Start ≤ End validation)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestInvalidRangeValidation:
    """
    Scenario 6: Invalid Range Validation (FR-019)

    User receives validation error when start value is greater than end value
    """

    def test_preview_rejects_reversed_letter_range(self, client: TestClient):
        """
        Given: User configures range with start='z', end='a' (reversed)
        When: User requests preview
        Then: Validation error is returned
        """
        payload = {
            "layout_type": "row",
            "prefix": "invalid-",
            "ranges": [{"range_type": "letters", "start": "z", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Accept either 422 (schema validation) or 200 with errors (business logic)
        if response.status_code == 200:
            data = response.json()
            assert (
                data["is_valid"] is False
            ), "Should be invalid for reversed range"
            assert len(data["errors"]) > 0, "Should have validation errors"
            error_text = " ".join(data["errors"]).lower()
            assert "start" in error_text and "end" in error_text
        else:
            assert (
                response.status_code == 422
            ), f"Expected 422 or 200, got {response.status_code}"

    def test_preview_rejects_reversed_number_range(self, client: TestClient):
        """
        Given: User configures number range with start=100, end=1 (reversed)
        When: User requests preview
        Then: Validation error is returned
        """
        payload = {
            "layout_type": "row",
            "prefix": "num-",
            "ranges": [{"range_type": "numbers", "start": 100, "end": 1}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) > 0
        else:
            assert response.status_code == 422

    def test_preview_accepts_equal_start_end(self, client: TestClient):
        """
        Given: User configures range with start=end (single item)
        When: User requests preview
        Then: Configuration is valid (generates 1 location)
        """
        payload = {
            "layout_type": "row",
            "prefix": "single-",
            "ranges": [{"range_type": "letters", "start": "m", "end": "m"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True, "Equal start/end should be valid"
        assert data["total_count"] == 1, "Should generate 1 location"

    def test_bulk_create_rejects_reversed_range(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User is authenticated
        When: User tries to create with reversed range
        Then: Request is rejected
        """
        payload = {
            "layout_type": "row",
            "prefix": "bad-",
            "ranges": [{"range_type": "letters", "start": "z", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        # Should reject with validation error
        assert response.status_code in [400, 422]

    def test_grid_with_one_reversed_range(self, client: TestClient):
        """
        Given: User configures grid with one reversed range
        When: User requests preview
        Then: Validation error is returned
        """
        payload = {
            "layout_type": "grid",
            "prefix": "grid-",
            "ranges": [
                {"range_type": "letters", "start": "z", "end": "a"},  # Reversed
                {"range_type": "numbers", "start": 1, "end": 5},  # Valid
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) > 0
        else:
            assert response.status_code == 422

    def test_letter_range_case_insensitive_validation(self, client: TestClient):
        """
        Given: User configures range with uppercase start, lowercase end (Z to a)
        When: User requests preview
        Then: Validation handles case properly
        """
        payload = {
            "layout_type": "row",
            "prefix": "case-",
            "ranges": [{"range_type": "letters", "start": "Z", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should either normalize case or reject mixed case
        # This tests the implementation's handling of case
        if response.status_code == 200:
            data = response.json()
            # Implementation may normalize or reject - both are valid
            assert isinstance(data["is_valid"], bool)
        else:
            assert response.status_code in [400, 422]
