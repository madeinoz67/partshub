"""
Simple unit tests for model methods that don't require database setup.
Focus on testing individual method logic for coverage improvement.
"""

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.unit
class TestKiCadDataMethods:
    """Test individual KiCad model methods without full ORM setup."""

    def test_kicad_data_source_enum_values(self):
        """Test KiCadDataSource enum values."""
        from backend.src.models.kicad_data import KiCadDataSource

        assert KiCadDataSource.CUSTOM.value == "custom"
        assert KiCadDataSource.PROVIDER.value == "provider"
        assert KiCadDataSource.AUTO_GENERATED.value == "auto"

    def test_kicad_has_symbol_logic(self):
        """Test has_symbol property logic."""
        from backend.src.models.kicad_data import KiCadLibraryData

        # Test with both values
        kicad = KiCadLibraryData(component_id="test")
        kicad.symbol_library = "lib"
        kicad.symbol_name = "name"
        assert kicad.has_symbol is True

        # Test missing library
        kicad.symbol_library = None
        assert kicad.has_symbol is False

        # Test missing name
        kicad.symbol_library = "lib"
        kicad.symbol_name = None
        assert kicad.has_symbol is False

    def test_kicad_get_symbol_reference(self):
        """Test get_symbol_reference method."""
        from backend.src.models.kicad_data import KiCadLibraryData

        kicad = KiCadLibraryData(component_id="test")
        kicad.symbol_library = "MyLib"
        kicad.symbol_name = "MySymbol"

        assert kicad.get_symbol_reference() == "MyLib:MySymbol"


@pytest.mark.unit
class TestMetaPartMethods:
    """Test individual MetaPart model methods."""

    def test_display_name_logic(self):
        """Test display_name property logic."""
        from backend.src.models.meta_part import MetaPart

        # With version
        meta = MetaPart(name="Test", version="v1.0")
        assert meta.display_name == "Test v1.0"

        # Without version
        meta = MetaPart(name="Test")
        assert meta.display_name == "Test"

    def test_total_component_count_calculation(self):
        """Test total_component_count calculation logic."""
        from backend.src.models.meta_part import MetaPart

        meta = MetaPart(name="Test")

        # Test the logic directly without mocking SQLAlchemy relationship
        # This would normally sum quantity_required from components
        # For unit testing, we can test the method exists and returns 0 for empty
        assert hasattr(meta, "total_component_count")
        # When no components are attached, should return 0
        assert meta.total_component_count == 0


@pytest.mark.unit
class TestProviderDataMethods:
    """Test individual provider data model methods."""

    def test_specifications_property(self):
        """Test specifications property returns correct data."""
        from backend.src.models.provider_data import ComponentProviderData

        # With data
        provider_data = ComponentProviderData(
            component_id="test", provider_id="test", provider_part_id="test"
        )
        provider_data.specifications_json = {"key": "value"}
        assert provider_data.specifications == {"key": "value"}

        # Without data
        provider_data.specifications_json = None
        assert provider_data.specifications == {}

    def test_is_cached_recently_logic(self):
        """Test is_cached_recently method logic."""
        from backend.src.models.provider_data import ComponentProviderData

        provider_data = ComponentProviderData(
            component_id="test", provider_id="test", provider_part_id="test"
        )

        # Test with actual recent time
        current_time = datetime.now(UTC)

        # Recent cache (12 hours ago)
        provider_data.cached_at = current_time - timedelta(hours=12)
        assert provider_data.is_cached_recently(24) is True

        # Old cache (36 hours ago)
        provider_data.cached_at = current_time - timedelta(hours=36)
        assert provider_data.is_cached_recently(24) is False

        # No cache time
        provider_data.cached_at = None
        assert provider_data.is_cached_recently(24) is False


@pytest.mark.unit
class TestComponentModelMethods:
    """Test Component model properties and methods."""

    def test_component_display_name(self):
        """Test Component display_name property."""
        from backend.src.models.component import Component

        # With part number
        component = Component(name="Resistor", part_number="R123")
        assert component.display_name == "Resistor (R123)"

        # Without part number
        component = Component(name="Resistor")
        assert component.display_name == "Resistor"


@pytest.mark.unit
class TestProjectModelMethods:
    """Test Project model properties and methods."""

    def test_project_display_name(self):
        """Test Project display_name property."""
        from backend.src.models.project import Project

        # With version
        project = Project(name="My Project", version="v2.0")
        assert project.display_name == "My Project v2.0"

        # Without version
        project = Project(name="My Project")
        assert project.display_name == "My Project"

    def test_project_status_enum(self):
        """Test ProjectStatus enum values."""
        from backend.src.models.project import ProjectStatus

        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.CANCELLED.value == "cancelled"


@pytest.mark.unit
class TestCategoryModelMethods:
    """Test Category model methods."""

    def test_category_display_name(self):
        """Test Category display_name property."""
        from backend.src.models.category import Category

        category = Category(name="Resistors", description="Test desc")
        assert category.display_name == "Resistors"

    def test_category_full_path_simple(self):
        """Test Category full_path without parent."""
        from backend.src.models.category import Category

        category = Category(name="Electronics")
        # Mock the parent relationship
        category.parent = None
        # full_path returns a list of Category objects
        path = category.full_path
        assert len(path) == 1
        assert path[0] == category
        assert path[0].name == "Electronics"


@pytest.mark.unit
class TestStorageLocationMethods:
    """Test StorageLocation model methods."""

    def test_storage_location_display_name(self):
        """Test StorageLocation display_name property."""
        from backend.src.models.storage_location import StorageLocation

        # With code
        location = StorageLocation(name="Shelf A", location_code="A1")
        assert location.display_name == "Shelf A (A1)"

        # Without code
        location = StorageLocation(name="Shelf A")
        assert location.display_name == "Shelf A"

    def test_storage_location_full_path_simple(self):
        """Test StorageLocation full_path without parent."""
        from backend.src.models.storage_location import StorageLocation

        location = StorageLocation(name="Lab")
        # Mock the parent relationship
        location.parent = None
        # full_path returns a list of StorageLocation objects
        path = location.full_path
        assert len(path) == 1
        assert path[0] == location
        assert path[0].name == "Lab"


@pytest.mark.unit
class TestCustomFieldMethods:
    """Test CustomField model methods."""

    def test_field_type_enum(self):
        """Test FieldType enum values."""
        from backend.src.models.custom_field import FieldType

        assert FieldType.TEXT.value == "text"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.BOOLEAN.value == "boolean"
        assert FieldType.DATE.value == "date"
        assert FieldType.URL.value == "url"


@pytest.mark.unit
class TestStockTransactionMethods:
    """Test StockTransaction model methods."""

    def test_transaction_type_enum(self):
        """Test TransactionType enum values."""
        from backend.src.models.stock_transaction import TransactionType

        assert TransactionType.ADD.value == "add"
        assert TransactionType.REMOVE.value == "remove"
        assert TransactionType.MOVE.value == "move"
        assert TransactionType.ADJUST.value == "adjust"

    def test_transaction_display_description(self):
        """Test StockTransaction display_description property."""
        from backend.src.models.stock_transaction import (
            StockTransaction,
            TransactionType,
        )

        transaction = StockTransaction(
            transaction_type=TransactionType.ADD,
            quantity_change=10,
            notes="Test purchase",
        )

        result = transaction.display_description
        assert "ADD" in result
        assert "+10" in result
        assert "Test purchase" in result


@pytest.mark.unit
class TestAttachmentMethods:
    """Test Attachment model methods."""

    def test_attachment_display_name(self):
        """Test Attachment display_name property."""
        from backend.src.models.attachment import Attachment

        attachment = Attachment(
            filename="datasheet.pdf", original_filename="Original Datasheet.pdf"
        )

        # Should prefer original filename
        assert attachment.display_name == "Original Datasheet.pdf"

        # Fallback to filename
        attachment.original_filename = None
        assert attachment.display_name == "datasheet.pdf"
