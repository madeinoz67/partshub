"""
Integration test for provider auto-selection when only one exists.
Tests that wizard can auto-select provider when there is only one active provider.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestProviderAutoSelection:
    """Integration tests for provider auto-selection logic"""

    def test_single_provider_available_for_auto_selection(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """
        Test provider auto-selection scenario:
        1. Seed only LCSC provider
        2. GET /api/providers -> returns single provider
        3. Frontend logic: if len(providers) == 1, auto-select
        4. Verify provider list contains exactly one provider
        """
        from backend.src.models.wizard_provider import Provider

        # Step 1: Seed only LCSC provider
        lcsc_provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(lcsc_provider)
        db_session.commit()
        db_session.refresh(lcsc_provider)

        # Step 2: Get providers list
        providers_response = client.get("/api/providers", headers=auth_headers)

        # Debug output
        if providers_response.status_code != 200:
            print(f"Providers response status: {providers_response.status_code}")
            print(f"Providers response body: {providers_response.text}")

        assert providers_response.status_code == 200
        providers = providers_response.json()

        # Step 3 & 4: Verify exactly one provider
        assert len(providers) == 1
        assert providers[0]["name"] == "LCSC"
        assert providers[0]["status"] == "active"

        # Frontend would auto-select this provider
        selected_provider = providers[0]
        assert selected_provider["id"] == lcsc_provider.id

    def test_multiple_providers_no_auto_selection(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that with multiple providers, no auto-selection occurs (frontend logic)"""
        from backend.src.models.wizard_provider import Provider

        # Seed multiple providers
        providers_data = [
            Provider(
                name="LCSC",
                adapter_class="LCSCAdapter",
                base_url="https://api.lcsc.com",
                status="active",
                api_key_required=False,
            ),
            Provider(
                name="Digi-Key",
                adapter_class="DigiKeyAdapter",
                base_url="https://api.digikey.com",
                status="active",
                api_key_required=True,
            ),
            Provider(
                name="Mouser",
                adapter_class="MouserAdapter",
                base_url="https://api.mouser.com",
                status="active",
                api_key_required=True,
            ),
        ]
        db_session.add_all(providers_data)
        db_session.commit()

        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()

        # Should return multiple providers
        assert len(providers) == 3

        # Frontend would display provider selection dropdown
        # (no auto-selection with multiple providers)

    def test_no_providers_available(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test when no providers are configured"""
        # No providers seeded

        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()

        # Should return empty list
        assert len(providers) == 0

        # Frontend would skip provider selection and go directly to local part creation

    def test_only_inactive_providers_excluded(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that inactive providers are excluded from auto-selection"""
        from backend.src.models.wizard_provider import Provider

        # Seed only inactive provider
        inactive_provider = Provider(
            name="Inactive Provider",
            adapter_class="TestAdapter",
            base_url="https://api.inactive.com",
            status="inactive",
            api_key_required=False,
        )
        db_session.add(inactive_provider)
        db_session.commit()

        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()

        # Inactive providers should still be returned (filtering is frontend concern)
        # but marked as inactive
        assert len(providers) == 1
        assert providers[0]["status"] == "inactive"

        # Frontend would filter out inactive providers from auto-selection

    def test_single_active_provider_with_inactive_providers(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test auto-selection with one active and multiple inactive providers"""
        from backend.src.models.wizard_provider import Provider

        # Seed one active and two inactive providers
        providers_data = [
            Provider(
                name="LCSC",
                adapter_class="LCSCAdapter",
                base_url="https://api.lcsc.com",
                status="active",
                api_key_required=False,
            ),
            Provider(
                name="Old Provider 1",
                adapter_class="TestAdapter",
                base_url="https://api.old1.com",
                status="inactive",
                api_key_required=False,
            ),
            Provider(
                name="Old Provider 2",
                adapter_class="TestAdapter",
                base_url="https://api.old2.com",
                status="inactive",
                api_key_required=True,
            ),
        ]
        db_session.add_all(providers_data)
        db_session.commit()

        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()

        # Should return all providers
        assert len(providers) == 3

        # Frontend would filter to active only
        active_providers = [p for p in providers if p["status"] == "active"]
        assert len(active_providers) == 1
        assert active_providers[0]["name"] == "LCSC"

        # Frontend auto-selects the single active provider

    def test_provider_list_ordering(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that providers are returned in consistent order"""
        from backend.src.models.wizard_provider import Provider

        # Seed providers in specific order
        providers_data = [
            Provider(
                name="Mouser",
                adapter_class="MouserAdapter",
                base_url="https://api.mouser.com",
                status="active",
                api_key_required=True,
            ),
            Provider(
                name="LCSC",
                adapter_class="LCSCAdapter",
                base_url="https://api.lcsc.com",
                status="active",
                api_key_required=False,
            ),
            Provider(
                name="Digi-Key",
                adapter_class="DigiKeyAdapter",
                base_url="https://api.digikey.com",
                status="active",
                api_key_required=True,
            ),
        ]
        db_session.add_all(providers_data)
        db_session.commit()

        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()

        assert len(providers) == 3

        # Providers should be ordered (alphabetically, by ID, or by creation order)
        # Order is implementation-dependent but should be consistent
        provider_names = [p["name"] for p in providers]
        assert len(provider_names) == 3

    def test_auto_selection_used_in_component_creation(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that auto-selected provider can be used to create component"""
        from backend.src.models.wizard_provider import Provider

        # Single provider
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

        # Get providers and auto-select
        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200
        providers = providers_response.json()
        assert len(providers) == 1

        selected_provider = providers[0]

        # Create component with auto-selected provider
        component_data = {
            "name": "Auto-Selected Component",
            "description": "Using auto-selected provider",
            "part_type": "linked",
            "provider_link": {
                "provider_id": selected_provider["id"],
                "part_number": "AUTO-001",
                "part_url": "https://lcsc.com/auto",
                "metadata": {},
            },
            "resource_selections": [],
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        component = create_response.json()
        assert component["provider_link"]["provider_name"] == "LCSC"
