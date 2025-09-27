"""
Integration test for project-based component management.
Tests project creation, component allocation, and tracking workflows.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from src.main import app
from src.database.connection import get_db, Base


class TestProjectManagement:
    """Integration tests for project-based component management"""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing"""
        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        yield engine

        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, test_db):
        """Test client with isolated database"""
        return TestClient(app)

    @pytest.fixture
    def admin_headers(self, client):
        """Get admin authentication headers"""
        login_response = client.post("/api/v1/auth/login", json={
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
        new_login = client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "newPass123!"
        })
        return {"Authorization": f"Bearer {new_login.json()['access_token']}"}

    def test_complete_project_workflow(self, client: TestClient, admin_headers: dict):
        """Test complete project workflow from creation to completion"""

        # Step 1: Create project
        project_response = client.post("/api/v1/projects",
            json={
                "name": "LED Matrix Display",
                "description": "8x8 LED matrix with Arduino control",
                "status": "planning",
                "budget_allocated": 150.00,
                "client_project_id": "CLIENT-LED-001"
            },
            headers=admin_headers
        )
        assert project_response.status_code == 201
        project_data = project_response.json()
        project_id = project_data["id"]

        assert project_data["name"] == "LED Matrix Display"
        assert project_data["status"] == "planning"
        assert project_data["budget_allocated"] == 150.00

        # Step 2: Setup components for allocation
        # Create category
        category_response = client.post("/api/v1/categories",
            json={"name": "Electronics", "description": "Electronic components"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        # Create storage location
        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Main Storage", "description": "Primary storage"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        # Create components for the project
        components_data = [
            {
                "name": "Arduino Uno R3",
                "part_number": "A000066",
                "manufacturer": "Arduino",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "microcontroller",
                "quantity_on_hand": 5,
                "unit_cost": 25.00
            },
            {
                "name": "8x8 LED Matrix",
                "part_number": "MAX7219",
                "manufacturer": "Maxim",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "display",
                "quantity_on_hand": 10,
                "unit_cost": 8.50
            },
            {
                "name": "220Ω Resistor",
                "part_number": "CFR25J220R",
                "manufacturer": "Yageo",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "resistor",
                "value": "220Ω",
                "quantity_on_hand": 100,
                "unit_cost": 0.02
            }
        ]

        component_ids = []
        for comp_data in components_data:
            comp_response = client.post("/api/v1/components", json=comp_data, headers=admin_headers)
            assert comp_response.status_code == 201
            component_ids.append(comp_response.json()["id"])

        # Step 3: Allocate components to project
        allocations = [
            {"component_id": component_ids[0], "quantity": 1, "notes": "Main microcontroller"},
            {"component_id": component_ids[1], "quantity": 1, "notes": "Display module"},
            {"component_id": component_ids[2], "quantity": 8, "notes": "Current limiting resistors"}
        ]

        for allocation in allocations:
            alloc_response = client.post(f"/api/v1/projects/{project_id}/allocate",
                json=allocation,
                headers=admin_headers
            )
            assert alloc_response.status_code == 200
            alloc_data = alloc_response.json()
            assert alloc_data["quantity_allocated"] == allocation["quantity"]

        # Step 4: Verify component allocations
        project_components_response = client.get(f"/api/v1/projects/{project_id}/components")
        assert project_components_response.status_code == 200
        project_components = project_components_response.json()
        assert len(project_components) == 3

        # Verify component names are included
        component_names = [pc["component_name"] for pc in project_components]
        assert "Arduino Uno R3" in component_names
        assert "8x8 LED Matrix" in component_names
        assert "220Ω Resistor" in component_names

        # Step 5: Check project statistics
        stats_response = client.get(f"/api/v1/projects/{project_id}/statistics")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()

        assert stats_data["unique_components"] == 3
        assert stats_data["total_allocated_quantity"] == 10  # 1 + 1 + 8
        assert stats_data["estimated_cost"] > 0

        # Step 6: Update project status
        update_response = client.patch(f"/api/v1/projects/{project_id}",
            json={"status": "in_progress"},
            headers=admin_headers
        )
        assert update_response.status_code == 200
        updated_project = update_response.json()
        assert updated_project["status"] == "in_progress"

        # Step 7: Verify stock was reduced
        for i, comp_id in enumerate(component_ids):
            comp_response = client.get(f"/api/v1/components/{comp_id}")
            comp_data = comp_response.json()

            original_qty = components_data[i]["quantity_on_hand"]
            allocated_qty = allocations[i]["quantity"]
            expected_remaining = original_qty - allocated_qty

            assert comp_data["quantity_on_hand"] == expected_remaining

        # Step 8: Return some components
        return_response = client.post(f"/api/v1/projects/{project_id}/return",
            json={
                "component_id": component_ids[2],  # Return some resistors
                "quantity": 3,
                "notes": "Spares not needed"
            },
            headers=admin_headers
        )
        assert return_response.status_code == 200

        # Verify stock was restored
        comp_response = client.get(f"/api/v1/components/{component_ids[2]}")
        comp_data = comp_response.json()
        assert comp_data["quantity_on_hand"] == 95  # 100 - 8 + 3

        # Step 9: Close project
        close_response = client.post(f"/api/v1/projects/{project_id}/close",
            params={"return_components": True},
            headers=admin_headers
        )
        assert close_response.status_code == 200
        close_data = close_response.json()
        assert close_data["components_returned"] is True

        # Verify project status
        final_project = client.get(f"/api/v1/projects/{project_id}")
        final_data = final_project.json()
        assert final_data["status"] == "completed"

    def test_project_budget_tracking(self, client: TestClient, admin_headers: dict):
        """Test project budget allocation and tracking"""

        # Create project with budget
        project_response = client.post("/api/v1/projects",
            json={
                "name": "Budget Test Project",
                "description": "Testing budget functionality",
                "budget_allocated": 100.00
            },
            headers=admin_headers
        )
        project_id = project_response.json()["id"]

        # Create high-cost component
        category_response = client.post("/api/v1/categories",
            json={"name": "Expensive Parts", "description": "High cost components"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Secure Storage", "description": "High value storage"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        # Create expensive component
        expensive_component = client.post("/api/v1/components",
            json={
                "name": "High-End Microprocessor",
                "part_number": "EXPENSIVE-001",
                "manufacturer": "Premium Corp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "microprocessor",
                "quantity_on_hand": 2,
                "unit_cost": 75.00
            },
            headers=admin_headers
        )
        expensive_id = expensive_component.json()["id"]

        # Allocate component within budget
        alloc_response = client.post(f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": expensive_id,
                "quantity": 1,
                "notes": "Main processor"
            },
            headers=admin_headers
        )
        assert alloc_response.status_code == 200

        # Check budget usage
        stats_response = client.get(f"/api/v1/projects/{project_id}/statistics")
        stats_data = stats_response.json()
        assert stats_data["estimated_cost"] == 75.00

        # Try to allocate beyond budget (should still work, but we can track overspend)
        over_budget_response = client.post(f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": expensive_id,
                "quantity": 1,
                "notes": "Second processor - over budget"
            },
            headers=admin_headers
        )
        # This should succeed (business decision to allow overspend)
        assert over_budget_response.status_code == 200

        # Check final budget status
        final_stats = client.get(f"/api/v1/projects/{project_id}/statistics")
        final_data = final_stats.json()
        assert final_data["estimated_cost"] == 150.00  # Over budget

    def test_multi_project_component_sharing(self, client: TestClient, admin_headers: dict):
        """Test multiple projects sharing components"""

        # Create two projects
        project1_response = client.post("/api/v1/projects",
            json={
                "name": "Project Alpha",
                "description": "First project",
                "budget_allocated": 50.00
            },
            headers=admin_headers
        )
        project1_id = project1_response.json()["id"]

        project2_response = client.post("/api/v1/projects",
            json={
                "name": "Project Beta",
                "description": "Second project",
                "budget_allocated": 75.00
            },
            headers=admin_headers
        )
        project2_id = project2_response.json()["id"]

        # Create shared component
        category_response = client.post("/api/v1/categories",
            json={"name": "Shared Components", "description": "Components used across projects"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Shared Storage", "description": "Shared component storage"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        shared_component = client.post("/api/v1/components",
            json={
                "name": "Common Resistor",
                "part_number": "COMMON-R-001",
                "manufacturer": "StandardCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "resistor",
                "quantity_on_hand": 100,
                "unit_cost": 0.05
            },
            headers=admin_headers
        )
        component_id = shared_component.json()["id"]

        # Allocate to both projects
        alloc1_response = client.post(f"/api/v1/projects/{project1_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 20,
                "notes": "Project Alpha allocation"
            },
            headers=admin_headers
        )
        assert alloc1_response.status_code == 200

        alloc2_response = client.post(f"/api/v1/projects/{project2_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 30,
                "notes": "Project Beta allocation"
            },
            headers=admin_headers
        )
        assert alloc2_response.status_code == 200

        # Verify remaining stock
        comp_response = client.get(f"/api/v1/components/{component_id}")
        comp_data = comp_response.json()
        assert comp_data["quantity_on_hand"] == 50  # 100 - 20 - 30

        # Verify both projects have allocations
        project1_components = client.get(f"/api/v1/projects/{project1_id}/components")
        project2_components = client.get(f"/api/v1/projects/{project2_id}/components")

        assert len(project1_components.json()) == 1
        assert len(project2_components.json()) == 1

        assert project1_components.json()[0]["quantity_allocated"] == 20
        assert project2_components.json()[0]["quantity_allocated"] == 30

        # Test insufficient stock scenario
        insufficient_response = client.post(f"/api/v1/projects/{project1_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 100,  # More than available
                "notes": "Should fail"
            },
            headers=admin_headers
        )
        assert insufficient_response.status_code == 400

    def test_project_search_and_filtering(self, client: TestClient, admin_headers: dict):
        """Test project search and filtering functionality"""

        # Create multiple projects with different statuses
        projects_data = [
            {
                "name": "Active Development Project",
                "description": "Currently in development",
                "status": "in_progress"
            },
            {
                "name": "Completed Production Project",
                "description": "Finished and shipped",
                "status": "completed"
            },
            {
                "name": "Planning Phase Project",
                "description": "Still in planning",
                "status": "planning"
            }
        ]

        created_projects = []
        for proj_data in projects_data:
            proj_response = client.post("/api/v1/projects", json=proj_data, headers=admin_headers)
            created_projects.append(proj_response.json())

        # Test search by name
        search_response = client.get("/api/v1/projects?search=Development")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1
        assert any("Development" in proj["name"] for proj in search_data["projects"])

        # Test filter by status
        active_filter = client.get("/api/v1/projects?status=in_progress")
        assert active_filter.status_code == 200
        active_data = active_filter.json()
        assert all(proj["status"] == "in_progress" for proj in active_data["projects"])

        completed_filter = client.get("/api/v1/projects?status=completed")
        assert completed_filter.status_code == 200
        completed_data = completed_filter.json()
        assert all(proj["status"] == "completed" for proj in completed_data["projects"])

        # Test sorting
        name_sort = client.get("/api/v1/projects?sort_by=name&sort_order=asc")
        assert name_sort.status_code == 200
        name_data = name_sort.json()
        project_names = [proj["name"] for proj in name_data["projects"]]
        assert project_names == sorted(project_names)

        # Test pagination
        paginated = client.get("/api/v1/projects?limit=2&offset=0")
        assert paginated.status_code == 200
        paginated_data = paginated.json()
        assert len(paginated_data["projects"]) <= 2
        assert paginated_data["total"] >= 3

    def test_project_deletion_with_components(self, client: TestClient, admin_headers: dict):
        """Test project deletion behavior with allocated components"""

        # Create project and components
        project_response = client.post("/api/v1/projects",
            json={
                "name": "Delete Test Project",
                "description": "Project for testing deletion"
            },
            headers=admin_headers
        )
        project_id = project_response.json()["id"]

        # Setup component
        category_response = client.post("/api/v1/categories",
            json={"name": "Delete Test", "description": "For deletion testing"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]

        storage_response = client.post("/api/v1/storage-locations",
            json={"name": "Delete Test Storage", "description": "For deletion testing"},
            headers=admin_headers
        )
        storage_id = storage_response.json()["id"]

        component_response = client.post("/api/v1/components",
            json={
                "name": "Delete Test Component",
                "part_number": "DELETE-001",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "quantity_on_hand": 50,
                "unit_cost": 1.00
            },
            headers=admin_headers
        )
        component_id = component_response.json()["id"]

        # Allocate component
        client.post(f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 10,
                "notes": "Test allocation"
            },
            headers=admin_headers
        )

        # Try to delete project without force (should fail)
        delete_response = client.delete(f"/api/v1/projects/{project_id}", headers=admin_headers)
        assert delete_response.status_code == 400  # Should fail due to allocated components

        # Force delete project
        force_delete_response = client.delete(f"/api/v1/projects/{project_id}?force=true", headers=admin_headers)
        assert force_delete_response.status_code == 200

        # Verify project is deleted
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

        # Verify components were returned to inventory
        comp_response = client.get(f"/api/v1/components/{component_id}")
        comp_data = comp_response.json()
        assert comp_data["quantity_on_hand"] == 50  # Stock restored