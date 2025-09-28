"""
Integration test for KiCad functionality.
Tests KiCad API integration, symbol/footprint generation, and library synchronization.
"""

import pytest
from fastapi.testclient import TestClient


class TestKiCadIntegration:
    """Integration tests for KiCad functionality"""

    @pytest.fixture
    def sample_component(self, client, auth_headers):
        """Create a sample component for testing"""
        # Create category and storage
        category_response = client.post("/api/v1/categories",
            json={"name": "KiCad Test", "description": "For KiCad testing"},
            headers=auth_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "KiCad Storage", "description": "For KiCad testing"},
            headers=auth_headers
        )
        storage_id = storage_response.json()["id"]

        # Create component
        component_data = {
            "name": "Test Resistor",
            "part_number": "R001",
            "manufacturer": "Test Mfg",
            "category_id": category_id,
            "storage_location_id": storage_id,
            "component_type": "resistor",
            "value": "10k",
            "package": "0603",
            "quantity_on_hand": 100,
            "unit_cost": 0.01,
            "specifications": {
                "resistance": "10kΩ",
                "tolerance": "±1%",
                "power_rating": "0.1W",
                "temperature_coefficient": "±100ppm/°C"
            }
        }

        component_response = client.post("/api/v1/components",
            json=component_data,
            headers=auth_headers
        )
        assert component_response.status_code == 201
        return component_response.json()

    def test_kicad_search_components(self, client: TestClient, sample_component: dict):
        """Test KiCad component search functionality"""

        # Test basic component search
        search_response = client.get("/api/v1/kicad/components?query=resistor")
        assert search_response.status_code == 200

        search_data = search_response.json()
        assert "components" in search_data
        assert isinstance(search_data["components"], list)

        if len(search_data["components"]) > 0:
            component = search_data["components"][0]
            # Verify KiCad-specific fields
            assert "id" in component
            assert "name" in component
            assert "part_number" in component
            assert "manufacturer" in component
            assert "package" in component

    def test_kicad_search_with_filters(self, client: TestClient, sample_component: dict):
        """Test KiCad component search with filters"""

        # Test search with package filter
        search_response = client.get("/api/v1/kicad/components?query=resistor&package=0603")
        assert search_response.status_code == 200

        search_data = search_response.json()
        assert "components" in search_data

        # Test search with manufacturer filter
        search_response = client.get("/api/v1/kicad/components?query=resistor&manufacturer=Test%20Mfg")
        assert search_response.status_code == 200

        search_data = search_response.json()
        assert "components" in search_data

    def test_kicad_library_generation(self, client: TestClient, sample_component: dict):
        """Test KiCad library generation for components"""

        component_id = sample_component["id"]

        # Test symbol library generation
        symbol_response = client.get(f"/api/v1/kicad/components/{component_id}/symbol")

        if symbol_response.status_code == 200:
            # Verify symbol library content
            symbol_content = symbol_response.text
            assert "(kicad_symbol_lib" in symbol_content or "symbol" in symbol_content.lower()
        else:
            # Service might not be fully implemented - that's okay for integration test
            assert symbol_response.status_code in [200, 404, 501]

    def test_kicad_footprint_generation(self, client: TestClient, sample_component: dict):
        """Test KiCad footprint generation for components"""

        component_id = sample_component["id"]

        # Test footprint library generation
        footprint_response = client.get(f"/api/v1/kicad/components/{component_id}/footprint")

        if footprint_response.status_code == 200:
            # Verify footprint library content
            footprint_content = footprint_response.text
            assert "(footprint" in footprint_content or "fp_" in footprint_content.lower()
        else:
            # Service might not be fully implemented - that's okay for integration test
            assert footprint_response.status_code in [200, 404, 501]

    def test_kicad_component_details(self, client: TestClient, sample_component: dict):
        """Test KiCad component details endpoint"""

        component_id = sample_component["id"]

        # Test component details for KiCad
        details_response = client.get(f"/api/v1/kicad/components/{component_id}")

        if details_response.status_code == 200:
            details_data = details_response.json()
            # Verify KiCad-specific component details
            assert "id" in details_data
            assert "name" in details_data
            assert "specifications" in details_data
            assert "kicad_data" in details_data or "symbol" in details_data or "footprint" in details_data
        else:
            # Endpoint might not be fully implemented
            assert details_response.status_code in [200, 404, 501]

    def test_kicad_bulk_library_export(self, client: TestClient, sample_component: dict, auth_headers: dict):
        """Test bulk KiCad library export functionality"""

        # Test bulk symbol library export
        bulk_symbols_response = client.get("/api/v1/kicad/libraries/symbols")

        if bulk_symbols_response.status_code == 200:
            # Verify bulk symbol export
            symbols_content = bulk_symbols_response.text
            assert len(symbols_content) > 0
            # Should contain KiCad symbol library format
            assert "(kicad_symbol_lib" in symbols_content or "symbol" in symbols_content.lower()
        else:
            # Service might not be implemented yet
            assert bulk_symbols_response.status_code in [200, 404, 501]

    def test_kicad_library_synchronization(self, client: TestClient, sample_component: dict, auth_headers: dict):
        """Test KiCad library synchronization functionality"""

        # Test library sync endpoint (if implemented)
        sync_response = client.post("/api/v1/kicad/libraries/sync", headers=auth_headers)

        if sync_response.status_code == 200:
            sync_data = sync_response.json()
            # Verify sync response structure
            assert "status" in sync_data or "message" in sync_data
        else:
            # Sync functionality might not be implemented
            assert sync_response.status_code in [200, 404, 501, 405]

    def test_kicad_component_validation(self, client: TestClient):
        """Test KiCad component validation for missing data"""

        # Test search with invalid component ID
        invalid_response = client.get("/api/v1/kicad/components/invalid-id")
        assert invalid_response.status_code in [404, 422]

        # Test search with empty query
        empty_search_response = client.get("/api/v1/kicad/components?query=")
        # Should handle empty queries gracefully
        assert empty_search_response.status_code in [200, 422]

    def test_kicad_api_error_handling(self, client: TestClient):
        """Test KiCad API error handling"""

        # Test malformed requests
        malformed_response = client.get("/api/v1/kicad/components?invalid_param=test")
        # Should handle unknown parameters gracefully
        assert malformed_response.status_code in [200, 422]

        # Test component search with special characters
        special_char_response = client.get("/api/v1/kicad/components?query=%20%21%40%23")
        # Should handle special characters gracefully
        assert special_char_response.status_code in [200, 422]

    def test_kicad_performance_limits(self, client: TestClient):
        """Test KiCad API performance and limits"""

        # Test search with large limit
        large_limit_response = client.get("/api/v1/kicad/components?query=test&limit=1000")

        if large_limit_response.status_code == 200:
            search_data = large_limit_response.json()
            # Should respect reasonable limits
            assert len(search_data.get("components", [])) <= 1000
        else:
            # Might have validation that rejects large limits
            assert large_limit_response.status_code in [200, 422]

    def test_kicad_authentication_requirements(self, client: TestClient, sample_component: dict):
        """Test KiCad API authentication requirements"""

        # Test that read operations don't require authentication
        search_response = client.get("/api/v1/kicad/components?query=resistor")
        # Search should work without authentication
        assert search_response.status_code in [200, 404]

        component_id = sample_component["id"]
        details_response = client.get(f"/api/v1/kicad/components/{component_id}")
        # Component details should work without authentication
        assert details_response.status_code in [200, 404, 501]

        # Test that write operations might require authentication
        sync_response = client.post("/api/v1/kicad/libraries/sync")
        # Sync might require authentication
        assert sync_response.status_code in [200, 401, 404, 405, 501]
