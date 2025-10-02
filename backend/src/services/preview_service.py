"""
Preview service for generating location previews without database writes.

This service generates preview information for location layouts, showing a sample
of what would be created without actually creating any database records.
"""

from sqlalchemy.orm import Session

from ..schemas.location_layout import LayoutConfiguration, PreviewResponse
from .location_generator import LocationGeneratorService
from .location_validator import LocationValidatorService


class PreviewService:
    """
    Service for generating location layout previews.

    Provides read-only preview of location names with validation feedback.
    No database writes are performed by this service.
    """

    def __init__(self, db: Session):
        """
        Initialize preview service.

        Args:
            db: SQLAlchemy database session (read-only access)
        """
        self.db = db
        self.generator = LocationGeneratorService()
        self.validator = LocationValidatorService(db)

    def generate_preview(self, config: LayoutConfiguration) -> PreviewResponse:
        """
        Generate a preview of locations without creating them.

        Returns first 5 names, last name, total count, and validation results.
        This method is idempotent and has no side effects.

        Args:
            config: Layout configuration to preview

        Returns:
            PreviewResponse with sample names, validation errors, and warnings
        """
        # Validate configuration
        errors, warnings = self.validator.validate_configuration(config)

        # If validation fails, return preview with errors and no names
        if errors:
            return PreviewResponse(
                sample_names=[],
                last_name="",
                total_count=0,
                warnings=warnings,
                errors=errors,
                is_valid=False,
            )

        # Generate names
        all_names = self.generator.generate_names(config)
        total_count = len(all_names)

        # Get first 5 and last name (FR-013)
        sample_names = all_names[:5]
        last_name = all_names[-1] if all_names else ""

        return PreviewResponse(
            sample_names=sample_names,
            last_name=last_name,
            total_count=total_count,
            warnings=warnings,
            errors=[],
            is_valid=True,
        )
