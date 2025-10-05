"""
Resource service for managing provider-linked resource downloads.

Handles synchronous and asynchronous resource downloads, progress tracking,
and file storage for datasheets, images, footprints, and other resources.
"""

import logging
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from ..models.resource import Resource

logger = logging.getLogger(__name__)


class ResourceService:
    """
    Service for managing resource downloads and status tracking.

    Provides operations for downloading resources synchronously and
    asynchronously, tracking progress, and managing file storage.
    """

    # Storage configuration
    UPLOAD_DIR = Path("backend/uploads/resources")
    DOWNLOAD_TIMEOUT = 30.0  # seconds
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def _get_storage_path(provider_link_id: int, file_name: str) -> Path:
        """
        Get storage path for a resource file.

        Args:
            provider_link_id: Provider link ID
            file_name: Resource filename

        Returns:
            Path to storage location
        """
        # Create directory structure: uploads/resources/{provider_link_id}/
        storage_dir = ResourceService.UPLOAD_DIR / str(provider_link_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        return storage_dir / file_name

    @staticmethod
    async def download_resource_sync(db: Session, resource_id: int) -> Resource:
        """
        Download a resource synchronously (blocking).

        Used for critical resources like datasheets that should be downloaded
        immediately during component creation.

        Args:
            db: Database session
            resource_id: Resource ID to download

        Returns:
            Updated Resource object

        Raises:
            ValueError: If resource not found
            Exception: If download fails
        """
        # Get resource
        resource = db.query(Resource).filter(Resource.id == resource_id).first()

        if not resource:
            raise ValueError(f"Resource with ID {resource_id} not found")

        try:
            # Update status to downloading
            resource.download_status = "downloading"
            db.commit()

            # Download file
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    resource.source_url,
                    timeout=ResourceService.DOWNLOAD_TIMEOUT,
                    follow_redirects=True,
                )
                response.raise_for_status()

                # Check file size
                content_length = int(response.headers.get("content-length", 0))
                if (
                    content_length > ResourceService.MAX_FILE_SIZE
                    and content_length > 0
                ):
                    raise ValueError(
                        f"File too large: {content_length} bytes (max {ResourceService.MAX_FILE_SIZE})"
                    )

                # Get storage path
                storage_path = ResourceService._get_storage_path(
                    resource.provider_link_id, resource.file_name
                )

                # Write file
                with open(storage_path, "wb") as f:
                    f.write(response.content)

                # Update resource
                resource.file_path = str(storage_path)
                resource.file_size_bytes = len(response.content)
                resource.download_status = "complete"
                resource.downloaded_at = datetime.utcnow()

                db.commit()
                db.refresh(resource)

                logger.info(
                    f"Successfully downloaded resource {resource_id}: {resource.file_name}"
                )

                return resource

        except Exception as e:
            logger.error(f"Failed to download resource {resource_id}: {str(e)}")

            # Update status to failed
            resource.download_status = "failed"
            db.commit()

            raise

    @staticmethod
    async def download_resource_async(resource_id: int) -> None:
        """
        Download a resource asynchronously (background task).

        Used for non-critical resources like images and footprints that can
        be downloaded in the background after component creation.

        Args:
            resource_id: Resource ID to download

        Note: This function creates its own database session since it runs
        in a background task.
        """
        from ..database import SessionLocal

        db = SessionLocal()

        try:
            await ResourceService.download_resource_sync(db, resource_id)
        except Exception as e:
            logger.error(
                f"Background download failed for resource {resource_id}: {str(e)}"
            )
        finally:
            db.close()

    @staticmethod
    async def get_resource_status(db: Session, resource_id: int) -> dict:
        """
        Get download status and progress for a resource.

        Args:
            db: Database session
            resource_id: Resource ID

        Returns:
            Dictionary containing:
            - id: Resource ID
            - download_status: Current status
            - progress_percent: Download progress (0-100)
            - error_message: Error message if failed

        Raises:
            ValueError: If resource not found
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()

        if not resource:
            raise ValueError(f"Resource with ID {resource_id} not found")

        # Calculate progress
        progress_percent = 0
        if resource.download_status == "complete":
            progress_percent = 100
        elif resource.download_status == "downloading":
            progress_percent = 50  # Indeterminate progress
        elif resource.download_status == "pending":
            progress_percent = 0

        error_message = None
        if resource.download_status == "failed":
            error_message = "Download failed. Please try again."

        return {
            "id": resource.id,
            "download_status": resource.download_status,
            "progress_percent": progress_percent,
            "error_message": error_message,
            "file_size_bytes": resource.file_size_bytes,
            "downloaded_at": (
                resource.downloaded_at.isoformat() if resource.downloaded_at else None
            ),
        }

    @staticmethod
    async def add_resource(
        db: Session,
        link_id: int,
        resource_data: dict,
        background_tasks: BackgroundTasks | None = None,
    ) -> Resource:
        """
        Add a new resource to a provider link and queue for download.

        Args:
            db: Database session
            link_id: Provider link ID
            resource_data: Resource data:
                - type: Resource type
                - url: Source URL
                - file_name: Filename
            background_tasks: FastAPI background tasks

        Returns:
            Created Resource object

        Raises:
            ValueError: If provider link not found or validation fails
        """
        from ..models.provider_link import ProviderLink

        # Validate provider link exists
        link = db.query(ProviderLink).filter(ProviderLink.id == link_id).first()

        if not link:
            raise ValueError(f"Provider link with ID {link_id} not found")

        # Validate resource type
        valid_types = ["datasheet", "image", "footprint", "symbol", "model_3d"]
        if resource_data.get("type") not in valid_types:
            raise ValueError(
                f"Invalid resource type. Must be one of: {', '.join(valid_types)}"
            )

        # Create resource
        resource = Resource(
            provider_link_id=link_id,
            resource_type=resource_data["type"],
            file_name=resource_data["file_name"],
            source_url=resource_data["url"],
            download_status="pending",
        )

        db.add(resource)
        db.commit()
        db.refresh(resource)

        # Queue for background download
        if background_tasks:
            background_tasks.add_task(
                ResourceService.download_resource_async, resource.id
            )

        return resource

    @staticmethod
    async def retry_failed_downloads(db: Session) -> dict:
        """
        Retry all failed resource downloads.

        Args:
            db: Database session

        Returns:
            Dictionary with retry statistics:
            - total_failed: Number of failed resources found
            - retry_queued: Number of retries queued
            - retry_failed: Number that failed to queue
        """
        # Find all failed resources
        failed_resources = (
            db.query(Resource).filter(Resource.download_status == "failed").all()
        )

        stats = {
            "total_failed": len(failed_resources),
            "retry_queued": 0,
            "retry_failed": 0,
        }

        for resource in failed_resources:
            try:
                # Reset status to pending
                resource.download_status = "pending"
                db.commit()

                # Attempt download
                await ResourceService.download_resource_sync(db, resource.id)
                stats["retry_queued"] += 1

            except Exception as e:
                logger.error(f"Retry failed for resource {resource.id}: {str(e)}")
                stats["retry_failed"] += 1

        return stats
