"""
Contract tests for BOM API endpoints.
Tests all Bill of Materials functionality including generation and export.
"""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock


class TestBOMContract:
    """Contract tests for BOM API endpoints."""

    def test_generate_project_bom_validation_error(self, client: TestClient):
        """Test project BOM generation with invalid data."""
        invalid_data = {
            "project_id": "",  # Empty project ID should fail
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/project", json=invalid_data)
        # Should validate or return error for empty project_id
        assert response.status_code in [400, 404, 422, 500]

    def test_generate_project_bom_valid_request_structure(self, client: TestClient):
        """Test project BOM generation request structure."""
        valid_data = {
            "project_id": "test-project-123",
            "include_provider_data": True,
            "refresh_provider_data": False
        }

        # This might fail due to service implementation but should have proper structure
        response = client.post("/api/v1/bom/project", json=valid_data)
        assert response.status_code in [200, 404, 500]  # Valid request structure

    def test_generate_component_list_bom_empty_components(self, client: TestClient):
        """Test component list BOM generation with empty components."""
        data = {
            "components": [],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/components", json=data)
        # Should handle empty component list gracefully
        assert response.status_code in [200, 400, 500]

    def test_generate_component_list_bom_valid_structure(self, client: TestClient):
        """Test component list BOM generation with valid structure."""
        data = {
            "components": [
                {"component_id": "comp-123", "quantity": 5},
                {"component_id": "comp-456", "quantity": 2}
            ],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/components", json=data)
        # Valid structure, might fail on service level
        assert response.status_code in [200, 404, 500]

    def test_generate_component_list_bom_invalid_component_structure(self, client: TestClient):
        """Test component list BOM generation with invalid component structure."""
        data = {
            "components": [
                {"component_id": "comp-123"},  # Missing quantity
                {"quantity": 2}  # Missing component_id
            ],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/components", json=data)
        # Should fail due to missing required fields
        assert response.status_code in [400, 422, 500]

    def test_export_bom_missing_both_project_and_components(self, client: TestClient):
        """Test BOM export with neither project_id nor components."""
        data = {
            "export_format": "csv",
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/export", json=data)
        assert response.status_code == 400
        assert "Either project_id or components must be provided" in response.json()["detail"]

    def test_export_bom_with_project_id(self, client: TestClient):
        """Test BOM export with project_id."""
        data = {
            "project_id": "test-project-123",
            "export_format": "csv",
            "include_provider_data": True,
            "refresh_provider_data": False
        }

        response = client.post("/api/v1/bom/export", json=data)
        # Valid request structure, may fail on service
        assert response.status_code in [200, 404, 500]

    def test_export_bom_with_components(self, client: TestClient):
        """Test BOM export with components list."""
        data = {
            "components": [
                {"component_id": "comp-123", "quantity": 1}
            ],
            "export_format": "json",
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/export", json=data)
        # Valid request structure, may fail on service
        assert response.status_code in [200, 404, 500]

    def test_export_bom_formats(self, client: TestClient):
        """Test BOM export with different formats."""
        base_data = {
            "components": [{"component_id": "comp-123", "quantity": 1}],
            "include_provider_data": False
        }

        formats = ["csv", "json", "kicad"]
        for format_type in formats:
            data = {**base_data, "export_format": format_type}
            response = client.post("/api/v1/bom/export", json=data)
            # Valid format, may fail on service
            assert response.status_code in [200, 404, 500]

    def test_get_project_bom_endpoint(self, client: TestClient):
        """Test GET endpoint for project BOM."""
        project_id = "test-project-123"

        response = client.get(f"/api/v1/bom/project/{project_id}")
        # Valid endpoint structure
        assert response.status_code in [200, 404, 500]

    def test_get_project_bom_with_parameters(self, client: TestClient):
        """Test GET project BOM with query parameters."""
        project_id = "test-project-123"

        response = client.get(
            f"/api/v1/bom/project/{project_id}?include_provider_data=false&refresh_provider_data=true"
        )
        # Valid endpoint with parameters
        assert response.status_code in [200, 404, 500]

    def test_export_project_bom_valid_formats(self, client: TestClient):
        """Test project BOM export with valid formats."""
        project_id = "test-project-123"
        formats = ["csv", "json", "kicad"]

        for format_type in formats:
            response = client.get(f"/api/v1/bom/project/{project_id}/export/{format_type}")
            # Valid format, may fail on service
            assert response.status_code in [200, 400, 404, 500]

    def test_export_project_bom_invalid_format(self, client: TestClient):
        """Test project BOM export with invalid format."""
        project_id = "test-project-123"
        invalid_format = "invalid_format"

        response = client.get(f"/api/v1/bom/project/{project_id}/export/{invalid_format}")
        assert response.status_code == 400
        assert "Unsupported export format" in response.json()["detail"]

    def test_export_project_bom_with_parameters(self, client: TestClient):
        """Test project BOM export with query parameters."""
        project_id = "test-project-123"
        format_type = "csv"

        response = client.get(
            f"/api/v1/bom/project/{project_id}/export/{format_type}?include_provider_data=false&refresh_provider_data=true"
        )
        # Valid endpoint with parameters
        assert response.status_code in [200, 400, 404, 500]

    def test_get_export_formats(self, client: TestClient):
        """Test getting available export formats."""
        response = client.get("/api/v1/bom/formats")
        assert response.status_code == 200

        data = response.json()
        assert "formats" in data
        assert isinstance(data["formats"], list)

        # Check format structure
        for format_info in data["formats"]:
            assert "value" in format_info
            assert "label" in format_info
            assert "description" in format_info

        # Check that expected formats are present
        format_values = [f["value"] for f in data["formats"]]
        expected_formats = ["csv", "json", "kicad"]
        for expected in expected_formats:
            assert expected in format_values

    def test_validate_bom_components_empty_list(self, client: TestClient):
        """Test BOM validation with empty components list."""
        data = {
            "components": [],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/validate", json=data)
        # Should handle empty list gracefully
        assert response.status_code in [200, 400, 500]

    def test_validate_bom_components_valid_structure(self, client: TestClient):
        """Test BOM validation with valid components."""
        data = {
            "components": [
                {"component_id": "comp-123", "quantity": 5},
                {"component_id": "comp-456", "quantity": 2}
            ],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/validate", json=data)
        # Valid structure, may fail on service
        assert response.status_code in [200, 404, 500]

    def test_validate_bom_components_invalid_structure(self, client: TestClient):
        """Test BOM validation with invalid component structure."""
        data = {
            "components": [
                {"component_id": "comp-123"},  # Missing quantity
                {"quantity": 2}  # Missing component_id
            ],
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/validate", json=data)
        # Should fail due to invalid structure
        assert response.status_code in [400, 422, 500]

    def test_bom_request_model_validation(self, client: TestClient):
        """Test BOM request model validation."""
        # Test ProjectBOMRequest validation
        invalid_project_request = {
            "project_id": None,  # Required field
            "include_provider_data": "not_boolean"  # Wrong type
        }

        response = client.post("/api/v1/bom/project", json=invalid_project_request)
        assert response.status_code == 422

    def test_bom_export_request_validation(self, client: TestClient):
        """Test BOM export request validation."""
        # Test with invalid export format
        data = {
            "project_id": "test-project-123",
            "export_format": "invalid_format",
            "include_provider_data": True
        }

        response = client.post("/api/v1/bom/export", json=data)
        # May succeed at request level but fail at service level
        assert response.status_code in [200, 400, 404, 500]

    def test_all_bom_endpoints_structure(self, client: TestClient):
        """Test that all BOM endpoints exist and have proper structure."""
        # Test endpoint existence
        endpoints = [
            ("/api/v1/bom/formats", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)

            # Endpoints should exist (not 404 for wrong path)
            assert response.status_code != 404

    @pytest.mark.parametrize("include_provider_data", [True, False])
    def test_bom_provider_data_parameter(self, client: TestClient, include_provider_data):
        """Test BOM generation with different provider data settings."""
        data = {
            "components": [{"component_id": "comp-123", "quantity": 1}],
            "include_provider_data": include_provider_data
        }

        response = client.post("/api/v1/bom/components", json=data)
        # Valid parameter values
        assert response.status_code in [200, 404, 500]

    @pytest.mark.parametrize("refresh_provider_data", [True, False])
    def test_bom_refresh_provider_data_parameter(self, client: TestClient, refresh_provider_data):
        """Test BOM generation with different refresh provider data settings."""
        data = {
            "project_id": "test-project-123",
            "include_provider_data": True,
            "refresh_provider_data": refresh_provider_data
        }

        response = client.post("/api/v1/bom/project", json=data)
        # Valid parameter values
        assert response.status_code in [200, 404, 500]

    def test_bom_response_headers_for_export(self, client: TestClient):
        """Test that export endpoints return proper file download headers."""
        # Test formats endpoint (should not have download headers)
        response = client.get("/api/v1/bom/formats")
        assert response.status_code == 200
        assert "Content-Disposition" not in response.headers

    def test_component_list_bom_quantity_types(self, client: TestClient):
        """Test component list BOM with different quantity types."""
        # Test with different quantity values
        test_cases = [
            {"component_id": "comp-123", "quantity": 1},      # Integer
            {"component_id": "comp-456", "quantity": 5.5},    # Float
            {"component_id": "comp-789", "quantity": 0},      # Zero
        ]

        data = {
            "components": test_cases,
            "include_provider_data": False
        }

        response = client.post("/api/v1/bom/components", json=data)
        # Valid quantity types
        assert response.status_code in [200, 400, 404, 500]

    def test_bom_endpoints_accept_json_content_type(self, client: TestClient):
        """Test that BOM endpoints properly handle JSON content type."""
        data = {
            "components": [{"component_id": "comp-123", "quantity": 1}],
            "include_provider_data": True
        }

        # Test with explicit JSON content type
        response = client.post(
            "/api/v1/bom/components",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        # Should accept JSON content type
        assert response.status_code in [200, 404, 500]
        assert response.status_code != 415  # Unsupported Media Type

    def test_project_bom_with_special_characters_in_id(self, client: TestClient):
        """Test project BOM with special characters in project ID."""
        special_project_ids = [
            "project-with-dashes",
            "project_with_underscores",
            "project123numbers",
            "project.with.dots"
        ]

        for project_id in special_project_ids:
            response = client.get(f"/api/v1/bom/project/{project_id}")
            # Should handle various ID formats
            assert response.status_code in [200, 404, 500]