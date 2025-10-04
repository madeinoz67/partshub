"""
Integration tests for Remove Stock acceptance scenarios from spec.md
Tests user scenarios (lines 66-70) with end-to-end workflows
"""

import pytest
from fastapi.testclient import TestClient
from backend.src.models import ComponentLocation, StockTransaction, TransactionType


@pytest.mark.integration
class TestRemoveStockScenarios:
    """Integration tests for Remove Stock acceptance scenarios"""

    def test_scenario_1_inline_form_with_location_quantity_display(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """
        Scenario 1: Given a component row is expanded and has stock in one or more locations,
        When user selects "Remove Stock" from the row expansion menu,
        Then system displays a simple form inline within the expanded row showing available
        locations with quantities
        """
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add initial stock
        add_stock_request = {
            "location_id": location_id,
            "quantity": 100,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Verify backend provides data for form display (GET component with locations)
        response = client.get(
            f"/api/v1/components/{component_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        component_data = response.json()

        # Verify stock is available for display in form
        assert component_data["quantity_on_hand"] >= 100

    def test_scenario_2_quantity_validation_against_available_stock(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """
        Scenario 2: Given remove stock form is open in the expanded row,
        When user selects a location and enters quantity to remove,
        Then system validates quantity against available stock
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add 50 units
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Test valid removal (within available stock)
        remove_valid = {
            "location_id": location_id,
            "quantity": 25,
            "comments": "Valid removal within stock"
        }
        response_valid = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_valid,
            headers=auth_headers
        )
        assert response_valid.status_code == 200
        assert response_valid.json()["quantity_removed"] == 25

        # Test removal exceeding available stock (auto-capped per FR-017)
        remove_exceed = {
            "location_id": location_id,
            "quantity": 100,  # More than remaining 25
            "comments": "Exceeds available stock"
        }
        response_exceed = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_exceed,
            headers=auth_headers
        )
        assert response_exceed.status_code == 200
        data = response_exceed.json()
        assert data["quantity_removed"] == 25  # Auto-capped
        assert data["capped"] is True

    def test_scenario_3_stock_reduction_and_total_update(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """
        Scenario 3: Given user enters valid quantity and optional comments,
        When user confirms removal,
        Then system reduces stock at that location and updates total quantity
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock to both locations
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_b_id, "quantity": 50},
            headers=auth_headers
        )

        # Remove stock from location A
        remove_request = {
            "location_id": location_a_id,
            "quantity": 30,
            "comments": "Used in assembly"
        }
        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_request,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Verify location stock reduced
        assert data["previous_quantity"] == 100
        assert data["new_quantity"] == 70
        assert data["quantity_removed"] == 30

        # Verify total stock updated
        assert data["total_stock"] == 120  # 70 + 50

        # Verify database state
        comp_location = db_session.query(ComponentLocation).filter(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == location_a_id
        ).first()
        assert comp_location.quantity_on_hand == 70

    def test_scenario_4_zero_quantity_cleanup(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """
        Scenario 4: Given user removes all stock from a location,
        When removal is confirmed,
        Then system removes the stock entry entirely
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 50},
            headers=auth_headers
        )

        # Verify ComponentLocation exists
        comp_location_before = db_session.query(ComponentLocation).filter(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == location_id
        ).first()
        assert comp_location_before is not None
        assert comp_location_before.quantity_on_hand == 50

        # Remove all stock
        remove_all_request = {
            "location_id": location_id,
            "quantity": 50,
            "comments": "Clearing location"
        }
        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_all_request,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response indicates location deletion
        assert data["quantity_removed"] == 50
        assert data["new_quantity"] == 0
        assert data["location_deleted"] is True

        # Verify ComponentLocation record was deleted
        db_session.expire_all()  # Clear session cache
        comp_location_after = db_session.query(ComponentLocation).filter(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == location_id
        ).first()
        assert comp_location_after is None

        # Verify transaction was still created (audit trail)
        transaction = db_session.query(StockTransaction).filter(
            StockTransaction.component_id == component_id,
            StockTransaction.transaction_type == TransactionType.REMOVE
        ).first()
        assert transaction is not None
        assert transaction.quantity_change == -50

    def test_scenario_5_multi_row_operations(
        self, client: TestClient, db_session, auth_headers
    ):
        """
        Scenario 5: Given multiple component rows have remove stock forms open,
        When user submits a form,
        Then system applies the removal only to the component associated with that specific row
        """
        # Create two components
        component_a_resp = client.post(
            "/api/v1/components",
            json={"name": "Component A", "quantity_on_hand": 0, "minimum_stock": 0},
            headers=auth_headers
        )
        component_a_id = component_a_resp.json()["id"]

        component_b_resp = client.post(
            "/api/v1/components",
            json={"name": "Component B", "quantity_on_hand": 0, "minimum_stock": 0},
            headers=auth_headers
        )
        component_b_id = component_b_resp.json()["id"]

        # Create locations
        location_1_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 1"},
            headers=auth_headers
        )
        location_1_id = location_1_resp.json()["id"]

        location_2_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 2"},
            headers=auth_headers
        )
        location_2_id = location_2_resp.json()["id"]

        # Add stock to both components
        client.post(
            f"/api/v1/components/{component_a_id}/stock/add",
            json={"location_id": location_1_id, "quantity": 100},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/components/{component_b_id}/stock/add",
            json={"location_id": location_2_id, "quantity": 200},
            headers=auth_headers
        )

        # Remove from Component A only
        response_a = client.post(
            f"/api/v1/components/{component_a_id}/stock/remove",
            json={"location_id": location_1_id, "quantity": 25},
            headers=auth_headers
        )
        assert response_a.status_code == 200
        assert response_a.json()["component_id"] == component_a_id
        assert response_a.json()["quantity_removed"] == 25

        # Remove from Component B only
        response_b = client.post(
            f"/api/v1/components/{component_b_id}/stock/remove",
            json={"location_id": location_2_id, "quantity": 50},
            headers=auth_headers
        )
        assert response_b.status_code == 200
        assert response_b.json()["component_id"] == component_b_id
        assert response_b.json()["quantity_removed"] == 50

        # Verify each component's stock was updated independently
        comp_a_location = db_session.query(ComponentLocation).filter(
            ComponentLocation.component_id == component_a_id
        ).first()
        assert comp_a_location.quantity_on_hand == 75  # 100 - 25

        comp_b_location = db_session.query(ComponentLocation).filter(
            ComponentLocation.component_id == component_b_id
        ).first()
        assert comp_b_location.quantity_on_hand == 150  # 200 - 50
