"""
Contract test for GET /api/wizard/manufacturers/search
Tests fuzzy manufacturer search endpoint for wizard autocomplete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestWizardManufacturersContract:
    """Contract tests for wizard manufacturer search endpoint"""

    def test_manufacturer_search_requires_admin_auth(self, client: TestClient):
        """Test that manufacturer search requires admin authentication"""
        response = client.get("/api/wizard/manufacturers/search?query=TI&limit=10")

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_manufacturer_search_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot search manufacturers"""
        response = client.get(
            "/api/wizard/manufacturers/search?query=TI&limit=10",
            headers=user_auth_headers,
        )

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_manufacturer_search_with_admin_auth(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test manufacturer search with admin authentication"""
        # Seed test manufacturers
        from backend.src.models.component import Component

        # Create components with different manufacturers
        components = [
            Component(name="Component 1", manufacturer="Texas Instruments"),
            Component(name="Component 2", manufacturer="TI Automotive"),
            Component(name="Component 3", manufacturer="Microchip Technology"),
            Component(name="Component 4", manufacturer="STMicroelectronics"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=TI&limit=10",
            headers=auth_headers,
        )

        # Debug output if fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Should return manufacturers matching "TI"
        # Each result should have ManufacturerSuggestion schema
        for suggestion in data:
            assert "id" in suggestion or "name" in suggestion  # id might be null for new
            assert "name" in suggestion
            assert "score" in suggestion
            assert isinstance(suggestion["score"], (int, float))

    def test_manufacturer_search_fuzzy_matching(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test fuzzy matching returns relevant results ranked by score"""
        from backend.src.models.component import Component

        # Seed manufacturers with varying similarity to "TI"
        components = [
            Component(name="Comp 1", manufacturer="Texas Instruments"),  # Exact match
            Component(name="Comp 2", manufacturer="TI Automotive"),  # Starts with TI
            Component(name="Comp 3", manufacturer="Microchip"),  # No match
            Component(name="Comp 4", manufacturer="STMicroelectronics"),  # Contains "ti"
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=TI&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return results ranked by score
        # Texas Instruments should have highest score
        assert len(data) > 0

        # Verify results are sorted by score descending
        scores = [s["score"] for s in data]
        assert scores == sorted(scores, reverse=True)

        # Texas Instruments should be first (highest score)
        top_result = data[0]
        assert "Texas Instruments" in top_result["name"] or "TI" in top_result["name"]

    def test_manufacturer_search_missing_query_param(
        self, client: TestClient, auth_headers
    ):
        """Test search without required query parameter"""
        response = client.get(
            "/api/wizard/manufacturers/search?limit=10",
            headers=auth_headers,
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_manufacturer_search_respects_limit(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that limit parameter is respected"""
        from backend.src.models.component import Component

        # Create many manufacturers
        components = [
            Component(name=f"Comp {i}", manufacturer=f"Manufacturer {i}")
            for i in range(20)
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=Manufacturer&limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return at most 5 results
        assert len(data) <= 5

    def test_manufacturer_search_empty_query(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test search with empty query string"""
        from backend.src.models.component import Component

        components = [
            Component(name="Comp 1", manufacturer="Texas Instruments"),
            Component(name="Comp 2", manufacturer="Microchip"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=&limit=10",
            headers=auth_headers,
        )

        # Empty query should either return validation error or empty results
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Empty query might return all manufacturers or none
            assert isinstance(data, list)

    def test_manufacturer_search_no_results(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test search with query that matches no manufacturers"""
        from backend.src.models.component import Component

        components = [
            Component(name="Comp 1", manufacturer="Texas Instruments"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=ZZZNOMATCH&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty list for no matches
        assert isinstance(data, list)
        assert len(data) == 0

    def test_manufacturer_search_deduplication(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that duplicate manufacturers are deduplicated in results"""
        from backend.src.models.component import Component

        # Create multiple components with same manufacturer
        components = [
            Component(name="Comp 1", manufacturer="Texas Instruments"),
            Component(name="Comp 2", manufacturer="Texas Instruments"),
            Component(name="Comp 3", manufacturer="Texas Instruments"),
            Component(name="Comp 4", manufacturer="TI Automotive"),
        ]
        db_session.add_all(components)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=Texas&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # "Texas Instruments" should appear only once
        manufacturer_names = [s["name"] for s in data]
        assert len(manufacturer_names) == len(set(manufacturer_names))  # No duplicates

    def test_manufacturer_search_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches ManufacturerSuggestion schema"""
        from backend.src.models.component import Component

        component = Component(name="Test", manufacturer="STMicroelectronics")
        db_session.add(component)
        db_session.commit()

        response = client.get(
            "/api/wizard/manufacturers/search?query=STM&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        suggestion = data[0]

        # Required fields
        assert "name" in suggestion
        assert "score" in suggestion
        assert suggestion["name"] == "STMicroelectronics"
        assert isinstance(suggestion["score"], (int, float))
        assert suggestion["score"] > 0

        # Optional id field (might be null for suggestions without explicit manufacturer table)
        # id present if using manufacturer table, absent if using distinct manufacturer strings
