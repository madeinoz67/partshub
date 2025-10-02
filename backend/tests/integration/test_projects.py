"""
Integration test for project-based component management.
Tests project creation, component allocation, and tracking workflows.
"""

from fastapi.testclient import TestClient


class TestProjectManagement:
    """Integration tests for project-based component management"""

    def test_complete_project_workflow(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test complete project workflow from creation to completion"""

        import uuid

        test_id = str(uuid.uuid4())[:8]

        # Step 1: Create project
        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": f"LED Matrix Display {test_id}",
                "description": "8x8 LED matrix with Arduino control",
                "status": "planning",
                "budget_allocated": 150.00,
                "client_project_id": f"CLIENT-LED-{test_id}",
            },
            headers=auth_headers,
        )
        assert project_response.status_code in [200, 201]  # Accept both success codes
        project_data = project_response.json()
        project_id = project_data["id"]

        assert project_data["name"] == f"LED Matrix Display {test_id}"
        assert project_data["status"] == "planning"
        assert project_data["budget_allocated"] == 150.00

        # Step 2: Setup components for allocation
        # Create category
        category_response = client.post(
            "/api/v1/categories",
            json={
                "name": f"Electronics {test_id}",
                "description": "Electronic components",
            },
            headers=auth_headers,
        )
        assert (
            category_response.status_code == 201
        ), f"Category creation failed: {category_response.text}"
        category_id = category_response.json()["id"]

        # Create storage location
        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": f"Main Storage {test_id}",
                "description": "Primary storage",
                "type": "container",
            },
            headers=auth_headers,
        )
        assert (
            storage_response.status_code == 201
        ), f"Storage creation failed: {storage_response.text}"
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
                "average_purchase_price": 25.00,
            },
            {
                "name": "8x8 LED Matrix",
                "part_number": "MAX7219",
                "manufacturer": "Maxim",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "display",
                "quantity_on_hand": 10,
                "average_purchase_price": 8.50,
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
                "average_purchase_price": 0.02,
            },
        ]

        component_ids = []
        for comp_data in components_data:
            comp_response = client.post(
                "/api/v1/components", json=comp_data, headers=auth_headers
            )
            assert comp_response.status_code == 201
            component_ids.append(comp_response.json()["id"])

        # Step 3: Allocate components to project
        allocations = [
            {
                "component_id": component_ids[0],
                "quantity": 1,
                "notes": "Main microcontroller",
            },
            {
                "component_id": component_ids[1],
                "quantity": 1,
                "notes": "Display module",
            },
            {
                "component_id": component_ids[2],
                "quantity": 8,
                "notes": "Current limiting resistors",
            },
        ]

        for allocation in allocations:
            alloc_response = client.post(
                f"/api/v1/projects/{project_id}/allocate",
                json=allocation,
                headers=auth_headers,
            )
            assert alloc_response.status_code == 200
            alloc_data = alloc_response.json()
            assert alloc_data["quantity_allocated"] == allocation["quantity"]

        # Step 4: Verify component allocations
        project_components_response = client.get(
            f"/api/v1/projects/{project_id}/components"
        )
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
        update_response = client.patch(
            f"/api/v1/projects/{project_id}",
            json={"status": "active"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        updated_project = update_response.json()
        assert updated_project["status"] == "active"

        # Step 7: Verify stock was reduced
        for i, comp_id in enumerate(component_ids):
            comp_response = client.get(f"/api/v1/components/{comp_id}")
            comp_data = comp_response.json()

            original_qty = components_data[i]["quantity_on_hand"]
            allocated_qty = allocations[i]["quantity"]
            expected_remaining = original_qty - allocated_qty

            assert comp_data["quantity_on_hand"] == expected_remaining

        # Step 8: Return some components
        return_response = client.post(
            f"/api/v1/projects/{project_id}/return",
            json={
                "component_id": component_ids[2],  # Return some resistors
                "quantity": 3,
                "notes": "Spares not needed",
            },
            headers=auth_headers,
        )
        assert return_response.status_code == 200

        # Verify stock was restored
        comp_response = client.get(f"/api/v1/components/{component_ids[2]}")
        comp_data = comp_response.json()
        assert comp_data["quantity_on_hand"] == 95  # 100 - 8 + 3

        # Step 9: Close project
        close_response = client.post(
            f"/api/v1/projects/{project_id}/close",
            params={"return_components": True},
            headers=auth_headers,
        )
        assert close_response.status_code == 200
        close_data = close_response.json()
        assert close_data["components_returned"] is True

        # Verify project status
        final_project = client.get(f"/api/v1/projects/{project_id}")
        final_data = final_project.json()
        assert final_data["status"] == "completed"

    def test_project_budget_tracking(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test project budget allocation and tracking"""

        # Create project with budget
        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Budget Test Project",
                "description": "Testing budget functionality",
                "budget_allocated": 100.00,
            },
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        # Create high-cost component
        category_response = client.post(
            "/api/v1/categories",
            json={"name": "Expensive Parts", "description": "High cost components"},
            headers=auth_headers,
        )
        category_id = category_response.json()["id"]

        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "Secure Storage",
                "description": "High value storage",
                "type": "cabinet",
            },
            headers=auth_headers,
        )
        storage_id = storage_response.json()["id"]

        # Create expensive component
        expensive_component = client.post(
            "/api/v1/components",
            json={
                "name": "High-End Microprocessor",
                "part_number": "EXPENSIVE-001",
                "manufacturer": "Premium Corp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "microprocessor",
                "quantity_on_hand": 2,
                "average_purchase_price": 75.00,
            },
            headers=auth_headers,
        )
        expensive_id = expensive_component.json()["id"]

        # Allocate component within budget
        alloc_response = client.post(
            f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": expensive_id,
                "quantity": 1,
                "notes": "Main processor",
            },
            headers=auth_headers,
        )
        assert alloc_response.status_code == 200

        # Check budget usage
        stats_response = client.get(f"/api/v1/projects/{project_id}/statistics")
        stats_data = stats_response.json()
        assert stats_data["estimated_cost"] == 75.00

        # Try to allocate beyond budget (should still work, but we can track overspend)
        over_budget_response = client.post(
            f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": expensive_id,
                "quantity": 1,
                "notes": "Second processor - over budget",
            },
            headers=auth_headers,
        )
        # This should succeed (business decision to allow overspend)
        assert over_budget_response.status_code == 200

        # Check final budget status
        final_stats = client.get(f"/api/v1/projects/{project_id}/statistics")
        final_data = final_stats.json()
        assert final_data["estimated_cost"] == 150.00  # Over budget

    def test_multi_project_component_sharing(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test multiple projects sharing components"""

        # Create two projects
        project1_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Project Alpha",
                "description": "First project",
                "budget_allocated": 50.00,
            },
            headers=auth_headers,
        )
        project1_id = project1_response.json()["id"]

        project2_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Project Beta",
                "description": "Second project",
                "budget_allocated": 75.00,
            },
            headers=auth_headers,
        )
        project2_id = project2_response.json()["id"]

        # Create shared component
        category_response = client.post(
            "/api/v1/categories",
            json={
                "name": "Shared Components",
                "description": "Components used across projects",
            },
            headers=auth_headers,
        )
        category_id = category_response.json()["id"]

        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "Shared Storage",
                "description": "Shared component storage",
                "type": "container",
            },
            headers=auth_headers,
        )
        storage_id = storage_response.json()["id"]

        shared_component = client.post(
            "/api/v1/components",
            json={
                "name": "Common Resistor",
                "part_number": "COMMON-R-001",
                "manufacturer": "StandardCorp",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "component_type": "resistor",
                "quantity_on_hand": 100,
                "average_purchase_price": 0.05,
            },
            headers=auth_headers,
        )
        component_id = shared_component.json()["id"]

        # Allocate to both projects
        alloc1_response = client.post(
            f"/api/v1/projects/{project1_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 20,
                "notes": "Project Alpha allocation",
            },
            headers=auth_headers,
        )
        assert alloc1_response.status_code == 200

        alloc2_response = client.post(
            f"/api/v1/projects/{project2_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 30,
                "notes": "Project Beta allocation",
            },
            headers=auth_headers,
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
        insufficient_response = client.post(
            f"/api/v1/projects/{project1_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 100,  # More than available
                "notes": "Should fail",
            },
            headers=auth_headers,
        )
        assert insufficient_response.status_code == 400

    def test_project_search_and_filtering(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test project search and filtering functionality"""

        # Create multiple projects with different statuses
        projects_data = [
            {
                "name": "Active Development Project",
                "description": "Currently in development",
                "status": "active",
            },
            {
                "name": "Completed Production Project",
                "description": "Finished and shipped",
                "status": "completed",
            },
            {
                "name": "Planning Phase Project",
                "description": "Still in planning",
                "status": "planning",
            },
        ]

        created_projects = []
        for proj_data in projects_data:
            proj_response = client.post(
                "/api/v1/projects", json=proj_data, headers=auth_headers
            )
            created_projects.append(proj_response.json())

        # Test search by name
        search_response = client.get("/api/v1/projects?search=Development")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1
        assert any("Development" in proj["name"] for proj in search_data["projects"])

        # Test filter by status
        active_filter = client.get("/api/v1/projects?status=active")
        assert active_filter.status_code == 200
        active_data = active_filter.json()
        assert all(proj["status"] == "active" for proj in active_data["projects"])

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

    def test_project_deletion_with_components(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test project deletion behavior with allocated components"""

        # Create project and components
        project_response = client.post(
            "/api/v1/projects",
            json={
                "name": "Delete Test Project",
                "description": "Project for testing deletion",
            },
            headers=auth_headers,
        )
        project_id = project_response.json()["id"]

        # Setup component
        category_response = client.post(
            "/api/v1/categories",
            json={"name": "Delete Test", "description": "For deletion testing"},
            headers=auth_headers,
        )
        category_id = category_response.json()["id"]

        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": "Delete Test Storage",
                "description": "For deletion testing",
                "type": "shelf",
            },
            headers=auth_headers,
        )
        storage_id = storage_response.json()["id"]

        component_response = client.post(
            "/api/v1/components",
            json={
                "name": "Delete Test Component",
                "part_number": "DELETE-001",
                "manufacturer": "TestCorp",
                "component_type": "resistor",
                "category_id": category_id,
                "storage_location_id": storage_id,
                "quantity_on_hand": 50,
                "average_purchase_price": 1.00,
            },
            headers=auth_headers,
        )
        component_id = component_response.json()["id"]

        # Allocate component
        client.post(
            f"/api/v1/projects/{project_id}/allocate",
            json={
                "component_id": component_id,
                "quantity": 10,
                "notes": "Test allocation",
            },
            headers=auth_headers,
        )

        # Try to delete project without force (should fail)
        delete_response = client.delete(
            f"/api/v1/projects/{project_id}", headers=auth_headers
        )
        assert (
            delete_response.status_code == 400
        )  # Should fail due to allocated components

        # Force delete project
        force_delete_response = client.delete(
            f"/api/v1/projects/{project_id}?force=true", headers=auth_headers
        )
        assert force_delete_response.status_code == 200

        # Verify project is deleted
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

        # Verify components were returned to inventory
        comp_response = client.get(f"/api/v1/components/{component_id}")
        comp_data = comp_response.json()
        assert comp_data["quantity_on_hand"] == 50  # Stock restored
