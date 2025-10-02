"""
Test-Driven Development tests for FileStorageService.
Tests written BEFORE implementation to define expected behavior.
"""

import io
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image


class TestFileStorageService:
    """Test suite for FileStorageService following TDD principles."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for test file storage."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def file_storage_service(self, temp_storage_dir):
        """Create FileStorageService instance with temp directory."""
        from backend.src.services.file_storage import FileStorageService

        return FileStorageService(base_path=temp_storage_dir)

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample JPEG image bytes for testing."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        return img_bytes.getvalue()

    @pytest.fixture
    def sample_pdf_bytes(self):
        """Create sample PDF bytes for testing."""
        # Minimal PDF file structure
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000074 00000 n
0000000120 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
178
%%EOF"""

    def test_init_creates_base_directory(self, temp_storage_dir):
        """Test that FileStorageService creates base directory on initialization."""
        from backend.src.services.file_storage import FileStorageService

        # Create service with non-existent directory
        service_dir = Path(temp_storage_dir) / "new_storage"
        FileStorageService(base_path=str(service_dir))

        # Verify directory was created
        assert service_dir.exists()
        assert service_dir.is_dir()

    def test_get_component_hash_consistent(self, file_storage_service):
        """Test that component hash generation is consistent."""
        component_id = "test-component-123"

        hash1 = file_storage_service._get_component_hash(component_id)
        hash2 = file_storage_service._get_component_hash(component_id)

        assert hash1 == hash2
        assert len(hash1) == 2  # First 2 chars of MD5
        assert isinstance(hash1, str)

    def test_get_component_dir_structure(self, file_storage_service, temp_storage_dir):
        """Test that component directory follows hashed structure."""
        component_id = "test-component-123"

        expected_hash = file_storage_service._get_component_hash(component_id)
        component_dir = file_storage_service._get_component_dir(component_id)

        expected_path = Path(temp_storage_dir) / expected_hash / component_id
        assert component_dir == expected_path

    def test_validate_file_jpeg_valid(self, file_storage_service, sample_image_bytes):
        """Test validation of valid JPEG file."""
        mime_type, safe_filename = file_storage_service._validate_file(
            sample_image_bytes, "test.jpg"
        )

        assert mime_type == "image/jpeg"
        assert safe_filename == "test.jpg"

    def test_validate_file_pdf_valid(self, file_storage_service, sample_pdf_bytes):
        """Test validation of valid PDF file."""
        mime_type, safe_filename = file_storage_service._validate_file(
            sample_pdf_bytes, "datasheet.pdf"
        )

        assert mime_type == "application/pdf"
        assert safe_filename == "datasheet.pdf"

    def test_validate_file_too_large(self, file_storage_service):
        """Test that oversized files are rejected."""
        # Create file content larger than MAX_FILE_SIZE
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB

        with pytest.raises(ValueError, match="File size exceeds maximum"):
            file_storage_service._validate_file(large_content, "large.jpg")

    def test_validate_file_invalid_type(self, file_storage_service):
        """Test that invalid file types are rejected."""
        invalid_content = b"invalid content"

        with pytest.raises(ValueError, match="File type .* is not allowed"):
            file_storage_service._validate_file(invalid_content, "test.exe")

    def test_validate_file_cleans_filename(
        self, file_storage_service, sample_image_bytes
    ):
        """Test that unsafe filenames are cleaned."""
        mime_type, safe_filename = file_storage_service._validate_file(
            sample_image_bytes, "test@#$%^&*()file.jpg"
        )

        assert mime_type == "image/jpeg"
        assert safe_filename == "testfile.jpg"

    def test_validate_file_generates_filename_if_empty(
        self, file_storage_service, sample_image_bytes
    ):
        """Test that filename is generated if original is invalid."""
        mime_type, safe_filename = file_storage_service._validate_file(
            sample_image_bytes, "!@#$%^&*()"
        )

        assert mime_type == "image/jpeg"
        assert safe_filename.endswith(".jpg")
        assert len(safe_filename) > 4  # Has hash prefix

    def test_store_file_image_success(self, file_storage_service, sample_image_bytes):
        """Test successful image file storage."""
        component_id = "test-component-123"
        filename = "component_image.jpg"

        (
            file_path,
            thumbnail_path,
            file_size,
            mime_type,
            safe_filename,
        ) = file_storage_service.store_file(
            component_id, sample_image_bytes, filename, "image"
        )

        # Verify return values
        assert mime_type == "image/jpeg"
        assert safe_filename == "component_image.jpg"
        assert file_size == len(sample_image_bytes)
        assert "images" in file_path
        assert thumbnail_path is not None
        assert "thumb.jpg" in thumbnail_path

        # Verify files exist
        full_path = file_storage_service.get_file_path(file_path)
        assert full_path.exists()

        thumb_path = file_storage_service.get_file_path(thumbnail_path)
        assert thumb_path.exists()

    def test_store_file_pdf_success(self, file_storage_service, sample_pdf_bytes):
        """Test successful PDF file storage."""
        component_id = "test-component-456"
        filename = "datasheet.pdf"

        (
            file_path,
            thumbnail_path,
            file_size,
            mime_type,
            safe_filename,
        ) = file_storage_service.store_file(
            component_id, sample_pdf_bytes, filename, "datasheet"
        )

        # Verify return values
        assert mime_type == "application/pdf"
        assert safe_filename == "datasheet.pdf"
        assert file_size == len(sample_pdf_bytes)
        assert "datasheets" in file_path
        assert thumbnail_path is None  # No thumbnail for PDF

        # Verify file exists
        full_path = file_storage_service.get_file_path(file_path)
        assert full_path.exists()

    def test_store_file_prevents_name_conflicts(
        self, file_storage_service, sample_image_bytes
    ):
        """Test that storing same filename twice creates unique files."""
        component_id = "test-component-789"
        filename = "duplicate.jpg"

        # Store first file
        file_path1, _, _, _, _ = file_storage_service.store_file(
            component_id, sample_image_bytes, filename, "image"
        )

        # Store second file with same name
        file_path2, _, _, _, _ = file_storage_service.store_file(
            component_id, sample_image_bytes, filename, "image"
        )

        # Verify different paths
        assert file_path1 != file_path2
        assert file_storage_service.get_file_path(file_path1).exists()
        assert file_storage_service.get_file_path(file_path2).exists()

    @patch("backend.src.services.file_storage.Image.open")
    def test_generate_thumbnail_failure_handling(
        self, mock_image_open, file_storage_service
    ):
        """Test thumbnail generation failure handling."""
        # Mock Image.open to raise exception
        mock_image_open.side_effect = Exception("Mock PIL error")

        # This should not raise an exception but return False
        result = file_storage_service._generate_thumbnail(
            Path("fake_path.jpg"), Path("fake_thumb.jpg")
        )

        assert result is False

    def test_delete_file_success(self, file_storage_service, sample_image_bytes):
        """Test successful file deletion."""
        component_id = "test-component-delete"
        filename = "to_delete.jpg"

        # Store file first
        file_path, thumbnail_path, _, _, _ = file_storage_service.store_file(
            component_id, sample_image_bytes, filename, "image"
        )

        # Verify files exist
        assert file_storage_service.file_exists(file_path)
        assert file_storage_service.file_exists(thumbnail_path)

        # Delete files
        result = file_storage_service.delete_file(file_path, thumbnail_path)

        assert result is True
        assert not file_storage_service.file_exists(file_path)
        assert not file_storage_service.file_exists(thumbnail_path)

    def test_delete_file_nonexistent(self, file_storage_service):
        """Test deletion of non-existent file."""
        result = file_storage_service.delete_file("nonexistent/file.jpg")
        assert result is True  # Should not fail

    def test_file_exists_check(self, file_storage_service, sample_image_bytes):
        """Test file existence checking."""
        component_id = "test-component-exists"
        filename = "exists_test.jpg"

        # File doesn't exist initially
        fake_path = "fake/path/file.jpg"
        assert not file_storage_service.file_exists(fake_path)

        # Store file
        file_path, _, _, _, _ = file_storage_service.store_file(
            component_id, sample_image_bytes, filename, "image"
        )

        # File exists after storage
        assert file_storage_service.file_exists(file_path)

    def test_get_component_files(
        self, file_storage_service, sample_image_bytes, sample_pdf_bytes
    ):
        """Test getting all files for a component."""
        component_id = "test-component-files"

        # Initially no files
        files = file_storage_service.get_component_files(component_id)
        assert files == []

        # Store multiple files
        file_storage_service.store_file(
            component_id, sample_image_bytes, "image1.jpg", "image"
        )
        file_storage_service.store_file(
            component_id, sample_pdf_bytes, "datasheet.pdf", "datasheet"
        )
        file_storage_service.store_file(
            component_id, sample_image_bytes, "image2.jpg", "image"
        )

        # Get files
        files = file_storage_service.get_component_files(component_id)

        # Should have at least 4 files (2 images + 2 thumbnails + 1 PDF)
        assert len(files) >= 4

        # Check file types
        file_names = [f.name for f in files]
        jpg_files = [name for name in file_names if name.endswith(".jpg")]
        pdf_files = [name for name in file_names if name.endswith(".pdf")]

        assert len(pdf_files) >= 1
        assert len(jpg_files) >= 3  # 2 original + 2 thumbnails (at least)

    def test_get_extension_from_mime(self, file_storage_service):
        """Test MIME type to extension mapping."""
        assert file_storage_service._get_extension_from_mime("image/jpeg") == ".jpg"
        assert file_storage_service._get_extension_from_mime("image/png") == ".png"
        assert (
            file_storage_service._get_extension_from_mime("application/pdf") == ".pdf"
        )
        assert file_storage_service._get_extension_from_mime("unknown/type") == ""

    def test_concurrent_file_storage(self, file_storage_service, sample_image_bytes):
        """Test that concurrent file storage operations work correctly."""
        component_id = "test-component-concurrent"

        # Simulate concurrent storage of same file
        results = []
        for i in range(5):
            result = file_storage_service.store_file(
                component_id, sample_image_bytes, f"concurrent_{i}.jpg", "image"
            )
            results.append(result)

        # All files should be stored with unique paths
        file_paths = [result[0] for result in results]
        assert len(set(file_paths)) == 5  # All unique paths

        # All files should exist
        for file_path, _, _, _, _ in results:
            assert file_storage_service.file_exists(file_path)
