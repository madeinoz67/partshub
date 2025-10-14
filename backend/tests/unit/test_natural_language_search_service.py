"""
Unit tests for Natural Language Search Service.

Tests the parsing of natural language queries into structured search parameters.
"""

import pytest

from backend.src.services.natural_language_search_service import (
    NaturalLanguageSearchService,
)


class TestNaturalLanguageSearchService:
    """Test suite for NaturalLanguageSearchService."""

    @pytest.fixture
    def service(self):
        """Create a NaturalLanguageSearchService instance for testing."""
        return NaturalLanguageSearchService()

    def test_simple_component_type_query(self, service):
        """Test parsing simple component type query."""
        result = service.parse_query("find resistors")

        assert result["component_type"] == "resistor"
        assert result["confidence"] > 0.5
        assert result["fallback_to_fts5"] is False
        assert result["intent"] == "search_by_type"

    def test_stock_status_query(self, service):
        """Test parsing query with stock status."""
        result = service.parse_query("resistors with low stock")

        assert result["component_type"] == "resistor"
        assert result["stock_status"] == "low"
        assert result["confidence"] > 0.7  # Multi-entity should boost confidence
        assert result["fallback_to_fts5"] is False

    def test_out_of_stock_query(self, service):
        """Test parsing out of stock query."""
        result = service.parse_query("out of stock capacitors")

        assert result["component_type"] == "capacitor"
        assert result["stock_status"] == "out"
        assert result["confidence"] > 0.5

    def test_location_query(self, service):
        """Test parsing query with storage location."""
        result = service.parse_query("components in A1")

        assert result["storage_location"].upper() == "A1"
        assert result["confidence"] > 0.5

    def test_location_with_type_query(self, service):
        """Test parsing query with location and component type."""
        result = service.parse_query("resistors in Bin-23")

        assert result["component_type"] == "resistor"
        assert result["storage_location"].lower() == "bin-23"
        assert result["confidence"] > 0.7

    def test_value_query_resistance(self, service):
        """Test parsing query with resistance value."""
        result = service.parse_query("10k resistors")

        assert result["component_type"] == "resistor"
        assert "search" in result  # Value goes into search field
        assert "kΩ" in result["search"]  # Check for normalized format
        assert result["confidence"] > 0.5

    def test_value_query_capacitance(self, service):
        """Test parsing query with capacitance value."""
        result = service.parse_query("100μF capacitors")

        assert result["component_type"] == "capacitor"
        assert "search" in result
        assert "μF" in result["search"]  # Check for normalized format

    def test_package_query(self, service):
        """Test parsing query with package/footprint."""
        result = service.parse_query("0805 resistors")

        assert result["component_type"] == "resistor"
        assert result["package"] == "0805"
        assert result["confidence"] > 0.5

    def test_price_query_cheap(self, service):
        """Test parsing query with 'cheap' keyword."""
        result = service.parse_query("cheap resistors")

        assert result["component_type"] == "resistor"
        # Cheap keyword should set max_price in both parsed_entities and result
        assert "max_price" in result["parsed_entities"]
        assert result["price_max"] == 5.0  # Default cheap threshold
        assert result["confidence"] > 0.5

    def test_price_query_under(self, service):
        """Test parsing query with price limit."""
        result = service.parse_query("components under $5")

        assert result["price_max"] == 5.0
        assert result["confidence"] > 0.5

    def test_multi_entity_query(self, service):
        """Test parsing complex multi-entity query."""
        result = service.parse_query("10k SMD resistors with low stock")

        assert result["component_type"] == "resistor"
        assert result["stock_status"] == "low"
        assert result["package"] == "SMD"
        assert "search" in result  # 10k value
        # Multi-entity should have high confidence
        assert result["confidence"] > 0.8
        assert result["fallback_to_fts5"] is False

    def test_ambiguous_query_fallback(self, service):
        """Test that ambiguous queries fallback to FTS5."""
        result = service.parse_query("banana spaceship")

        assert result["fallback_to_fts5"] is True
        assert result["confidence"] < 0.5
        assert result["search"] == "banana spaceship"

    def test_empty_query(self, service):
        """Test handling of empty query."""
        result = service.parse_query("")

        assert result["confidence"] == 0.0
        assert result["fallback_to_fts5"] is True

    def test_whitespace_query(self, service):
        """Test handling of whitespace-only query."""
        result = service.parse_query("   ")

        assert result["confidence"] == 0.0
        assert result["fallback_to_fts5"] is True

    def test_batch_parsing(self, service):
        """Test batch parsing of multiple queries."""
        queries = ["find resistors", "capacitors with low stock", "10k SMD"]
        results = service.parse_batch(queries)

        assert len(results) == 3
        assert results[0]["component_type"] == "resistor"
        assert results[1]["component_type"] == "capacitor"
        assert results[1]["stock_status"] == "low"

    def test_confidence_threshold_get(self, service):
        """Test getting confidence threshold."""
        threshold = service.get_confidence_threshold()
        assert threshold == 0.5  # Default value

    def test_confidence_threshold_set(self, service):
        """Test setting confidence threshold."""
        service.set_confidence_threshold(0.7)
        assert service.get_confidence_threshold() == 0.7

    def test_confidence_threshold_invalid(self, service):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError):
            service.set_confidence_threshold(1.5)

        with pytest.raises(ValueError):
            service.set_confidence_threshold(-0.1)

    def test_confidence_calculation_multi_entity_boost(self, service):
        """Test that multiple entities boost confidence."""
        single_entity_result = service.parse_query("resistors")
        multi_entity_result = service.parse_query("resistors with low stock")

        assert multi_entity_result["confidence"] > single_entity_result["confidence"]

    def test_manufacturer_query(self, service):
        """Test parsing query with manufacturer."""
        result = service.parse_query("Texas Instruments ICs")

        assert result["manufacturer"] == "Texas Instruments"
        assert result["component_type"] == "ic"
        assert result["confidence"] > 0.5

    def test_available_stock_query(self, service):
        """Test parsing available stock query."""
        result = service.parse_query("available resistors")

        assert result["component_type"] == "resistor"
        assert result["stock_status"] == "available"
        assert result["confidence"] > 0.5

    def test_parsed_entities_included(self, service):
        """Test that parsed_entities are included in result."""
        result = service.parse_query("10k resistors")

        assert "parsed_entities" in result
        assert "component_type" in result["parsed_entities"]
        assert result["parsed_entities"]["component_type"] == "resistor"

    def test_intent_classification(self, service):
        """Test that intent is properly classified."""
        result = service.parse_query("low stock components")

        assert result["intent"] == "filter_by_stock"
        assert result["stock_status"] == "low"
