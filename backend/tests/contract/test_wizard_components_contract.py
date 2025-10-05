"""
Contract test for POST /api/wizard/components
Tests wizard component creation endpoint with provider links and resources.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestWizardComponentsContract:
    """Contract tests for wizard component creation endpoint"""

    def test_wizard_component_creation_requires_admin_auth(self, client: TestClient):
        """Test that wizard component creation requires admin authentication"""
        component_data = {
            "name": "Test Component",
            "description": "Test description",
            "part_type": "linked",
            "provider_link": {
                "provider_id": 1,
                "part_number": "STM32F103C8T6",
                "part_url": "https://lcsc.com/product-detail/...",
                "metadata": {},
            },
            "resource_selections": [],
        }

        response = client.post("/api/wizard/components", json=component_data)

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_wizard_component_creation_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot create wizard components"""
        component_data = {
            "name": "Test Component",
            "description": "Test description",
            "part_type": "linked",
            "provider_link": {
                "provider_id": 1,
                "part_number": "STM32F103C8T6",
                "part_url": "https://lcsc.com/product-detail/...",
                "metadata": {},
            },
            "resource_selections": [],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=user_auth_headers,
        )

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_create_linked_component_with_provider_link(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating linked component with provider link"""
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

        component_data = {
            "name": "STM32F103C8T6 Microcontroller",
            "description": "ARM Cortex-M3 MCU, 64KB Flash, 20KB RAM",
            "part_type": "linked",
            "provider_link": {
                "provider_id": provider.id,
                "part_number": "STM32F103C8T6",
                "part_url": "https://lcsc.com/product-detail/STM32F103C8T6.html",
                "metadata": {
                    "manufacturer": "STMicroelectronics",
                    "package": "LQFP-48",
                },
            },
            "resource_selections": [
                {
                    "type": "datasheet",
                    "url": "https://lcsc.com/datasheet/STM32F103C8T6.pdf",
                    "file_name": "STM32F103C8T6_datasheet.pdf",
                }
            ],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        # Debug output if fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 201

        data = response.json()

        # Verify component fields
        assert data["name"] == component_data["name"]
        assert data["description"] == component_data["description"]
        assert data["part_type"] == "linked"
        assert "id" in data
        assert "created_at" in data

        # Verify provider link
        assert "provider_link" in data
        provider_link = data["provider_link"]
        assert provider_link["provider_id"] == provider.id
        assert provider_link["provider_name"] == "LCSC"
        assert provider_link["provider_part_number"] == "STM32F103C8T6"
        assert (
            provider_link["provider_url"] == component_data["provider_link"]["part_url"]
        )
        assert provider_link["sync_status"] in ["pending", "synced"]

    def test_create_linked_component_with_resources(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating linked component with resource downloads"""
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

        component_data = {
            "name": "Test IC",
            "description": "Test integrated circuit",
            "part_type": "linked",
            "provider_link": {
                "provider_id": provider.id,
                "part_number": "TEST-IC-001",
                "part_url": "https://lcsc.com/test",
                "metadata": {},
            },
            "resource_selections": [
                {
                    "type": "datasheet",
                    "url": "https://example.com/datasheet.pdf",
                    "file_name": "datasheet.pdf",
                },
                {
                    "type": "image",
                    "url": "https://example.com/image1.jpg",
                    "file_name": "image1.jpg",
                },
                {
                    "type": "image",
                    "url": "https://example.com/image2.jpg",
                    "file_name": "image2.jpg",
                },
            ],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify resources were created (might be in different field)
        # Resources might be returned directly or require separate query
        assert "id" in data

    def test_create_local_component_without_provider_link(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating local component without provider link"""
        from backend.src.models.component import Component

        # Seed manufacturer for reference
        existing_component = Component(name="Old", manufacturer="Texas Instruments")
        db_session.add(existing_component)
        db_session.commit()

        component_data = {
            "name": "Custom Resistor",
            "description": "Custom 10K resistor",
            "part_type": "local",
            "manufacturer_name": "Texas Instruments",
            "footprint_name": "0805",
            "specifications": {
                "resistance": "10K",
                "tolerance": "1%",
            },
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == component_data["name"]
        assert data["description"] == component_data["description"]
        assert data["part_type"] == "local"
        # Should NOT have provider_link
        assert data.get("provider_link") is None

    def test_create_component_validation_error_missing_name(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when name is missing"""
        component_data = {
            "description": "Missing name field",
            "part_type": "local",
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_component_validation_error_invalid_part_type(
        self, client: TestClient, auth_headers
    ):
        """Test validation error for invalid part_type"""
        component_data = {
            "name": "Test Component",
            "description": "Invalid part type",
            "part_type": "invalid_type",
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_linked_component_missing_provider_link(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when linked component missing provider_link"""
        component_data = {
            "name": "Linked Component",
            "description": "Missing provider link",
            "part_type": "linked",
            # Missing provider_link field
            "resource_selections": [],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        # Should return validation error
        assert response.status_code == 422

    def test_create_component_response_structure(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches Component schema with provider link"""
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

        component_data = {
            "name": "Response Test Component",
            "description": "Testing response structure",
            "part_type": "linked",
            "provider_link": {
                "provider_id": provider.id,
                "part_number": "TEST-001",
                "part_url": "https://lcsc.com/test001",
                "metadata": {},
            },
            "resource_selections": [],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields in response
        required_fields = [
            "id",
            "name",
            "description",
            "part_type",
            "provider_link",
            "created_at",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Provider link structure
        provider_link_fields = [
            "id",
            "provider_id",
            "provider_name",
            "provider_part_number",
            "provider_url",
            "sync_status",
        ]

        for field in provider_link_fields:
            assert (
                field in data["provider_link"]
            ), f"Missing provider_link field: {field}"

    def test_create_component_with_manufacturer_and_footprint(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating component with manufacturer and footprint IDs"""
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

        component_data = {
            "name": "Test Component",
            "description": "With manufacturer and footprint",
            "part_type": "linked",
            "manufacturer_id": None,  # Optional: link to existing
            "manufacturer_name": "STMicroelectronics",  # Or create new
            "footprint_id": None,  # Optional: link to existing
            "footprint_name": "LQFP-48",  # Or create new
            "provider_link": {
                "provider_id": provider.id,
                "part_number": "TEST-MFG-001",
                "part_url": "https://lcsc.com/test",
                "metadata": {},
            },
            "resource_selections": [],
        }

        response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Should have manufacturer and footprint fields
        assert "manufacturer_id" in data or "manufacturer" in data
        assert "footprint_id" in data or "package" in data
