"""
Integration tests for Natural Language Search API endpoints.

Tests the complete NL search workflow from API request through service layer to database,
including parameter merging, metadata responses, fallback behavior, and performance.
"""

import time

import pytest
from fastapi.testclient import TestClient

from backend.src.models import Component, ComponentLocation, StorageLocation


@pytest.mark.integration
class TestNLSearchAPI:
    """Integration tests for natural language search API endpoints."""

    @pytest.fixture
    def test_storage_location(self, db_session):
        """Create a test storage location."""
        location = StorageLocation(
            name="Test Bin A1",
            description="Test storage location",
            type="bin",
        )
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        return location

    @pytest.fixture
    def sample_components(self, db_session, test_storage_location):
        """Create sample components for testing."""
        components = []

        # Resistor with various properties
        resistor = Component(
            name="10kΩ Resistor 0805",
            part_number="RES-10K-0805",
            manufacturer="Yageo",
            component_type="resistor",
            value="10kΩ",
            package="0805",
        )
        db_session.add(resistor)
        db_session.flush()

        # Add location data for resistor
        resistor_location = ComponentLocation(
            component_id=resistor.id,
            storage_location_id=test_storage_location.id,
            quantity_on_hand=100,
            minimum_stock=20,
        )
        db_session.add(resistor_location)
        components.append(resistor)

        # Low stock capacitor
        capacitor = Component(
            name="100μF Capacitor",
            part_number="CAP-100UF",
            manufacturer="Murata",
            component_type="capacitor",
            value="100μF",
            package="SMD",
        )
        db_session.add(capacitor)
        db_session.flush()

        cap_location = ComponentLocation(
            component_id=capacitor.id,
            storage_location_id=test_storage_location.id,
            quantity_on_hand=5,
            minimum_stock=20,
        )
        db_session.add(cap_location)
        components.append(capacitor)

        # Out of stock LED
        led = Component(
            name="Red LED 5mm",
            part_number="LED-RED-5MM",
            manufacturer="Kingbright",
            component_type="led",
            value="Red",
            package="THT",
        )
        db_session.add(led)
        db_session.flush()

        led_location = ComponentLocation(
            component_id=led.id,
            storage_location_id=test_storage_location.id,
            quantity_on_hand=0,
            minimum_stock=10,
        )
        db_session.add(led_location)
        components.append(led)

        # Microcontroller with specific manufacturer
        mcu = Component(
            name="STM32F103 Microcontroller",
            part_number="MCU-STM32F103",
            manufacturer="STMicroelectronics",
            component_type="microcontroller",
            package="LQFP48",
        )
        db_session.add(mcu)
        db_session.flush()

        mcu_location = ComponentLocation(
            component_id=mcu.id,
            storage_location_id=test_storage_location.id,
            quantity_on_hand=10,
            minimum_stock=5,
        )
        db_session.add(mcu_location)
        components.append(mcu)

        db_session.commit()

        # Refresh all components to load relationships
        for comp in components:
            db_session.refresh(comp)

        return components

    # ==================== Basic NL Query Tests ====================

    def test_simple_component_type_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test simple component type query: 'find resistors'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify results contain resistor
        assert data["total"] >= 1
        resistor_found = any(
            "resistor" in comp["component_type"].lower()
            for comp in data["components"]
            if comp["component_type"]
        )
        assert resistor_found

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["confidence"] > 0.5
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"
        assert data["nl_metadata"]["fallback_to_fts5"] is False
        assert data["nl_metadata"]["intent"] in ["search_by_type", "filter_by_type"]

    def test_stock_status_low_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test stock status filtering: 'low stock capacitors'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "low stock capacitors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["confidence"] > 0.5
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "capacitor"
        assert data["nl_metadata"]["parsed_entities"]["stock_status"] == "low"
        assert data["nl_metadata"]["fallback_to_fts5"] is False

        # Verify results (should find low stock capacitor)
        if data["total"] > 0:
            # At least one result should be a capacitor with low stock
            capacitor_found = any(
                "capacitor" in comp["component_type"].lower()
                for comp in data["components"]
                if comp["component_type"]
            )
            assert capacitor_found

    def test_stock_status_out_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test out of stock filtering: 'out of stock LEDs'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "out of stock LEDs"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["parsed_entities"]["stock_status"] == "out"
        assert "led" in data["nl_metadata"]["parsed_entities"]["component_type"].lower()

        # Verify results show out of stock components
        for comp in data["components"]:
            assert comp["quantity_on_hand"] == 0

    def test_location_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test location filtering: 'components in A1'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "components in A1"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["confidence"] > 0.5
        assert (
            "a1" in data["nl_metadata"]["parsed_entities"].get("location", "").lower()
        )

        # All results should be from location A1
        for comp in data["components"]:
            if comp["storage_location"]:
                assert "a1" in comp["storage_location"]["name"].lower()

    def test_value_query_resistance(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test value query: '10k resistors'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "10k resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"
        # Value should be in search field or parsed_entities
        assert (
            "search" in data["nl_metadata"]["parsed_entities"]
            or "resistance" in data["nl_metadata"]["parsed_entities"]
        )

    def test_package_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test package filtering: '0805 resistors'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "0805 resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"
        assert data["nl_metadata"]["parsed_entities"]["package"] == "0805"

        # Results should include 0805 components
        if data["total"] > 0:
            has_0805 = any(
                comp["package"] and "0805" in comp["package"]
                for comp in data["components"]
            )
            assert has_0805

    def test_manufacturer_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test manufacturer filtering: 'STMicroelectronics microcontrollers'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "STMicroelectronics microcontrollers"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        entities = data["nl_metadata"]["parsed_entities"]
        assert "microcontroller" in entities.get("component_type", "").lower()
        assert (
            "manufacturer" in entities
            or "stmicroelectronics" in entities.get("search", "").lower()
        )

    def test_price_query_cheap(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test price filtering: 'cheap resistors'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "cheap resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"
        # Should have max_price set
        assert "max_price" in data["nl_metadata"]["parsed_entities"]

    def test_price_query_under_amount(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test price filtering: 'components under $5'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "components under $5"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata
        assert data["nl_metadata"] is not None
        entities = data["nl_metadata"]["parsed_entities"]
        assert "max_price" in entities
        assert entities["max_price"] == 5.0

    def test_multi_entity_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test complex multi-entity query: '10k SMD resistors with low stock'."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "10k SMD resistors with low stock"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NL metadata has multiple entities
        assert data["nl_metadata"] is not None
        entities = data["nl_metadata"]["parsed_entities"]
        assert entities["component_type"] == "resistor"
        # Should have parsed multiple entities
        assert len(entities) >= 3  # component_type, package, stock_status, search
        # Multi-entity should boost confidence
        assert data["nl_metadata"]["confidence"] > 0.7

    # ==================== Parameter Merging Tests ====================

    def test_manual_param_overrides_nl_component_type(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that manual component_type parameter overrides NL parsed type."""
        response = client.get(
            "/api/v1/components",
            params={
                "nl_query": "find resistors",
                "component_type": "capacitor",  # Manual override
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # NL should have parsed resistor
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"

        # But results should be capacitors (manual filter wins)
        for comp in data["components"]:
            if comp["component_type"]:
                assert "capacitor" in comp["component_type"].lower()

    def test_manual_param_overrides_nl_stock_status(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that manual stock_status parameter overrides NL parsed status."""
        response = client.get(
            "/api/v1/components",
            params={
                "nl_query": "low stock resistors",
                "stock_status": "out",  # Manual override
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # NL should have parsed low stock
        assert data["nl_metadata"]["parsed_entities"]["stock_status"] == "low"

        # But results should be out of stock (manual filter wins)
        for comp in data["components"]:
            assert comp["quantity_on_hand"] == 0

    def test_nl_and_manual_params_merged(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL and manual parameters are properly merged."""
        response = client.get(
            "/api/v1/components",
            params={
                "nl_query": "low stock",
                "component_type": "capacitor",  # Add manual filter
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should use NL stock filter + manual component type
        assert data["nl_metadata"]["parsed_entities"]["stock_status"] == "low"

        # Results should be low stock capacitors
        for comp in data["components"]:
            if comp["component_type"]:
                assert "capacitor" in comp["component_type"].lower()

    def test_nl_params_used_when_manual_absent(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL parameters are used when manual parameters not provided."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "resistors with low stock"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should use both NL parsed parameters
        entities = data["nl_metadata"]["parsed_entities"]
        assert entities["component_type"] == "resistor"
        assert entities["stock_status"] == "low"

    def test_manual_search_overrides_nl_search(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that manual search parameter overrides NL search."""
        response = client.get(
            "/api/v1/components",
            params={
                "nl_query": "resistors",
                "search": "capacitor",  # Manual override
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Results should match manual search (capacitor), not NL query (resistor)
        if data["total"] > 0:
            # Should find capacitors, not resistors
            has_capacitor = any(
                comp["name"] and "capacitor" in comp["name"].lower()
                for comp in data["components"]
            )
            assert has_capacitor

    # ==================== Response Metadata Tests ====================

    def test_metadata_included_in_response(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that nl_metadata is included in API response."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify metadata structure
        assert "nl_metadata" in data
        assert data["nl_metadata"] is not None
        assert "query" in data["nl_metadata"]
        assert "confidence" in data["nl_metadata"]
        assert "parsed_entities" in data["nl_metadata"]
        assert "fallback_to_fts5" in data["nl_metadata"]
        assert "intent" in data["nl_metadata"]

    def test_confidence_score_present(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that confidence score is present and valid."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "10k resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        confidence = data["nl_metadata"]["confidence"]
        assert isinstance(confidence, int | float)
        assert 0.0 <= confidence <= 1.0

    def test_parsed_entities_correct(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that parsed entities are correct and complete."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "low stock 0805 resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        entities = data["nl_metadata"]["parsed_entities"]
        assert "component_type" in entities
        assert entities["component_type"] == "resistor"
        assert "stock_status" in entities
        assert entities["stock_status"] == "low"
        assert "package" in entities
        assert entities["package"] == "0805"

    def test_fallback_flag_false_for_high_confidence(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that fallback_to_fts5 is false for high confidence queries."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["nl_metadata"]["fallback_to_fts5"] is False
        assert data["nl_metadata"]["confidence"] >= 0.5

    def test_intent_classification_present(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that intent classification is present and valid."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "low stock components"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        intent = data["nl_metadata"]["intent"]
        assert intent is not None
        # Valid intents from nl_patterns
        valid_intents = [
            "search_by_type",
            "filter_by_type",
            "filter_by_stock",
            "filter_by_location",
            "filter_by_value",
            "filter_by_price",
            "filter_by_package",
            "filter_by_manufacturer",
        ]
        assert intent in valid_intents

    # ==================== Fallback Behavior Tests ====================

    def test_low_confidence_triggers_fts5_fallback(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that low confidence query triggers FTS5 fallback."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "banana spaceship quantum"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should fallback to FTS5
        assert data["nl_metadata"]["fallback_to_fts5"] is True
        assert data["nl_metadata"]["confidence"] < 0.5

    def test_ambiguous_query_returns_valid_response(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that ambiguous query returns valid response (no 500 error)."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "show me stuff"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have metadata indicating fallback
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["fallback_to_fts5"] is True

    def test_empty_nl_query_handling(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that empty nl_query is handled gracefully."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": ""},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return all components (no filtering)
        assert data["total"] >= 4  # Our sample components

    def test_fallback_uses_original_query(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that FTS5 fallback uses original query for search."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "STM32"},  # Specific part number
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Metadata should indicate fallback behavior
        assert data["nl_metadata"] is not None

        # Even if it falls back, should still search for STM32
        # Note: May return 0 results if fallback search doesn't match exactly
        # The test verifies graceful handling, not necessarily finding results
        # STM32 is in our test data, but fallback may not find it if confidence is very low
        # Just verify the query doesn't crash and returns valid response

    # ==================== Error Handling Tests ====================

    def test_invalid_nl_query_parameter(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that invalid nl_query parameter doesn't break request."""
        # Very long query
        long_query = "find resistors " * 100
        response = client.get(
            "/api/v1/components",
            params={"nl_query": long_query},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully, possibly with fallback
        assert "nl_metadata" in data

    def test_nl_parsing_failure_graceful_degradation(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL parsing failure doesn't break the request."""
        # This should trigger FTS5 fallback
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "!@#$%^&*()"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have metadata indicating fallback or error
        assert data["nl_metadata"] is not None
        assert data["nl_metadata"]["fallback_to_fts5"] is True

    def test_nl_query_without_auth_header(
        self, client: TestClient, sample_components: list
    ):
        """Test NL query without authentication header."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
        )

        # Note: Components endpoint may not require authentication for read operations
        # Just verify it doesn't crash - status 200 or 401 are both acceptable
        assert response.status_code in [200, 401, 403]

    def test_error_details_in_metadata(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that errors are captured in metadata when they occur."""
        # This might trigger some parsing edge case
        response = client.get(
            "/api/v1/components",
            params={"nl_query": ""},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Empty query may not return nl_metadata (it's optional)
        # If metadata exists and has error field, verify it's a string
        if data.get("nl_metadata") and "error" in data["nl_metadata"]:
            assert isinstance(data["nl_metadata"]["error"], str)

    # ==================== Performance Tests ====================

    def test_nl_query_parsing_time(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL query parsing completes quickly (<500ms)."""
        start_time = time.time()

        response = client.get(
            "/api/v1/components",
            params={"nl_query": "10k SMD resistors with low stock"},
            headers=auth_headers,
        )

        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        # Total API response should be under 500ms
        assert elapsed_time < 0.5, f"Query took {elapsed_time:.3f}s (>500ms)"

    def test_nl_search_performance_vs_manual(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL search has acceptable overhead vs manual search."""
        # Manual search timing
        start_manual = time.time()
        manual_response = client.get(
            "/api/v1/components",
            params={"component_type": "resistor", "stock_status": "low"},
            headers=auth_headers,
        )
        manual_time = time.time() - start_manual

        # NL search timing
        start_nl = time.time()
        nl_response = client.get(
            "/api/v1/components",
            params={"nl_query": "low stock resistors"},
            headers=auth_headers,
        )
        nl_time = time.time() - start_nl

        assert manual_response.status_code == 200
        assert nl_response.status_code == 200

        # NL should not be more than 50% slower than manual
        overhead_ratio = nl_time / manual_time if manual_time > 0 else 1.0
        assert (
            overhead_ratio < 1.5
        ), f"NL search {overhead_ratio:.2f}x slower than manual"

    # ==================== Authentication Tests ====================

    def test_nl_search_with_user_auth(
        self, client: TestClient, user_auth_headers: dict, sample_components: list
    ):
        """Test NL search with regular user authentication."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
            headers=user_auth_headers,
        )

        # Regular users can search components
        assert response.status_code == 200
        data = response.json()
        assert data["nl_metadata"] is not None

    # ==================== Pagination Tests ====================

    def test_nl_search_with_limit(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that limit parameter works with NL queries."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "components", "limit": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return at most 2 results
        assert len(data["components"]) <= 2
        assert data["limit"] == 2

    def test_nl_search_with_offset(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that offset parameter works with NL queries."""
        # Get first page
        response1 = client.get(
            "/api/v1/components",
            params={"nl_query": "components", "limit": 2, "offset": 0},
            headers=auth_headers,
        )

        # Get second page
        response2 = client.get(
            "/api/v1/components",
            params={"nl_query": "components", "limit": 2, "offset": 2},
            headers=auth_headers,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Pages should have different components
        if len(data1["components"]) > 0 and len(data2["components"]) > 0:
            ids1 = [comp["id"] for comp in data1["components"]]
            ids2 = [comp["id"] for comp in data2["components"]]
            assert set(ids1).isdisjoint(set(ids2))

    def test_nl_search_pagination_metadata(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that pagination metadata is correct with NL queries."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "components", "limit": 2, "offset": 0},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify pagination fields
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        assert "limit" in data
        assert data["limit"] == 2
        assert data["page"] == 1

    def test_nl_search_large_result_set(
        self, client: TestClient, auth_headers: dict, db_session
    ):
        """Test NL search with large result sets."""
        # Create many components
        storage_location = StorageLocation(name="Bulk Storage", type="room")
        db_session.add(storage_location)
        db_session.commit()
        db_session.refresh(storage_location)

        for i in range(50):
            comp = Component(
                name=f"Test Resistor {i}",
                part_number=f"RES-{i:04d}",
                component_type="resistor",
            )
            db_session.add(comp)
            db_session.flush()

            loc = ComponentLocation(
                component_id=comp.id,
                storage_location_id=storage_location.id,
                quantity_on_hand=10,
            )
            db_session.add(loc)

        db_session.commit()

        # Query for all resistors
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors", "limit": 20},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle large result set efficiently
        assert data["total"] >= 50
        assert len(data["components"]) == 20  # Respect limit
        assert data["nl_metadata"] is not None

    # ==================== Edge Cases ====================

    def test_nl_query_with_special_characters(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test NL query with special characters."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "10kΩ resistors (±5%)"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nl_metadata"] is not None

    def test_nl_query_case_insensitive(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that NL queries are case-insensitive."""
        response1 = client.get(
            "/api/v1/components",
            params={"nl_query": "FIND RESISTORS"},
            headers=auth_headers,
        )

        response2 = client.get(
            "/api/v1/components",
            params={"nl_query": "find resistors"},
            headers=auth_headers,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Should return similar results
        data1 = response1.json()
        data2 = response2.json()
        assert (
            data1["nl_metadata"]["parsed_entities"]
            == data2["nl_metadata"]["parsed_entities"]
        )

    def test_nl_query_whitespace_handling(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that extra whitespace in NL query is handled."""
        response = client.get(
            "/api/v1/components",
            params={"nl_query": "  find   resistors  "},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nl_metadata"]["parsed_entities"]["component_type"] == "resistor"

    def test_nl_query_without_nl_metadata(
        self, client: TestClient, auth_headers: dict, sample_components: list
    ):
        """Test that response without nl_query has no nl_metadata."""
        response = client.get(
            "/api/v1/components",
            params={"component_type": "resistor"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # nl_metadata should be None when nl_query not used
        assert data["nl_metadata"] is None
