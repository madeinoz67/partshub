"""
Integration test for component search and inventory management.
Tests the complete inventory workflows including search, filtering, stock management.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import get_db
from src.main import app
from src.models import Base


class TestInventoryManagement:
    """Integration tests for inventory management scenarios"""

    @pytest.fixture
    def db_session(self):
        """Create a shared database session for testing"""
        from fastapi.security import HTTPAuthorizationCredentials
        from src.auth.dependencies import get_optional_user
        from src.auth.jwt_auth import get_current_user as get_user_from_token
        from src.models import User

        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)
        session = TestingSessionLocal()

        def override_get_db():
            yield session

        async def test_get_optional_user(
            credentials: HTTPAuthorizationCredentials = None,
            db = None
        ):
            """TestClient-compatible version of get_optional_user"""
            if not credentials:
                return None

            try:
                user_data = get_user_from_token(credentials.credentials)
                user = session.query(User).filter(User.id == user_data["user_id"]).first()
                if user and user.is_active:
                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "is_admin": user.is_admin,
                        "auth_type": "jwt"
                    }
            except Exception:
                pass

            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_optional_user] = test_get_optional_user
        yield session

        session.close()
        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, db_session):
        """Test client with shared database session"""
        return TestClient(app)

    @pytest.fixture
    def admin_headers(self, db_session):
        """Get admin authentication headers using direct token creation"""
        from src.auth.jwt_auth import create_access_token
        from src.models import User

        # Create admin user directly in shared test database session
        admin_user = User(
            username="testadmin",
            full_name="Test Admin",
            is_admin=True,
            is_active=True
        )
        admin_user.set_password("testpassword")

        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

        # Create JWT token directly
        token = create_access_token({
            "sub": admin_user.id,
            "user_id": admin_user.id,
            "username": admin_user.username,
            "is_admin": admin_user.is_admin
        })

        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def seeded_data(self, db_session):
        """Create foundational data for integration tests"""
        from src.models import Category, StorageLocation

        # Create categories
        categories = {
            "resistors": Category(name="Resistors", description="Fixed value resistors"),
            "capacitors": Category(name="Capacitors", description="Capacitors and supercaps"),
            "semiconductors": Category(name="Semiconductors", description="ICs, transistors, diodes")
        }

        for category in categories.values():
            db_session.add(category)

        # Create storage locations
        storage_locations = {
            "main": StorageLocation(name="Main Storage", description="Primary component storage", type="room"),
            "drawer1": StorageLocation(name="Drawer 1", description="Small parts drawer", type="drawer"),
            "shelf_a": StorageLocation(name="Shelf A", description="Large components shelf", type="shelf")
        }

        for location in storage_locations.values():
            db_session.add(location)

        db_session.commit()

        # Refresh to get IDs
        for category in categories.values():
            db_session.refresh(category)
        for location in storage_locations.values():
            db_session.refresh(location)

        return {
            "categories": categories,
            "storage_locations": storage_locations
        }

    def test_comprehensive_component_search(self, client: TestClient, admin_headers: dict, seeded_data: dict):
        """Test comprehensive component search functionality"""

        # Use seeded data instead of creating via API
        categories = seeded_data["categories"]
        storage_locations = seeded_data["storage_locations"]

        category_ids = {
            "Resistors": categories["resistors"].id,
            "Capacitors": categories["capacitors"].id,
            "Semiconductors": categories["semiconductors"].id
        }
        storage_id = storage_locations["main"].id

        # Create diverse test components
        test_components = [
            {
                "name": "10kΩ Carbon Film Resistor",
                "part_number": "CFR25J10K",
                "manufacturer": "Yageo",
                "category_id": category_ids["Resistors"],
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
                "unit_cost": 0.02
            },
            {
                "name": "1µF Ceramic Capacitor",
                "part_number": "C1608X7R1H105K",
                "manufacturer": "TDK",
                "category_id": category_ids["Capacitors"],
                "storage_location_id": storage_id,
                "component_type": "capacitor",
                "value": "1µF",
                "package": "0603",
                "specifications": {
                    "capacitance": "1000000",  # pF
                    "voltage_rating": "50V",
                    "dielectric": "X7R",
                    "package": "0603"
                },
                "quantity_on_hand": 50,
                "unit_cost": 0.05
            },
            {
                "name": "ESP32-WROOM-32 WiFi Module",
                "part_number": "ESP32-WROOM-32",
                "manufacturer": "Espressif",
                "category_id": category_ids["Semiconductors"],
                "storage_location_id": storage_id,
                "component_type": "microcontroller",
                "package": "LGA",
                "specifications": {
                    "cpu_cores": "2",
                    "cpu_frequency": "240MHz",
                    "flash_memory": "4MB",
                    "wifi": "802.11 b/g/n",
                    "bluetooth": "4.2",
                    "package": "LGA"
                },
                "quantity_on_hand": 25,
                "unit_cost": 3.50
            },
            {
                "name": "1N4148 Switching Diode",
                "part_number": "1N4148",
                "manufacturer": "ON Semiconductor",
                "category_id": category_ids["Semiconductors"],
                "storage_location_id": storage_id,
                "component_type": "diode",
                "package": "SOD-323",
                "specifications": {
                    "forward_voltage": "1.0V",
                    "reverse_voltage": "100V",
                    "forward_current": "300mA",
                    "package": "SOD-323"
                },
                "quantity_on_hand": 200,
                "unit_cost": 0.01
            }
        ]

        # Create all components
        component_ids = []
        for comp in test_components:
            response = client.post("/api/v1/components", json=comp, headers=admin_headers)
            assert response.status_code == 201
            component_ids.append(response.json()["id"])

        # Test 1: Basic text search
        search_response = client.get("/api/v1/components?search=ESP32")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] == 1
        assert "ESP32" in search_data["components"][0]["name"]

        # Test 2: Manufacturer search
        yageo_search = client.get("/api/v1/components?search=Yageo")
        assert yageo_search.status_code == 200
        yageo_data = yageo_search.json()
        assert yageo_data["total"] >= 1

        # Test 3: Part number search
        part_search = client.get("/api/v1/components?search=1N4148")
        assert part_search.status_code == 200
        part_data = part_search.json()
        assert part_data["total"] == 1

        # Test 4: Category filtering
        resistor_filter = client.get(f"/api/v1/components?category_id={category_ids['Resistors']}")
        assert resistor_filter.status_code == 200
        resistor_data = resistor_filter.json()
        assert resistor_data["total"] >= 1
        assert all("resistor" in comp["component_type"].lower() for comp in resistor_data["components"])

        # Test 5: Package filtering
        package_search = client.get("/api/v1/components?search=0603")
        assert package_search.status_code == 200
        package_data = package_search.json()
        assert package_data["total"] >= 2  # Resistor and capacitor

        # Test 6: Specification-based search
        spec_search = client.get("/api/v1/components?search=240MHz")
        assert spec_search.status_code == 200
        spec_data = spec_search.json()
        assert spec_data["total"] >= 1

        # Test 7: Combined search with pagination
        paginated_search = client.get("/api/v1/components?limit=2&offset=0")
        assert paginated_search.status_code == 200
        paginated_data = paginated_search.json()
        assert len(paginated_data["components"]) <= 2
        assert paginated_data["total"] >= 4

    def test_stock_management_workflows(self, client: TestClient, admin_headers: dict):
        """Test comprehensive stock management workflows"""

        # Setup: Create category and storage
        category_response = client.post("/api/v1/categories",
            json={"name": "Test Components", "description": "For testing"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Test Storage", "description": "For testing"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        # Create test component
        component_response = client.post("/api/v1/components",
            json={
                "name": "Test Resistor",
                "part_number": "TEST-R-001",
                "manufacturer": "TestCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "resistor",
                "value": "1kΩ",
                "quantity_on_hand": 100,
                "unit_cost": 0.10
            },
            headers=admin_headers
        )
        component_id = component_response.json()["id"]

        # Test 1: Stock addition (purchase)
        purchase_response = client.post(f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "purchase",
                "quantity": 50,
                "unit_cost": 0.09,
                "notes": "Bulk purchase discount"
            },
            headers=admin_headers
        )
        assert purchase_response.status_code == 200

        # Verify stock increase
        component_check = client.get(f"/api/v1/components/{component_id}")
        component_data = component_check.json()
        assert component_data["quantity_on_hand"] == 150

        # Test 2: Stock usage
        usage_response = client.post(f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "usage",
                "quantity": 25,
                "notes": "Used in project Alpha"
            },
            headers=admin_headers
        )
        assert usage_response.status_code == 200

        # Verify stock decrease
        component_check = client.get(f"/api/v1/components/{component_id}")
        component_data = component_check.json()
        assert component_data["quantity_on_hand"] == 125

        # Test 3: Stock adjustment
        adjustment_response = client.post(f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "adjustment",
                "quantity": -5,  # Remove 5 (perhaps damaged)
                "notes": "Damaged components removed"
            },
            headers=admin_headers
        )
        assert adjustment_response.status_code == 200

        # Verify adjustment
        component_check = client.get(f"/api/v1/components/{component_id}")
        component_data = component_check.json()
        assert component_data["quantity_on_hand"] == 120

        # Test 4: View transaction history
        history_response = client.get(f"/api/v1/components/{component_id}/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) >= 3  # Initial + 3 transactions

        # Verify transaction types
        transaction_types = [txn["transaction_type"] for txn in history_data]
        assert "purchase" in transaction_types
        assert "usage" in transaction_types
        assert "adjustment" in transaction_types

        # Test 5: Error handling - insufficient stock
        excessive_usage = client.post(f"/api/v1/components/{component_id}/stock",
            json={
                "transaction_type": "usage",
                "quantity": 1000,  # More than available
                "notes": "Should fail"
            },
            headers=admin_headers
        )
        assert excessive_usage.status_code == 400

    def test_advanced_filtering_and_sorting(self, client: TestClient, admin_headers: dict):
        """Test advanced filtering and sorting capabilities"""

        # Setup test data with varied specifications
        category_response = client.post("/api/v1/categories",
            json={"name": "Mixed Components", "description": "Various components"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Mixed Storage", "description": "Various storage"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        # Create components with different stock levels and costs
        varied_components = [
            {
                "name": "High Value Component",
                "part_number": "HVC-001",
                "manufacturer": "PremiumCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "quantity_on_hand": 5,
                "unit_cost": 25.00
            },
            {
                "name": "Medium Value Component",
                "part_number": "MVC-001",
                "manufacturer": "StandardCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "quantity_on_hand": 50,
                "unit_cost": 2.50
            },
            {
                "name": "Low Value Component",
                "part_number": "LVC-001",
                "manufacturer": "BudgetCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "quantity_on_hand": 500,
                "unit_cost": 0.05
            }
        ]

        for comp in varied_components:
            response = client.post("/api/v1/components", json=comp, headers=admin_headers)
            assert response.status_code == 201

        # Test 1: Sort by cost (ascending)
        cost_asc = client.get("/api/v1/components?sort_by=unit_cost&sort_order=asc")
        assert cost_asc.status_code == 200
        cost_data = cost_asc.json()
        costs = [comp["unit_cost"] for comp in cost_data["components"]]
        assert costs == sorted(costs)

        # Test 2: Sort by quantity (descending)
        qty_desc = client.get("/api/v1/components?sort_by=quantity_on_hand&sort_order=desc")
        assert qty_desc.status_code == 200
        qty_data = qty_desc.json()
        quantities = [comp["quantity_on_hand"] for comp in qty_data["components"]]
        assert quantities == sorted(quantities, reverse=True)

        # Test 3: Sort by name
        name_sort = client.get("/api/v1/components?sort_by=name&sort_order=asc")
        assert name_sort.status_code == 200
        name_data = name_sort.json()
        names = [comp["name"] for comp in name_data["components"]]
        assert names == sorted(names)

        # Test 4: Filter low stock (assuming low stock threshold)
        # This would depend on implementation of stock level filtering
        all_components = client.get("/api/v1/components")
        all_data = all_components.json()

        # Verify we have components with different stock levels
        stock_levels = [comp["quantity_on_hand"] for comp in all_data["components"]]
        assert min(stock_levels) < 50  # Low stock component
        assert max(stock_levels) > 100  # High stock component

    def test_inventory_analytics_and_reporting(self, client: TestClient, admin_headers: dict):
        """Test inventory analytics and reporting features"""

        # Get initial dashboard stats
        initial_stats = client.get("/api/v1/reports/dashboard-stats", headers=admin_headers)
        assert initial_stats.status_code == 200
        initial_data = initial_stats.json()

        # Create test data for analytics
        category_response = client.post("/api/v1/categories",
            json={"name": "Analytics Test", "description": "For analytics testing"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Analytics Storage", "description": "For analytics testing"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        # Add several components with different values
        test_components = []
        for i in range(3):
            comp_response = client.post("/api/v1/components",
                json={
                    "name": f"Analytics Component {i+1}",
                    "part_number": f"ANLY-{i+1:03d}",
                    "manufacturer": "AnalyticsCorp",
                    "category_id": category_id,
                    "storage_location_id": storage_id,
                    "quantity_on_hand": (i+1) * 10,
                    "unit_cost": (i+1) * 1.00
                },
                headers=admin_headers
            )
            test_components.append(comp_response.json()["id"])

        # Get updated dashboard stats
        updated_stats = client.get("/api/v1/reports/dashboard-stats", headers=admin_headers)
        assert updated_stats.status_code == 200
        updated_data = updated_stats.json()

        # Verify stats increased
        assert updated_data["total_components"] > initial_data["total_components"]
        assert updated_data["total_categories"] > initial_data["total_categories"]
        assert updated_data["total_value"] > initial_data["total_value"]

        # Test category breakdown
        category_stats = client.get("/api/v1/reports/category-breakdown", headers=admin_headers)
        assert category_stats.status_code == 200
        category_data = category_stats.json()

        # Should include our new category
        category_names = [cat["category_name"] for cat in category_data]
        assert "Analytics Test" in category_names

        # Test inventory value analysis
        value_analysis = client.get("/api/v1/reports/inventory-value", headers=admin_headers)
        assert value_analysis.status_code == 200
        value_data = value_analysis.json()

        assert "total_inventory_value" in value_data
        assert "component_count" in value_data
        assert value_data["total_inventory_value"] > 0
