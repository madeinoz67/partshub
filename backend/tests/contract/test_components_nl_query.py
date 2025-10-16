"""
Contract test for Natural Language Query parameter in GET /api/v1/components.

Tests the nl_query parameter end-to-end through the API endpoint to verify:
- Query parsing and entity extraction
- Integration with component search service
- Confidence scoring and metadata
- Fallback behavior for ambiguous queries
- Manual parameter override behavior
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestComponentsNLQueryContract:
    """Contract tests for natural language query parameter"""

    def test_simple_nl_query_resistors(
        self, client: TestClient, db_session, auth_headers
    ):
        """Test simple NL query 'find resistors' returns resistors."""
        # Create test components
        from backend.src.models.component import Component

        resistor = Component(
            name="Test Resistor 10kΩ",
            part_number="RES-10K",
            component_type="resistor",
            value="10kΩ",
            package="0805",
        )
        capacitor = Component(
            name="Test Capacitor 100μF",
            part_number="CAP-100U",
            component_type="capacitor",
            value="100μF",
            package="1206",
        )
        db_session.add_all([resistor, capacitor])
        db_session.commit()

        # Query using natural language
        response = client.get("/api/v1/components?nl_query=find resistors")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "components" in data
        assert "nl_metadata" in data
        assert data["nl_metadata"] is not None

        # Check NL metadata
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["query"] == "find resistors"
        assert nl_metadata["confidence"] > 0.5
        assert nl_metadata["fallback_to_fts5"] is False
        assert nl_metadata["intent"] == "search_by_type"
        assert "component_type" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["component_type"] == "resistor"

        # Verify results contain only resistors
        components = data["components"]
        if components:
            for component in components:
                assert component["component_type"] == "resistor"

    def test_multi_entity_query_low_stock(
        self, client: TestClient, db_session, auth_headers
    ):
        """Test multi-entity query '10k resistors with low stock'."""
        # Create test components with stock levels
        from backend.src.models.component import Component
        from backend.src.models.storage_location import StorageLocation

        # Create storage location first
        location = StorageLocation(
            name="Test Bin", description="Test storage", type="bin"
        )
        db_session.add(location)
        db_session.commit()

        # Create components with different stock levels
        low_stock_resistor = Component(
            name="Low Stock Resistor 10kΩ",
            part_number="RES-10K-LOW",
            component_type="resistor",
            value="10kΩ",
            package="0805",
        )
        good_stock_resistor = Component(
            name="Good Stock Resistor 10kΩ",
            part_number="RES-10K-GOOD",
            component_type="resistor",
            value="10kΩ",
            package="0805",
        )

        db_session.add_all([low_stock_resistor, good_stock_resistor])
        db_session.commit()

        # Add stock via component locations
        from backend.src.models.component_location import ComponentLocation

        # Low stock component (below minimum)
        low_location = ComponentLocation(
            component_id=low_stock_resistor.id,
            storage_location_id=location.id,
            quantity_on_hand=5,
            minimum_stock=10,
        )
        # Good stock component (above minimum)
        good_location = ComponentLocation(
            component_id=good_stock_resistor.id,
            storage_location_id=location.id,
            quantity_on_hand=20,
            minimum_stock=10,
        )

        db_session.add_all([low_location, good_location])
        db_session.commit()

        # Query using natural language
        response = client.get(
            "/api/v1/components?nl_query=10k resistors with low stock"
        )

        assert response.status_code == 200
        data = response.json()

        # Check NL metadata for multi-entity parsing
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["confidence"] > 0.7  # Multi-entity should boost confidence
        assert nl_metadata["fallback_to_fts5"] is False
        assert "component_type" in nl_metadata["parsed_entities"]
        assert "stock_status" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["component_type"] == "resistor"
        assert nl_metadata["parsed_entities"]["stock_status"] == "low"

    def test_fallback_behavior_ambiguous_query(self, client: TestClient):
        """Test fallback to FTS5 for ambiguous queries."""
        # Test with nonsensical query
        response = client.get("/api/v1/components?nl_query=banana spaceship quantum")

        assert response.status_code == 200
        data = response.json()

        # Check that it falls back to FTS5
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["confidence"] < 0.5
        assert nl_metadata["fallback_to_fts5"] is True
        # When falling back, the original query should be used for search
        assert nl_metadata["query"] == "banana spaceship quantum"

    def test_manual_params_override_nl_query(
        self, client: TestClient, db_session, auth_headers
    ):
        """Test that manual parameters override NL query parameters."""
        # Create test components
        from backend.src.models.component import Component

        resistor = Component(
            name="Test Resistor",
            part_number="RES-001",
            component_type="resistor",
        )
        capacitor = Component(
            name="Test Capacitor",
            part_number="CAP-001",
            component_type="capacitor",
        )
        db_session.add_all([resistor, capacitor])
        db_session.commit()

        # NL query says "resistors" but manual param overrides with "capacitor"
        response = client.get(
            "/api/v1/components?nl_query=find resistors&component_type=capacitor"
        )

        assert response.status_code == 200
        data = response.json()

        # Manual parameter should take precedence
        components = data["components"]
        if components:
            for component in components:
                # Should return capacitors, not resistors
                assert component["component_type"] == "capacitor"

        # NL metadata should still show what was parsed from query
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["parsed_entities"]["component_type"] == "resistor"

    def test_location_query(self, client: TestClient, db_session, auth_headers):
        """Test NL query with location 'components in A1'."""
        # Create test components in different locations
        from backend.src.models.component import Component
        from backend.src.models.component_location import ComponentLocation
        from backend.src.models.storage_location import StorageLocation

        # Create locations
        location_a1 = StorageLocation(name="A1", description="Location A1", type="bin")
        location_b2 = StorageLocation(name="B2", description="Location B2", type="bin")
        db_session.add_all([location_a1, location_b2])
        db_session.commit()

        # Create components
        comp_a1 = Component(
            name="Component in A1", part_number="COMP-A1", component_type="resistor"
        )
        comp_b2 = Component(
            name="Component in B2", part_number="COMP-B2", component_type="capacitor"
        )
        db_session.add_all([comp_a1, comp_b2])
        db_session.commit()

        # Add component locations
        loc_a1 = ComponentLocation(
            component_id=comp_a1.id,
            storage_location_id=location_a1.id,
            quantity_on_hand=10,
        )
        loc_b2 = ComponentLocation(
            component_id=comp_b2.id,
            storage_location_id=location_b2.id,
            quantity_on_hand=10,
        )
        db_session.add_all([loc_a1, loc_b2])
        db_session.commit()

        # Query for components in A1
        response = client.get("/api/v1/components?nl_query=components in A1")

        assert response.status_code == 200
        data = response.json()

        # Check NL metadata
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["confidence"] > 0.5
        assert "location" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["location"].upper() == "A1"

    def test_price_query(self, client: TestClient, db_session, auth_headers):
        """Test NL query with price constraints 'under $5'."""
        # Create test components with different prices
        from backend.src.models.component import Component

        cheap_comp = Component(
            name="Cheap Resistor",
            part_number="CHEAP-001",
            component_type="resistor",
            average_purchase_price=3.50,
        )
        expensive_comp = Component(
            name="Expensive Resistor",
            part_number="EXP-001",
            component_type="resistor",
            average_purchase_price=10.00,
        )
        db_session.add_all([cheap_comp, expensive_comp])
        db_session.commit()

        # Query for cheap components
        response = client.get("/api/v1/components?nl_query=components under $5")

        assert response.status_code == 200
        data = response.json()

        # Check NL metadata
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["confidence"] > 0.5
        assert "max_price" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["max_price"] == 5.0

    def test_package_query(self, client: TestClient, db_session, auth_headers):
        """Test NL query with package type '0805 resistors'."""
        # Create test components with different packages
        from backend.src.models.component import Component

        smd_resistor = Component(
            name="SMD Resistor 0805",
            part_number="RES-0805",
            component_type="resistor",
            package="0805",
        )
        dip_resistor = Component(
            name="Through-hole Resistor",
            part_number="RES-DIP",
            component_type="resistor",
            package="DIP",
        )
        db_session.add_all([smd_resistor, dip_resistor])
        db_session.commit()

        # Query for 0805 resistors
        response = client.get("/api/v1/components?nl_query=0805 resistors")

        assert response.status_code == 200
        data = response.json()

        # Check NL metadata
        nl_metadata = data["nl_metadata"]
        assert nl_metadata["confidence"] > 0.5
        assert "package" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["package"] == "0805"
        assert "component_type" in nl_metadata["parsed_entities"]
        assert nl_metadata["parsed_entities"]["component_type"] == "resistor"

    def test_confidence_metadata_in_response(self, client: TestClient):
        """Test that confidence metadata is included in response."""
        response = client.get("/api/v1/components?nl_query=find resistors")

        assert response.status_code == 200
        data = response.json()

        # Verify metadata structure
        assert "nl_metadata" in data
        nl_metadata = data["nl_metadata"]
        assert "confidence" in nl_metadata
        assert "parsed_entities" in nl_metadata
        assert "fallback_to_fts5" in nl_metadata
        assert "intent" in nl_metadata
        assert "query" in nl_metadata

        # Confidence should be a float between 0.0 and 1.0
        assert isinstance(nl_metadata["confidence"], int | float)
        assert 0.0 <= nl_metadata["confidence"] <= 1.0

    def test_empty_nl_query_handling(self, client: TestClient):
        """Test handling of empty nl_query parameter."""
        # Empty string
        response = client.get("/api/v1/components?nl_query=")

        assert response.status_code == 200
        data = response.json()

        # Should still return components (no filtering)
        assert "components" in data
        # NL metadata should indicate empty query
        if data["nl_metadata"]:
            nl_metadata = data["nl_metadata"]
            assert nl_metadata["confidence"] == 0.0
            assert nl_metadata["fallback_to_fts5"] is True

    def test_results_match_expected_component_types(
        self, client: TestClient, db_session, auth_headers
    ):
        """Test that NL query results match expected component types."""
        # Create diverse component types
        from backend.src.models.component import Component

        components = [
            Component(
                name="Test Resistor", part_number="R1", component_type="resistor"
            ),
            Component(
                name="Test Capacitor", part_number="C1", component_type="capacitor"
            ),
            Component(name="Test IC", part_number="IC1", component_type="ic"),
            Component(name="Test LED", part_number="LED1", component_type="led"),
        ]
        db_session.add_all(components)
        db_session.commit()

        # Test each component type
        test_cases = [
            ("resistors", "resistor"),
            ("capacitors", "capacitor"),
            ("ICs", "ic"),
            ("LEDs", "led"),
        ]

        for query_term, expected_type in test_cases:
            response = client.get(f"/api/v1/components?nl_query=find {query_term}")

            assert response.status_code == 200
            data = response.json()

            # Check parsed entity
            nl_metadata = data["nl_metadata"]
            if not nl_metadata["fallback_to_fts5"]:
                assert (
                    nl_metadata["parsed_entities"].get("component_type")
                    == expected_type
                )

                # Verify results (if any) match the expected type
                components_list = data["components"]
                if components_list:
                    for comp in components_list:
                        assert comp["component_type"] == expected_type

    def test_nl_query_with_pagination(
        self, client: TestClient, db_session, auth_headers
    ):
        """Test that nl_query works correctly with pagination parameters."""
        # Create multiple test resistors
        from backend.src.models.component import Component

        resistors = [
            Component(
                name=f"Test Resistor {i}",
                part_number=f"RES-{i:03d}",
                component_type="resistor",
            )
            for i in range(15)
        ]
        db_session.add_all(resistors)
        db_session.commit()

        # Query with pagination
        response = client.get("/api/v1/components?nl_query=resistors&limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        # Check pagination metadata
        assert data["limit"] == 10
        assert data["page"] == 1
        assert len(data["components"]) <= 10

        # NL metadata should still be present
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"

    def test_nl_query_with_sorting(self, client: TestClient, db_session, auth_headers):
        """Test that nl_query works correctly with sorting parameters."""
        # Create test components with different names
        from backend.src.models.component import Component

        components = [
            Component(name="AAA Resistor", part_number="R1", component_type="resistor"),
            Component(name="ZZZ Resistor", part_number="R2", component_type="resistor"),
            Component(name="MMM Resistor", part_number="R3", component_type="resistor"),
        ]
        db_session.add_all(components)
        db_session.commit()

        # Query with sorting
        response = client.get(
            "/api/v1/components?nl_query=resistors&sort_by=name&sort_order=asc"
        )

        assert response.status_code == 200
        data = response.json()

        # Check sorting
        components_list = data["components"]
        if len(components_list) >= 2:
            # Verify ascending order by name
            assert components_list[0]["name"] <= components_list[1]["name"]

        # NL metadata should still be present
        assert data["nl_metadata"] is not None
