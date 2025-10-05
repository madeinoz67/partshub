"""
Wizard service for creating components with provider links and resources.

Handles the complete component creation workflow including validation,
manufacturer/footprint creation, provider linking, and resource downloads.
"""

import logging
import re

from fastapi import BackgroundTasks
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.component import Component
from ..models.provider_link import ProviderLink
from ..models.resource import Resource

logger = logging.getLogger(__name__)


class WizardService:
    """
    Service for wizard-based component creation.

    Provides high-level operations for creating components with automatic
    manufacturer/footprint creation, provider linking, and resource management.
    """

    # Validation constants
    MAX_NAME_LENGTH = 255
    NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-._]+$")

    @staticmethod
    def _validate_name(name: str, field_name: str) -> None:
        """
        Validate manufacturer or footprint name.

        Args:
            name: Name to validate
            field_name: Field name for error messages

        Raises:
            ValueError: If validation fails
        """
        if not name or not name.strip():
            raise ValueError(f"{field_name} cannot be empty")

        if len(name) > WizardService.MAX_NAME_LENGTH:
            raise ValueError(
                f"{field_name} exceeds maximum length of {WizardService.MAX_NAME_LENGTH}"
            )

        if not WizardService.NAME_PATTERN.match(name):
            raise ValueError(
                f"{field_name} contains invalid characters. "
                "Only alphanumeric, spaces, hyphens, periods, and underscores allowed"
            )

    @staticmethod
    def _check_duplicate_name(db: Session, name: str, field_name: str) -> bool:
        """
        Check if a manufacturer or footprint name already exists (case-insensitive).

        Args:
            db: Database session
            name: Name to check
            field_name: Field to check ('manufacturer' or 'package')

        Returns:
            True if duplicate exists, False otherwise
        """
        # Check for existing components with same name (case-insensitive)
        if field_name == "manufacturer":
            existing = (
                db.query(Component)
                .filter(func.lower(Component.manufacturer) == name.lower())
                .first()
            )
        elif field_name == "package":
            existing = (
                db.query(Component)
                .filter(func.lower(Component.package) == name.lower())
                .first()
            )
        else:
            return False

        return existing is not None

    @staticmethod
    async def create_component(
        db: Session,
        data: dict,
        background_tasks: BackgroundTasks | None = None,
    ) -> Component:
        """
        Create a component with optional provider link and resources.

        Args:
            db: Database session
            data: Component creation data:
                - name (required): Component name
                - description (optional): Component description
                - part_type (required): 'linked' or 'local'
                - manufacturer_id (optional): Existing manufacturer ID
                - manufacturer_name (optional): New manufacturer name
                - footprint_id (optional): Existing footprint ID
                - footprint_name (optional): New footprint name
                - provider_link (optional): Provider link data
                    - provider_id: Provider ID
                    - part_number: Provider's part number
                    - part_url: URL to part page
                    - metadata: Provider-specific metadata
                - resource_selections (optional): List of resource data
                    - type: Resource type
                    - url: Resource URL
                    - file_name: Filename
                - specifications (optional): Component specifications
            background_tasks: FastAPI background tasks for async downloads

        Returns:
            Created Component with relationships loaded

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint violated
        """

        try:
            # Start transaction
            # Validate required fields
            if not data.get("name"):
                raise ValueError("Component name is required")

            if not data.get("part_type") or data["part_type"] not in [
                "linked",
                "local",
            ]:
                raise ValueError("part_type must be 'linked' or 'local'")

            # Validate linked parts have provider_link
            if data["part_type"] == "linked" and not data.get("provider_link"):
                raise ValueError("Linked components must have provider_link data")

            # Validate and create/get manufacturer
            manufacturer_name = None
            if data.get("manufacturer_name"):
                WizardService._validate_name(
                    data["manufacturer_name"], "Manufacturer name"
                )
                manufacturer_name = data["manufacturer_name"]

            # Validate and create/get footprint
            footprint_name = None
            if data.get("footprint_name"):
                WizardService._validate_name(data["footprint_name"], "Footprint name")
                footprint_name = data["footprint_name"]

            # Create component
            component = Component(
                name=data["name"],
                notes=data.get("description", ""),
                manufacturer=manufacturer_name,
                package=footprint_name,
                specifications=data.get("specifications"),
            )

            db.add(component)
            db.flush()  # Get component ID

            # Create provider link if provided
            if data.get("provider_link"):
                link_data = data["provider_link"]

                provider_link = ProviderLink(
                    component_id=component.id,
                    provider_id=link_data["provider_id"],
                    provider_part_number=link_data["part_number"],
                    provider_url=link_data.get(
                        "part_url", link_data.get("provider_url", "")
                    ),
                    metadata=link_data.get("metadata"),
                    sync_status="pending",
                )

                db.add(provider_link)
                db.flush()  # Get provider_link ID

                # Create resources if provided
                if data.get("resource_selections"):
                    from .resource_service import ResourceService

                    for resource_data in data["resource_selections"]:
                        # Create resource record
                        resource = Resource(
                            provider_link_id=provider_link.id,
                            resource_type=resource_data["type"],
                            file_name=resource_data["file_name"],
                            source_url=resource_data["url"],
                            download_status="pending",
                        )

                        db.add(resource)
                        db.flush()  # Get resource ID

                        # Download critical resources synchronously (datasheets)
                        if resource_data["type"] == "datasheet":
                            try:
                                await ResourceService.download_resource_sync(
                                    db, resource.id
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to download datasheet synchronously: {str(e)}"
                                )
                                # Continue - background task will retry

                        # Queue non-critical resources for background download
                        if background_tasks and resource_data["type"] in [
                            "image",
                            "footprint",
                            "symbol",
                            "model_3d",
                        ]:
                            background_tasks.add_task(
                                ResourceService.download_resource_async, resource.id
                            )

            # Commit transaction
            db.commit()

            # Refresh to load relationships
            db.refresh(component)

            return component

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error creating component: {str(e)}")
            raise ValueError(f"Component creation failed: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating component: {str(e)}")
            raise
