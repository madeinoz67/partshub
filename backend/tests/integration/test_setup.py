"""
Integration test for first-time setup and component addition.
Tests the complete flow from initial setup to adding the first component.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base, get_db
from src.main import app


class TestFirstTimeSetup:
    """Integration tests for first-time setup scenario"""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing"""
        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        yield engine

        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, test_db):
        """Test client with isolated database"""
        return TestClient(app)

    def test_complete_first_time_setup_flow(self, client: TestClient):
        """
        Test complete first-time setup flow:
        1. Check initial admin exists
        2. Login as admin
        3. Change default password
        4. Create first storage location
        5. Add first component
        6. Verify everything works together
        """

        # Step 1: Verify default admin exists after database initialization
        # The admin should be created automatically via startup event
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"  # Default password
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["must_change_password"] is True

        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Change default password (required for first login)
        password_change_response = client.post("/api/v1/auth/change-password",
            json={
                "current_password": "admin123",
                "new_password": "newSecurePassword123!"
            },
            headers=headers
        )
        assert password_change_response.status_code == 200

        # Step 3: Login with new password
        new_login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "newSecurePassword123!"
        })
        assert new_login_response.status_code == 200
        new_login_data = new_login_response.json()
        assert new_login_data["must_change_password"] is False

        new_token = new_login_data["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # Step 4: Create first storage location
        storage_response = client.post("/api/v1/storage-locations",
            json={
                "name": "Main Workshop",
                "description": "Primary electronics workbench",
                "location_type": "workbench"
            },
            headers=new_headers
        )
        assert storage_response.status_code == 201
        storage_data = storage_response.json()
        storage_id = storage_data["id"]

        # Step 5: Create first category
        category_response = client.post("/api/v1/categories",
            json={
                "name": "Resistors",
                "description": "Fixed value resistors"
            },
            headers=new_headers
        )
        assert category_response.status_code == 201
        category_data = category_response.json()
        category_id = category_data["id"]

        # Step 6: Add first component
        component_response = client.post("/api/v1/components",
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
                    "package": "0603"
                },
                "quantity_on_hand": 100,
                "unit_cost": 0.02,
                "datasheet_url": "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-CFR_51.pdf"
            },
            headers=new_headers
        )
        assert component_response.status_code == 201
        component_data = component_response.json()
        component_id = component_data["id"]

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
        search_response = client.get("/api/v1/components?search=10k")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1
        assert any(comp["part_number"] == "CFR25J10K" for comp in search_data["components"])

        # Step 9: Test stock transaction
        stock_response = client.post(f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "usage",
                "quantity": 5,
                "notes": "Used in first project"
            },
            headers=new_headers
        )
        assert stock_response.status_code == 200

        # Verify stock was updated
        updated_component_response = client.get(f"/api/v1/components/{component_id}")
        updated_component = updated_component_response.json()
        assert updated_component["quantity_on_hand"] == 95

        # Step 10: Test dashboard statistics
        dashboard_response = client.get("/api/v1/reports/dashboard-stats", headers=new_headers)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        assert dashboard_data["total_components"] >= 1
        assert dashboard_data["total_categories"] >= 1
        assert dashboard_data["total_storage_locations"] >= 1

    def test_setup_with_bulk_storage_creation(self, client: TestClient):
        """Test setup with bulk storage location creation"""

        # Login as admin
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password first
        client.post("/api/v1/auth/change-password",
            json={"current_password": "admin123", "new_password": "newPass123!"},
            headers=headers
        )

        # Re-login
        new_login = client.post("/api/v1/auth/token", json={
            "username": "admin", "password": "newPass123!"
        })
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Create bulk storage locations
        bulk_locations = [
            {
                "name": "Drawer A1",
                "description": "Small components drawer A1",
                "location_type": "drawer"
            },
            {
                "name": "Drawer A2",
                "description": "Small components drawer A2",
                "location_type": "drawer"
            },
            {
                "name": "Shelf B1",
                "description": "Large components shelf B1",
                "location_type": "shelf"
            }
        ]

        bulk_response = client.post("/api/v1/storage-locations/bulk-create",
            json={"locations": bulk_locations},
            headers=new_headers
        )
        assert bulk_response.status_code == 201
        bulk_data = bulk_response.json()
        assert len(bulk_data["created_locations"]) == 3

        # Verify all locations were created
        list_response = client.get("/api/v1/storage-locations")
        list_data = list_response.json()
        location_names = [loc["name"] for loc in list_data["storage_locations"]]

        assert "Drawer A1" in location_names
        assert "Drawer A2" in location_names
        assert "Shelf B1" in location_names

    def test_component_with_attachments_flow(self, client: TestClient):
        """Test adding component with file attachments"""

        # Setup authentication
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin", "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        client.post("/api/v1/auth/change-password",
            json={"current_password": "admin123", "new_password": "newPass123!"},
            headers=headers
        )

        # Re-login
        new_login = client.post("/api/v1/auth/token", json={
            "username": "admin", "password": "newPass123!"
        })
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Create category and storage
        category_response = client.post("/api/v1/categories",
            json={"name": "Microcontrollers", "description": "MCU components"},
            headers=new_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "IC Storage", "description": "Integrated circuits storage"},
            headers=new_headers
        )
        storage_id = storage_response.json()["id"]

        # Create component
        component_response = client.post("/api/v1/components",
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
                    "bluetooth": "4.2"
                },
                "quantity_on_hand": 10,
                "unit_cost": 3.50
            },
            headers=new_headers
        )
        assert component_response.status_code == 201
        component_response.json()["id"]

        # Test that component shows up in search
        search_response = client.get("/api/v1/components?search=ESP32")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1

        # Verify component specifications are searchable
        spec_search_response = client.get("/api/v1/components?search=240MHz")
        assert spec_search_response.status_code == 200
        spec_search_data = spec_search_response.json()
        assert spec_search_data["total"] >= 1

    def test_error_handling_during_setup(self, client: TestClient):
        """Test error handling during setup process"""

        # Test invalid login
        invalid_login = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert invalid_login.status_code == 401

        # Test creating component without authentication
        component_response = client.post("/api/v1/components", json={
            "name": "Test Component",
            "part_number": "TEST123"
        })
        assert component_response.status_code == 401

        # Login properly
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin", "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test creating component with invalid data
        invalid_component = client.post("/api/v1/components",
            json={
                "name": "",  # Empty name should fail
                "part_number": "TEST123"
            },
            headers=headers
        )
        assert invalid_component.status_code == 422

        # Test creating storage location with invalid data
        invalid_storage = client.post("/api/v1/storage-locations",
            json={
                "name": "",  # Empty name should fail
                "description": "Test storage"
            },
            headers=headers
        )
        assert invalid_storage.status_code == 422
