"""
Contract test for GET /api/wizard/footprints/search
Tests fuzzy footprint search endpoint for wizard autocomplete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestWizardFootprintsContract:
    """Contract tests for wizard footprint search endpoint"""

    def test_footprint_search_requires_admin_auth(self, client: TestClient):
        """Test that footprint search requires admin authentication"""
        response = client.get("/api/wizard/footprints/search?query=SOIC&limit=10")

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_footprint_search_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot search footprints"""
        response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=user_auth_headers,
        )

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_footprint_search_with_admin_auth(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test footprint search with admin authentication"""
        # Seed test footprints (using components with different packages)
        from backend.src.models.component import Component

        components = [
            Component(name="IC 1", package="SOIC-8"),
            Component(name="IC 2", package="SOIC-14"),
            Component(name="IC 3", package="TSSOP-8"),
            Component(name="IC 4", package="QFN-32"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=auth_headers,
        )

        # Debug output if fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Should return footprints matching "SOIC"
        # Each result should have FootprintSuggestion schema
        for suggestion in data:
            assert (
                "id" in suggestion or "name" in suggestion
            )  # id might be null for new
            assert "name" in suggestion
            assert "score" in suggestion
            assert isinstance(suggestion["score"], int | float)

    def test_footprint_search_fuzzy_matching(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test fuzzy matching returns relevant results ranked by score"""
        from backend.src.models.component import Component

        # Seed footprints with varying similarity to "SOIC"
        components = [
            Component(name="C1", package="SOIC-8"),  # Exact prefix match
            Component(name="C2", package="SOIC-14"),  # Exact prefix match
            Component(name="C3", package="TSSOP-8"),  # No match
            Component(name="C4", package="SO-8"),  # Partial match
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return results ranked by score
        assert len(data) > 0

        # Verify results are sorted by score descending
        scores = [s["score"] for s in data]
        assert scores == sorted(scores, reverse=True)

        # SOIC-8 or SOIC-14 should be in top results (highest scores)
        top_names = [s["name"] for s in data[:2]]
        assert any("SOIC" in name for name in top_names)

    def test_footprint_search_missing_query_param(
        self, client: TestClient, auth_headers
    ):
        """Test search without required query parameter"""
        response = client.get(
            "/api/wizard/footprints/search?limit=10",
            headers=auth_headers,
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_footprint_search_respects_limit(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that limit parameter is respected"""
        from backend.src.models.component import Component

        # Create many footprints
        components = [
            Component(name=f"IC {i}", package=f"PACKAGE-{i}") for i in range(20)
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=PACKAGE&limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return at most 5 results
        assert len(data) <= 5

    def test_footprint_search_empty_query(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test search with empty query string"""
        from backend.src.models.component import Component

        components = [
            Component(name="C1", package="SOIC-8"),
            Component(name="C2", package="QFN-32"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=&limit=10",
            headers=auth_headers,
        )

        # Empty query should either return validation error or empty results
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Empty query might return all footprints or none
            assert isinstance(data, list)

    def test_footprint_search_no_results(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test search with query that matches no footprints"""
        from backend.src.models.component import Component

        components = [
            Component(name="C1", package="SOIC-8"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=ZZZNOMATCH&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty list for no matches
        assert isinstance(data, list)
        assert len(data) == 0

    def test_footprint_search_deduplication(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that duplicate footprints are deduplicated in results"""
        from backend.src.models.component import Component

        # Create multiple components with same footprint
        components = [
            Component(name="IC 1", package="SOIC-8"),
            Component(name="IC 2", package="SOIC-8"),
            Component(name="IC 3", package="SOIC-8"),
            Component(name="IC 4", package="SOIC-14"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # "SOIC-8" should appear only once
        footprint_names = [s["name"] for s in data]
        assert len(footprint_names) == len(set(footprint_names))  # No duplicates

    def test_footprint_search_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches FootprintSuggestion schema"""
        from backend.src.models.component import Component

        component = Component(name="Test IC", package="LQFP-48")
        db_session.add(component)
        db_session.commit()

        response = client.get(
            "/api/wizard/footprints/search?query=LQFP&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        suggestion = data[0]

        # Required fields
        assert "name" in suggestion
        assert "score" in suggestion
        assert suggestion["name"] == "LQFP-48"
        assert isinstance(suggestion["score"], int | float)
        assert suggestion["score"] > 0

        # Optional id field (might be null for suggestions without explicit footprint table)
        # id present if using footprint table, absent if using distinct package strings

    def test_footprint_search_case_insensitive(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that search is case-insensitive"""
        from backend.src.models.component import Component

        component = Component(name="Test IC", package="SOIC-8")
        db_session.add(component)
        db_session.commit()

        # Test lowercase query
        response = client.get(
            "/api/wizard/footprints/search?query=soic&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should find SOIC-8 regardless of case
        assert len(data) >= 1
        assert any("SOIC" in s["name"].upper() for s in data)
