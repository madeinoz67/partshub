"""
Provider Attachment Service for auto-downloading datasheets and images from component providers.
Integrates with FileStorageService and AttachmentService to automatically download and store
files from external provider URLs.
"""

import asyncio
import logging
import mimetypes
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp

from ..database import get_db
from ..providers.base_provider import ComponentSearchResult
from ..services.attachment_service import AttachmentService
from ..services.file_storage import file_storage

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 2.0, burst_size: int = 5):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, blocking until available."""
        async with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size, self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return

            # Wait for next token
            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
            self.tokens = 0


class ProviderAttachmentService:
    """Service for auto-downloading component attachments from providers."""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout

        # Rate limiting per domain to be good API citizens
        self.rate_limiters: dict[str, RateLimiter] = defaultdict(
            lambda: RateLimiter(requests_per_second=1.0, burst_size=3)
        )

        # Track recent downloads to avoid duplicates
        self.recent_downloads: dict[str, float] = {}
        self.download_cache_duration = 3600  # 1 hour cache

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={
                    "User-Agent": "PartsHub/1.0 (Component Management System)",
                    "Accept": "application/pdf,image/*,*/*",
                },
            )
        return self.session

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _should_download_url(self, url: str) -> bool:
        """Check if URL should be downloaded based on recent cache."""
        now = time.time()

        # Clean old entries
        expired_keys = [
            k
            for k, v in self.recent_downloads.items()
            if now - v > self.download_cache_duration
        ]
        for key in expired_keys:
            del self.recent_downloads[key]

        # Check if recently downloaded
        if url in self.recent_downloads:
            logger.info(f"Skipping recent download: {url}")
            return False

        return True

    async def _apply_rate_limit(self, url: str):
        """Apply rate limiting based on URL domain."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if domain:
                rate_limiter = self.rate_limiters[domain]
                await rate_limiter.acquire()
                logger.debug(f"Rate limit applied for domain: {domain}")
        except Exception as e:
            logger.warning(f"Could not apply rate limiting for {url}: {e}")

    async def download_file_from_url(
        self, url: str, max_size: int | None = None
    ) -> tuple[bytes, str, str] | None:
        """
        Download file from URL and return content, filename, and MIME type.
        Includes rate limiting and duplicate detection for good API citizenship.

        Args:
            url: URL to download from
            max_size: Maximum file size in bytes (defaults to service limit)

        Returns:
            Tuple of (file_content, filename, mime_type) or None if failed
        """
        if not url:
            return None

        # Check if we should download this URL
        if not await self._should_download_url(url):
            return None

        max_size = max_size or self.max_file_size

        try:
            # Apply rate limiting
            await self._apply_rate_limit(url)

            session = await self._get_session()

            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {url}: HTTP {response.status}")
                    return None

                # Check content length if provided
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_size:
                    logger.warning(
                        f"File too large: {content_length} bytes > {max_size}"
                    )
                    return None

                # Read content in chunks to avoid memory issues
                content = bytearray()
                async for chunk in response.content.iter_chunked(8192):
                    content.extend(chunk)
                    if len(content) > max_size:
                        logger.warning(
                            f"File too large during download: {len(content)} bytes > {max_size}"
                        )
                        return None

                if not content:
                    logger.warning(f"Empty file downloaded from {url}")
                    return None

                # Determine MIME type
                mime_type = (
                    response.headers.get("Content-Type", "").split(";")[0].strip()
                )
                if not mime_type:
                    # Fallback to guessing from URL
                    mime_type, _ = mimetypes.guess_type(url)
                    mime_type = mime_type or "application/octet-stream"

                # Generate filename
                parsed_url = urlparse(url)
                filename = Path(parsed_url.path).name
                if not filename or "." not in filename:
                    # Generate filename based on MIME type
                    extension = mimetypes.guess_extension(mime_type) or ".bin"
                    filename = f"download_{hash(url) & 0x7fffffff}{extension}"

                # Mark as recently downloaded
                self.recent_downloads[url] = time.time()

                logger.info(f"Successfully downloaded {len(content)} bytes from {url}")
                return bytes(content), filename, mime_type

        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading from {url}")
        except Exception as e:
            logger.error(f"Error downloading from {url}: {e}")

        return None

    async def download_component_attachments(
        self,
        component_id: str,
        search_result: ComponentSearchResult,
        download_options: dict[str, bool] = None,
    ) -> dict[str, Any]:
        """
        Download attachments for a component based on provider search results.

        Args:
            component_id: ID of the component to attach files to
            search_result: Provider search result containing URLs
            download_options: Dict with keys 'datasheet', 'image' (defaults to both True)

        Returns:
            Dict with download results and created attachment info
        """
        if download_options is None:
            download_options = {"datasheet": True, "image": True}

        results = {
            "component_id": component_id,
            "provider": search_result.provider_id,
            "downloads": [],
            "errors": [],
        }

        # Get database session
        db = next(get_db())
        attachment_service = AttachmentService(db)

        try:
            # Download datasheet if available and requested
            if download_options.get("datasheet", True) and search_result.datasheet_url:
                try:
                    download_result = await self.download_file_from_url(
                        search_result.datasheet_url
                    )
                    if download_result:
                        file_content, filename, mime_type = download_result

                        # Store file using FileStorageService
                        (
                            file_path,
                            thumbnail_path,
                            file_size,
                            detected_mime,
                            safe_filename,
                        ) = file_storage.store_file(
                            component_id=component_id,
                            file_content=file_content,
                            filename=filename,
                            attachment_type="datasheet",
                        )

                        # Create attachment record
                        attachment_data = {
                            "component_id": component_id,
                            "filename": safe_filename,
                            "original_filename": filename,
                            "file_size": file_size,
                            "mime_type": detected_mime,
                            "file_path": file_path,
                            "thumbnail_path": thumbnail_path,
                            "title": f"{search_result.part_number} Datasheet",
                            "description": f"Auto-downloaded from {search_result.provider_id}",
                            "attachment_type": "datasheet",
                            "display_order": 0,
                        }

                        attachment = attachment_service.create_attachment(
                            attachment_data
                        )

                        results["downloads"].append(
                            {
                                "type": "datasheet",
                                "url": search_result.datasheet_url,
                                "attachment_id": attachment.id,
                                "filename": safe_filename,
                                "file_size": file_size,
                                "mime_type": detected_mime,
                            }
                        )

                        logger.info(
                            f"Successfully downloaded datasheet for component {component_id}"
                        )

                except Exception as e:
                    error_msg = f"Failed to download datasheet: {e}"
                    logger.error(error_msg)
                    results["errors"].append(
                        {
                            "type": "datasheet",
                            "url": search_result.datasheet_url,
                            "error": error_msg,
                        }
                    )

            # Download image if available and requested
            if download_options.get("image", True) and search_result.image_url:
                try:
                    download_result = await self.download_file_from_url(
                        search_result.image_url
                    )
                    if download_result:
                        file_content, filename, mime_type = download_result

                        # Store file using FileStorageService
                        (
                            file_path,
                            thumbnail_path,
                            file_size,
                            detected_mime,
                            safe_filename,
                        ) = file_storage.store_file(
                            component_id=component_id,
                            file_content=file_content,
                            filename=filename,
                            attachment_type="image",
                        )

                        # Set as primary image if it's the first image
                        is_primary = not attachment_service.get_primary_image(
                            component_id
                        )

                        # Create attachment record
                        attachment_data = {
                            "component_id": component_id,
                            "filename": safe_filename,
                            "original_filename": filename,
                            "file_size": file_size,
                            "mime_type": detected_mime,
                            "file_path": file_path,
                            "thumbnail_path": thumbnail_path,
                            "title": f"{search_result.part_number} Image",
                            "description": f"Auto-downloaded from {search_result.provider_id}",
                            "attachment_type": "image",
                            "is_primary_image": is_primary,
                            "display_order": 1,
                        }

                        attachment = attachment_service.create_attachment(
                            attachment_data
                        )

                        results["downloads"].append(
                            {
                                "type": "image",
                                "url": search_result.image_url,
                                "attachment_id": attachment.id,
                                "filename": safe_filename,
                                "file_size": file_size,
                                "mime_type": detected_mime,
                                "is_primary_image": is_primary,
                                "thumbnail_available": thumbnail_path is not None,
                            }
                        )

                        logger.info(
                            f"Successfully downloaded image for component {component_id}"
                        )

                except Exception as e:
                    error_msg = f"Failed to download image: {e}"
                    logger.error(error_msg)
                    results["errors"].append(
                        {
                            "type": "image",
                            "url": search_result.image_url,
                            "error": error_msg,
                        }
                    )

        finally:
            db.close()

        return results

    async def download_attachments_for_components(
        self,
        components_with_results: list[tuple[str, ComponentSearchResult]],
        download_options: dict[str, bool] = None,
    ) -> list[dict[str, Any]]:
        """
        Download attachments for multiple components concurrently.

        Args:
            components_with_results: List of (component_id, search_result) tuples
            download_options: Download options to apply to all components

        Returns:
            List of download results for each component
        """
        if not components_with_results:
            return []

        # Create download tasks
        tasks = []
        for component_id, search_result in components_with_results:
            task = self.download_component_attachments(
                component_id, search_result, download_options
            )
            tasks.append(task)

        # Execute downloads concurrently with limited concurrency
        # Be conservative with concurrent requests to avoid overloading providers
        semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent downloads

        async def bounded_download(task):
            async with semaphore:
                return await task

        bounded_tasks = [bounded_download(task) for task in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_id, search_result = components_with_results[i]
                processed_results.append(
                    {
                        "component_id": component_id,
                        "provider": search_result.provider_id,
                        "downloads": [],
                        "errors": [{"error": f"Download task failed: {result}"}],
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, "session") and self.session and not self.session.closed:
            # Note: Can't await in __del__, session should be closed explicitly
            logger.warning("ProviderAttachmentService session not properly closed")


# Global provider attachment service instance
provider_attachment_service = ProviderAttachmentService()
