"""
Unit tests for service layer with mocked external dependencies.
Focuses on high-coverage testing of business logic without external services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.component_service import ComponentService
from src.services.project_service import ProjectService
from src.services.file_storage import FileStorageService
from src.services.kicad_service import KiCadService


class TestComponentServiceMocked:
    """Test ComponentService with mocked dependencies."""

    @patch('src.services.component_service.get_session')
    def test_search_components_basic(self, mock_get_session):
        """Test basic component search functionality."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock component results
        mock_component = Mock()
        mock_component.id = "comp-123"
        mock_component.name = "Test Resistor"
        mock_component.part_number = "R123"

        mock_session.query.return_value.options.return_value.filter.return_value.limit.return_value.all.return_value = [mock_component]

        service = ComponentService()
        results = service.search_components("resistor")

        assert len(results) == 1
        assert results[0].name == "Test Resistor"

    @patch('src.services.component_service.get_session')
    def test_get_component_by_id(self, mock_get_session):
        """Test getting component by ID."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_component = Mock()
        mock_component.id = "comp-456"
        mock_component.name = "Test Capacitor"

        mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_component

        service = ComponentService()
        result = service.get_component_by_id("comp-456")

        assert result.id == "comp-456"
        assert result.name == "Test Capacitor"

    @patch('src.services.component_service.get_session')
    def test_create_component_basic(self, mock_get_session):
        """Test basic component creation."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        service = ComponentService()

        component_data = {
            "name": "New Resistor",
            "part_number": "R999",
            "manufacturer": "TestCorp",
            "description": "Test resistor component"
        }

        # Mock the component creation
        with patch('src.models.Component') as mock_component_class:
            mock_component = Mock()
            mock_component.id = "new-comp-123"
            mock_component_class.return_value = mock_component

            result = service.create_component(component_data)

            assert result.id == "new-comp-123"
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


class TestProjectServiceMocked:
    """Test ProjectService with mocked dependencies."""

    @patch('src.services.project_service.get_session')
    def test_get_project_by_id(self, mock_get_session):
        """Test getting project by ID."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_project = Mock()
        mock_project.id = "proj-123"
        mock_project.name = "Test Project"

        mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_project

        service = ProjectService()
        result = service.get_project_by_id("proj-123")

        assert result.id == "proj-123"
        assert result.name == "Test Project"

    @patch('src.services.project_service.get_session')
    def test_create_project_basic(self, mock_get_session):
        """Test basic project creation."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        service = ProjectService()

        project_data = {
            "name": "New Project",
            "description": "Test project",
            "status": "planning"
        }

        with patch('src.models.Project') as mock_project_class:
            mock_project = Mock()
            mock_project.id = "new-proj-456"
            mock_project_class.return_value = mock_project

            result = service.create_project(project_data)

            assert result.id == "new-proj-456"
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @patch('src.services.project_service.get_session')
    def test_add_component_to_project(self, mock_get_session):
        """Test adding component to project."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock project and component
        mock_project = Mock()
        mock_project.id = "proj-789"
        mock_component = Mock()
        mock_component.id = "comp-789"

        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_project, mock_component]

        service = ProjectService()

        with patch('src.models.ProjectComponent') as mock_proj_comp_class:
            mock_proj_comp = Mock()
            mock_proj_comp_class.return_value = mock_proj_comp

            result = service.add_component_to_project("proj-789", "comp-789", 5)

            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


class TestFileStorageServiceMocked:
    """Test FileStorageService with mocked file operations."""

    @patch('src.services.file_storage.os.makedirs')
    @patch('src.services.file_storage.Path')
    def test_init_creates_directories(self, mock_path, mock_makedirs):
        """Test FileStorageService initialization creates required directories."""
        mock_path.return_value.exists.return_value = False

        service = FileStorageService("/test/storage")

        mock_makedirs.assert_called()

    @patch('src.services.file_storage.os.makedirs')
    @patch('src.services.file_storage.Path')
    def test_get_component_hash_consistent(self, mock_path, mock_makedirs):
        """Test component hash generation is consistent."""
        service = FileStorageService("/test/storage")

        hash1 = service.get_component_hash("comp-123")
        hash2 = service.get_component_hash("comp-123")

        assert hash1 == hash2
        assert len(hash1) > 0

    @patch('src.services.file_storage.os.makedirs')
    @patch('src.services.file_storage.Path')
    def test_validate_file_checks_size(self, mock_path, mock_makedirs):
        """Test file validation checks file size limits."""
        service = FileStorageService("/test/storage")

        # Mock a large file
        mock_file = Mock()
        mock_file.size = 50 * 1024 * 1024  # 50MB
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "test.jpg"

        result = service.validate_file(mock_file)

        assert result["valid"] is False
        assert "too large" in result["error"]

    @patch('src.services.file_storage.os.makedirs')
    @patch('src.services.file_storage.Path')
    def test_validate_file_checks_type(self, mock_path, mock_makedirs):
        """Test file validation checks file types."""
        service = FileStorageService("/test/storage")

        # Mock an invalid file type
        mock_file = Mock()
        mock_file.size = 1024  # 1KB
        mock_file.content_type = "application/exe"
        mock_file.filename = "malware.exe"

        result = service.validate_file(mock_file)

        assert result["valid"] is False
        assert "Invalid file type" in result["error"]

    @patch('src.services.file_storage.os.makedirs')
    @patch('src.services.file_storage.Path')
    def test_validate_file_valid_image(self, mock_path, mock_makedirs):
        """Test file validation accepts valid images."""
        service = FileStorageService("/test/storage")

        # Mock a valid image file
        mock_file = Mock()
        mock_file.size = 1024  # 1KB
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "photo.jpg"

        result = service.validate_file(mock_file)

        assert result["valid"] is True
        assert "error" not in result


class TestKiCadServiceMocked:
    """Test KiCadService with mocked dependencies."""

    @patch('src.services.kicad_service.get_session')
    def test_get_component_kicad_data(self, mock_get_session):
        """Test getting KiCad data for component."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock component with KiCad data
        mock_component = Mock()
        mock_component.id = "comp-kicad"
        mock_kicad_data = Mock()
        mock_kicad_data.symbol_library = "symbols"
        mock_kicad_data.symbol_name = "resistor"
        mock_component.kicad_data = mock_kicad_data

        mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_component

        service = KiCadService()
        result = service.get_component_kicad_data("comp-kicad")

        assert result is not None
        assert result.symbol_library == "symbols"
        assert result.symbol_name == "resistor"

    @patch('src.services.kicad_service.get_session')
    def test_create_kicad_data_for_component(self, mock_get_session):
        """Test creating KiCad data for component."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock component without KiCad data
        mock_component = Mock()
        mock_component.id = "comp-no-kicad"
        mock_component.kicad_data = None

        mock_session.query.return_value.filter.return_value.first.return_value = mock_component

        service = KiCadService()

        kicad_data = {
            "symbol_library": "my_symbols",
            "symbol_name": "my_resistor",
            "footprint_library": "my_footprints",
            "footprint_name": "R_0603"
        }

        with patch('src.models.KiCadLibraryData') as mock_kicad_class:
            mock_kicad = Mock()
            mock_kicad_class.return_value = mock_kicad

            result = service.create_kicad_data_for_component("comp-no-kicad", kicad_data)

            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


class TestBOMServiceMocked:
    """Test BOMService with mocked provider dependencies."""

    @patch('src.services.bom_service.get_session')
    @patch('src.services.bom_service.ProviderService')
    def test_generate_component_list_bom_basic(self, mock_provider_service, mock_get_session):
        """Test generating BOM from component list."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock components
        mock_component = Mock()
        mock_component.id = "comp-bom"
        mock_component.name = "BOM Component"
        mock_component.part_number = "BOM123"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_component

        # Mock provider service
        mock_provider_service.return_value = Mock()

        from src.services.bom_service import BOMService
        service = BOMService()

        component_quantities = [("comp-bom", 10)]
        result = service.generate_component_list_bom(component_quantities, include_provider_data=False)

        assert len(result) == 1
        assert result[0].component.id == "comp-bom"
        assert result[0].quantity == 10

    @patch('src.services.bom_service.get_session')
    @patch('src.services.bom_service.ProviderService')
    def test_calculate_bom_cost(self, mock_provider_service, mock_get_session):
        """Test calculating BOM cost summary."""
        from src.services.bom_service import BOMService, BOMItem

        service = BOMService()

        # Mock BOM items with pricing
        mock_component1 = Mock()
        mock_component1.average_purchase_price = 5.0

        mock_component2 = Mock()
        mock_component2.average_purchase_price = 10.0

        bom_items = [
            BOMItem(mock_component1, 2),  # 2 * 5.0 = 10.0
            BOMItem(mock_component2, 3),  # 3 * 10.0 = 30.0
        ]

        result = service.calculate_bom_cost(bom_items)

        assert result["total_cost"] == 40.0
        assert result["total_components"] == 5  # 2 + 3
        assert result["unique_components"] == 2


class TestReportServiceMocked:
    """Test ReportService with mocked database queries."""

    @patch('src.services.report_service.get_session')
    def test_get_component_count_by_category(self, mock_get_session):
        """Test getting component count by category."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query results
        mock_results = [
            ("Resistors", 50),
            ("Capacitors", 30),
            ("ICs", 20)
        ]

        mock_session.query.return_value.join.return_value.group_by.return_value.all.return_value = mock_results

        from src.services.report_service import ReportService
        service = ReportService(mock_session)

        result = service.get_component_count_by_category()

        assert len(result) == 3
        assert result[0]["category"] == "Resistors"
        assert result[0]["count"] == 50

    @patch('src.services.report_service.get_session')
    def test_get_recent_activity_summary(self, mock_get_session):
        """Test getting recent activity summary."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock transaction count
        mock_session.query.return_value.filter.return_value.count.return_value = 15

        from src.services.report_service import ReportService
        service = ReportService(mock_session)

        result = service.get_recent_activity_summary(days=7)

        assert result["transactions_last_7_days"] == 15
        assert "period_start" in result
        assert "period_end" in result