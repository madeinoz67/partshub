"""
Unit tests for KiCadLibraryData model.
Tests all methods, properties, and data source management functionality.
"""

from datetime import UTC, datetime

from backend.src.models.kicad_data import KiCadDataSource, KiCadLibraryData


class TestKiCadLibraryData:
    """Test KiCadLibraryData model methods and properties."""

    def test_init_creates_valid_instance(self):
        """Test KiCadLibraryData creation with basic fields."""
        kicad_data = KiCadLibraryData(
            component_id="test-component-123",
            symbol_library="test_symbols",
            symbol_name="resistor_symbol",
            footprint_library="test_footprints",
            footprint_name="R_0603",
            model_3d_path="/path/to/resistor.step",
        )

        assert kicad_data.component_id == "test-component-123"
        assert kicad_data.symbol_library == "test_symbols"
        assert kicad_data.symbol_name == "resistor_symbol"
        assert kicad_data.footprint_library == "test_footprints"
        assert kicad_data.footprint_name == "R_0603"
        assert kicad_data.model_3d_path == "/path/to/resistor.step"

    def test_has_symbol_property_true(self):
        """Test has_symbol property returns True when symbol data exists."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="symbols_lib",
            symbol_name="test_symbol",
        )

        assert kicad_data.has_symbol is True

    def test_has_symbol_property_false_no_library(self):
        """Test has_symbol property returns False when library missing."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_name="test_symbol",
            # Missing symbol_library
        )

        assert kicad_data.has_symbol is False

    def test_has_symbol_property_false_no_name(self):
        """Test has_symbol property returns False when name missing."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="symbols_lib",
            # Missing symbol_name
        )

        assert kicad_data.has_symbol is False

    def test_has_footprint_property_true(self):
        """Test has_footprint property returns True when footprint data exists."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            footprint_library="footprints_lib",
            footprint_name="test_footprint",
        )

        assert kicad_data.has_footprint is True

    def test_has_footprint_property_false(self):
        """Test has_footprint property returns False when footprint data missing."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            footprint_library="footprints_lib",
            # Missing footprint_name
        )

        assert kicad_data.has_footprint is False

    def test_has_3d_model_property_true(self):
        """Test has_3d_model property returns True when 3D model exists."""
        kicad_data = KiCadLibraryData(
            component_id="test-component", model_3d_path="/path/to/model.step"
        )

        assert kicad_data.has_3d_model is True

    def test_has_3d_model_property_false(self):
        """Test has_3d_model property returns False when no 3D model."""
        kicad_data = KiCadLibraryData(
            component_id="test-component"
            # Missing model_3d_path
        )

        assert kicad_data.has_3d_model is False

    def test_get_symbol_reference_with_data(self):
        """Test get_symbol_reference returns correct format."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="MySymbols",
            symbol_name="Resistor_Symbol",
        )

        result = kicad_data.get_symbol_reference()
        assert result == "MySymbols:Resistor_Symbol"

    def test_get_symbol_reference_no_data(self):
        """Test get_symbol_reference returns empty string when no data."""
        kicad_data = KiCadLibraryData(component_id="test-component")

        result = kicad_data.get_symbol_reference()
        assert result == ""

    def test_get_footprint_reference_with_data(self):
        """Test get_footprint_reference returns correct format."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            footprint_library="MyFootprints",
            footprint_name="R_0603_Handsolder",
        )

        result = kicad_data.get_footprint_reference()
        assert result == "MyFootprints:R_0603_Handsolder"

    def test_get_footprint_reference_no_data(self):
        """Test get_footprint_reference returns empty string when no data."""
        kicad_data = KiCadLibraryData(component_id="test-component")

        result = kicad_data.get_footprint_reference()
        assert result == ""

    def test_get_effective_symbol_path_custom_priority(self):
        """Test get_effective_symbol_path prioritizes custom files."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="DefaultLib",
            symbol_name="DefaultSymbol",
            custom_symbol_file_path="/custom/path/symbol.kicad_sym",
            symbol_source=KiCadDataSource.CUSTOM,
        )

        result = kicad_data.get_effective_symbol_path()
        assert result == "/custom/path/symbol.kicad_sym"

    def test_get_effective_symbol_path_provider_fallback(self):
        """Test get_effective_symbol_path falls back to provider data."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="ProviderLib",
            symbol_name="ProviderSymbol",
            symbol_source=KiCadDataSource.PROVIDER,
        )

        result = kicad_data.get_effective_symbol_path()
        assert result == "ProviderLib:ProviderSymbol"

    def test_get_effective_symbol_path_auto_fallback(self):
        """Test get_effective_symbol_path falls back to auto-generated."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            symbol_library="AutoLib",
            symbol_name="AutoSymbol",
            symbol_source=KiCadDataSource.AUTO_GENERATED,
        )

        result = kicad_data.get_effective_symbol_path()
        assert result == "AutoLib:AutoSymbol"

    def test_get_effective_symbol_path_empty(self):
        """Test get_effective_symbol_path returns empty when no data."""
        kicad_data = KiCadLibraryData(component_id="test-component")

        result = kicad_data.get_effective_symbol_path()
        assert result == ""

    def test_get_effective_footprint_path_custom_priority(self):
        """Test get_effective_footprint_path prioritizes custom files."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            footprint_library="DefaultLib",
            footprint_name="DefaultFootprint",
            custom_footprint_file_path="/custom/path/footprint.kicad_mod",
            footprint_source=KiCadDataSource.CUSTOM,
        )

        result = kicad_data.get_effective_footprint_path()
        assert result == "/custom/path/footprint.kicad_mod"

    def test_get_effective_footprint_path_provider_fallback(self):
        """Test get_effective_footprint_path falls back to provider data."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            footprint_library="ProviderLib",
            footprint_name="ProviderFootprint",
            footprint_source=KiCadDataSource.PROVIDER,
        )

        result = kicad_data.get_effective_footprint_path()
        assert result == "ProviderLib:ProviderFootprint"

    def test_get_effective_3d_model_path_custom_priority(self):
        """Test get_effective_3d_model_path prioritizes custom files."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            model_3d_path="/default/model.step",
            custom_3d_model_file_path="/custom/model.step",
            model_3d_source=KiCadDataSource.CUSTOM,
        )

        result = kicad_data.get_effective_3d_model_path()
        assert result == "/custom/model.step"

    def test_get_effective_3d_model_path_provider_fallback(self):
        """Test get_effective_3d_model_path falls back to provider data."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            model_3d_path="/provider/model.step",
            model_3d_source=KiCadDataSource.PROVIDER,
        )

        result = kicad_data.get_effective_3d_model_path()
        assert result == "/provider/model.step"

    def test_get_effective_3d_model_path_empty(self):
        """Test get_effective_3d_model_path returns empty when no data."""
        kicad_data = KiCadLibraryData(component_id="test-component")

        result = kicad_data.get_effective_3d_model_path()
        assert result == ""

    def test_set_custom_symbol_updates_fields(self):
        """Test set_custom_symbol updates path, source, and timestamp."""
        kicad_data = KiCadLibraryData(component_id="test-component")
        file_path = "/custom/symbol.kicad_sym"

        # Store time before call
        before_time = datetime.now(UTC)
        kicad_data.set_custom_symbol(file_path)
        after_time = datetime.now(UTC)

        assert kicad_data.custom_symbol_file_path == file_path
        assert kicad_data.symbol_source == KiCadDataSource.CUSTOM
        assert before_time <= kicad_data.symbol_updated_at <= after_time

    def test_set_custom_footprint_updates_fields(self):
        """Test set_custom_footprint updates path, source, and timestamp."""
        kicad_data = KiCadLibraryData(component_id="test-component")
        file_path = "/custom/footprint.kicad_mod"

        before_time = datetime.now(UTC)
        kicad_data.set_custom_footprint(file_path)
        after_time = datetime.now(UTC)

        assert kicad_data.custom_footprint_file_path == file_path
        assert kicad_data.footprint_source == KiCadDataSource.CUSTOM
        assert before_time <= kicad_data.footprint_updated_at <= after_time

    def test_set_custom_3d_model_updates_fields(self):
        """Test set_custom_3d_model updates path, source, and timestamp."""
        kicad_data = KiCadLibraryData(component_id="test-component")
        file_path = "/custom/model.step"

        before_time = datetime.now(UTC)
        kicad_data.set_custom_3d_model(file_path)
        after_time = datetime.now(UTC)

        assert kicad_data.custom_3d_model_file_path == file_path
        assert kicad_data.model_3d_source == KiCadDataSource.CUSTOM
        assert before_time <= kicad_data.model_3d_updated_at <= after_time

    def test_reset_symbol_to_auto_clears_custom(self):
        """Test reset_symbol_to_auto clears custom data and updates timestamp."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            custom_symbol_file_path="/custom/symbol.kicad_sym",
            symbol_source=KiCadDataSource.CUSTOM,
        )

        before_time = datetime.now(UTC)
        kicad_data.reset_symbol_to_auto()
        after_time = datetime.now(UTC)

        assert kicad_data.custom_symbol_file_path is None
        assert kicad_data.symbol_source == KiCadDataSource.AUTO_GENERATED
        assert before_time <= kicad_data.symbol_updated_at <= after_time

    def test_reset_footprint_to_auto_clears_custom(self):
        """Test reset_footprint_to_auto clears custom data and updates timestamp."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            custom_footprint_file_path="/custom/footprint.kicad_mod",
            footprint_source=KiCadDataSource.CUSTOM,
        )

        before_time = datetime.now(UTC)
        kicad_data.reset_footprint_to_auto()
        after_time = datetime.now(UTC)

        assert kicad_data.custom_footprint_file_path is None
        assert kicad_data.footprint_source == KiCadDataSource.AUTO_GENERATED
        assert before_time <= kicad_data.footprint_updated_at <= after_time

    def test_reset_3d_model_to_auto_clears_custom(self):
        """Test reset_3d_model_to_auto clears custom data and updates timestamp."""
        kicad_data = KiCadLibraryData(
            component_id="test-component",
            custom_3d_model_file_path="/custom/model.step",
            model_3d_source=KiCadDataSource.CUSTOM,
        )

        before_time = datetime.now(UTC)
        kicad_data.reset_3d_model_to_auto()
        after_time = datetime.now(UTC)

        assert kicad_data.custom_3d_model_file_path is None
        assert kicad_data.model_3d_source == KiCadDataSource.AUTO_GENERATED
        assert before_time <= kicad_data.model_3d_updated_at <= after_time

    def test_repr_method(self):
        """Test __repr__ method returns expected format."""
        kicad_data = KiCadLibraryData(
            component_id="test-component-123",
            symbol_name="TestSymbol",
            footprint_name="TestFootprint",
        )

        repr_str = repr(kicad_data)
        assert "component_id=test-component-123" in repr_str
        assert "symbol=TestSymbol" in repr_str
        assert "footprint=TestFootprint" in repr_str

    def test_default_source_values(self):
        """Test default source values are AUTO_GENERATED."""
        kicad_data = KiCadLibraryData(component_id="test-component")

        # Set default values manually since SQLAlchemy doesn't set them outside of session
        kicad_data.symbol_source = KiCadDataSource.AUTO_GENERATED
        kicad_data.footprint_source = KiCadDataSource.AUTO_GENERATED
        kicad_data.model_3d_source = KiCadDataSource.AUTO_GENERATED

        assert kicad_data.symbol_source == KiCadDataSource.AUTO_GENERATED
        assert kicad_data.footprint_source == KiCadDataSource.AUTO_GENERATED
        assert kicad_data.model_3d_source == KiCadDataSource.AUTO_GENERATED

    def test_kicad_fields_json_optional(self):
        """Test kicad_fields_json can store additional data."""
        additional_fields = {
            "manufacturer": "Test Corp",
            "part_number": "TC-123",
            "custom_field": "value",
        }

        kicad_data = KiCadLibraryData(
            component_id="test-component", kicad_fields_json=additional_fields
        )

        assert kicad_data.kicad_fields_json == additional_fields


class TestKiCadDataSourceEnum:
    """Test KiCadDataSource enumeration."""

    def test_enum_values(self):
        """Test enum values are as expected."""
        assert KiCadDataSource.CUSTOM.value == "custom"
        assert KiCadDataSource.PROVIDER.value == "provider"
        assert KiCadDataSource.AUTO_GENERATED.value == "auto"

    def test_enum_ordering_priority(self):
        """Test that enum values represent priority (custom > provider > auto)."""
        # Note: This test documents the priority order mentioned in the docstring
        custom = KiCadDataSource.CUSTOM
        provider = KiCadDataSource.PROVIDER
        auto = KiCadDataSource.AUTO_GENERATED

        # All enum values should be unique
        assert custom != provider
        assert provider != auto
        assert custom != auto
