"""
Bulk create service for creating storage locations in transactions.

This service handles transactional bulk creation of storage locations with
proper error handling and rollback support.
"""

from sqlalchemy.orm import Session

from ..models.storage_location import StorageLocation
from ..schemas.location_layout import BulkCreateResponse, LayoutConfiguration
from .location_generator import LocationGeneratorService
from .location_validator import LocationValidatorService


class BulkCreateService:
    """
    Service for bulk creating storage locations from layout configurations.

    Handles transactional creation with all-or-nothing semantics:
    - All locations created successfully, or
    - Transaction rolled back and no locations created
    """

    def __init__(self, db: Session):
        """
        Initialize bulk create service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.generator = LocationGeneratorService()
        self.validator = LocationValidatorService(db)

    def bulk_create_locations(
        self, config: LayoutConfiguration, user_id: str | None = None
    ) -> BulkCreateResponse:
        """
        Create storage locations in bulk based on layout configuration.

        This method performs an all-or-nothing transaction: either all locations
        are created successfully, or the entire operation is rolled back.

        Args:
            config: Layout configuration with all parameters
            user_id: User ID for audit trail (optional)

        Returns:
            BulkCreateResponse with created IDs and operation status

        Raises:
            ValueError: If configuration validation fails
            IntegrityError: If database constraints are violated
        """
        # Validate configuration first (FR-006, FR-007, FR-008)
        errors, _ = self.validator.validate_configuration(config)

        if errors:
            # Validation failed - return error response without creating anything
            return BulkCreateResponse(
                created_ids=[],
                created_count=0,
                success=False,
                errors=errors,
            )

        # Generate all location names
        all_names = self.generator.generate_names(config)

        # Prepare layout_config for storage (FR-016 - audit trail)
        layout_config = {
            "layout_type": config.layout_type.value,
            "prefix": config.prefix,
            "ranges": [
                {
                    "range_type": r.range_type.value,
                    "start": r.start,
                    "end": r.end,
                    "capitalize": r.capitalize,
                    "zero_pad": r.zero_pad,
                }
                for r in config.ranges
            ],
            "separators": config.separators,
        }

        # Create location objects
        created_locations = []

        try:
            for name in all_names:
                location = StorageLocation(
                    name=name,
                    type=config.location_type,  # FR-021
                    parent_id=config.parent_id,  # FR-014
                    description=f"Auto-generated {config.layout_type.value} layout location",
                )

                # Store the layout configuration as JSON (FR-016)
                # Note: SQLite stores this as JSON text, but SQLAlchemy handles conversion
                location.layout_config = layout_config

                self.db.add(location)
                created_locations.append(location)

            # Commit all at once (transactional)
            self.db.commit()

            # Refresh to get generated IDs and timestamps
            for location in created_locations:
                self.db.refresh(location)

            # Extract IDs
            created_ids = [str(location.id) for location in created_locations]

            return BulkCreateResponse(
                created_ids=created_ids,
                created_count=len(created_ids),
                success=True,
                errors=None,
            )

        except Exception as e:
            # Rollback on any error (all-or-nothing)
            self.db.rollback()

            # Return error response
            return BulkCreateResponse(
                created_ids=[],
                created_count=0,
                success=False,
                errors=[f"Failed to create locations: {str(e)}"],
            )
