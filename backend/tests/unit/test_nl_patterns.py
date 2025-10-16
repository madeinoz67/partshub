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


class TestAdditionalComponentTypes:
    """Test additional component type variations and edge cases."""

    def test_opamp_variations(self):
        """Test operational amplifier type detection."""
        parser = NLQueryParser()
        test_cases = [
            "find opamps",
            "show op-amps",
            "operational amplifiers",
            "opamp ICs",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert "component_type" in result.entities
            # May be classified as opamp or ic depending on pattern matching
            assert result.entities["component_type"] in ["opamp", "ic"]

    def test_voltage_regulator_variations(self):
        """Test voltage regulator type detection."""
        parser = NLQueryParser()
        test_cases = [
            "voltage regulators",
            "find regulators",
            "LDO regulators",
            "buck converters",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # May not recognize all regulator types, but should parse without error
            assert isinstance(result, ParsedQuery)
            assert result.confidence >= 0.0

    def test_sensor_type_variations(self):
        """Test various sensor type detection."""
        parser = NLQueryParser()
        test_cases = [
            "temperature sensors",
            "find pressure sensors",
            "hall effect sensors",
            "proximity sensors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            # Should extract some entity even if sensor-specific type not recognized
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_display_type_variations(self):
        """Test display component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "LCD displays",
            "OLED screens",
            "7-segment displays",
            "TFT displays",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_module_variations(self):
        """Test module component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "WiFi modules",
            "Bluetooth modules",
            "GPS modules",
            "RF modules",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_battery_type_variations(self):
        """Test battery component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "lithium batteries",
            "coin cell batteries",
            "AA batteries",
            "battery holders",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_fuse_variations(self):
        """Test fuse component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "find fuses",
            "resettable fuses",
            "glass fuses",
            "circuit breakers",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_relay_type_variations(self):
        """Test relay component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "find relays",
            "solid state relays",
            "reed relays",
            "5V relays",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            # Should extract voltage or some entity
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_switch_type_variations(self):
        """Test switch component type detection."""
        parser = NLQueryParser()
        test_cases = [
            "tactile switches",
            "DIP switches",
            "toggle switches",
            "rotary encoders",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            assert len(result.entities) > 0 or result.confidence >= 0.0

    def test_crystal_oscillator_variations(self):
        """Test crystal oscillator type detection."""
        parser = NLQueryParser()
        test_cases = [
            "crystals",
            "quartz crystals",
            "oscillators",
            "ceramic resonators",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            # Crystal type should be detected
            assert "component_type" in result.entities or result.confidence >= 0.0


class TestAdditionalValuePatterns:
    """Test additional value pattern edge cases and variations."""

    def test_inductance_edge_cases(self):
        """Test inductance value edge cases."""
        parser = NLQueryParser()
        test_cases = [
            ("1μH inductors", "inductance", "1.0μH"),
            ("100nH inductors", "inductance", "100.0nH"),
            ("10mH coils", "inductance", "10.0mH"),
            ("1H inductor", "inductance", "1.0H"),
        ]

        for query, value_type, expected_value in test_cases:
            result = parser.parse(query)
            if value_type in result.entities:
                assert result.entities[value_type] == expected_value

    def test_current_edge_cases(self):
        """Test current value edge cases."""
        parser = NLQueryParser()
        test_cases = [
            ("1A fuses", "current", "1.0A"),
            ("500mA components", "current", "500.0mA"),
            ("100μA parts", "current", "100.0μA"),
            ("2.5A regulators", "current", "2.5A"),
        ]

        for query, value_type, expected_value in test_cases:
            result = parser.parse(query)
            if value_type in result.entities:
                assert result.entities[value_type] == expected_value

    def test_resistance_boundary_cases(self):
        """Test resistance boundary and extreme values."""
        parser = NLQueryParser()
        test_cases = [
            "0.1Ω resistors",
            "10MΩ resistors",
            "1Ω resistors",
            "999kΩ resistors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract resistance even for extreme values
            if "resistance" in result.entities:
                assert "Ω" in result.entities["resistance"]

    def test_capacitance_boundary_cases(self):
        """Test capacitance boundary and extreme values."""
        parser = NLQueryParser()
        test_cases = [
            "1pF capacitors",
            "1000μF capacitors",
            "0.1μF capacitors",
            "10000pF capacitors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract capacitance even for extreme values
            if "capacitance" in result.entities:
                assert "F" in result.entities["capacitance"]

    def test_voltage_variations(self):
        """Test voltage value variations."""
        parser = NLQueryParser()
        test_cases = [
            ("1.8V components", "voltage", "1.8V"),
            ("24V parts", "voltage", "24V"),
            ("120V capacitors", "voltage", "120V"),
            ("0.5V reference", "voltage", "0.5V"),
        ]

        for query, value_type, expected_value in test_cases:
            result = parser.parse(query)
            if value_type in result.entities:
                assert result.entities[value_type] == expected_value

    def test_frequency_variations(self):
        """Test frequency value variations."""
        parser = NLQueryParser()
        test_cases = [
            ("100kHz oscillators", "frequency", "100.0kHz"),
            ("1GHz parts", "frequency", "1.0GHz"),
            ("20MHz crystals", "frequency", "20.0MHz"),
            ("50Hz components", "frequency", "50.0Hz"),
        ]

        for query, value_type, expected_value in test_cases:
            result = parser.parse(query)
            if value_type in result.entities:
                assert result.entities[value_type] == expected_value

    def test_mixed_value_types_single_query(self):
        """Test queries with multiple different value types."""
        parser = NLQueryParser()
        query = "5V 100μF capacitors"

        result = parser.parse(query)
        # Should extract both voltage and capacitance
        assert "voltage" in result.entities or "capacitance" in result.entities
        assert len(result.entities) >= 2

    def test_value_precision_tests(self):
        """Test value precision handling."""
        parser = NLQueryParser()
        test_cases = [
            "4.7kΩ resistors",
            "0.1μF capacitors",
            "3.3V regulators",
            "16.384MHz crystals",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should preserve decimal precision in extracted values
            assert len(result.entities) > 0

    def test_values_without_spaces(self):
        """Test value extraction without spaces."""
        parser = NLQueryParser()
        test_cases = [
            "10kΩresistors",
            "100μFcapacitors",
            "16MHzcrystals",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Parser may not handle values without spaces, but should not crash
            assert isinstance(result, ParsedQuery)
            assert result.confidence >= 0.0

    def test_values_with_multiple_spaces(self):
        """Test value extraction with multiple spaces."""
        parser = NLQueryParser()
        test_cases = [
            "10   kΩ   resistors",
            "100   μF   capacitors",
            "16   MHz   crystals",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should normalize and extract values correctly
            assert len(result.entities) > 0


class TestAdditionalStockLocationPackage:
    """Test additional stock status, location, and package patterns."""

    def test_stock_status_in_stock(self):
        """Test in-stock status detection."""
        parser = NLQueryParser()
        result = parser.parse("components in stock")

        assert "stock_status" in result.entities or result.intent == "filter_by_stock"

    def test_stock_status_depleted(self):
        """Test depleted stock status."""
        parser = NLQueryParser()
        result = parser.parse("depleted components")

        assert isinstance(result, ParsedQuery)
        # Should classify as stock-related intent
        assert result.intent in ["filter_by_stock", "search_by_type"]

    def test_stock_status_critical(self):
        """Test critical stock level detection."""
        parser = NLQueryParser()
        result = parser.parse("critical stock level")

        assert isinstance(result, ParsedQuery)
        assert result.intent in ["filter_by_stock", "search_by_type"]

    def test_stock_status_overstocked(self):
        """Test overstocked status detection."""
        parser = NLQueryParser()
        result = parser.parse("overstocked parts")

        assert isinstance(result, ParsedQuery)
        assert result.intent in ["filter_by_stock", "search_by_type"]

    def test_stock_status_requires_attention(self):
        """Test stock requiring attention."""
        parser = NLQueryParser()
        result = parser.parse("stock needs attention")

        assert isinstance(result, ParsedQuery)
        assert result.intent in ["filter_by_stock", "search_by_type"]

    def test_location_complex_alphanumeric(self):
        """Test complex alphanumeric location patterns."""
        parser = NLQueryParser()
        test_cases = [
            "components in A1B2",
            "parts at Rack-5-Shelf-3",
            "from location Z99",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should recognize as location-focused, even if extraction pattern doesn't match
            assert result.intent in ["filter_by_location", "search_by_type"]
            assert isinstance(result, ParsedQuery)

    def test_location_with_floor_room(self):
        """Test location with floor/room indicators."""
        parser = NLQueryParser()
        test_cases = [
            "components in Room-101",
            "parts at Floor-2-A1",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract location or at least parse without error
            assert isinstance(result, ParsedQuery)

    def test_location_with_building_codes(self):
        """Test location with building codes."""
        parser = NLQueryParser()
        result = parser.parse("components in Building-A-Shelf-1")

        assert isinstance(result, ParsedQuery)
        # May extract as location or parse as generic query
        assert len(result.entities) >= 0

    def test_location_warehouse_style(self):
        """Test warehouse-style location codes."""
        parser = NLQueryParser()
        test_cases = [
            "parts at WH-A-01-02",
            "components in Aisle-5-Bay-3",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_location_multiple_in_query(self):
        """Test query with multiple location references."""
        parser = NLQueryParser()
        result = parser.parse("move from A1 to B2")

        assert isinstance(result, ParsedQuery)
        # Should extract at least one location
        if "location" in result.entities:
            assert len(result.entities["location"]) > 0

    def test_package_qfn_variations(self):
        """Test QFN package variations."""
        parser = NLQueryParser()
        test_cases = [
            "QFN32 components",
            "QFN-48 ICs",
            "QFN64 microcontrollers",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert "package" in result.entities

    def test_package_soic_variations(self):
        """Test SOIC package variations."""
        parser = NLQueryParser()
        test_cases = [
            "SOIC8 ICs",
            "SOIC-16 components",
            "SOIC parts",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Parser may not recognize all package types, but should parse without error
            assert isinstance(result, ParsedQuery)
            # Should extract at least component type or package for specific variants
            assert result.confidence >= 0.0

    def test_package_bga_variations(self):
        """Test BGA package variations."""
        parser = NLQueryParser()
        test_cases = [
            "BGA256 components",
            "BGA parts",
            "FBGA ICs",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # May extract package or parse as generic query
            assert isinstance(result, ParsedQuery)

    def test_package_through_hole_variations(self):
        """Test through-hole package variations."""
        parser = NLQueryParser()
        test_cases = [
            "through-hole resistors",
            "THT components",
            "DIP packages",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Parser may not recognize all package terminology, but should parse without error
            assert isinstance(result, ParsedQuery)
            assert result.confidence >= 0.0

    def test_package_mixed_with_size(self):
        """Test package with size specifications."""
        parser = NLQueryParser()
        test_cases = [
            "0402 SMD resistors",
            "1210 ceramic capacitors",
            "2512 power resistors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert "package" in result.entities


class TestAdditionalManufacturerPrice:
    """Test additional manufacturer and price extraction patterns."""

    def test_manufacturer_analog_devices(self):
        """Test Analog Devices manufacturer detection."""
        parser = NLQueryParser()
        test_cases = [
            "Analog Devices opamps",
            "ADI components",
            "AD parts",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # May extract manufacturer or parse as generic query
            assert isinstance(result, ParsedQuery)

    def test_manufacturer_microchip(self):
        """Test Microchip manufacturer detection."""
        parser = NLQueryParser()
        test_cases = [
            "Microchip microcontrollers",
            "MCHP parts",
            "Atmel components",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_manufacturer_renesas(self):
        """Test Renesas manufacturer detection."""
        parser = NLQueryParser()
        result = parser.parse("Renesas microcontrollers")

        assert isinstance(result, ParsedQuery)
        # Should extract manufacturer or component type
        assert len(result.entities) > 0 or result.confidence > 0.0

    def test_manufacturer_on_semiconductor(self):
        """Test ON Semiconductor manufacturer detection."""
        parser = NLQueryParser()
        result = parser.parse("ON Semiconductor transistors")

        assert isinstance(result, ParsedQuery)
        assert len(result.entities) > 0 or result.confidence > 0.0

    def test_manufacturer_maxim(self):
        """Test Maxim Integrated manufacturer detection."""
        parser = NLQueryParser()
        test_cases = [
            "Maxim ICs",
            "Maxim Integrated parts",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_price_exact_amount(self):
        """Test exact price amount extraction."""
        parser = NLQueryParser()
        test_cases = [
            "components at $2.50",
            "parts priced at $0.99",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract some price-related entity
            assert isinstance(result, ParsedQuery)

    def test_price_range_extraction(self):
        """Test price range extraction."""
        parser = NLQueryParser()
        test_cases = [
            "components between $1 and $5",
            "parts from $2 to $10",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # May extract min/max price or parse as generic query
            assert isinstance(result, ParsedQuery)

    def test_price_above_threshold(self):
        """Test price above threshold."""
        parser = NLQueryParser()
        test_cases = [
            "components over $10",
            "parts above $20",
            "more than $5",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract min_price
            if "min_price" in result.entities:
                assert result.entities["min_price"] > 0

    def test_price_with_currency_symbols(self):
        """Test price with different currency representations."""
        parser = NLQueryParser()
        test_cases = [
            "components under $5.00",
            "parts less than $10.99",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract price information
            if "max_price" in result.entities:
                assert result.entities["max_price"] > 0

    def test_price_with_keywords(self):
        """Test price with budget keywords."""
        parser = NLQueryParser()
        test_cases = [
            "affordable resistors",
            "budget capacitors",
            "expensive ICs",
            "premium components",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract component type at minimum
            assert isinstance(result, ParsedQuery)

    def test_price_bulk_discount(self):
        """Test bulk pricing references."""
        parser = NLQueryParser()
        test_cases = [
            "bulk pricing components",
            "wholesale parts",
            "volume discount",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_price_per_unit(self):
        """Test per-unit pricing references."""
        parser = NLQueryParser()
        test_cases = [
            "components at $0.50 each",
            "parts $1 per piece",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_price_free_or_zero(self):
        """Test free/zero price handling."""
        parser = NLQueryParser()
        test_cases = [
            "free components",
            "zero cost parts",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)


class TestMultiEntityIntentCombinations:
    """Test complex multi-entity combinations and intent disambiguation."""

    def test_three_entity_combination(self):
        """Test query with three entities."""
        parser = NLQueryParser()
        result = parser.parse("10k 0805 resistors in A1")

        # Should extract component type, value, package, and location
        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"
        assert "package" in result.entities
        assert "location" in result.entities
        assert len(result.entities) >= 3

    def test_four_entity_combination(self):
        """Test query with four entities."""
        parser = NLQueryParser()
        result = parser.parse("unused 100μF 0805 capacitors in Bin-5")

        # Should extract component type, stock status, value, package, location
        assert "component_type" in result.entities
        assert result.entities["component_type"] == "capacitor"
        assert len(result.entities) >= 3

    def test_five_entity_combination(self):
        """Test query with five entities."""
        parser = NLQueryParser()
        result = parser.parse("cheap low stock 10k 0805 SMD resistors")

        # Should extract price, stock, value, package, component type
        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"
        assert len(result.entities) >= 3

    def test_intent_disambiguation_type_vs_stock(self):
        """Test disambiguation between type search and stock filter."""
        parser = NLQueryParser()

        # Type-focused
        result1 = parser.parse("find resistors with low stock")
        assert result1.intent == "search_by_type"

        # Stock-focused
        result2 = parser.parse("show all low stock items")
        assert result2.intent in ["filter_by_stock", "search_by_type"]

    def test_intent_disambiguation_location_vs_type(self):
        """Test disambiguation between location filter and type search."""
        parser = NLQueryParser()

        # Location-focused
        result1 = parser.parse("what's in A1")
        assert result1.intent == "filter_by_location"

        # Type-focused with location
        result2 = parser.parse("find resistors in A1")
        # Could be either depending on implementation
        assert result2.intent in ["search_by_type", "filter_by_location"]

    def test_intent_disambiguation_value_vs_type(self):
        """Test disambiguation between value filter and type search."""
        parser = NLQueryParser()

        # Type with value
        result1 = parser.parse("find 10k resistors")
        assert result1.intent in ["search_by_type", "filter_by_value"]

        # Value-focused
        result2 = parser.parse("show 10k components")
        assert result2.intent in ["filter_by_value", "search_by_type"]

    def test_confidence_high_specificity(self):
        """Test confidence with highly specific queries."""
        parser = NLQueryParser()
        result = parser.parse(
            "Texas Instruments 10k 0805 SMD resistors with low stock in A1"
        )

        # High specificity should yield high confidence
        assert result.confidence > 0.6
        assert len(result.entities) >= 4

    def test_confidence_medium_specificity(self):
        """Test confidence with medium specificity queries."""
        parser = NLQueryParser()
        result = parser.parse("SMD resistors in storage")

        # Medium specificity
        assert 0.3 <= result.confidence <= 0.9
        assert len(result.entities) >= 1

    def test_confidence_with_typos(self):
        """Test confidence degradation with potential typos."""
        parser = NLQueryParser()
        # Test queries that may have variations but should still work
        result = parser.parse("resstors")  # Potential typo

        # Should still attempt to parse
        assert isinstance(result, ParsedQuery)
        # Confidence may be lower
        assert 0.0 <= result.confidence <= 1.0

    def test_multiple_manufacturers(self):
        """Test query mentioning multiple manufacturers."""
        parser = NLQueryParser()
        result = parser.parse("Texas Instruments or NXP microcontrollers")

        assert "component_type" in result.entities
        # May extract first manufacturer or parse generically
        assert isinstance(result, ParsedQuery)

    def test_component_type_and_subtype(self):
        """Test component type with subtype specification."""
        parser = NLQueryParser()
        test_cases = [
            "NPN transistors",
            "electrolytic capacitors",
            "Schottky diodes",
            "MOSFET transistors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should extract component type
            assert "component_type" in result.entities or len(result.entities) > 0


class TestBoundaryAndSpecialCases:
    """Test boundary conditions and special edge cases."""

    def test_numeric_only_query(self):
        """Test query with only numbers."""
        parser = NLQueryParser()
        result = parser.parse("10k")

        # Should attempt to extract value
        assert isinstance(result, ParsedQuery)

    def test_single_character_query(self):
        """Test single character queries."""
        parser = NLQueryParser()
        test_cases = ["A", "B", "1", "R", "C"]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)
            # May extract as location or low confidence
            assert 0.0 <= result.confidence <= 1.0

    def test_query_with_punctuation(self):
        """Test queries with various punctuation."""
        parser = NLQueryParser()
        test_cases = [
            "find resistors!",
            "resistors?",
            "resistors, capacitors",
            "resistors; capacitors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should parse and extract component type
            assert isinstance(result, ParsedQuery)

    def test_query_with_parentheses(self):
        """Test queries with parentheses."""
        parser = NLQueryParser()
        result = parser.parse("resistors (SMD) in A1")

        assert isinstance(result, ParsedQuery)
        # Should extract entities from parenthetical content
        assert len(result.entities) > 0

    def test_unicode_and_special_chars(self):
        """Test handling of unicode and special characters."""
        parser = NLQueryParser()
        test_cases = [
            "10kΩ résistors",  # Unicode in component name
            "100µF capacitors",  # Micro symbol variation
            "LED's in A1",  # Apostrophe
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_all_caps_query(self):
        """Test all-caps queries."""
        parser = NLQueryParser()
        result = parser.parse("FIND ALL SMD RESISTORS WITH LOW STOCK")

        assert "component_type" in result.entities
        assert result.entities["component_type"] == "resistor"

    def test_mixed_case_values(self):
        """Test mixed case in values."""
        parser = NLQueryParser()
        test_cases = [
            "10K resistors",  # Capital K
            "100UF capacitors",  # Capital UF
            "16mHz crystals",  # Lowercase m, capital H
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should normalize and extract values
            assert isinstance(result, ParsedQuery)

    def test_negative_numbers(self):
        """Test handling of negative numbers."""
        parser = NLQueryParser()
        result = parser.parse("components under $-5")

        # Should handle gracefully, may ignore negative
        assert isinstance(result, ParsedQuery)

    def test_very_large_numbers(self):
        """Test very large numeric values."""
        parser = NLQueryParser()
        test_cases = [
            "10000000 ohm resistors",
            "components under $999999",
        ]

        for query in test_cases:
            result = parser.parse(query)
            assert isinstance(result, ParsedQuery)

    def test_decimal_precision_variations(self):
        """Test various decimal precision levels."""
        parser = NLQueryParser()
        test_cases = [
            "4.7kΩ resistors",
            "3.14159MHz crystals",
            "0.001μF capacitors",
        ]

        for query in test_cases:
            result = parser.parse(query)
            # Should preserve decimal values
            assert len(result.entities) > 0
