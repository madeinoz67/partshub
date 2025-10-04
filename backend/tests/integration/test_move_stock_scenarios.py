"""
Integration tests for Move Stock acceptance scenarios from spec.md
Tests user scenarios (lines 73-79) with end-to-end workflows
"""

import pytest
from fastapi.testclient import TestClient

from backend.src.models import ComponentLocation, StockTransaction, TransactionType


@pytest.mark.integration
class TestMoveStockScenarios:
    """Integration tests for Move Stock acceptance scenarios"""

    def test_scenario_1_inline_form_with_preselected_source(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 1: Given a component row is expanded and has stock in multiple locations,
        When user selects "Move Stock" from the row expansion menu,
        Then system displays a form inline within the expanded row with source location
        pre-selected (current row's location)
        """
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create multiple locations with stock
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock to both locations
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_b_id, "quantity": 50},
            headers=auth_headers,
        )

        # Verify backend provides data for form (GET component locations)
        response = client.get(
            f"/api/v1/components/{component_id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Frontend would pre-select source based on current row
        # Backend just needs to accept the source in the request

    def test_scenario_2_destination_options_existing_and_other(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 2: Given move stock form is open in the expanded row,
        When user views destination options,
        Then system shows existing locations that already contain this component
        and option for "Other locations that can accept this part"
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create three locations
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        location_c_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location C - Other"},
            headers=auth_headers,
        )
        location_c_id = location_c_resp.json()["id"]

        # Add stock to A and B (so they're "existing" locations for this component)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_b_id, "quantity": 50},
            headers=auth_headers,
        )

        # Move to existing location (B)
        move_to_existing = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }
        response_existing = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_to_existing,
            headers=auth_headers,
        )
        assert response_existing.status_code == 200
        assert response_existing.json()["destination_location_created"] is False

        # Move to "other" location (C - doesn't have this component yet)
        move_to_other = {
            "source_location_id": location_a_id,
            "destination_location_id": location_c_id,
            "quantity": 30,
        }
        response_other = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_to_other,
            headers=auth_headers,
        )
        assert response_other.status_code == 200
        assert response_other.json()["destination_location_created"] is True

    def test_scenario_3_quantity_validation_against_source(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 3: Given user selects an existing location as destination,
        When user enters quantity to move,
        Then system validates quantity against source location's available stock
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        # Add 50 units to source
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 50},
            headers=auth_headers,
        )

        # Valid move within available stock
        move_valid = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 30,
        }
        response_valid = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_valid,
            headers=auth_headers,
        )
        assert response_valid.status_code == 200
        assert response_valid.json()["quantity_moved"] == 30

        # Move exceeding available stock (auto-capped per FR-029)
        move_exceed = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 100,  # More than remaining 20
        }
        response_exceed = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_exceed,
            headers=auth_headers,
        )
        assert response_exceed.status_code == 200
        data = response_exceed.json()
        assert data["quantity_moved"] == 20  # Auto-capped
        assert data["capped"] is True

    def test_scenario_4_new_location_creation_during_move(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 4: Given user selects "Other locations" option,
        When user chooses or creates a new location,
        Then system allows moving stock to a location that doesn't currently have this component
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create source location with stock
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers,
        )

        # User creates new location (simulating "Create new location" workflow)
        new_location_resp = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "New Location Created During Move",
                "description": "Fresh location",
            },
            headers=auth_headers,
        )
        new_location_id = new_location_resp.json()["id"]

        # Move to newly created location
        move_request = {
            "source_location_id": location_a_id,
            "destination_location_id": new_location_id,
            "quantity": 40,
        }
        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_request,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify new ComponentLocation was created
        assert data["destination_location_created"] is True
        assert data["destination_previous_quantity"] == 0
        assert data["destination_new_quantity"] == 40

        # Verify in database
        new_comp_location = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == new_location_id,
            )
            .first()
        )
        assert new_comp_location is not None
        assert new_comp_location.quantity_on_hand == 40

    def test_scenario_5_atomic_transfer(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 5: Given user enters valid move parameters and optional comments,
        When user confirms move,
        Then system transfers stock from source to destination location atomically
        (both succeed or both fail)
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock to source
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 100},
            headers=auth_headers,
        )

        # Add stock to destination
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_b_id, "quantity": 50},
            headers=auth_headers,
        )

        # Get quantities before move
        source_before = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_a_id,
            )
            .first()
        )
        dest_before = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_b_id,
            )
            .first()
        )

        assert source_before.quantity_on_hand == 100
        assert dest_before.quantity_on_hand == 50

        # Perform atomic move
        move_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 40,
            "comments": "Consolidating inventory",
        }
        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_request,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify atomic operation
        assert data["source_previous_quantity"] == 100
        assert data["source_new_quantity"] == 60
        assert data["destination_previous_quantity"] == 50
        assert data["destination_new_quantity"] == 90
        assert data["total_stock"] == 150  # Unchanged (60 + 90)

        # Verify database consistency
        db_session.expire_all()
        source_after = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_a_id,
            )
            .first()
        )
        dest_after = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_b_id,
            )
            .first()
        )

        assert source_after.quantity_on_hand == 60
        assert dest_after.quantity_on_hand == 90

        # Verify transaction was created
        transaction = (
            db_session.query(StockTransaction)
            .filter(
                StockTransaction.component_id == component_id,
                StockTransaction.transaction_type == TransactionType.MOVE,
            )
            .first()
        )
        assert transaction is not None
        assert transaction.quantity_change == 0  # MOVE doesn't change total

    def test_scenario_6_source_cleanup_when_all_moved(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """
        Scenario 6: Given user moves all stock from a location,
        When move is confirmed,
        Then system removes source stock entry if all stock is moved
        """
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers,
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers,
        )
        location_b_id = location_b_resp.json()["id"]

        # Add 60 units to source
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_a_id, "quantity": 60},
            headers=auth_headers,
        )

        # Verify source exists before move
        source_before = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_a_id,
            )
            .first()
        )
        assert source_before is not None
        assert source_before.quantity_on_hand == 60

        # Move all stock
        move_all_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 60,
            "comments": "Moving all stock to main warehouse",
        }
        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_all_request,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify source was deleted
        assert data["source_location_deleted"] is True
        assert data["source_new_quantity"] == 0

        # Verify in database
        db_session.expire_all()
        source_after = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_a_id,
            )
            .first()
        )
        assert source_after is None

    def test_scenario_7_multi_row_operations(
        self, client: TestClient, db_session, auth_headers
    ):
        """
        Scenario 7: Given multiple component rows have move stock forms open,
        When user submits a form,
        Then system applies the move operation only to the component associated
        with that specific row
        """
        # Create two components
        component_a_resp = client.post(
            "/api/v1/components",
            json={"name": "Component A", "quantity_on_hand": 0, "minimum_stock": 0},
            headers=auth_headers,
        )
        component_a_id = component_a_resp.json()["id"]

        component_b_resp = client.post(
            "/api/v1/components",
            json={"name": "Component B", "quantity_on_hand": 0, "minimum_stock": 0},
            headers=auth_headers,
        )
        component_b_id = component_b_resp.json()["id"]

        # Create four locations
        locations = []
        for i in range(4):
            loc_resp = client.post(
                "/api/v1/storage-locations",
                json={"name": f"Location {i+1}"},
                headers=auth_headers,
            )
            locations.append(loc_resp.json()["id"])

        # Component A: stock in locations 0 and 1
        client.post(
            f"/api/v1/components/{component_a_id}/stock/add",
            json={"location_id": locations[0], "quantity": 100},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_a_id}/stock/add",
            json={"location_id": locations[1], "quantity": 50},
            headers=auth_headers,
        )

        # Component B: stock in locations 2 and 3
        client.post(
            f"/api/v1/components/{component_b_id}/stock/add",
            json={"location_id": locations[2], "quantity": 200},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_b_id}/stock/add",
            json={"location_id": locations[3], "quantity": 75},
            headers=auth_headers,
        )

        # Move stock for Component A (0 -> 1)
        response_a = client.post(
            f"/api/v1/components/{component_a_id}/stock/move",
            json={
                "source_location_id": locations[0],
                "destination_location_id": locations[1],
                "quantity": 40,
            },
            headers=auth_headers,
        )
        assert response_a.status_code == 200
        assert response_a.json()["component_id"] == component_a_id
        assert response_a.json()["quantity_moved"] == 40

        # Move stock for Component B (2 -> 3)
        response_b = client.post(
            f"/api/v1/components/{component_b_id}/stock/move",
            json={
                "source_location_id": locations[2],
                "destination_location_id": locations[3],
                "quantity": 50,
            },
            headers=auth_headers,
        )
        assert response_b.status_code == 200
        assert response_b.json()["component_id"] == component_b_id
        assert response_b.json()["quantity_moved"] == 50

        # Verify Component A stocks
        comp_a_loc_0 = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_a_id,
                ComponentLocation.storage_location_id == locations[0],
            )
            .first()
        )
        assert comp_a_loc_0.quantity_on_hand == 60  # 100 - 40

        comp_a_loc_1 = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_a_id,
                ComponentLocation.storage_location_id == locations[1],
            )
            .first()
        )
        assert comp_a_loc_1.quantity_on_hand == 90  # 50 + 40

        # Verify Component B stocks
        comp_b_loc_2 = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_b_id,
                ComponentLocation.storage_location_id == locations[2],
            )
            .first()
        )
        assert comp_b_loc_2.quantity_on_hand == 150  # 200 - 50

        comp_b_loc_3 = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component_b_id,
                ComponentLocation.storage_location_id == locations[3],
            )
            .first()
        )
        assert comp_b_loc_3.quantity_on_hand == 125  # 75 + 50
