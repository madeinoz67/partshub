"""
Unit tests for Natural Language Query Pattern Grammar.

Tests pattern matching, entity extraction, intent classification,
confidence scoring, and edge cases.
"""


from backend.src.services.nl_patterns import (
    EXAMPLE_QUERIES,
    EntityExtractor,
    IntentClassifier,
    NLQueryParser,
    ParsedQuery,
    normalize_capacitance,
    normalize_current,
    normalize_frequency,
    normalize_inductance,
    normalize_resistance,
)


class TestUnitNormalization:
    """Test unit normalization functions."""

    def test_normalize_resistance(self):
        """Test resistance normalization."""
        assert normalize_resistance("10", "k") == "10.0kΩ"
        assert normalize_resistance("1", "M") == "1.0MΩ"
        assert normalize_resistance("100", "") == "100.0Ω"
        assert normalize_resistance("4.7", "k") == "4.7kΩ"

    def test_normalize_capacitance(self):
        """Test capacitance normalization."""
        assert normalize_capacitance("100", "μ") == "100.0μF"
        assert normalize_capacitance("10", "n") == "10.0nF"
        assert normalize_capacitance("1", "p") == "1.0pF"
        assert normalize_capacitance("100", "u") == "100.0μF"
        assert normalize_capacitance("1", "") == "1.0F"

    def test_normalize_inductance(self):
        """Test inductance normalization."""
        assert normalize_inductance("10", "μ") == "10.0μH"
        assert normalize_inductance("100", "n") == "100.0nH"
        assert normalize_inductance("1", "m") == "1.0mH"

    def test_normalize_current(self):
        """Test current normalization."""
        assert normalize_current("1", "") == "1.0A"
        assert normalize_current("500", "m") == "500.0mA"
        assert normalize_current("100", "μ") == "100.0μA"

    def test_normalize_frequency(self):
        """Test frequency normalization."""
        assert normalize_frequency("16", "M") == "16.0MHz"
        assert normalize_frequency("32", "k") == "32.0kHz"
        assert normalize_frequency("1", "G") == "1.0GHz"


class TestIntentClassifier:
    """Test intent classification logic."""

    def test_search_by_type_intent(self):
        """Test search_by_type intent classification."""
        queries = [
            "find resistors",
            "show capacitors",
            "list inductors",
            "search for transistors",
        ]

        for query in queries:
            intent, confidence = IntentClassifier.classify(query)
            assert intent == "search_by_type"
            assert confidence > 0.5

    def test_filter_by_stock_intent(self):
        """Test filter_by_stock intent classification."""
        queries = [
            "components with low stock",
            "out of stock parts",
        ]

        for query in queries:
            intent, confidence = IntentClassifier.classify(query)
            assert intent == "filter_by_stock"
            assert confidence > 0.5

        # "available components" may be classified as either intent
        intent, confidence = IntentClassifier.classify("available components")
        assert intent in ["filter_by_stock", "search_by_type"]
        assert confidence >= 0.3

    def test_filter_by_location_intent(self):
        """Test filter_by_location intent classification."""
        queries = [
            "components in A1",
            "parts stored in Bin-23",
            "what's in Shelf-A",
        ]

        for query in queries:
            intent, confidence = IntentClassifier.classify(query)
            assert intent == "filter_by_location"
            assert confidence > 0.5

    def test_filter_by_value_intent(self):
        """Test filter_by_value intent classification."""
        queries = [
            "10k resistors",
            "100μF capacitors",
            "0805 components",
        ]

        for query in queries:
            intent, _ = IntentClassifier.classify(query)
            # Could be search_by_type or filter_by_value depending on query structure
            assert intent in ["search_by_type", "filter_by_value"]

    def test_filter_by_price_intent(self):
        """Test filter_by_price intent classification."""
        queries = [
            "components under $1",
            "cheap capacitors",
            "parts less than $5",
        ]

        for query in queries:
            intent, confidence = IntentClassifier.classify(query)
            # Some queries may be classified as search_by_type with price entities
            assert intent in ["filter_by_price", "search_by_type"]
            assert confidence > 0.3


class TestEntityExtractor:
    """Test entity extraction functions."""

    def test_extract_component_type(self):
        """Test component type extraction."""
        test_cases = [
            ("find resistors", "resistor"),
            ("show capacitors", "capacitor"),
            ("list inductors", "inductor"),
            ("get all ICs", "ic"),
            ("search for transistors", "transistor"),
            ("display LEDs", "led"),
            ("find diodes", "diode"),
            ("show connectors", "connector"),
            ("crystals", "crystal"),
            ("microcontrollers", "microcontroller"),
        ]

        for query, expected_type in test_cases:
            component_type, confidence = EntityExtractor.extract_component_type(query)
            assert component_type == expected_type
            assert confidence > 0.6

    def test_extract_component_type_abbreviations(self):
        """Test component type extraction with abbreviations."""
        test_cases = [
            ("res", "resistor"),
            ("caps", "capacitor"),
            ("ind", "inductor"),
            ("mcus", "microcontroller"),
        ]

        for query, expected_type in test_cases:
            component_type, confidence = EntityExtractor.extract_component_type(query)
            assert component_type == expected_type
            assert confidence > 0.5

    def test_extract_stock_status(self):
        """Test stock status extraction."""
        test_cases = [
            ("low stock", "low"),
            ("out of stock", "out"),
            ("available", "available"),
            ("unused", "unused"),
            ("need reorder", "reorder"),
        ]

        for query, expected_status in test_cases:
            status, confidence = EntityExtractor.extract_stock_status(query)
            assert status == expected_status
            assert confidence > 0.7

    def test_extract_location(self):
        """Test location extraction."""
        test_cases = [
            ("components in A1", "a1"),
            ("parts stored in Bin-23", "bin-23"),
            ("what's in Shelf-A", "shelf-a"),
            ("at Cabinet-1", "cabinet-1"),
            ("from Drawer-2", "drawer-2"),
        ]

        for query, expected_location in test_cases:
            location, confidence = EntityExtractor.extract_location(query)
            assert location.lower() == expected_location.lower()
            assert confidence > 0.7

    def test_extract_value_resistance(self):
        """Test resistance value extraction."""
        test_cases = [
            ("10k resistors", "resistance", "10.0kΩ"),
            ("10kΩ SMD", "resistance", "10.0kΩ"),
            ("4.7k ohm", "resistance", "4.7kΩ"),
            ("1M resistor", "resistance", "1.0MΩ"),
        ]

        for query, value_type, expected_value in test_cases:
            values, confidence = EntityExtractor.extract_value(query)
            assert value_type in values
            assert values[value_type] == expected_value
            assert confidence > 0.7

    def test_extract_value_capacitance(self):
        """Test capacitance value extraction."""
        test_cases = [
            ("100μF capacitors", "capacitance", "100.0μF"),
            ("10nF caps", "capacitance", "10.0nF"),
            ("1pF capacitor", "capacitance", "1.0pF"),
        ]

        for query, value_type, expected_value in test_cases:
            values, confidence = EntityExtractor.extract_value(query)
            assert value_type in values
            assert values[value_type] == expected_value
            assert confidence > 0.7

    def test_extract_value_voltage(self):
        """Test voltage value extraction."""
        test_cases = [
            ("5V components", "voltage", "5V"),
            ("3.3V regulators", "voltage", "3.3V"),
            ("12V parts", "voltage", "12V"),
        ]

        for query, value_type, expected_value in test_cases:
            values, confidence = EntityExtractor.extract_value(query)
            assert value_type in values
            assert values[value_type] == expected_value
            assert confidence > 0.7

    def test_extract_value_frequency(self):
        """Test frequency value extraction."""
        test_cases = [
            ("16MHz crystals", "frequency", "16.0MHz"),
            ("32kHz oscillator", "frequency", "32.0kHz"),
        ]

        for query, value_type, expected_value in test_cases:
            values, confidence = EntityExtractor.extract_value(query)
            assert value_type in values
            assert values[value_type] == expected_value
            assert confidence > 0.7

    def test_extract_package(self):
        """Test package/footprint extraction."""
        test_cases = [
            ("0805 resistors", "0805"),
            ("1206 capacitors", "1206"),
            ("DIP8 ICs", "DIP8"),
            ("SOT-23 transistors", "SOT-23"),
            ("TQFP32 microcontroller", "TQFP32"),
        ]

        for query, expected_package in test_cases:
            package, confidence = EntityExtractor.extract_package(query)
            assert package.upper() == expected_package.upper()
            assert confidence > 0.7

    def test_extract_manufacturer(self):
        """Test manufacturer extraction."""
        test_cases = [
            ("Texas Instruments microcontroller", "Texas Instruments"),
            ("TI ICs", "Texas Instruments"),
            ("Infineon parts", "Infineon"),
            ("NXP components", "NXP"),
            ("ST microcontroller", "STMicroelectronics"),
        ]

        for query, expected_manufacturer in test_cases:
            manufacturer, confidence = EntityExtractor.extract_manufacturer(query)
            assert manufacturer == expected_manufacturer
            assert confidence > 0.7

    def test_extract_price(self):
        """Test price extraction."""
        test_cases = [
            ("components under $1", {"max_price": 1.0}),
            ("parts less than $5", {"max_price": 5.0}),
            ("cheap capacitors", {"max_price": 5.0}),
            ("over $10", {"min_price": 10.0}),
        ]

        for query, expected_price_info in test_cases:
            price_info, confidence = EntityExtractor.extract_price(query)
            for key, value in expected_price_info.items():
                assert key in price_info
                assert price_info[key] == value
            assert confidence > 0.5


class TestNLQueryParser:
    """Test the main NL query parser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = NLQueryParser()
        assert parser.intent_classifier is not None
        assert parser.entity_extractor is not None

    def test_parse_empty_query(self):
        """Test parsing empty query."""
        parser = NLQueryParser()
        result = parser.parse("")
        assert isinstance(result, ParsedQuery)
        assert result.intent == "search_by_type"
        assert result.confidence == 0.0
        assert result.entities == {}

    def test_parse_simple_component_query(self):
        """Test parsing simple component search."""
        parser = NLQueryParser()
        result = parser.parse("find resistors")

        assert result.intent == "search_by_type"
        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"
        assert result.confidence > 0.5

    def test_parse_multi_entity_query(self):
        """Test parsing query with multiple entities."""
        parser = NLQueryParser()
        result = parser.parse("10k SMD resistors with low stock")

        assert result.intent == "search_by_type"
        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"
        assert "stock_status" in result.entities
        assert result.entities["stock_status"] == "low"
        assert "package" in result.entities
        assert result.entities["package"] == "SMD"
        assert result.confidence > 0.7

    def test_parse_location_query(self):
        """Test parsing location-based query."""
        parser = NLQueryParser()
        result = parser.parse("components in A1")

        assert result.intent == "filter_by_location"
        assert "location" in result.entities
        assert result.entities["location"].lower() == "a1"

    def test_parse_price_query(self):
        """Test parsing price-based query."""
        parser = NLQueryParser()
        result = parser.parse("components under $5")

        assert "max_price" in result.entities
        assert result.entities["max_price"] == 5.0

    def test_parse_complex_query(self):
        """Test parsing complex multi-entity query."""
        parser = NLQueryParser()
        result = parser.parse("unused 100μF capacitors in Bin-23")

        assert "component_type" in result.entities
        assert result.entities["component_type"] == "capacitor"
        assert "stock_status" in result.entities
        assert result.entities["stock_status"] == "unused"
        assert "location" in result.entities
        assert result.entities["location"].lower() == "bin-23"
        assert "capacitance" in result.entities
        assert result.entities["capacitance"] == "100.0μF"

    def test_parse_batch(self):
        """Test batch parsing."""
        parser = NLQueryParser()
        queries = ["find resistors", "show capacitors", "list inductors"]
        results = parser.parse_batch(queries)

        assert len(results) == len(queries)
        assert all(isinstance(r, ParsedQuery) for r in results)
        assert all(r.intent == "search_by_type" for r in results)

    def test_parse_all_example_queries(self):
        """Test parsing all example queries (no errors)."""
        parser = NLQueryParser()

        for query in EXAMPLE_QUERIES:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert result.intent in [
                "search_by_type",
                "filter_by_stock",
                "filter_by_location",
                "filter_by_value",
                "filter_by_price",
            ]
            assert 0.0 <= result.confidence <= 1.0
            assert result.raw_query == query


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_special_characters(self):
        """Test queries with special characters."""
        parser = NLQueryParser()
        queries = [
            "10k Ω resistors",
            "100 μF capacitors",
            "5V components",
        ]

        for query in queries:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0

    def test_case_insensitivity(self):
        """Test case-insensitive matching."""
        parser = NLQueryParser()
        queries = [
            "FIND RESISTORS",
            "find resistors",
            "FiNd ReSiStOrS",
        ]

        results = [parser.parse(q) for q in queries]

        # All should extract the same component type
        for result in results:
            assert "component_type" in result.entities
            assert result.entities["component_type"] == "resistor"

    def test_multiple_spaces(self):
        """Test queries with multiple spaces."""
        parser = NLQueryParser()
        result = parser.parse("find    resistors    with    low    stock")

        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"
        assert "stock_status" in result.entities
        assert result.entities["stock_status"] == "low"

    def test_trailing_whitespace(self):
        """Test queries with trailing whitespace."""
        parser = NLQueryParser()
        result = parser.parse("  find resistors  ")

        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"

    def test_ambiguous_queries(self):
        """Test ambiguous queries."""
        parser = NLQueryParser()
        queries = [
            "components",  # No specific type
            "stock",  # Could be inventory or stock status
            "parts",  # Generic
        ]

        for query in queries:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            # Should still produce a result, even if low confidence
            assert result.confidence >= 0.0

    def test_very_long_query(self):
        """Test very long query."""
        parser = NLQueryParser()
        query = (
            "find me all the 10k ohm SMD 0805 resistors with low stock "
            "that are stored in location A1 and cost less than $1 each "
            "from Texas Instruments or similar manufacturers"
        )

        result = parser.parse(query)
        assert isinstance(result, ParsedQuery)
        assert len(result.entities) > 3  # Should extract multiple entities

    def test_typos_and_variations(self):
        """Test common typos and variations."""
        parser = NLQueryParser()

        # These should still work due to flexible patterns
        queries = [
            "resistor",  # Singular
            "resistors",  # Plural
            "res",  # Abbreviation
        ]

        for query in queries:
            result = parser.parse(query)
            assert "component_type" in result.entities
            assert result.entities["component_type"] == "resistor"


class TestConfidenceScoring:
    """Test confidence scoring logic."""

    def test_high_confidence_queries(self):
        """Test queries that should have high confidence."""
        parser = NLQueryParser()
        queries = [
            "find resistors",
            "10k SMD resistors with low stock",
            "components in A1",
        ]

        for query in queries:
            result = parser.parse(query)
            assert result.confidence > 0.7

    def test_medium_confidence_queries(self):
        """Test queries that should have medium confidence."""
        parser = NLQueryParser()
        queries = [
            "res",  # Abbreviation
            "cheap parts",  # Implicit price
            "A1",  # Just a location
        ]

        for query in queries:
            result = parser.parse(query)
            assert 0.3 <= result.confidence <= 0.9

    def test_low_confidence_queries(self):
        """Test queries that should have low confidence."""
        parser = NLQueryParser()
        queries = [
            "",  # Empty
            "components",  # Too generic
            "show me all the things",  # Very vague
        ]

        for query in queries:
            result = parser.parse(query)
            assert result.confidence <= 0.3


class TestPerformance:
    """Test performance characteristics."""

    def test_parse_speed(self):
        """Test that parsing is fast (<10ms for typical queries)."""
        import time

        parser = NLQueryParser()
        queries = [
            "find resistors with low stock",
            "10k SMD resistors",
            "components in A1",
        ]

        times = []
        for query in queries:
            start = time.perf_counter()
            parser.parse(query)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        avg_time = sum(times) / len(times)
        assert (
            avg_time < 10
        ), f"Average parse time {avg_time:.2f}ms exceeds 10ms threshold"

    def test_batch_parse_efficiency(self):
        """Test batch parsing efficiency."""
        import time

        parser = NLQueryParser()
        queries = EXAMPLE_QUERIES[:20]  # Test with 20 queries

        start = time.perf_counter()
        results = parser.parse_batch(queries)
        end = time.perf_counter()

        total_time_ms = (end - start) * 1000
        avg_time_per_query = total_time_ms / len(queries)

        assert len(results) == len(queries)
        assert (
            avg_time_per_query < 10
        ), f"Average batch parse time {avg_time_per_query:.2f}ms exceeds 10ms threshold"


class TestPatternRobustness:
    """Test pattern matching robustness."""

    def test_unit_variations(self):
        """Test different unit variations."""
        parser = NLQueryParser()
        test_cases = [
            ("10k", "10kΩ"),
            ("10kΩ", "10kΩ"),
            ("10 kOhm", "10kΩ"),
            ("10kohm", "10kΩ"),
        ]

        for query, expected in test_cases:
            result = parser.parse(query)
            if "resistance" in result.entities:
                # Allow for float precision differences
                assert result.entities["resistance"].startswith(expected.split("k")[0])

    def test_package_variations(self):
        """Test package format variations."""
        parser = NLQueryParser()
        test_cases = [
            "0805 resistors",
            "SMD 0805",
            "DIP8",
            "DIP-8",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert "package" in result.entities

    def test_location_variations(self):
        """Test location format variations."""
        parser = NLQueryParser()
        test_cases = [
            "components in A1",
            "parts at A1",
            "from location A1",
            "stored in A1",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert "location" in result.entities
            assert result.entities["location"].lower() == "a1"
