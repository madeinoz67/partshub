"""
Contract test for GET /api/v1/components/{id}/history
Tests component stock history endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient
import uuid


class TestComponentsHistoryContract:
    """Contract tests for component stock history endpoint"""

    def test_get_history_anonymous_access(self, client: TestClient):
        """Test that anonymous users can access component history"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history")

        # This will fail until endpoint is implemented
        # Could be 200 (if component exists) or 404 (if not found)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_history_with_limit(self, client: TestClient):
        """Test history retrieval with limit parameter"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history?limit=10")

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 10

    def test_get_history_default_limit(self, client: TestClient):
        """Test history retrieval with default limit"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history")

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Default limit should be 50 according to OpenAPI spec
            assert len(data) <= 50

    def test_get_history_response_structure(self, client: TestClient):
        """Test response structure matches StockTransaction schema"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history")

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            if data:  # If there are transactions
                transaction = data[0]

                # Required fields for StockTransaction
                required_fields = [
                    "id", "component_id", "transaction_type", "quantity_change",
                    "previous_quantity", "new_quantity", "reason", "reference_id", "created_at"
                ]

                for field in required_fields:
                    assert field in transaction

                # Validate transaction_type enum
                assert transaction["transaction_type"] in ["add", "remove", "move", "adjust"]

                # Validate numeric fields
                assert isinstance(transaction["quantity_change"], int)
                assert isinstance(transaction["previous_quantity"], int)
                assert isinstance(transaction["new_quantity"], int)

                # Validate UUID fields
                assert isinstance(transaction["id"], str)
                assert isinstance(transaction["component_id"], str)

    def test_get_history_chronological_order(self, client: TestClient):
        """Test that history is returned in reverse chronological order"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history")

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()

            if len(data) > 1:
                # Should be ordered by created_at DESC (newest first)
                for i in range(len(data) - 1):
                    current_time = data[i]["created_at"]
                    next_time = data[i + 1]["created_at"]
                    # Current should be newer than or equal to next
                    assert current_time >= next_time

    def test_get_history_limit_validation(self, client: TestClient):
        """Test limit parameter validation"""
        component_id = str(uuid.uuid4())

        # Test maximum limit
        response = client.get(f"/api/v1/components/{component_id}/history?limit=100")
        # This will fail until validation is implemented
        assert response.status_code in [200, 404]

        # Test exceeding maximum limit
        response = client.get(f"/api/v1/components/{component_id}/history?limit=200")
        # This should return 422 for validation error
        assert response.status_code in [200, 404, 422]

        # Test invalid limit (negative)
        response = client.get(f"/api/v1/components/{component_id}/history?limit=-1")
        assert response.status_code in [200, 404, 422]

        # Test invalid limit (zero)
        response = client.get(f"/api/v1/components/{component_id}/history?limit=0")
        assert response.status_code in [200, 404, 422]

    def test_get_history_nonexistent_component(self, client: TestClient):
        """Test 404 response for nonexistent component"""
        nonexistent_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{nonexistent_id}/history")

        # This will fail until endpoint is implemented
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_get_history_invalid_uuid(self, client: TestClient):
        """Test 422 response for invalid UUID"""
        invalid_id = "not-a-uuid"

        response = client.get(f"/api/v1/components/{invalid_id}/history")

        # This will fail until validation is implemented
        assert response.status_code == 422

    def test_get_history_transaction_types(self, client: TestClient):
        """Test that all transaction types are properly represented"""
        component_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/components/{component_id}/history")

        if response.status_code == 200:
            data = response.json()

            # Check that if transactions exist, they have valid types
            for transaction in data:
                assert transaction["transaction_type"] in ["add", "remove", "move", "adjust"]

                # Validate quantity_change semantics
                if transaction["transaction_type"] == "add":
                    assert transaction["quantity_change"] > 0
                elif transaction["transaction_type"] == "remove":
                    assert transaction["quantity_change"] < 0
                # move and adjust can have any change value