"""
Natural Language Search Service for PartsHub Component Search.

Converts natural language queries into structured search parameters using the
pattern grammar from nl_patterns.py. Provides confidence scoring and fallback
to FTS5 full-text search for low-confidence queries.

Example usage:
    >>> service = NaturalLanguageSearchService()
    >>> result = service.parse_query("find resistors with low stock")
    >>> print(result)
    {
        "component_type": "resistor",
        "stock_status": "low",
        "confidence": 0.89,
        "parsed_entities": {...},
        "fallback_to_fts5": False
    }
"""

import logging
from typing import Any

from .nl_patterns import NLQueryParser, ParsedQuery

logger = logging.getLogger(__name__)


class NaturalLanguageSearchService:
    """
    Service for parsing natural language queries into structured search parameters.

    This service uses the pattern-based NLQueryParser to extract entities from
    natural language queries and maps them to API-compatible search parameters
    for the ComponentService.

    Attributes:
        parser: Instance of NLQueryParser for pattern-based parsing
        confidence_threshold: Minimum confidence score for using NL parsing (0.5)
    """

    # Confidence threshold for using NL parsing vs FTS5 fallback
    CONFIDENCE_THRESHOLD = 0.5

    # Minimum confidence boost for multiple entity matches
    MULTI_ENTITY_BOOST = 0.1

    # Confidence penalty for ambiguous queries
    AMBIGUITY_PENALTY = 0.15

    def __init__(self):
        """Initialize the Natural Language Search Service."""
        self.parser = NLQueryParser()
        self.confidence_threshold = self.CONFIDENCE_THRESHOLD
        logger.info("Initialized Natural Language Search Service")

    def parse_query(self, query: str) -> dict[str, Any]:
        """
        Parse natural language query into search parameters.

        This is the main entry point for the service. It parses the query,
        calculates confidence, and returns either structured search parameters
        or falls back to FTS5 search.

        Args:
            query: Natural language query string (e.g., "find resistors with low stock")

        Returns:
            Dictionary with search parameters and metadata:
            {
                "component_type": "resistor",      # Structured search parameters
                "stock_status": "low",
                "confidence": 0.89,                # Parsing confidence score
                "parsed_entities": {...},          # Raw extracted entities
                "fallback_to_fts5": False,         # Whether to use FTS5 fallback
                "intent": "search_by_type"         # Classified query intent
            }

        Example:
            >>> service = NaturalLanguageSearchService()
            >>> result = service.parse_query("10k resistors in A1")
            >>> print(result["component_type"])
            'resistor'
            >>> print(result["storage_location"])
            'A1'
            >>> print(result["confidence"])
            0.87
        """
        if not query or not query.strip():
            logger.debug("Empty query received")
            return self._empty_query_result()

        # Parse query using pattern-based parser
        parsed: ParsedQuery = self.parser.parse(query)
        logger.debug(
            f"Parsed query: '{query}' -> Intent: {parsed.intent}, "
            f"Entities: {parsed.entities}, Confidence: {parsed.confidence}"
        )

        # Classify intent and extract entities
        intent = self._classify_intent(parsed)
        entities = self._extract_entities(parsed)

        # Calculate confidence score with adjustments
        confidence = self._calculate_confidence(parsed, entities)

        # Decide whether to use structured search or FTS5 fallback
        fallback_to_fts5 = confidence < self.confidence_threshold

        if fallback_to_fts5:
            logger.info(
                f"Low confidence ({confidence:.2f}) for query '{query}', "
                f"falling back to FTS5 search"
            )
            return self._build_fallback_params(query, parsed, confidence)

        # Build structured search parameters
        search_params = self._build_search_params(entities)
        search_params["confidence"] = confidence
        search_params["parsed_entities"] = entities
        search_params["fallback_to_fts5"] = False
        search_params["intent"] = intent

        logger.info(
            f"Successfully parsed query '{query}' with confidence {confidence:.2f}"
        )
        return search_params

    def _classify_intent(self, parsed: ParsedQuery) -> str:
        """
        Determine query type from parsed result.

        Intents:
        - search_by_type: Finding components by type (e.g., "find resistors")
        - filter_by_stock: Filtering by stock status (e.g., "low stock")
        - filter_by_location: Filtering by location (e.g., "in A1")
        - filter_by_value: Filtering by specifications (e.g., "10k resistors")
        - filter_by_price: Filtering by price (e.g., "under $5")

        Args:
            parsed: ParsedQuery object from nl_patterns parser

        Returns:
            Intent string
        """
        return parsed.intent

    def _extract_entities(self, parsed: ParsedQuery) -> dict[str, Any]:
        """
        Extract specific values from parsed result.

        Entities include:
        - component_type: Component type (resistor, capacitor, etc.)
        - stock_status: Stock status (low, out, available)
        - location: Storage location (A1, Bin-23, etc.)
        - resistance/capacitance/voltage/etc.: Component values
        - package: Package/footprint (0805, SMD, DIP8, etc.)
        - manufacturer: Manufacturer name
        - min_price/max_price/exact_price: Price constraints

        Args:
            parsed: ParsedQuery object from nl_patterns parser

        Returns:
            Dictionary of extracted entities
        """
        return parsed.entities.copy()

    def _build_search_params(self, entities: dict[str, Any]) -> dict[str, Any]:
        """
        Map entities to API-compatible search parameters.

        Entity to parameter mapping:
        - component_type -> component_type
        - stock_status -> stock_status
        - location -> storage_location
        - resistance/capacitance/voltage/etc. -> specifications__<key>
        - package -> package (stored in component.package field)
        - manufacturer -> manufacturer
        - max_price/min_price -> price_max/price_min

        Args:
            entities: Dictionary of extracted entities

        Returns:
            Dictionary of search parameters compatible with ComponentService.list_components()

        Example:
            >>> entities = {"component_type": "resistor", "stock_status": "low"}
            >>> params = service._build_search_params(entities)
            >>> print(params)
            {'component_type': 'resistor', 'stock_status': 'low'}
        """
        params: dict[str, Any] = {}

        # Direct mappings (no transformation needed)
        direct_mappings = {
            "component_type": "component_type",
            "stock_status": "stock_status",
            "manufacturer": "manufacturer",
            "package": "package",
        }

        for entity_key, param_key in direct_mappings.items():
            if entity_key in entities:
                params[param_key] = entities[entity_key]

        # Location mapping
        if "location" in entities:
            params["storage_location"] = entities["location"]

        # Component value specifications (resistance, capacitance, etc.)
        # These are stored in specifications JSON field, so we need to search
        # using the component.value field or specifications field
        value_fields = [
            "resistance",
            "capacitance",
            "voltage",
            "inductance",
            "current",
            "frequency",
        ]

        # Collect all value specifications
        value_specs = {}
        for field in value_fields:
            if field in entities:
                value_specs[field] = entities[field]

        # If we have value specifications, we'll use the 'search' parameter
        # to search across value and specifications fields
        # Note: The ComponentService uses hybrid_search_components which includes
        # searching in the value field and notes
        if value_specs:
            # For now, include the first value spec in the search parameter
            # In the future, this could be enhanced to search in specifications JSON
            first_value = list(value_specs.values())[0]
            params["search"] = first_value

        # Price filtering
        if "max_price" in entities:
            params["price_max"] = entities["max_price"]
        if "min_price" in entities:
            params["price_min"] = entities["min_price"]
        if "exact_price" in entities:
            # For exact price, set both min and max
            params["price_min"] = entities["exact_price"]
            params["price_max"] = entities["exact_price"]

        return params

    def _calculate_confidence(
        self, parsed: ParsedQuery, entities: dict[str, Any]
    ) -> float:
        """
        Calculate parsing confidence with adjustments.

        Confidence calculation:
        1. Start with base confidence from nl_patterns parser (0.0-1.0)
        2. Boost confidence for multiple entity matches (+0.1 per additional entity)
        3. Decrease confidence for ambiguous queries (-0.15 if vague intent)
        4. Clamp final confidence to [0.0, 1.0] range

        Args:
            parsed: ParsedQuery object from nl_patterns parser
            entities: Extracted entities dictionary

        Returns:
            Confidence score between 0.0 and 1.0

        Example:
            >>> # Single entity query
            >>> parsed = ParsedQuery(intent="search_by_type", entities={"component_type": "resistor"}, confidence=0.75)
            >>> entities = {"component_type": "resistor"}
            >>> confidence = service._calculate_confidence(parsed, entities)
            >>> print(confidence)
            0.75

            >>> # Multi-entity query (boosted)
            >>> parsed = ParsedQuery(intent="search_by_type", entities={"component_type": "resistor", "stock_status": "low"}, confidence=0.75)
            >>> entities = {"component_type": "resistor", "stock_status": "low"}
            >>> confidence = service._calculate_confidence(parsed, entities)
            >>> print(confidence)
            0.85  # +0.1 boost for second entity
        """
        # Start with base confidence from parser
        confidence = parsed.confidence

        # Boost for multiple entities
        entity_count = len(entities)
        if entity_count > 1:
            # Add 0.1 for each additional entity (beyond the first)
            boost = (entity_count - 1) * self.MULTI_ENTITY_BOOST
            confidence += boost
            logger.debug(
                f"Multi-entity boost: +{boost:.2f} for {entity_count} entities"
            )

        # Penalty for ambiguous queries
        if self._is_ambiguous_query(parsed):
            confidence -= self.AMBIGUITY_PENALTY
            logger.debug(f"Ambiguity penalty: -{self.AMBIGUITY_PENALTY:.2f}")

        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        return round(confidence, 2)

    def _is_ambiguous_query(self, parsed: ParsedQuery) -> bool:
        """
        Check if query is ambiguous or vague.

        A query is considered ambiguous if:
        - It has no specific entities extracted
        - The intent confidence is very low (< 0.3)
        - The query contains generic terms like "show me" or "what do you have"

        Args:
            parsed: ParsedQuery object from nl_patterns parser

        Returns:
            True if query is ambiguous, False otherwise
        """
        # No entities extracted
        if not parsed.entities:
            return True

        # Very low base confidence
        if parsed.confidence < 0.3:
            return True

        # Generic query patterns
        generic_patterns = [
            "show me",
            "what do you have",
            "list everything",
            "all the things",
            "anything",
        ]

        query_lower = parsed.raw_query.lower()
        for pattern in generic_patterns:
            if pattern in query_lower:
                return True

        return False

    def _build_fallback_params(
        self, query: str, parsed: ParsedQuery, confidence: float
    ) -> dict[str, Any]:
        """
        Build fallback parameters for FTS5 full-text search.

        When confidence is too low for structured search, fall back to FTS5
        by returning the original query as a 'search' parameter.

        Args:
            query: Original query string
            parsed: ParsedQuery object (for logging purposes)
            confidence: Calculated confidence score

        Returns:
            Dictionary with fallback search parameters
        """
        logger.debug(
            f"Building fallback params for query '{query}' "
            f"(confidence: {confidence:.2f}, threshold: {self.confidence_threshold})"
        )

        return {
            "search": query,  # Use FTS5 full-text search
            "confidence": confidence,
            "fallback_to_fts5": True,
            "intent": parsed.intent,
            "parsed_entities": parsed.entities,  # Include for debugging
        }

    def _empty_query_result(self) -> dict[str, Any]:
        """
        Return result for empty query.

        Returns:
            Dictionary with empty search parameters
        """
        return {
            "confidence": 0.0,
            "fallback_to_fts5": True,
            "intent": "search_by_type",
            "parsed_entities": {},
        }

    def parse_batch(self, queries: list[str]) -> list[dict[str, Any]]:
        """
        Parse multiple queries in batch.

        Useful for testing or bulk query analysis.

        Args:
            queries: List of query strings

        Returns:
            List of parsed query results (one per input query)

        Example:
            >>> service = NaturalLanguageSearchService()
            >>> queries = ["find resistors", "capacitors with low stock"]
            >>> results = service.parse_batch(queries)
            >>> len(results)
            2
        """
        return [self.parse_query(query) for query in queries]

    def get_confidence_threshold(self) -> float:
        """
        Get current confidence threshold.

        Returns:
            Current confidence threshold value
        """
        return self.confidence_threshold

    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Set confidence threshold for FTS5 fallback.

        Args:
            threshold: New threshold value (0.0-1.0)

        Raises:
            ValueError: If threshold is not in [0.0, 1.0] range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0.0, 1.0], got {threshold}")

        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold set to {threshold}")
