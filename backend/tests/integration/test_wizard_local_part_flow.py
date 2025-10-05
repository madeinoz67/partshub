"""
Integration test for local part creation with fuzzy manufacturer search.
Tests end-to-end workflow for creating local parts using autocomplete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestWizardLocalPartFlow:
    """Integration tests for local part creation workflow"""

    def test_local_part_creation_with_fuzzy_manufacturer_search(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """
        Test local part creation flow:
        1. Admin authenticates
        2. Seed manufacturers: "Texas Instruments", "Microchip Technology"
        3. GET /api/wizard/manufacturers/search?query=TI -> returns "Texas Instruments" with high score
        4. POST /api/wizard/components with {part_type: "local", manufacturer_name: ...} -> creates component
        5. Verify component created and linked to manufacturer
        """
        from backend.src.models.component import Component

        # Step 1: Admin already authenticated via auth_headers fixture

        # Step 2: Seed manufacturers via existing components
        existing_components = [
            Component(name="Existing 1", manufacturer="Texas Instruments"),
            Component(name="Existing 2", manufacturer="Microchip Technology"),
            Component(name="Existing 3", manufacturer="STMicroelectronics"),
        ]
        db_session.add_all(existing_components)
        db_session.commit()

        # Step 3: Search for manufacturer "Texas"
        mfg_search_response = client.get(
            "/api/wizard/manufacturers/search?query=Texas&limit=10",
            headers=auth_headers,
        )

        assert mfg_search_response.status_code == 200
        manufacturers = mfg_search_response.json()

        # Should return "Texas Instruments" with high score
        assert len(manufacturers) > 0
        top_manufacturer = manufacturers[0]
        assert "Texas Instruments" in top_manufacturer["name"]
        assert top_manufacturer["score"] > 0

        # Step 4: Create local part with manufacturer
        component_data = {
            "name": "Custom Voltage Regulator",
            "description": "TI voltage regulator for 5V rail",
            "part_type": "local",
            "manufacturer_name": "Texas Instruments",  # Using autocomplete result
            "footprint_name": "SOT-23",
            "specifications": {
                "voltage_in": "7-35V",
                "voltage_out": "5V",
                "current_max": "1.5A",
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
        created_component = create_response.json()

        # Step 5: Verify component created
        assert created_component["name"] == "Custom Voltage Regulator"
        assert created_component["description"] == "TI voltage regulator for 5V rail"
        assert created_component["part_type"] == "local"

        # Should NOT have provider_link
        assert created_component.get("provider_link") is None

        # Should have manufacturer (either ID or name)
        assert (
            "manufacturer" in created_component
            or "manufacturer_id" in created_component
        )

    def test_local_part_creation_with_new_manufacturer(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test creating local part with new manufacturer not in database"""
        from backend.src.models.component import Component

        # Seed existing manufacturers
        existing = Component(name="Old", manufacturer="Texas Instruments")
        db_session.add(existing)
        db_session.commit()

        # Create part with NEW manufacturer
        component_data = {
            "name": "Custom Sensor",
            "description": "Proprietary temperature sensor",
            "part_type": "local",
            "manufacturer_name": "Custom Electronics Inc",  # New manufacturer
            "footprint_name": "TO-92",
            "specifications": {
                "sensor_type": "temperature",
                "range": "-40C to 125C",
            },
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        component = create_response.json()

        assert component["name"] == "Custom Sensor"
        assert component["part_type"] == "local"

        # New manufacturer should be created and linked
        # (implementation-dependent: might be in component.manufacturer field)

    def test_local_part_creation_with_footprint_autocomplete(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test local part creation using footprint autocomplete"""
        from backend.src.models.component import Component

        # Seed existing footprints
        existing_components = [
            Component(name="IC1", package="SOIC-8"),
            Component(name="IC2", package="SOIC-14"),
            Component(name="IC3", package="SOIC-16"),
            Component(name="IC4", package="TSSOP-8"),
        ]
        db_session.add_all(existing_components)
        db_session.commit()

        # Search for footprint "SOIC"
        footprint_response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=auth_headers,
        )

        assert footprint_response.status_code == 200
        footprints = footprint_response.json()

        # Should return SOIC variants
        assert len(footprints) > 0
        soic_footprints = [f for f in footprints if "SOIC" in f["name"]]
        assert len(soic_footprints) >= 3

        # Create component with autocompleted footprint
        component_data = {
            "name": "Dual Op-Amp",
            "description": "General purpose op-amp",
            "part_type": "local",
            "manufacturer_name": "Texas Instruments",
            "footprint_name": "SOIC-8",  # From autocomplete
            "specifications": {
                "channels": 2,
                "voltage_supply": "±15V",
            },
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        component = create_response.json()
        assert component["name"] == "Dual Op-Amp"

    def test_local_part_creation_with_manufacturer_id(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test creating local part by linking to existing manufacturer ID"""
        from backend.src.models.component import Component

        # Create existing component with manufacturer
        existing = Component(
            name="Existing Component",
            manufacturer="STMicroelectronics",
        )
        db_session.add(existing)
        db_session.commit()
        db_session.refresh(existing)

        # If manufacturers are stored separately, we'd get the ID from a manufacturer table
        # For now, test passing manufacturer_name which should link or create
        component_data = {
            "name": "Another STM32 Board",
            "description": "Custom development board",
            "part_type": "local",
            "manufacturer_name": "STMicroelectronics",  # Should reuse existing
            "footprint_name": "Custom",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        component = create_response.json()
        assert component["name"] == "Another STM32 Board"

    def test_local_part_fuzzy_search_case_insensitive(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that fuzzy search is case-insensitive"""
        from backend.src.models.component import Component

        # Seed manufacturer with specific casing
        existing = Component(name="Comp", manufacturer="STMicroelectronics")
        db_session.add(existing)
        db_session.commit()

        # Search with different case
        mfg_response_lower = client.get(
            "/api/wizard/manufacturers/search?query=stmicro&limit=10",
            headers=auth_headers,
        )
        assert mfg_response_lower.status_code == 200
        results_lower = mfg_response_lower.json()
        assert len(results_lower) > 0
        assert any("STMicroelectronics" in m["name"] for m in results_lower)

        # Search with uppercase
        mfg_response_upper = client.get(
            "/api/wizard/manufacturers/search?query=STMICRO&limit=10",
            headers=auth_headers,
        )
        assert mfg_response_upper.status_code == 200
        results_upper = mfg_response_upper.json()
        assert len(results_upper) > 0

    def test_local_part_with_specifications(
        self,
        client: TestClient,
        auth_headers,
    ):
        """Test creating local part with custom specifications"""
        component_data = {
            "name": "Custom Resistor Array",
            "description": "8-pin resistor network",
            "part_type": "local",
            "manufacturer_name": "Bourns",
            "footprint_name": "SIP-8",
            "specifications": {
                "resistance": "10K",
                "tolerance": "1%",
                "pins": 8,
                "power_rating": "0.125W",
                "configuration": "isolated",
            },
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        component = create_response.json()

        # Verify specifications stored correctly
        assert component["name"] == "Custom Resistor Array"
        if "specifications" in component:
            assert component["specifications"]["resistance"] == "10K"
            assert component["specifications"]["pins"] == 8

    def test_local_part_minimal_fields(
        self,
        client: TestClient,
        auth_headers,
    ):
        """Test creating local part with minimal required fields"""
        component_data = {
            "name": "Minimal Local Part",
            "description": "Minimal test",
            "part_type": "local",
            # No manufacturer, no footprint, no specifications
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )

        # Should succeed with minimal fields
        assert create_response.status_code == 201
        component = create_response.json()
        assert component["name"] == "Minimal Local Part"
        assert component["part_type"] == "local"
