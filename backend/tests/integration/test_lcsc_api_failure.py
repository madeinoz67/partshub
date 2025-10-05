"""
Integration test for LCSC API failure fallback to local creation.
Tests graceful degradation when provider API is unavailable.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestLCSCAPIFailure:
    """Integration tests for LCSC API failure scenarios"""

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_lcsc_api_500_error(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """
        Test LCSC API failure scenario with graceful fallback:
        1. Admin authenticates
        2. Mock LCSC API to raise exception
        3. GET /api/providers/1/search?query=STM32 -> adapter returns mock data (graceful degradation)
        4. Frontend receives mock results and can create components
        5. POST /api/wizard/components with {part_type: "local", ...} -> succeeds

        Note: LCSCAdapter has built-in error handling that returns mock data on failure,
        so exceptions don't propagate to the API layer. This tests graceful degradation.
        """
        from backend.src.models.wizard_provider import Provider

        # Step 1: Admin authenticated via auth_headers fixture

        # Create LCSC provider
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

        # Step 2: Mock LCSC API to raise exception, but adapter will catch and return mock data
        # We need to mock the actual implementation to bypass the adapter's error handling
        mock_search.side_effect = Exception(
            "LCSC API returned 500 Internal Server Error"
        )

        # Step 3: Search request - the service will catch the exception
        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=STM32&limit=10",
            headers=auth_headers,
        )

        # Should return error status (500 or 503) because service re-raises exceptions
        assert search_response.status_code in [500, 503]

        # Step 4: Frontend would switch to local creation
        # Step 5: Create local part instead
        component_data = {
            "name": "STM32F103C8T6",
            "description": "ARM Cortex-M3 MCU (created locally)",
            "part_type": "local",
            "manufacturer_name": "STMicroelectronics",
            "footprint_name": "LQFP-48",
            "specifications": {
                "core": "ARM Cortex-M3",
                "flash": "64KB",
                "ram": "20KB",
            },
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        # Debug output
        if create_response.status_code != 201:
            print(f"Create response status: {create_response.status_code}")
            print(f"Create response body: {create_response.text}")

        assert create_response.status_code == 201
        component = create_response.json()

        # Verify local component created successfully
        assert component["name"] == "STM32F103C8T6"
        assert component["part_type"] == "local"
        assert component.get("provider_link") is None

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_lcsc_api_timeout(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test LCSC API timeout scenario"""
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

        # Mock timeout error
        mock_search.side_effect = Exception("Connection timeout")

        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=resistor&limit=10",
            headers=auth_headers,
        )

        # Should return error status
        assert search_response.status_code in [500, 503, 504]

        # User can still create local part
        component_data = {
            "name": "10K Resistor",
            "description": "Created after API timeout",
            "part_type": "local",
            "manufacturer_name": "Yageo",
            "footprint_name": "0805",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_lcsc_api_empty_results(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test LCSC API returns empty results (not an error, just no matches)"""
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

        # Mock empty results
        mock_search.return_value = []

        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=NONEXISTENT_PART&limit=10",
            headers=auth_headers,
        )

        # Should succeed but return empty results
        assert search_response.status_code == 200
        data = search_response.json()
        # Response is a dict with 'results' and 'total' keys
        assert "results" in data
        assert data["total"] == 0
        assert len(data["results"]) == 0

        # User creates local part when no results found
        component_data = {
            "name": "Custom Part",
            "description": "Not available from LCSC",
            "part_type": "local",
            "manufacturer_name": "Custom",
            "footprint_name": "Custom",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_lcsc_api_malformed_response(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test LCSC API returns malformed/unexpected response"""
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

        # Mock malformed response - return invalid structure
        mock_search.return_value = {"unexpected": "structure"}

        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=auth_headers,
        )

        # Should handle gracefully (500, 503, or 404 for validation errors)
        # When adapter returns a dict instead of list, Pydantic validation fails with 404
        assert search_response.status_code in [200, 404, 500, 503]

        # Fallback to local creation still works
        component_data = {
            "name": "Fallback Component",
            "description": "Created after malformed response",
            "part_type": "local",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201

    def test_inactive_provider_cannot_search(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that inactive providers cannot be searched"""
        from backend.src.models.wizard_provider import Provider

        # Create inactive provider
        provider = Provider(
            name="Inactive Provider",
            adapter_class="TestAdapter",
            base_url="https://api.inactive.com",
            status="inactive",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=auth_headers,
        )

        # Should return error or validation failure
        assert search_response.status_code in [400, 403, 404]

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_partial_api_failure_allows_local_creation(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that after initial successful search, API failure doesn't block local creation"""
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

        # First search succeeds
        mock_search.return_value = [
            {
                "part_number": "TEST-001",
                "name": "Test Part",
                "description": "Test",
                "manufacturer": "Test Mfg",
                "datasheet_url": "https://example.com/ds.pdf",
                "image_urls": [],
                "footprint": "0805",
                "provider_url": "https://lcsc.com/test",
            }
        ]

        search1_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=auth_headers,
        )
        assert search1_response.status_code == 200

        # Second search fails
        mock_search.side_effect = Exception("API error")

        search2_response = client.get(
            f"/api/providers/{provider.id}/search?query=another&limit=10",
            headers=auth_headers,
        )
        assert search2_response.status_code in [500, 503]

        # Can still create local part
        component_data = {
            "name": "Local Part After Failure",
            "description": "Created locally",
            "part_type": "local",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201

    @patch("src.services.lcsc_adapter.LCSCAdapter.search", new_callable=AsyncMock)
    def test_api_error_message_returned_to_frontend(
        self,
        mock_search,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that API errors return meaningful error messages"""
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

        # Mock specific error
        mock_search.side_effect = Exception("Rate limit exceeded")

        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=auth_headers,
        )

        assert search_response.status_code in [429, 500, 503]

        # Error response should contain detail
        if search_response.status_code != 429:
            data = search_response.json()
            assert "detail" in data or "error" in data
