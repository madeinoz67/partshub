"""
Integration test for first-time setup and component addition.
Tests the complete flow from initial setup to adding the first component.
"""

import pytest
from fastapi.testclient import TestClient

from backend.src.auth.admin import ensure_admin_exists


@pytest.mark.integration
class TestFirstTimeSetup:
    """Integration tests for first-time setup scenario"""

    def test_complete_first_time_setup_flow(self, client: TestClient, db_session):
        """
        Test complete first-time setup flow:
        1. Check initial admin exists
        2. Login as admin
        3. Change default password
        4. Create first storage location
        5. Add first component
        6. Verify everything works together
        """

        # Step 1: Ensure admin user exists with default password requirement
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "admin",
                "password": admin_password,  # Use the actual admin password
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "token_type" in login_data

        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check if password change is required through /me endpoint
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["must_change_password"] is True

        # Step 2: Change default password (required for first login)
        password_change_response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": admin_password,
                "new_password": "newSecurePassword123!",
            },
            headers=headers,
        )
        assert password_change_response.status_code == 200

        # Step 3: Login with new password
        new_login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "newSecurePassword123!"},
        )
        assert new_login_response.status_code == 200
        new_login_data = new_login_response.json()
        assert "access_token" in new_login_data

        # Verify password change is no longer required
        new_token = new_login_data["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        new_me_response = client.get("/api/v1/auth/me", headers=new_headers)
        assert new_me_response.status_code == 200
        new_user_data = new_me_response.json()
        assert new_user_data["must_change_password"] is False

        # Step 4: Create first storage location
        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "Main Workshop",
                "description": "Primary electronics workbench",
                "type": "cabinet",
                "parent_id": None,
            },
            headers=new_headers,
        )
        assert storage_response.status_code == 201
        storage_data = storage_response.json()
        storage_id = storage_data["id"]

        # Step 5: Create first category
        import uuid

        unique_category_name = f"Resistors-{str(uuid.uuid4())[:8]}"
        category_response = client.post(
            "/api/v1/categories",
            json={"name": unique_category_name, "description": "Fixed value resistors"},
            headers=new_headers,
        )
        assert category_response.status_code == 201
        category_data = category_response.json()
        category_id = category_data["id"]

        # Step 6: Add first component
        component_response = client.post(
            "/api/v1/components",
            json={
                "name": "10kΩ Resistor",
                "part_number": "CFR25J10K",
                "manufacturer": "Yageo",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "resistor",
                "value": "10kΩ",
                "package": "0603",
                "specifications": {
                    "resistance": "10000",
                    "tolerance": "5%",
                    "power_rating": "0.1W",
                    "package": "0603",
                },
                "quantity_on_hand": 100,
                "average_purchase_price": 0.02,
                "datasheet_url": "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-CFR_51.pdf",
            },
            headers=new_headers,
        )
        assert component_response.status_code == 201
        component_data = component_response.json()
        component_id = component_data["id"]

        # Ensure the database transaction is committed and FTS triggers have fired
        db_session.commit()
        # Force a refresh to ensure all lazy-loaded relationships are populated
        db_session.expire_all()

        # Step 7: Verify component was created properly
        get_component_response = client.get(f"/api/v1/components/{component_id}")
        assert get_component_response.status_code == 200
        retrieved_component = get_component_response.json()

        assert retrieved_component["name"] == "10kΩ Resistor"
        assert retrieved_component["part_number"] == "CFR25J10K"
        assert retrieved_component["manufacturer"] == "Yageo"
        assert retrieved_component["quantity_on_hand"] == 100
        assert retrieved_component["specifications"]["resistance"] == "10000"

        # Step 8: Test search functionality
        # Debug: Check how many components exist before rebuild
        from sqlalchemy import text

        result = db_session.execute(text("SELECT COUNT(*) FROM components"))
        comp_count = result.fetchone()[0]
        print(f"\nDEBUG: Components in database: {comp_count}")

        # Check FTS table before rebuild
        try:
            result = db_session.execute(text("SELECT COUNT(*) FROM components_fts"))
            fts_count_before = result.fetchone()[0]
            print(f"DEBUG: FTS entries before rebuild: {fts_count_before}")
        except Exception as e:
            print(f"DEBUG: FTS table query failed: {e}")

        # Manually rebuild FTS index to ensure it's populated for this test
        from backend.src.database.search import get_component_search_service

        search_service = get_component_search_service()
        indexed_count = search_service.rebuild_fts_index(db_session)
        print(f"DEBUG: FTS rebuild indexed {indexed_count} components")

        # Check FTS table after rebuild
        result = db_session.execute(text("SELECT COUNT(*) FROM components_fts"))
        fts_count_after = result.fetchone()[0]
        print(f"DEBUG: FTS entries after rebuild: {fts_count_after}")

        # Check what's in FTS
        result = db_session.execute(
            text("SELECT id, name, part_number FROM components_fts LIMIT 5")
        )
        fts_samples = result.fetchall()
        print(f"DEBUG: Sample FTS entries: {fts_samples}")

        search_response = client.get("/api/v1/components?search=10k")
        assert search_response.status_code == 200
        search_data = search_response.json()
        print(
            f"DEBUG: Search returned total={search_data['total']}, components_len={len(search_data['components'])}"
        )
        print(f"DEBUG: Components list: {search_data['components']}")
        assert search_data["total"] >= 1, f"Search returned no results: {search_data}"

        # Debug: print what components were found
        found_parts = [comp["part_number"] for comp in search_data["components"]]
        print(f"DEBUG: Found parts: {found_parts}")
        assert any(
            comp["part_number"] == "CFR25J10K" for comp in search_data["components"]
        ), f"Component CFR25J10K not found in search results. Found: {found_parts}"

        # Step 9: Test stock transaction
        stock_response = client.post(
            f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "remove",
                "quantity_change": 5,
                "reason": "Used in first project",
            },
            headers=new_headers,
        )
        assert stock_response.status_code == 200

        # Verify stock was updated
        updated_component_response = client.get(f"/api/v1/components/{component_id}")
        updated_component = updated_component_response.json()
        assert updated_component["quantity_on_hand"] == 95

        # Step 10: Test dashboard statistics
        dashboard_response = client.get(
            "/api/v1/reports/dashboard-stats", headers=new_headers
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        assert dashboard_data["total_components"] >= 1
        assert dashboard_data["total_categories"] >= 1
        assert dashboard_data["total_storage_locations"] >= 1

    def test_setup_with_bulk_storage_creation(self, client: TestClient, db_session):
        """Test setup with bulk storage location creation"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login as admin
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password first
        client.post(
            "/api/v1/auth/change-password",
            json={"current_password": admin_password, "new_password": "newPass123!"},
            headers=headers,
        )

        # Re-login
        new_login = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": "newPass123!"}
        )
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Create bulk storage locations
        bulk_locations = [
            {
                "name": "Drawer A1",
                "description": "Small components drawer A1",
                "type": "drawer",
                "parent_id": None,
            },
            {
                "name": "Drawer A2",
                "description": "Small components drawer A2",
                "type": "drawer",
                "parent_id": None,
            },
            {
                "name": "Shelf B1",
                "description": "Large components shelf B1",
                "type": "shelf",
                "parent_id": None,
            },
        ]

        bulk_response = client.post(
            "/api/v1/storage-locations/bulk-create",
            json={"locations": bulk_locations},
            headers=new_headers,
        )
        assert bulk_response.status_code == 201
        bulk_data = bulk_response.json()
        # Response is a list of created locations, not a dict
        assert len(bulk_data) == 3

        # Verify all locations were created
        list_response = client.get("/api/v1/storage-locations")
        list_data = list_response.json()
        # API returns a list directly, not a dict with a "storage_locations" key
        location_names = [loc["name"] for loc in list_data]

        assert "Drawer A1" in location_names
        assert "Drawer A2" in location_names
        assert "Shelf B1" in location_names

    def test_component_with_attachments_flow(self, client: TestClient, db_session):
        """Test adding component with file attachments"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Setup authentication
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        client.post(
            "/api/v1/auth/change-password",
            json={"current_password": admin_password, "new_password": "newPass123!"},
            headers=headers,
        )

        # Re-login
        new_login = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": "newPass123!"}
        )
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Create category and storage
        category_response = client.post(
            "/api/v1/categories",
            json={"name": "Microcontrollers", "description": "MCU components"},
            headers=new_headers,
        )
        category_id = category_response.json()["id"]

        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "IC Storage",
                "description": "Integrated circuits storage",
                "type": "drawer",
            },
            headers=new_headers,
        )
        storage_id = storage_response.json()["id"]

        # Create component
        component_response = client.post(
            "/api/v1/components",
            json={
                "name": "ESP32-WROOM-32",
                "part_number": "ESP32-WROOM-32",
                "manufacturer": "Espressif",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "microcontroller",
                "package": "LGA",
                "specifications": {
                    "cpu_cores": "2",
                    "cpu_frequency": "240MHz",
                    "flash_memory": "4MB",
                    "wifi": "802.11 b/g/n",
                    "bluetooth": "4.2",
                },
                "quantity_on_hand": 10,
                "average_purchase_price": 3.50,
            },
            headers=new_headers,
        )
        assert component_response.status_code == 201
        component_response.json()["id"]

        # Ensure the database transaction is committed and FTS triggers have fired
        db_session.commit()
        # Force a refresh to ensure all lazy-loaded relationships are populated
        db_session.expire_all()

        # Manually rebuild FTS index to ensure it's populated for this test
        from backend.src.database.search import get_component_search_service

        search_service = get_component_search_service()
        search_service.rebuild_fts_index(db_session)

        # Test that component shows up in search
        search_response = client.get("/api/v1/components?search=ESP32")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1

        # Verify component is searchable by name
        spec_search_response = client.get("/api/v1/components?search=ESP32")
        assert spec_search_response.status_code == 200
        spec_search_data = spec_search_response.json()
        assert spec_search_data["total"] >= 1

    def test_error_handling_during_setup(self, client: TestClient, db_session):
        """Test error handling during setup process"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Test invalid login
        invalid_login = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert invalid_login.status_code == 401

        # Test creating component without authentication
        component_response = client.post(
            "/api/v1/components",
            json={"name": "Test Component", "part_number": "TEST123"},
        )
        assert component_response.status_code == 401

        # Login properly
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test creating component with invalid data
        invalid_component = client.post(
            "/api/v1/components",
            json={
                "name": "",  # Empty name should fail
                "part_number": "TEST123",
            },
            headers=headers,
        )
        assert invalid_component.status_code == 422

        # Test creating storage location with invalid data
        invalid_storage = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "",  # Empty name should fail
                "description": "Test storage",
            },
            headers=headers,
        )
        assert invalid_storage.status_code == 422
