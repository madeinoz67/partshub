"""
Contract test for GET /api/providers/{provider_id}/search
Tests provider search endpoint for component discovery in wizard.
"""

from unittest.mock import patch

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

    @patch("backend.src.services.lcsc_service.LCSCService.search_parts")
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

        # Mock LCSC API response
        mock_search.return_value = {
            "results": [
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
            ],
            "total": 1,
        }

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

    @patch("backend.src.services.lcsc_service.LCSCService.search_parts")
    def test_provider_search_response_schema(
        self, mock_search, client: TestClient, auth_headers, db_session
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

        # Mock complete LCSC API response
        mock_search.return_value = {
            "results": [
                {
                    "part_number": "STM32F103C8T6",
                    "name": "STM32F103C8T6",
                    "description": "ARM Cortex-M3 MCU, 64KB Flash, 20KB RAM",
                    "manufacturer": "STMicroelectronics",
                    "datasheet_url": "https://lcsc.com/datasheet/STM32F103C8T6.pdf",
                    "image_urls": [
                        "https://lcsc.com/images/STM32F103C8T6_1.jpg",
                        "https://lcsc.com/images/STM32F103C8T6_2.jpg",
                    ],
                    "footprint": "LQFP-48",
                    "provider_url": "https://lcsc.com/product-detail/STM32F103C8T6.html",
                }
            ],
            "total": 1,
        }

        response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32F103&limit=20",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify result structure
        assert len(data["results"]) == 1
        result = data["results"][0]

        # Required fields
        assert result["part_number"] == "STM32F103C8T6"
        assert result["name"] == "STM32F103C8T6"
        assert result["description"] == "ARM Cortex-M3 MCU, 64KB Flash, 20KB RAM"
        assert result["manufacturer"] == "STMicroelectronics"
        assert result["datasheet_url"] == "https://lcsc.com/datasheet/STM32F103C8T6.pdf"
        assert isinstance(result["image_urls"], list)
        assert len(result["image_urls"]) == 2
        assert result["footprint"] == "LQFP-48"
        assert (
            result["provider_url"]
            == "https://lcsc.com/product-detail/STM32F103C8T6.html"
        )

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

    @patch("backend.src.services.lcsc_service.LCSCService.search_parts")
    def test_provider_search_respects_limit(
        self, mock_search, client: TestClient, auth_headers, db_session
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

        # Mock API response with multiple results
        mock_results = [
            {
                "part_number": f"PART-{i:03d}",
                "name": f"Part {i}",
                "description": f"Test part {i}",
                "manufacturer": "Test Mfg",
                "datasheet_url": f"https://example.com/ds{i}.pdf",
                "image_urls": [],
                "footprint": "0603",
                "provider_url": f"https://lcsc.com/part{i}",
            }
            for i in range(50)
        ]

        mock_search.return_value = {"results": mock_results, "total": 50}

        response = client.get(
            f"/api/providers/{provider.id}/search?query=resistor&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Service should respect limit (might be handled by LCSC service)
        # Total should reflect actual total, results should be limited
        assert data["total"] == 50
        assert len(data["results"]) <= 10

    @patch("backend.src.services.lcsc_service.LCSCService.search_parts")
    def test_provider_search_handles_api_errors(
        self, mock_search, client: TestClient, auth_headers, db_session
    ):
        """Test handling of provider API errors"""
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

        # Mock API error
        mock_search.side_effect = Exception("LCSC API unavailable")

        response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=auth_headers,
        )

        # Should return 503 service unavailable or 500 internal error
        assert response.status_code in [500, 503]
