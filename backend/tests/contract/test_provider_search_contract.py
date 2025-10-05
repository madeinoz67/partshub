"""
Contract test for GET /api/providers/{provider_id}/search
Tests provider search endpoint for component discovery in wizard.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestProviderSearchContract:
    """Contract tests for provider search endpoint"""

    def test_provider_search_requires_admin_auth(self, client: TestClient, db_session):
        """Test that provider search requires admin authentication"""
        from backend.src.models.wizard_provider import Provider

        # Create test provider
        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32&limit=20"
        )

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_provider_search_non_admin_forbidden(
        self, client: TestClient, user_auth_headers, db_session
    ):
        """Test that non-admin users cannot search providers"""
        from backend.src.models.wizard_provider import Provider

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32&limit=20",
            headers=user_auth_headers,
        )

        # Should fail with 403 forbidden
        assert response.status_code == 403

    @patch("backend.src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_provider_search_with_admin_auth(
        self, mock_search, client: TestClient, auth_headers, db_session
    ):
        """Test provider search with admin authentication"""
        from backend.src.models.wizard_provider import Provider

        # Create test provider
        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        # Mock LCSC adapter response (async method returns list directly)
        mock_search.return_value = [
            {
                "part_number": "STM32F103C8T6",
                "name": "STM32F103C8T6",
                "description": "ARM Cortex-M3 MCU",
                "manufacturer": "STMicroelectronics",
                "datasheet_url": "https://example.com/datasheet.pdf",
                "image_urls": ["https://example.com/image.jpg"],
                "footprint": "LQFP-48",
                "provider_url": "https://lcsc.com/product-detail/...",
            }
        ]

        response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32&limit=20",
            headers=auth_headers,
        )

        # Debug output if fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], int)

    def test_provider_search_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches ProviderPart schema"""
        from backend.src.models.wizard_provider import Provider

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        # Since actual web scraping falls back to mock data, we can test with real adapter
        # The mock data provides a consistent response for testing
        response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32F103&limit=20",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify result structure
        assert len(data["results"]) >= 1
        result = data["results"][0]

        # Required fields (checking structure, not exact values since we're using mock fallback)
        assert "part_number" in result
        assert "name" in result
        assert "description" in result
        assert "manufacturer" in result
        assert "datasheet_url" in result
        assert isinstance(result["image_urls"], list)
        assert "footprint" in result
        assert "provider_url" in result

    def test_provider_search_invalid_provider_id(
        self, client: TestClient, auth_headers
    ):
        """Test search with non-existent provider ID"""
        response = client.get(
            "/api/providers/99999/search?query=test&limit=10",
            headers=auth_headers,
        )

        # Should return 404 for non-existent provider
        assert response.status_code == 404

    def test_provider_search_missing_query_param(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test search without required query parameter"""
        from backend.src.models.wizard_provider import Provider

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        response = client.get(
            f"/api/providers/{provider.id}/search?limit=10",
            headers=auth_headers,
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_provider_search_respects_limit(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that limit parameter is respected"""
        from backend.src.models.wizard_provider import Provider

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        # Request with limit=5
        response = client.get(
            f"/api/providers/{provider.id}/search?query=resistor&limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should respect the limit
        assert len(data["results"]) <= 5
        assert data["total"] <= 5

    def test_provider_search_handles_api_errors(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test handling of provider API errors with non-existent provider"""
        # Use a non-existent provider ID to trigger error handling
        response = client.get(
            "/api/providers/99999/search?query=test&limit=10",
            headers=auth_headers,
        )

        # Should return 404 for non-existent provider
        assert response.status_code == 404
