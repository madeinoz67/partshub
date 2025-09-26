"""
File storage service for component attachments.
Implemented following TDD approach based on comprehensive test requirements.
"""

import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
import magic
import logging

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Allowed file types
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
ALLOWED_DOCUMENT_TYPES = {'application/pdf'}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)


class FileStorageService:
    """Service for handling file storage with hashed directory structure."""

    def __init__(self, base_path: str = None):
        """Initialize file storage service.

        Args:
            base_path: Base directory for file storage. If None, uses default based on environment
        """
        if base_path is None:
            # Use different defaults based on environment
            import os
            if os.getenv("TESTING") == "true":
                # For testing, use local project directory
                base_path = "./test_data/attachments"
            elif os.getenv("ENVIRONMENT") == "production":
                # For production, use container path
                base_path = "/app/data/attachments"
            else:
                # For development, use local data directory
                base_path = "./data/attachments"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_component_hash(self, component_id: str) -> str:
        """Generate hash prefix for component directory structure.

        Args:
            component_id: Component ID to hash

        Returns:
            First 2 characters of MD5 hash
        """
        return hashlib.md5(component_id.encode()).hexdigest()[:2]

    def _get_component_dir(self, component_id: str) -> Path:
        """Get component directory path with hashed structure.

        Args:
            component_id: Component ID

        Returns:
            Path to component directory
        """
        hash_prefix = self._get_component_hash(component_id)
        return self.base_path / hash_prefix / component_id

    def _validate_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """Validate file content and return MIME type and cleaned filename.

        Args:
            file_content: File content bytes
            filename: Original filename

        Returns:
            Tuple of (mime_type, safe_filename)

        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        if len(file_content) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {MAX_FILE_SIZE // (1024*1024)}MB")

        # Detect MIME type
        mime_type = magic.from_buffer(file_content, mime=True)

        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"File type '{mime_type}' is not allowed")

        # Additional check for images
        if mime_type in ALLOWED_IMAGE_TYPES and len(file_content) > MAX_IMAGE_SIZE:
            raise ValueError(f"Image size exceeds maximum of {MAX_IMAGE_SIZE // (1024*1024)}MB")

        # Clean filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-").strip()
        if not safe_filename:
            # Generate filename from hash if original is invalid
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            extension = self._get_extension_from_mime(mime_type)
            safe_filename = f"{file_hash}{extension}"

        return mime_type, safe_filename

    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Get file extension from MIME type."""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'application/pdf': '.pdf'
        }
        return extensions.get(mime_type, '')

    def _generate_thumbnail(self, image_path: Path, thumbnail_path: Path) -> bool:
        """Generate thumbnail for image file.

        Args:
            image_path: Path to original image
            thumbnail_path: Path where thumbnail should be saved

        Returns:
            True if thumbnail was generated successfully
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, cannot generate thumbnails")
            return False

        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'LA'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Generate thumbnail maintaining aspect ratio
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

                # Center crop to exact size
                thumb = ImageOps.fit(img, THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

                # Save as JPEG for consistent format
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                thumb.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

                return True

        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return False

    def store_file(self, component_id: str, file_content: bytes, filename: str,
                   attachment_type: Optional[str] = None) -> Tuple[str, Optional[str], int, str, str]:
        """Store file with hashed directory structure.

        Args:
            component_id: Component ID
            file_content: File content bytes
            filename: Original filename
            attachment_type: Type of attachment (datasheet, image, etc.)

        Returns:
            Tuple of (file_path, thumbnail_path, file_size, mime_type, safe_filename)

        Raises:
            ValueError: If file is invalid
            IOError: If file cannot be stored
        """
        # Validate file
        mime_type, safe_filename = self._validate_file(file_content, filename)

        # Generate unique filename to prevent conflicts
        file_id = str(uuid.uuid4())[:8]
        name_without_ext = Path(safe_filename).stem
        extension = Path(safe_filename).suffix
        unique_filename = f"{name_without_ext}_{file_id}{extension}"

        # Create component directory
        component_dir = self._get_component_dir(component_id)
        component_dir.mkdir(parents=True, exist_ok=True)

        # Determine subdirectory based on type
        if attachment_type == 'datasheet' or mime_type == 'application/pdf':
            subdir = component_dir / 'datasheets'
        elif mime_type in ALLOWED_IMAGE_TYPES:
            subdir = component_dir / 'images'
        else:
            subdir = component_dir / 'documents'

        subdir.mkdir(parents=True, exist_ok=True)

        # Store file
        file_path = subdir / unique_filename
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
        except IOError as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise IOError(f"Failed to store file: {e}")

        # Generate thumbnail for images
        thumbnail_path = None
        if mime_type in ALLOWED_IMAGE_TYPES:
            thumb_filename = f"{Path(unique_filename).stem}_thumb.jpg"
            thumbnail_full_path = subdir / thumb_filename

            if self._generate_thumbnail(file_path, thumbnail_full_path):
                # Return relative path from base_path
                thumbnail_path = str(thumbnail_full_path.relative_to(self.base_path))

        # Return relative path from base_path
        relative_file_path = str(file_path.relative_to(self.base_path))

        return relative_file_path, thumbnail_path, len(file_content), mime_type, safe_filename

    def delete_file(self, file_path: str, thumbnail_path: Optional[str] = None) -> bool:
        """Delete file and its thumbnail.

        Args:
            file_path: Relative file path from base_path
            thumbnail_path: Relative thumbnail path from base_path

        Returns:
            True if file was deleted successfully
        """
        try:
            # Delete main file
            full_path = self.base_path / file_path
            if full_path.exists():
                full_path.unlink()

            # Delete thumbnail if exists
            if thumbnail_path:
                thumb_path = self.base_path / thumbnail_path
                if thumb_path.exists():
                    thumb_path.unlink()

            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path from relative path.

        Args:
            relative_path: Relative path from base_path

        Returns:
            Absolute path to file
        """
        return self.base_path / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists.

        Args:
            relative_path: Relative path from base_path

        Returns:
            True if file exists
        """
        return self.get_file_path(relative_path).exists()

    def get_component_files(self, component_id: str) -> List[Path]:
        """Get all files for a component.

        Args:
            component_id: Component ID

        Returns:
            List of file paths
        """
        component_dir = self._get_component_dir(component_id)
        if not component_dir.exists():
            return []

        files = []
        for subdir in component_dir.iterdir():
            if subdir.is_dir():
                files.extend([f for f in subdir.iterdir() if f.is_file()])

        return files


# Global file storage service instance - initialized on first use
file_storage = FileStorageService()