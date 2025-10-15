"""
Natural Language Query Pattern Grammar for PartsHub Component Search.

Provides pattern-based parsing to convert user queries like "find resistors with low stock"
into structured search parameters without requiring external NLP libraries.

Uses regex patterns for:
- Intent classification (5 intent categories)
- Entity extraction (component types, stock status, locations, values, packages, manufacturers)
- Confidence scoring based on match quality

Example usage:
    >>> parser = NLQueryParser()
    >>> result = parser.parse("find resistors with low stock")
    >>> print(result)
    {
        "intent": "search_by_type",
        "entities": {
            "component_type": "resistor",
            "stock_status": "low"
        },
        "confidence": 0.85
    }
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Structured result from natural language query parsing."""

    intent: str  # Primary intent category
    entities: dict[str, Any] = field(default_factory=dict)  # Extracted entities
    confidence: float = 0.0  # Confidence score 0.0-1.0
    raw_query: str = ""  # Original query string


# ============================================================================
# Entity Pattern Definitions
# ============================================================================

# Component types with common variations and abbreviations
COMPONENT_TYPES = {
    r"\b(resistors?|res|r)\b": "resistor",
    r"\b(capacitors?|caps?|c)\b": "capacitor",
    r"\b(inductors?|ind|l)\b": "inductor",
    r"\b(ics?|integrated circuits?|chips?)\b": "ic",
    r"\b(microcontrollers?|mcus?|micros?)\b": "microcontroller",
    r"\b(diodes?|d)\b": "diode",
    r"\b(transistors?|trans|q)\b": "transistor",
    r"\b(leds?|light[- ]?emitting[- ]?diodes?)\b": "led",
    r"\b(connectors?|conn)\b": "connector",
    r"\b(crystals?|xtals?|oscillators?)\b": "crystal",
    r"\b(switches?|sw)\b": "switch",
    r"\b(relays?)\b": "relay",
    r"\b(fuses?)\b": "fuse",
    r"\b(sensors?)\b": "sensor",
    r"\b(displays?|lcds?|oleds?)\b": "display",
    r"\b(modules?|boards?)\b": "module",
    r"\b(batteries?)\b": "battery",
    r"\b(voltage regulators?|regulators?|vreg)\b": "voltage_regulator",
    r"\b(opamps?|op[- ]?amps?|operational amplifiers?)\b": "opamp",
}

# Stock status keywords (use \s+ for flexible whitespace matching)
STOCK_STATUS = {
    r"\b(low[- ]?\s*stock|running\s+low|almost\s+out|nearly\s+out|few\s+left)\b": "low",
    r"\b(out\s+of\s+stock|no\s+stock|empty|none|depleted)\b": "out",
    r"\b(available|in[- ]?\s*stock|have|got|stocked)\b": "available",
    r"\b(unused|never\s+used|brand\s+new|new)\b": "unused",
    r"\b(need\s+reorder|need\s+to\s+order|should\s+order|reorder)\b": "reorder",
}

# Storage location patterns (alphanumeric locations like A1, Bin-23, Shelf-A)
LOCATION_PATTERNS = {
    # Simple alphanumeric: A1, B2, C3
    r"\b([A-Z]\d+)\b": "location_code",
    # Hyphenated: Bin-23, Shelf-A, Cabinet-1
    r"\b((?:bin|shelf|drawer|cabinet|box|bag)[- ]\w+)\b": "location_name",
    # In/at/from location
    r"\b(?:in|at|from|stored in)\s+([A-Z]\d+|(?:bin|shelf|drawer|cabinet|box|bag)[- ]\w+)\b": "location_ref",
}

# Value patterns with units (10k, 100μF, 5V, 3.3V)
VALUE_PATTERNS = [
    # Resistance with units: 10kΩ, 10 kOhm, 100R (R must be word-bounded)
    (
        r"\b(\d+\.?\d*)\s*([kKmM]?)(ohm|Ω)\b",
        "resistance",
        lambda v, u: normalize_resistance(v, u),
    ),
    # Resistance with R suffix: 100R, 10kR (R must be followed by non-letter)
    (
        r"\b(\d+\.?\d*)\s*([kKmM]?)([rR])(?!\w)",
        "resistance",
        lambda v, u: normalize_resistance(v, u),
    ),
    # Resistance with bare k/M suffix: 10k, 4.7k, 1M (only if NOT followed by a letter)
    (
        r"\b(\d+\.?\d*)\s*([kKmM])(?!\w)",
        "resistance",
        lambda v, u: normalize_resistance(v, u),
    ),
    # Capacitance: 100μF, 10nF, 1pF, 100uF
    (
        r"\b(\d+\.?\d*)\s*([pnuμµm]?)(f|F|farad)s?\b",
        "capacitance",
        lambda v, u: normalize_capacitance(v, u),
    ),
    # Voltage: 5V, 3.3V, 12V
    (r"\b(\d+\.?\d*)\s*v(?:olt)?s?\b", "voltage", lambda v, _: f"{v}V"),
    # Inductance: 10μH, 100nH, 1mH
    (
        r"\b(\d+\.?\d*)\s*([pnuμµm]?)(h|H|henry)s?\b",
        "inductance",
        lambda v, u: normalize_inductance(v, u),
    ),
    # Current: 1A, 500mA, 100μA
    (
        r"\b(\d+\.?\d*)\s*([munμµ]?)(a|A|amp)s?\b",
        "current",
        lambda v, u: normalize_current(v, u),
    ),
    # Frequency: 16MHz, 32kHz, 1GHz
    (
        r"\b(\d+\.?\d*)\s*([kKmMgG]?)(hz|Hz)s?\b",
        "frequency",
        lambda v, u: normalize_frequency(v, u),
    ),
]

# Package/footprint patterns
PACKAGE_PATTERNS = {
    # SMD imperial: 0805, 1206, 0603, etc.
    r"\b(0201|0402|0603|0805|1206|1210|1812|2010|2512)\b": "smd_imperial",
    # SMD metric: 0603M, 1005M, etc.
    r"\b(\d{4}m)\b": "smd_metric",
    # DIP packages: DIP8, DIP-14, DIP16
    r"\b(dip[- ]?\d+)\b": "dip",
    # Surface mount packages: SOT-23, SOT-223, SOIC8, TQFP32, QFN48
    r"\b(sot[- ]\d+|soic[- ]?\d+|ssop[- ]?\d+|tqfp[- ]?\d+|qfn[- ]?\d+|qfp[- ]?\d+)\b": "surface_mount",
    # Through-hole: TO-220, TO-92, TO-3
    r"\b(to[- ]\d+)\b": "through_hole",
    # Generic SMD/THT
    r"\b(smd|smt|through[- ]?hole|tht)\b": "mount_type",
}

# Manufacturer patterns (common manufacturers)
MANUFACTURERS = {
    r"\b(texas instruments?|ti)\b": "Texas Instruments",
    r"\b(infineon)\b": "Infineon",
    r"\b(nxp)\b": "NXP",
    r"\b(stmicroelectronics?|st)\b": "STMicroelectronics",
    r"\b(analog devices?|adi)\b": "Analog Devices",
    r"\b(linear technology|linear|lt)\b": "Linear Technology",
    r"\b(maxim integrated?|maxim)\b": "Maxim Integrated",
    r"\b(microchip)\b": "Microchip",
    r"\b(atmel)\b": "Atmel",
    r"\b(onsemi|on semiconductor)\b": "ON Semiconductor",
    r"\b(vishay)\b": "Vishay",
    r"\b(murata)\b": "Murata",
    r"\b(samsung)\b": "Samsung",
    r"\b(yageo)\b": "Yageo",
    r"\b(kemet)\b": "KEMET",
    r"\b(tdk)\b": "TDK",
    r"\b(panasonic)\b": "Panasonic",
    r"\b(rohm)\b": "ROHM",
    r"\b(bourns)\b": "Bourns",
    r"\b(diodes inc|diodes)\b": "Diodes Inc",
}

# Price patterns
PRICE_PATTERNS = [
    # Under/less than: "under $1", "less than $5", "below $10"
    (r"\b(?:under|less than|below|cheaper than)\s*\$?\s*(\d+\.?\d*)\b", "max_price"),
    # Over/more than: "over $5", "more than $10", "above $20"
    (r"\b(?:over|more than|above|pricier than)\s*\$?\s*(\d+\.?\d*)\b", "min_price"),
    # Exact: "exactly $5", "$5", "5 dollars"
    (r"\b(?:exactly\s*)?\$?\s*(\d+\.?\d*)\s*dollars?\b", "exact_price"),
    # Range: "$1 to $5", "between $1 and $5"
    (
        r"\b(?:between\s*)?\$?\s*(\d+\.?\d*)\s*(?:to|and|-)\s*\$?\s*(\d+\.?\d*)\b",
        "price_range",
    ),
]

# Keywords that suggest "cheap" without specific price
CHEAP_KEYWORDS = r"\b(cheap|inexpensive|affordable|budget|low[- ]?cost)\b"


# ============================================================================
# Unit Normalization Functions
# ============================================================================


def normalize_resistance(value: str, prefix: str) -> str:
    """Normalize resistance value to standard format."""
    val = float(value)
    prefix_lower = prefix.lower()

    if prefix_lower in ["k", "k"]:
        return f"{val}kΩ"
    elif prefix_lower in ["m", "m"]:
        return f"{val}MΩ"
    elif prefix_lower == "":
        return f"{val}Ω"
    return f"{val}{prefix}Ω"


def normalize_capacitance(value: str, prefix: str) -> str:
    """Normalize capacitance value to standard format."""
    val = float(value)
    prefix_lower = prefix.lower()

    prefix_map = {
        "p": "pF",
        "n": "nF",
        "u": "μF",
        "μ": "μF",
        "µ": "μF",
        "m": "mF",
        "": "F",
    }

    suffix = prefix_map.get(prefix_lower, f"{prefix}F")
    return f"{val}{suffix}"


def normalize_inductance(value: str, prefix: str) -> str:
    """Normalize inductance value to standard format."""
    val = float(value)
    prefix_lower = prefix.lower()

    prefix_map = {
        "p": "pH",
        "n": "nH",
        "u": "μH",
        "μ": "μH",
        "µ": "μH",
        "m": "mH",
        "": "H",
    }

    suffix = prefix_map.get(prefix_lower, f"{prefix}H")
    return f"{val}{suffix}"


def normalize_current(value: str, prefix: str) -> str:
    """Normalize current value to standard format."""
    val = float(value)
    prefix_lower = prefix.lower()

    prefix_map = {
        "m": "mA",
        "u": "μA",
        "μ": "μA",
        "µ": "μA",
        "n": "nA",
        "": "A",
    }

    suffix = prefix_map.get(prefix_lower, f"{prefix}A")
    return f"{val}{suffix}"


def normalize_frequency(value: str, prefix: str) -> str:
    """Normalize frequency value to standard format."""
    val = float(value)
    prefix_lower = prefix.lower()

    prefix_map = {
        "k": "kHz",
        "m": "MHz",
        "g": "GHz",
        "": "Hz",
    }

    suffix = prefix_map.get(prefix_lower, f"{prefix}Hz")
    return f"{val}{suffix}"


# ============================================================================
# Intent Classification
# ============================================================================


class IntentClassifier:
    """Classify query intent based on pattern matching."""

    # Intent patterns with associated keywords
    INTENT_PATTERNS = {
        "search_by_type": [
            r"\b(find|search|show|list|get|display)\s+\w*\s*(resistor|capacitor|inductor|ic|transistor|diode|led|connector|crystal)",
            r"\b(resistor|capacitor|inductor|ic|transistor|diode|led|connector|crystal)s?\b",
        ],
        "filter_by_stock": [
            r"\b(low|out of|no|empty|available|in)\s+stock\b",
            r"\b(running low|almost out|nearly out|few left)\b",
            r"\b(unused|never used|brand new)\b",
        ],
        "filter_by_location": [
            r"\b(in|at|from|stored in)\s+([A-Z]\d+|(?:bin|shelf|drawer|cabinet|box|bag))",
            r"\b(location|storage|stored|where)\b",
        ],
        "filter_by_value": [
            r"\b\d+\.?\d*\s*[kKmM]?(ohm|Ω|r|R)\b",
            r"\b\d+\.?\d*\s*[pnuμµm]?[fF]\b",
            r"\b\d+\.?\d*\s*v(?:olt)?s?\b",
            r"\b(0201|0402|0603|0805|1206|dip[- ]?\d+|sot[- ]\d+)\b",
        ],
        "filter_by_price": [
            r"\b(under|less than|below|cheaper|cheap|inexpensive|affordable|budget)\b",
            r"\$\s*\d+\.?\d*",
            r"\b\d+\.?\d*\s*dollars?\b",
        ],
    }

    @classmethod
    def classify(cls, query: str) -> tuple[str, float]:
        """
        Classify query intent and return confidence score.

        Args:
            query: Query string to classify

        Returns:
            Tuple of (intent, confidence)
        """
        query_lower = query.lower()

        # Score each intent based on pattern matches
        intent_scores: dict[str, float] = {
            "search_by_type": 0.0,
            "filter_by_stock": 0.0,
            "filter_by_location": 0.0,
            "filter_by_value": 0.0,
            "filter_by_price": 0.0,
        }

        for intent, patterns in cls.INTENT_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matches += 1

            # Calculate score based on number of matching patterns
            if matches > 0:
                # Each match contributes to confidence, max out at 1.0
                intent_scores[intent] = min(1.0, matches / len(patterns) + 0.3)

        # Find highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])

        # If no strong intent match, default to search_by_type with low confidence
        if best_intent[1] < 0.3:
            return "search_by_type", 0.3

        return best_intent


# ============================================================================
# Entity Extractors
# ============================================================================


class EntityExtractor:
    """Extract entities from natural language queries."""

    @staticmethod
    def extract_component_type(query: str) -> tuple[str | None, float]:
        """Extract component type from query."""
        query_lower = query.lower()

        for pattern, component_type in COMPONENT_TYPES.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Higher confidence for longer, more specific matches
                confidence = min(1.0, 0.7 + len(match.group(0)) * 0.05)
                return component_type, confidence

        return None, 0.0

    @staticmethod
    def extract_stock_status(query: str) -> tuple[str | None, float]:
        """Extract stock status from query."""
        query_lower = query.lower()

        for pattern, status in STOCK_STATUS.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return status, 0.9  # High confidence for explicit stock keywords

        return None, 0.0

    @staticmethod
    def extract_location(query: str) -> tuple[str | None, float]:
        """Extract storage location from query."""
        query_lower = query.lower()

        for pattern, loc_type in LOCATION_PATTERNS.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Extract the actual location identifier
                location = match.group(1) if match.lastindex else match.group(0)
                return location.strip(), 0.85

        return None, 0.0

    @staticmethod
    def extract_value(query: str) -> tuple[dict[str, str], float]:
        """Extract component value (resistance, capacitance, voltage, etc.)."""
        values = {}
        max_confidence = 0.0

        for pattern, value_type, normalizer in VALUE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    # Pattern with value, prefix, and unit
                    value, prefix, unit = match.groups()
                    normalized = normalizer(value, prefix)
                elif len(match.groups()) == 2:
                    # Pattern with value and prefix (bare k/M suffix) or value and unit
                    value, prefix_or_unit = match.groups()
                    # Pass the second group as prefix for normalizer
                    normalized = normalizer(value, prefix_or_unit)
                else:
                    # Pattern with just value
                    value = match.group(1)
                    normalized = normalizer(value, "")

                values[value_type] = normalized
                max_confidence = max(max_confidence, 0.85)

        return values, max_confidence

    @staticmethod
    def extract_package(query: str) -> tuple[str | None, float]:
        """Extract package/footprint from query."""
        query_lower = query.lower()

        for pattern, package_type in PACKAGE_PATTERNS.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                package = match.group(1).upper()
                return package, 0.9  # High confidence for explicit package codes

        return None, 0.0

    @staticmethod
    def extract_manufacturer(query: str) -> tuple[str | None, float]:
        """Extract manufacturer from query."""
        query_lower = query.lower()

        for pattern, manufacturer in MANUFACTURERS.items():
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return manufacturer, 0.85

        return None, 0.0

    @staticmethod
    def extract_price(query: str) -> tuple[dict[str, Any], float]:
        """Extract price constraints from query."""
        price_info = {}

        # Check for "cheap" keywords first
        if re.search(CHEAP_KEYWORDS, query, re.IGNORECASE):
            price_info["max_price"] = 5.0  # Default cheap threshold
            return price_info, 0.7

        for pattern, price_type in PRICE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if price_type == "price_range":
                    price_info["min_price"] = float(match.group(1))
                    price_info["max_price"] = float(match.group(2))
                    return price_info, 0.9
                elif price_type in ["max_price", "min_price", "exact_price"]:
                    price_info[price_type] = float(match.group(1))
                    return price_info, 0.85

        return price_info, 0.0 if not price_info else 0.7


# ============================================================================
# Main Parser
# ============================================================================


class NLQueryParser:
    """
    Natural Language Query Parser for PartsHub component search.

    Converts natural language queries into structured search parameters
    using pattern-based parsing.

    Example:
        >>> parser = NLQueryParser()
        >>> result = parser.parse("find resistors with low stock")
        >>> print(result.intent)
        'search_by_type'
        >>> print(result.entities)
        {'component_type': 'resistor', 'stock_status': 'low'}
        >>> print(result.confidence)
        0.85
    """

    def __init__(self):
        """Initialize the parser."""
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse natural language query into structured format.

        Args:
            query: Natural language query string

        Returns:
            ParsedQuery object with intent, entities, and confidence score
        """
        if not query or not query.strip():
            return ParsedQuery(
                intent="search_by_type", entities={}, confidence=0.0, raw_query=query
            )

        # Classify intent
        intent, intent_confidence = self.intent_classifier.classify(query)

        # Extract entities
        entities = {}
        entity_confidences = []

        # Component type
        component_type, comp_conf = self.entity_extractor.extract_component_type(query)
        if component_type:
            entities["component_type"] = component_type
            entity_confidences.append(comp_conf)

        # Stock status
        stock_status, stock_conf = self.entity_extractor.extract_stock_status(query)
        if stock_status:
            entities["stock_status"] = stock_status
            entity_confidences.append(stock_conf)

        # Location
        location, loc_conf = self.entity_extractor.extract_location(query)
        if location:
            entities["location"] = location
            entity_confidences.append(loc_conf)

        # Value (resistance, capacitance, etc.)
        values, val_conf = self.entity_extractor.extract_value(query)
        if values:
            entities.update(values)
            entity_confidences.append(val_conf)

        # Package
        package, pkg_conf = self.entity_extractor.extract_package(query)
        if package:
            entities["package"] = package
            entity_confidences.append(pkg_conf)

        # Manufacturer
        manufacturer, mfr_conf = self.entity_extractor.extract_manufacturer(query)
        if manufacturer:
            entities["manufacturer"] = manufacturer
            entity_confidences.append(mfr_conf)

        # Price
        price_info, price_conf = self.entity_extractor.extract_price(query)
        if price_info:
            entities.update(price_info)
            entity_confidences.append(price_conf)

        # Calculate overall confidence
        # Weighted average of intent confidence and entity confidences
        if entity_confidences:
            avg_entity_conf = sum(entity_confidences) / len(entity_confidences)
            overall_confidence = (intent_confidence * 0.3) + (avg_entity_conf * 0.7)
        else:
            overall_confidence = (
                intent_confidence * 0.5
            )  # Lower confidence with no entities

        return ParsedQuery(
            intent=intent,
            entities=entities,
            confidence=round(overall_confidence, 2),
            raw_query=query,
        )

    def parse_batch(self, queries: list[str]) -> list[ParsedQuery]:
        """
        Parse multiple queries in batch.

        Args:
            queries: List of query strings

        Returns:
            List of ParsedQuery objects
        """
        return [self.parse(query) for query in queries]


# ============================================================================
# Example Queries (50+ variations)
# ============================================================================

EXAMPLE_QUERIES = [
    # search_by_type intent
    "find resistors with low stock",
    "show capacitors in storage location A1",
    "list inductors",
    "get all ICs",
    "search for transistors",
    "display LEDs",
    "find diodes",
    "show connectors",
    # filter_by_stock intent
    "components with low stock",
    "out of stock parts",
    "available components",
    "unused resistors",
    "parts running low",
    "empty stock",
    "components in stock",
    "need reorder",
    # filter_by_location intent
    "components in A1",
    "parts stored in Bin-23",
    "what's in Shelf-A",
    "components at Cabinet-1",
    "parts from Drawer-2",
    "storage location B5",
    # filter_by_value intent
    "10k resistors",
    "10kΩ SMD resistors",
    "100μF capacitors",
    "5V components",
    "3.3V regulators",
    "16MHz crystals",
    "0805 resistors",
    "1206 capacitors",
    "DIP8 ICs",
    "SOT-23 transistors",
    # filter_by_price intent
    "components under $1",
    "cheap capacitors",
    "parts less than $5",
    "inexpensive resistors",
    "affordable ICs",
    "budget components",
    "parts under $10",
    "cheap SMD resistors",
    # Multi-entity queries
    "10k SMD resistors with low stock",
    "0805 capacitors in location A1",
    "TI ICs under $5",
    "available 5V regulators",
    "unused 100μF capacitors in Bin-23",
    "cheap 0603 resistors",
    "Texas Instruments microcontrollers under $10",
    "low stock 1206 components",
    "SMD resistors in storage A1 under $1",
    "available DIP8 ICs from Texas Instruments",
    # Edge cases
    "res",
    "caps",
    "components",
    "stock",
    "A1",
    "10k",
    "$1",
    "",
    "show me all the things",
    "what do you have",
]


# ============================================================================
# Utility Functions
# ============================================================================


def get_example_results() -> list[tuple[str, ParsedQuery]]:
    """
    Get parsed results for all example queries.

    Returns:
        List of tuples (query, parsed_result)
    """
    parser = NLQueryParser()
    results = []

    for query in EXAMPLE_QUERIES:
        result = parser.parse(query)
        results.append((query, result))

    return results


def print_example_results():
    """Print formatted results for all example queries."""
    results = get_example_results()

    print("=" * 80)
    print("Natural Language Query Parser - Example Results")
    print("=" * 80)
    print()

    for i, (query, result) in enumerate(results, 1):
        print(f"{i}. Query: '{query}'")
        print(f"   Intent: {result.intent}")
        print(f"   Entities: {result.entities}")
        print(f"   Confidence: {result.confidence}")
        print()

    # Statistics
    print("=" * 80)
    print("Statistics")
    print("=" * 80)
    print(f"Total queries: {len(results)}")
    print(
        f"Average confidence: {sum(r.confidence for _, r in results) / len(results):.2f}"
    )

    # Intent distribution
    intent_counts: dict[str, int] = {}
    for _, result in results:
        intent_counts[result.intent] = intent_counts.get(result.intent, 0) + 1

    print("\nIntent distribution:")
    for intent, count in sorted(
        intent_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {intent}: {count} ({count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    # Demo the parser
    print_example_results()
