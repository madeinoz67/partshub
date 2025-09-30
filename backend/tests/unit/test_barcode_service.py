"""
Unit tests for BarcodeService.
Tests barcode scanning functionality including mock and real implementations.
"""

import base64
import io
from unittest.mock import Mock, patch

from PIL import Image
from backend.src.services.barcode_service import BarcodeResult, BarcodeService


class TestBarcodeResult:
    """Test BarcodeResult data class."""

    def test_init_creates_valid_instance(self):
        """Test BarcodeResult creation with all parameters."""
        result = BarcodeResult(data="123456789", format_type="CODE128", confidence=0.95)

        assert result.data == "123456789"
        assert result.format == "CODE128"
        assert result.confidence == 0.95

    def test_init_default_confidence(self):
        """Test BarcodeResult creation with default confidence."""
        result = BarcodeResult(data="987654321", format_type="QRCODE")

        assert result.data == "987654321"
        assert result.format == "QRCODE"
        assert result.confidence == 1.0


class TestBarcodeService:
    """Test BarcodeService functionality."""

    def test_init_sets_supported_formats(self):
        """Test BarcodeService initialization sets supported formats."""
        service = BarcodeService()

        expected_formats = [
            "CODE128",
            "CODE39",
            "EAN13",
            "EAN8",
            "UPCA",
            "UPCE",
            "QRCODE",
            "DATAMATRIX",
            "PDF417",
        ]

        assert service.supported_formats == expected_formats

    def test_scan_barcode_from_base64_removes_data_url_prefix(self):
        """Test that data URL prefixes are correctly removed."""
        service = BarcodeService()

        # Create a simple white image for testing
        image = Image.new("RGB", (100, 100), color="white")
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        # Create base64 with data URL prefix
        base64_data = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_data}"

        with patch.object(service, "scan_barcode_from_image") as mock_scan:
            mock_scan.return_value = []
            service.scan_barcode_from_base64(data_url)

            # Should have been called with the PIL Image
            mock_scan.assert_called_once()

    def test_scan_barcode_from_base64_handles_plain_base64(self):
        """Test scanning from plain base64 without data URL prefix."""
        service = BarcodeService()

        # Create a simple white image for testing
        image = Image.new("RGB", (100, 100), color="white")
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        base64_data = base64.b64encode(img_bytes).decode("utf-8")

        with patch.object(service, "scan_barcode_from_image") as mock_scan:
            mock_scan.return_value = []
            service.scan_barcode_from_base64(base64_data)

            mock_scan.assert_called_once()

    def test_scan_barcode_from_base64_handles_invalid_data(self):
        """Test error handling for invalid base64 data."""
        service = BarcodeService()

        result = service.scan_barcode_from_base64("invalid_base64_data")
        assert result == []

    @patch("backend.src.services.barcode_service.PYZBAR_AVAILABLE", False)
    def test_scan_barcode_from_image_uses_mock_when_pyzbar_unavailable(self):
        """Test that mock scanning is used when pyzbar is not available."""
        service = BarcodeService()
        image = Image.new("RGB", (500, 400), color="white")

        with patch.object(service, "_mock_barcode_scan") as mock_scan:
            mock_scan.return_value = []
            service.scan_barcode_from_image(image)

            mock_scan.assert_called_once_with(image)

    @patch("backend.src.services.barcode_service.PYZBAR_AVAILABLE", True)
    @patch("backend.src.services.barcode_service.pyzbar")
    def test_scan_barcode_from_image_with_pyzbar_success(self, mock_pyzbar):
        """Test successful barcode scanning with pyzbar."""
        service = BarcodeService()
        image = Image.new("RGB", (100, 100), color="white")

        # Mock pyzbar decode result
        mock_barcode = Mock()
        mock_barcode.data = b"123456789"
        mock_barcode.type = "CODE128"
        mock_pyzbar.decode.return_value = [mock_barcode]

        results = service.scan_barcode_from_image(image)

        assert len(results) == 1
        assert results[0].data == "123456789"
        assert results[0].format == "CODE128"
        assert results[0].confidence == 1.0

    @patch("backend.src.services.barcode_service.PYZBAR_AVAILABLE", True)
    @patch("backend.src.services.barcode_service.pyzbar")
    def test_scan_barcode_from_image_converts_non_rgb_image(self, mock_pyzbar):
        """Test that non-RGB images are converted to RGB."""
        service = BarcodeService()
        # Create a grayscale image
        image = Image.new("L", (100, 100), color=128)

        mock_pyzbar.decode.return_value = []

        service.scan_barcode_from_image(image)

        # Should have been called with converted RGB image
        mock_pyzbar.decode.assert_called_once()
        called_image = mock_pyzbar.decode.call_args[0][0]
        assert called_image.mode == "RGB"

    @patch("backend.src.services.barcode_service.PYZBAR_AVAILABLE", True)
    @patch("backend.src.services.barcode_service.pyzbar")
    def test_scan_barcode_from_image_handles_decode_error(self, mock_pyzbar):
        """Test error handling during barcode decoding."""
        service = BarcodeService()
        image = Image.new("RGB", (100, 100), color="white")

        # Mock barcode with invalid data
        mock_barcode = Mock()
        mock_barcode.data = b"\xff\xfe"  # Invalid UTF-8
        mock_barcode.type = "CODE128"
        mock_pyzbar.decode.return_value = [mock_barcode]

        # Should not raise exception, just skip invalid barcode
        results = service.scan_barcode_from_image(image)
        assert results == []

    @patch("backend.src.services.barcode_service.PYZBAR_AVAILABLE", True)
    @patch("backend.src.services.barcode_service.pyzbar")
    def test_scan_barcode_from_image_handles_pyzbar_exception(self, mock_pyzbar):
        """Test error handling when pyzbar raises exception."""
        service = BarcodeService()
        image = Image.new("RGB", (100, 100), color="white")

        mock_pyzbar.decode.side_effect = Exception("Pyzbar error")

        results = service.scan_barcode_from_image(image)
        assert results == []

    def test_mock_barcode_scan_large_image(self):
        """Test mock barcode scanning for large images."""
        service = BarcodeService()
        # Large image should trigger QR code mock
        image = Image.new("RGB", (500, 400), color="white")

        results = service._mock_barcode_scan(image)

        assert len(results) >= 1
        # Should contain a QR code result
        qr_results = [r for r in results if r.format == "QRCODE"]
        assert len(qr_results) >= 1
        assert "STM32F407VGT6" in qr_results[0].data

    def test_mock_barcode_scan_medium_image(self):
        """Test mock barcode scanning for medium images."""
        service = BarcodeService()
        # Medium image should trigger CODE128 mock
        image = Image.new("RGB", (250, 150), color="white")

        results = service._mock_barcode_scan(image)

        # Should contain at least one result
        assert len(results) >= 1

    def test_mock_barcode_scan_small_image(self):
        """Test mock barcode scanning for small images."""
        service = BarcodeService()
        # Small image should trigger different mock behavior
        image = Image.new("RGB", (100, 50), color="white")

        results = service._mock_barcode_scan(image)

        # Should contain at least one result
        assert len(results) >= 1

    def test_search_component_by_barcode_simple_match(self):
        """Test searching components by barcode data."""
        service = BarcodeService()

        with patch("backend.src.services.barcode_service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock component found by part number
            mock_component = Mock()
            mock_component.id = "comp-123"
            mock_component.name = "Test Component"
            mock_component.part_number = "TEST123"

            mock_session.query.return_value.filter.return_value.first.return_value = (
                mock_component
            )

            result = service.search_component_by_barcode("TEST123")

            assert result is not None
            assert result["component_id"] == "comp-123"
            assert result["component_name"] == "Test Component"
            assert result["part_number"] == "TEST123"
            assert result["match_type"] == "part_number"

    def test_search_component_by_barcode_no_match(self):
        """Test searching components when no match found."""
        service = BarcodeService()

        with patch("backend.src.services.barcode_service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock no component found
            mock_session.query.return_value.filter.return_value.first.return_value = (
                None
            )

            result = service.search_component_by_barcode("UNKNOWN123")

            assert result is None

    def test_search_component_by_barcode_structured_data(self):
        """Test searching components with structured barcode data."""
        service = BarcodeService()

        # Test structured data format: "part_number|manufacturer|description"
        barcode_data = "STM32F407VGT6|STMicroelectronics|ARM Cortex-M4 MCU"

        with patch("backend.src.services.barcode_service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock component found
            mock_component = Mock()
            mock_component.id = "comp-456"
            mock_component.name = "STM32 MCU"
            mock_component.part_number = "STM32F407VGT6"
            mock_component.manufacturer = "STMicroelectronics"

            mock_session.query.return_value.filter.return_value.first.return_value = (
                mock_component
            )

            result = service.search_component_by_barcode(barcode_data)

            assert result is not None
            assert result["component_id"] == "comp-456"
            assert result["part_number"] == "STM32F407VGT6"

    def test_parse_structured_barcode_data_pipe_format(self):
        """Test parsing structured barcode data with pipe separators."""
        service = BarcodeService()

        data = "STM32F407VGT6|STMicroelectronics|ARM Cortex-M4 MCU"
        result = service.parse_structured_barcode_data(data)

        expected = {
            "part_number": "STM32F407VGT6",
            "manufacturer": "STMicroelectronics",
            "description": "ARM Cortex-M4 MCU",
        }
        assert result == expected

    def test_parse_structured_barcode_data_json_format(self):
        """Test parsing structured barcode data in JSON format."""
        service = BarcodeService()

        data = '{"part_number": "R123", "value": "10k", "tolerance": "1%"}'
        result = service.parse_structured_barcode_data(data)

        expected = {"part_number": "R123", "value": "10k", "tolerance": "1%"}
        assert result == expected

    def test_parse_structured_barcode_data_invalid_json(self):
        """Test parsing invalid JSON barcode data."""
        service = BarcodeService()

        data = '{"invalid": json}'
        result = service.parse_structured_barcode_data(data)

        # Should return empty dict for invalid JSON
        assert result == {}

    def test_parse_structured_barcode_data_plain_text(self):
        """Test parsing plain text barcode data."""
        service = BarcodeService()

        data = "SIMPLE_PART_NUMBER"
        result = service.parse_structured_barcode_data(data)

        # Should return empty dict for plain text
        assert result == {}

    def test_end_to_end_barcode_processing(self):
        """Test complete barcode processing workflow."""
        service = BarcodeService()

        # Create a test image
        image = Image.new("RGB", (500, 400), color="white")
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()
        base64_data = base64.b64encode(img_bytes).decode("utf-8")

        with patch("backend.src.services.barcode_service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock component found
            mock_component = Mock()
            mock_component.id = "comp-789"
            mock_component.name = "Mock Component"
            mock_component.part_number = "STM32F407VGT6"

            mock_session.query.return_value.filter.return_value.first.return_value = (
                mock_component
            )

            # Process barcode (will use mock scanning)
            barcode_results = service.scan_barcode_from_base64(base64_data)

            # Search for components based on barcode results
            component_matches = []
            for barcode in barcode_results:
                match = service.search_component_by_barcode(barcode.data)
                if match:
                    component_matches.append(match)

            # Should find at least one match from mock data
            assert len(component_matches) >= 1
