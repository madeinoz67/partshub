"""
Unit tests for ComponentProviderData model.
Tests all methods, properties, and caching functionality.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from backend.src.models.provider_data import ComponentProviderData


class TestComponentProviderData:
    """Test ComponentProviderData model methods and properties."""

    def test_init_creates_valid_instance(self):
        """Test ComponentProviderData creation with basic fields."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PROV-PART-789",
            datasheet_url="https://example.com/datasheet.pdf",
            image_url="https://example.com/image.jpg",
            specifications_json={"voltage": "5V", "current": "1A"},
        )

        assert provider_data.component_id == "component-123"
        assert provider_data.provider_id == "provider-456"
        assert provider_data.provider_part_id == "PROV-PART-789"
        assert provider_data.datasheet_url == "https://example.com/datasheet.pdf"
        assert provider_data.image_url == "https://example.com/image.jpg"
        assert provider_data.specifications_json == {"voltage": "5V", "current": "1A"}

    def test_specifications_property_with_data(self):
        """Test specifications property returns JSON data."""
        spec_data = {"voltage": "3.3V", "package": "0603", "tolerance": "1%"}
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
            specifications_json=spec_data,
        )

        assert provider_data.specifications == spec_data

    def test_specifications_property_empty(self):
        """Test specifications property returns empty dict when no data."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
            # No specifications_json
        )

        assert provider_data.specifications == {}

    def test_specifications_property_none(self):
        """Test specifications property returns empty dict when None."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
            specifications_json=None,
        )

        assert provider_data.specifications == {}

    def test_is_cached_recently_true_default_24h(self):
        """Test is_cached_recently returns True for recent cache (default 24h)."""
        # Use real datetime since datetime is imported inside the method
        current_time = datetime.now(UTC)
        # Cache time 12 hours ago (within 24h default)
        cache_time = current_time - timedelta(hours=12)

        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
        )
        provider_data.cached_at = cache_time

        assert provider_data.is_cached_recently() is True

    def test_is_cached_recently_false_default_24h(self):
        """Test is_cached_recently returns False for old cache (default 24h)."""
        # Use real datetime since datetime is imported inside the method
        current_time = datetime.now(UTC)
        # Cache time 36 hours ago (beyond 24h default)
        cache_time = current_time - timedelta(hours=36)

        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
        )
        provider_data.cached_at = cache_time

        assert provider_data.is_cached_recently() is False

    def test_is_cached_recently_custom_hours(self):
        """Test is_cached_recently with custom hours parameter."""
        # Use real datetime since datetime is imported inside the method
        current_time = datetime.now(UTC)
        # Cache time 6 hours ago
        cache_time = current_time - timedelta(hours=6)

        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
        )
        provider_data.cached_at = cache_time

        # Should be recent within 12 hours
        assert provider_data.is_cached_recently(hours=12) is True

        # Should not be recent within 3 hours
        assert provider_data.is_cached_recently(hours=3) is False

    def test_is_cached_recently_no_cache_time(self):
        """Test is_cached_recently returns False when no cached_at time."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-123",
        )
        # cached_at is None by default

        assert provider_data.is_cached_recently() is False

    @patch("backend.src.models.provider_data.func")
    def test_update_cache_all_fields(self, mock_func):
        """Test update_cache updates all fields correctly."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="OLD-PART",
        )

        new_specs = {"voltage": "5V", "current": "2A"}

        provider_data.update_cache(
            provider_part_id="NEW-PART-123",
            datasheet_url="https://new.com/datasheet.pdf",
            image_url="https://new.com/image.png",
            specifications=new_specs,
        )

        assert provider_data.provider_part_id == "NEW-PART-123"
        assert provider_data.datasheet_url == "https://new.com/datasheet.pdf"
        assert provider_data.image_url == "https://new.com/image.png"
        assert provider_data.specifications_json == new_specs
        # cached_at should be updated to func.now()
        mock_func.now.assert_called_once()

    @patch("backend.src.models.provider_data.func")
    def test_update_cache_partial_fields(self, mock_func):
        """Test update_cache with only some fields provided."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="OLD-PART",
            datasheet_url="old-url.com",
            image_url="old-image.com",
        )

        provider_data.update_cache(
            provider_part_id="NEW-PART-123"
            # Only providing part ID, others should be None
        )

        assert provider_data.provider_part_id == "NEW-PART-123"
        assert provider_data.datasheet_url is None
        assert provider_data.image_url is None
        assert provider_data.specifications_json is None
        mock_func.now.assert_called_once()

    def test_to_dict_basic(self):
        """Test to_dict returns basic dictionary structure."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
            datasheet_url="https://example.com/datasheet.pdf",
            image_url="https://example.com/image.jpg",
            specifications_json={"voltage": "3.3V"},
        )

        # Mock timestamps
        cache_time = datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC)
        create_time = datetime(2023, 1, 10, 10, 0, 0, tzinfo=UTC)
        update_time = datetime(2023, 1, 15, 11, 0, 0, tzinfo=UTC)

        provider_data.cached_at = cache_time
        provider_data.created_at = create_time
        provider_data.updated_at = update_time

        result = provider_data.to_dict()

        assert result["component_id"] == "component-123"
        assert result["provider_id"] == "provider-456"
        assert result["provider_part_id"] == "PART-789"
        assert result["datasheet_url"] == "https://example.com/datasheet.pdf"
        assert result["image_url"] == "https://example.com/image.jpg"
        assert result["specifications"] == {"voltage": "3.3V"}
        assert result["cached_at"] == cache_time.isoformat()
        assert result["created_at"] == create_time.isoformat()
        assert result["updated_at"] == update_time.isoformat()

    def test_to_dict_include_component(self):
        """Test to_dict includes component data when requested."""
        from unittest.mock import PropertyMock, patch

        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )

        # Mock component relationship using patch
        mock_component = Mock()
        mock_component.id = "component-123"
        mock_component.name = "Test Resistor"
        mock_component.part_number = "R-1234"
        mock_component.manufacturer = "Test Corp"

        with patch.object(
            type(provider_data), "component", new_callable=PropertyMock
        ) as mock_comp_prop:
            mock_comp_prop.return_value = mock_component
            result = provider_data.to_dict(include_component=True)

            assert "component" in result
            component_data = result["component"]
            assert component_data["id"] == "component-123"
            assert component_data["name"] == "Test Resistor"
            assert component_data["part_number"] == "R-1234"
            assert component_data["manufacturer"] == "Test Corp"

    def test_to_dict_include_provider(self):
        """Test to_dict includes provider data when requested."""
        from unittest.mock import PropertyMock, patch

        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )

        # Mock provider relationship using patch
        mock_provider = Mock()
        mock_provider.id = "provider-456"
        mock_provider.name = "Test Provider"
        mock_provider.is_enabled = True

        with patch.object(
            type(provider_data), "provider", new_callable=PropertyMock
        ) as mock_prov_prop:
            mock_prov_prop.return_value = mock_provider
            result = provider_data.to_dict(include_provider=True)

            assert "provider" in result
            provider_info = result["provider"]
            assert provider_info["id"] == "provider-456"
            assert provider_info["name"] == "Test Provider"
            assert provider_info["is_enabled"] is True

    def test_to_dict_no_component_relationship(self):
        """Test to_dict handles missing component relationship gracefully."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )
        provider_data.component = None

        result = provider_data.to_dict(include_component=True)

        # Should not include component section
        assert "component" not in result

    def test_to_dict_no_provider_relationship(self):
        """Test to_dict handles missing provider relationship gracefully."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )
        provider_data.provider = None

        result = provider_data.to_dict(include_provider=True)

        # Should not include provider section
        assert "provider" not in result

    def test_to_dict_none_timestamps(self):
        """Test to_dict handles None timestamps gracefully."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )
        # Timestamps are None by default

        result = provider_data.to_dict()

        assert result["cached_at"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_repr_method(self):
        """Test __repr__ method returns expected format."""
        provider_data = ComponentProviderData(
            component_id="component-123",
            provider_id="provider-456",
            provider_part_id="PART-789",
        )

        repr_str = repr(provider_data)
        assert "component='component-123'" in repr_str
        assert "provider='provider-456'" in repr_str
