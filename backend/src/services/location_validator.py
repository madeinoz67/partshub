"""
Location validation service for validating layout configurations.

This service validates layout configurations against business rules and database constraints.
"""

from sqlalchemy.orm import Session

from ..models.storage_location import StorageLocation
from ..schemas.location_layout import LayoutConfiguration
from .location_generator import LocationGeneratorService


class LocationValidatorService:
    """
    Service for validating location layout configurations.

    Validates business rules such as:
    - 500 location limit
    - 100+ location warning
    - Duplicate name detection
    - Parent location existence
    """

    def __init__(self, db: Session):
        """
        Initialize location validator service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.generator = LocationGeneratorService()

    def validate_configuration(
        self, config: LayoutConfiguration, validate_parent: bool = True
    ) -> tuple[list[str], list[str], int]:
        """
        Validate layout configuration against business rules.

        Args:
            config: Layout configuration to validate
            validate_parent: Whether to validate parent_id existence (default: True)
                           Set to False for preview mode where parent validation is not needed

        Returns:
            Tuple of (errors, warnings, total_count)
            - errors: List of validation errors (blocks creation)
            - warnings: List of warnings (allows creation but shows caution)
            - total_count: Total number of locations that would be generated
        """
        errors = []
        warnings = []

        # Calculate total count
        total_count = self.generator.calculate_total_count(config)

        # Validate total count <= 500 (FR-008)
        if total_count > 500:
            errors.append(
                f"Total location count ({total_count}) exceeds maximum limit of 500"
            )
            # Return early with total_count - no point in checking other validations if count is too high
            return errors, warnings, total_count

        # Check for duplicate names in database (FR-007)
        all_names = self.generator.generate_names(config)

        existing_names = (
            self.db.query(StorageLocation.name)
            .filter(StorageLocation.name.in_(all_names))
            .all()
        )

        if existing_names:
            duplicate_names = [name[0] for name in existing_names]
            errors.append(
                f"Duplicate location names already exist: {', '.join(duplicate_names[:5])}"
                + ("..." if len(duplicate_names) > 5 else "")
            )

        # Validate parent_id exists if provided (FR-014)
        # Skip parent validation in preview mode (validate_parent=False)
        if validate_parent and config.parent_id:
            parent = (
                self.db.query(StorageLocation).filter_by(id=config.parent_id).first()
            )
            if not parent:
                errors.append(f"Parent location with ID {config.parent_id} not found")

        # Add warning for large batches (FR-009)
        if 100 < total_count <= 500:
            warnings.append(
                f"Creating {total_count} locations cannot be undone. Locations cannot be deleted."
            )

        return errors, warnings, total_count
