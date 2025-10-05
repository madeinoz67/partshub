"""
Integration tests for Add Stock acceptance scenarios from spec.md
Tests user scenarios (lines 58-63) with end-to-end workflows
"""

import pytest
from fastapi.testclient import TestClient

from backend.src.models import (
    ComponentLocation,
    StockTransaction,
)


@pytest.mark.integration
class TestAddStockScenarios:
    """Integration tests for Add Stock acceptance scenarios"""

    def test_scenario_1_inline_form_display_with_quantity_pricing_options(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 1: Given a component row is expanded, When user selects "Add Stock"
        from the row expansion menu, Then system displays a multi-step form inline
        within the expanded row with quantity/pricing and storage location options
        """
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        assert component_resp.status_code == 201
        component_id = component_resp.json()["id"]

        # This scenario tests UI behavior (form display)
        # For backend API, we verify the endpoint exists and accepts valid data
        # The actual form is handled by frontend

        # Verify GET endpoint for component stock locations (for populating form)
        response = client.get(
            f"/api/v1/components/{component_id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify component data is accessible for inline form
        component_data = response.json()
        assert component_data["id"] == component_id
        assert "quantity_on_hand" in component_data

    def test_scenario_2_manual_entry_with_pricing_calculation(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Scenario 2: Given user is on "Enter manually" tab in the inline form,
        When user enters quantity and pricing (per component or entire lot),
        Then system calculates and displays total lot price
        """
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Test per-unit pricing (backend should calculate total)
        add_stock_per_unit = {
            "location_id": location_id,
            "quantity": 100,
            "price_per_unit": 0.50,
            "comments": "Manual entry with per-unit pricing",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_per_unit,
            headers=auth_headers,
        )
        assert response.status_code == 200
        # Backend should accept and store pricing data

        # Test total lot pricing (backend should calculate per-unit)
        add_stock_total = {
            "location_id": location_id,
            "quantity": 50,
            "total_price": 37.50,
            "comments": "Manual entry with total lot pricing",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_total,
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify stock transactions were created with pricing
        transactions = (
            db_session.query(StockTransaction)
            .filter(StockTransaction.component_id == component_id)
            .all()
        )
        assert len(transactions) >= 2

    def test_scenario_3_location_selection_existing_or_new(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 3: Given user completes quantity/pricing step,
        When user selects or creates a storage location,
        Then system adds stock entry with all provided information
        """
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create existing location
        location_resp = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "Existing Location",
                "description": "Already exists",
                "type": "drawer",
            },
            headers=auth_headers,
        )
        existing_location_id = location_resp.json()["id"]

        # Add stock to existing location
        add_stock_request = {
            "location_id": existing_location_id,
            "quantity": 100,
            "price_per_unit": 0.25,
            "lot_id": "LOT-001",
            "comments": "Added to existing location",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify ComponentLocation was created
        comp_location = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == existing_location_id,
            )
            .first()
        )
        assert comp_location is not None
        assert comp_location.quantity_on_hand == 100

        # Create new location on-the-fly (for user workflow: select "Create new location")
        new_location_resp = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "New Location Created During Add Stock",
                "description": "New",
                "type": "drawer",
            },
            headers=auth_headers,
        )
        new_location_id = new_location_resp.json()["id"]

        # Add stock to newly created location
        add_stock_new = {
            "location_id": new_location_id,
            "quantity": 50,
            "comments": "Stock added to new location",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_new,
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify stock was added to new location
        comp_location_new = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == new_location_id,
            )
            .first()
        )
        assert comp_location_new is not None
        assert comp_location_new.quantity_on_hand == 50

    def test_scenario_4_order_receiving_with_prefilled_data(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Scenario 4: Given user is on "Receive against an order" tab,
        When user selects an order,
        Then system pre-fills quantity and pricing from order details
        """
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Simulate receiving against an order (pre-filled data from order system)
        add_stock_order = {
            "location_id": location_id,
            "quantity": 200,
            "total_price": 125.00,
            "reference_id": "PO-2025-12345",
            "reference_type": "purchase_order",
            "lot_id": "VENDOR-LOT-789",
            "comments": "Received shipment against PO-2025-12345",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_order,
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify transaction has reference data
        transaction = (
            db_session.query(StockTransaction)
            .filter(
                StockTransaction.component_id == component_id,
                StockTransaction.reference_id == "PO-2025-12345",
            )
            .first()
        )
        assert transaction is not None
        assert transaction.reference_type == "purchase_order"

    def test_scenario_5_stock_quantity_updates_across_all_locations(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 5: Given user completes add stock workflow,
        When stock is successfully added,
        Then system updates component's total quantity and displays success confirmation
        """
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create multiple locations
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A", "type": "drawer"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B", "type": "drawer"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock to location A
        response_a = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers,
        )
        assert response_a.status_code == 200
        data_a = response_a.json()
        assert data_a["quantity_added"] == 100
        assert data_a["total_stock"] == 100

        # Add stock to location B
        response_b = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_b_id, "quantity": 50},
            headers=auth_headers,
        )
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert data_b["quantity_added"] == 50
        assert data_b["total_stock"] == 150  # Total across all locations

        # Add more stock to location A
        response_a2 = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 25},
            headers=auth_headers,
        )
        assert response_a2.status_code == 200
        data_a2 = response_a2.json()
        assert data_a2["quantity_added"] == 25
        assert data_a2["new_quantity"] == 125  # Location A: 100 + 25
        assert data_a2["total_stock"] == 175  # Total: 125 + 50

    def test_scenario_6_multi_row_operations(
        self, client: TestClient, db_session, auth_headers
    ):
        """
        Scenario 6: Given multiple component rows are expanded with add stock forms open,
        When user submits a form,
        Then system applies the operation only to the component associated with that specific row
        """
        # Create two different components (without quantity_on_hand - will be set via ComponentLocation)
        component_a_resp = client.post(
            "/api/v1/components",
            json={"name": "Component A"},
            headers=auth_headers,
        )
        component_a_id = component_a_resp.json()["id"]

        component_b_resp = client.post(
            "/api/v1/components",
            json={"name": "Component B"},
            headers=auth_headers,
        )
        component_b_id = component_b_resp.json()["id"]

        # Create locations
        location_1_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 1", "type": "drawer"},
            headers=auth_headers,
        )
        location_1_id = location_1_resp.json()["id"]

        location_2_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 2", "type": "drawer"},
            headers=auth_headers,
        )
        location_2_id = location_2_resp.json()["id"]

        # Add stock to Component A at Location 1
        response_a = client.post(
            f"/api/v1/components/{component_a_id}/stock/add",
            json={"location_id": location_1_id, "quantity": 100},
            headers=auth_headers,
        )
        assert response_a.status_code == 200
        assert response_a.json()["component_id"] == component_a_id

        # Add stock to Component B at Location 2
        response_b = client.post(
            f"/api/v1/components/{component_b_id}/stock/add",
            json={"location_id": location_2_id, "quantity": 200},
            headers=auth_headers,
        )
        assert response_b.status_code == 200
        assert response_b.json()["component_id"] == component_b_id

        # Verify each component has stock only at its respective location
        comp_a_location = (
            db_session.query(ComponentLocation)
            .filter(ComponentLocation.component_id == component_a_id)
            .all()
        )
        assert len(comp_a_location) == 1
        assert comp_a_location[0].storage_location_id == location_1_id
        assert comp_a_location[0].quantity_on_hand == 100

        comp_b_location = (
            db_session.query(ComponentLocation)
            .filter(ComponentLocation.component_id == component_b_id)
            .all()
        )
        assert len(comp_b_location) == 1
        assert comp_b_location[0].storage_location_id == location_2_id
        assert comp_b_location[0].quantity_on_hand == 200
