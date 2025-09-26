"""
Contract test for POST /api/v1/components
Tests component creation endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


class TestComponentsCreateContract:
    """Contract tests for component creation endpoint"""

    def test_create_component_requires_auth(self, client: TestClient, sample_component_data):
        """Test that component creation requires authentication"""
        response = client.post("/api/v1/components", json=sample_component_data)

        # This should fail with 401 until auth is implemented
        assert response.status_code == 401

    def test_create_component_with_jwt_token(self, client: TestClient, sample_component_data):
        """Test component creation with JWT token"""
        # Mock JWT token (will fail until auth is implemented)
        headers = {"Authorization": "Bearer mock_jwt_token"}
        response = client.post("/api/v1/components", json=sample_component_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == sample_component_data["name"]
        assert data["part_number"] == sample_component_data["part_number"]
        assert data["manufacturer"] == sample_component_data["manufacturer"]
        assert "id" in data
        assert "created_at" in data

    def test_create_component_with_api_key(self, client: TestClient, sample_component_data):
        """Test component creation with API key"""
        headers = {"X-API-Key": "mock_api_key"}
        response = client.post("/api/v1/components", json=sample_component_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

    def test_create_component_validation_errors(self, client: TestClient):
        """Test validation errors for invalid component data"""
        headers = {"Authorization": "Bearer mock_jwt_token"}

        # Missing required fields
        invalid_data = {"name": "Test Component"}
        response = client.post("/api/v1/components", json=invalid_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_create_component_with_negative_quantity(self, client: TestClient, sample_component_data):
        """Test that negative quantities are rejected"""
        headers = {"Authorization": "Bearer mock_jwt_token"}

        invalid_data = sample_component_data.copy()
        invalid_data["quantity_on_hand"] = -10

        response = client.post("/api/v1/components", json=invalid_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code == 422

    def test_create_component_response_structure(self, client: TestClient, sample_component_data):
        """Test response structure matches OpenAPI spec"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        response = client.post("/api/v1/components", json=sample_component_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

        data = response.json()

        # Required fields in response
        required_fields = [
            "id", "name", "part_number", "manufacturer", "category",
            "storage_location", "component_type", "value", "package",
            "quantity_on_hand", "quantity_ordered", "minimum_stock",
            "average_purchase_price", "total_purchase_value", "notes",
            "tags", "attachments", "created_at", "updated_at"
        ]

        for field in required_fields:
            assert field in data

    def test_create_component_with_json_specifications(self, client: TestClient):
        """Test component creation with JSON specifications field"""
        headers = {"Authorization": "Bearer mock_jwt_token"}

        component_data = {
            "name": "STM32F103C8T6 Microcontroller",
            "part_number": "STM32F103C8T6",
            "manufacturer": "STMicroelectronics",
            "category_id": "mock_uuid",
            "storage_location_id": "mock_uuid",
            "component_type": "microcontroller",
            "value": "32-bit ARM Cortex-M3",
            "package": "LQFP-48",
            "specifications": {
                "voltage_supply": "3.3V",
                "current_consumption": "15mA",
                "flash_memory": "64KB",
                "ram": "20KB",
                "frequency": "72MHz",
                "io_pins": 37,
                "interfaces": ["SPI", "I2C", "UART", "CAN"]
            },
            "quantity_on_hand": 5,
            "minimum_stock": 2
        }

        response = client.post("/api/v1/components", json=component_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

        data = response.json()
        assert data["specifications"] == component_data["specifications"]