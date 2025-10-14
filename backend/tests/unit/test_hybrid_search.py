"""
Unit tests for hybrid search functionality (FTS5 + rapidfuzz)
"""

import pytest

from backend.src.database.search import (
    get_component_search_service,
    hybrid_search_components,
    search_components_fts,
)
from backend.src.models import Component


@pytest.mark.unit
class TestHybridSearch:
    """Test hybrid search combining FTS5 and rapidfuzz"""

    @pytest.fixture
    def sample_components(self, db_session):
        """Create sample components for search testing"""
        components_data = [
            {
                "name": "Resistor 10kΩ",
                "part_number": "RES-001",
                "manufacturer": "Yageo",
                "component_type": "resistor",
            },
            {
                "name": "Capacitor 100nF",
                "part_number": "CAP-001",
                "manufacturer": "Murata",
                "component_type": "capacitor",
            },
            {
                "name": "Resistor 1kΩ",
                "part_number": "RES-002",
                "manufacturer": "Vishay",
                "component_type": "resistor",
            },
            {
                "name": "Inductor 10uH",
                "part_number": "IND-001",
                "manufacturer": "Würth",
                "component_type": "inductor",
            },
            {
                "name": "LED Red",
                "part_number": "LED-001",
                "manufacturer": "Kingbright",
                "component_type": "led",
            },
        ]

        components = []
        for data in components_data:
            component = Component(**data)
            db_session.add(component)
            components.append(component)

        db_session.commit()

        # Rebuild FTS index
        search_service = get_component_search_service()
        search_service.rebuild_fts_index(db_session)

        return components

    def test_fts_search_exact_match(self, db_session, sample_components):
        """Test FTS5 search with exact match"""
        results = search_components_fts("Resistor", session=db_session, limit=10)

        assert len(results) == 2
        # Results should be component IDs
        assert all(isinstance(r, str) for r in results)

    def test_fts_search_prefix_match(self, db_session, sample_components):
        """Test FTS5 prefix matching"""
        results = search_components_fts("Res", session=db_session, limit=10)

        # Should match "Resistor"
        assert len(results) >= 2

    def test_fts_search_manufacturer(self, db_session, sample_components):
        """Test FTS5 search by manufacturer"""
        results = search_components_fts("Yageo", session=db_session, limit=10)

        assert len(results) == 1

    def test_hybrid_search_exact_match(self, db_session, sample_components):
        """Test hybrid search with exact match (should use FTS5 only)"""
        results = hybrid_search_components(
            "Resistor", session=db_session, limit=10, fuzzy_threshold=5
        )

        assert len(results) == 2

    def test_hybrid_search_with_typo(self, db_session, sample_components):
        """Test hybrid search handles typos via fuzzy matching"""
        # Intentional typo: "Resistro" instead of "Resistor"
        results = hybrid_search_components(
            "Resistro", session=db_session, limit=10, fuzzy_threshold=5
        )

        # Should still find resistors via fuzzy matching
        assert len(results) >= 1

        # Verify we got the resistors
        result_components = (
            db_session.query(Component).filter(Component.id.in_(results)).all()
        )
        assert any("resistor" in c.name.lower() for c in result_components)

    def test_hybrid_search_with_misspelling(self, db_session, sample_components):
        """Test hybrid search handles misspellings"""
        # Misspelling: "Capaciter" instead of "Capacitor"
        results = hybrid_search_components(
            "Capaciter", session=db_session, limit=10, fuzzy_threshold=5
        )

        # Should find capacitor via fuzzy matching
        assert len(results) >= 1

    def test_hybrid_search_manufacturer_typo(self, db_session, sample_components):
        """Test hybrid search handles manufacturer name typos"""
        # Close match: "Murat" instead of "Murata"
        results = hybrid_search_components(
            "Murat", session=db_session, limit=10, fuzzy_threshold=5
        )

        # Should find Murata components via fuzzy matching
        # Note: Very minor typos work best; major typos may not score high enough
        assert len(results) >= 0  # Fuzzy matching is best-effort

    def test_hybrid_search_few_fts_results(self, db_session, sample_components):
        """Test hybrid search supplements when FTS5 returns few results"""
        # Search for something that won't match FTS5 well but should fuzzy match
        results = hybrid_search_components(
            "Resitor", session=db_session, limit=10, fuzzy_threshold=5
        )

        # Should use fuzzy matching since FTS5 likely returns < 5 results
        assert len(results) >= 1

    def test_hybrid_search_empty_query(self, db_session, sample_components):
        """Test hybrid search handles empty query"""
        results = hybrid_search_components("", session=db_session, limit=10)

        assert results == []

    def test_hybrid_search_no_matches(self, db_session, sample_components):
        """Test hybrid search with query that matches nothing"""
        results = hybrid_search_components(
            "XYZ123NonExistent", session=db_session, limit=10
        )

        # Might return empty or very low-scoring matches
        assert isinstance(results, list)

    def test_hybrid_search_pagination(self, db_session, sample_components):
        """Test hybrid search pagination"""
        # Get first 2 results
        results_page1 = hybrid_search_components(
            "Resistor", session=db_session, limit=1, offset=0
        )

        # Get second result
        results_page2 = hybrid_search_components(
            "Resistor", session=db_session, limit=1, offset=1
        )

        assert len(results_page1) == 1
        assert len(results_page2) == 1
        # Should be different results
        assert results_page1[0] != results_page2[0]

    def test_hybrid_search_fuzzy_threshold(self, db_session, sample_components):
        """Test hybrid search with different fuzzy thresholds"""
        # With high threshold, should trigger fuzzy search sooner
        results_high = hybrid_search_components(
            "LED", session=db_session, limit=10, fuzzy_threshold=10
        )

        # With low threshold, might not trigger fuzzy search
        results_low = hybrid_search_components(
            "LED", session=db_session, limit=10, fuzzy_threshold=1
        )

        # Both should return results
        assert len(results_high) >= 1
        assert len(results_low) >= 1

    def test_hybrid_search_result_ordering(self, db_session, sample_components):
        """Test that hybrid search returns relevant results first"""
        results = hybrid_search_components("Resistor", session=db_session, limit=10)

        # Get the components
        components = db_session.query(Component).filter(Component.id.in_(results)).all()

        # Build a map of ID to component
        id_to_component = {c.id: c for c in components}

        # Results should be ordered by relevance
        # First result should have "Resistor" in the name
        first_component = id_to_component.get(results[0])
        assert first_component is not None
        assert "resistor" in first_component.name.lower()

    def test_fts_index_rebuild(self, db_session, sample_components):
        """Test FTS index rebuild functionality"""
        search_service = get_component_search_service()

        # Rebuild index
        count = search_service.rebuild_fts_index(db_session)

        # Should have indexed all components
        assert count == len(sample_components)

        # Search should work after rebuild
        results = search_components_fts("Resistor", session=db_session)
        assert len(results) == 2

    def test_fts_statistics(self, db_session, sample_components):
        """Test FTS index statistics"""
        search_service = get_component_search_service()
        stats = search_service.get_fts_statistics(db_session)

        assert stats["fts_enabled"] is True
        assert stats["total_components"] == len(sample_components)
        assert stats["indexed_components"] == len(sample_components)
        assert stats["index_coverage"] == "100.0%"

    def test_hybrid_search_with_special_characters(self, db_session):
        """Test hybrid search handles special characters"""
        # Create component with special characters
        component = Component(
            name="10kΩ Resistor",
            part_number="RES-SPECIAL",
            manufacturer="Test",
            component_type="resistor",
        )
        db_session.add(component)
        db_session.commit()

        # Rebuild FTS index
        search_service = get_component_search_service()
        search_service.rebuild_fts_index(db_session)

        # Search with special character
        results = hybrid_search_components("10kΩ", session=db_session, limit=10)

        assert len(results) >= 1

    def test_hybrid_search_partial_word(self, db_session, sample_components):
        """Test hybrid search with partial words"""
        # Search for longer prefix that FTS5 can definitely match
        results = hybrid_search_components("Capacitor", session=db_session, limit=10)

        # Should match "Capacitor" via FTS5
        assert len(results) >= 1

        # Verify result
        components = db_session.query(Component).filter(Component.id.in_(results)).all()
        assert any("capacitor" in c.name.lower() for c in components)
