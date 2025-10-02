"""
Location generator service for creating storage locations with various layouts.

This service implements the business logic for generating storage location names
based on configurable layouts (single, row, grid, 3D grid) using range specifications.
"""

import itertools
import string
from collections.abc import Generator

from sqlalchemy.orm import Session

from ..models.storage_location import StorageLocation


class LocationGeneratorService:
    """Service for generating storage location layouts and validating configurations."""

    def __init__(self, db: Session):
        """
        Initialize location generator service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def generate_range(
        self,
        range_type: str,
        start: str | int,
        end: str | int,
        capitalize: bool = False,
        zero_pad: bool = False,
    ) -> Generator[str, None, None]:
        """
        Generate a range of values based on type (letters or numbers).

        Args:
            range_type: Type of range ('letters' or 'numbers')
            start: Start value (single char for letters, int for numbers)
            end: End value (single char for letters, int for numbers)
            capitalize: Whether to capitalize letters (letters only)
            zero_pad: Whether to zero-pad numbers (numbers only)

        Yields:
            Generated values as strings

        Raises:
            ValueError: If invalid range configuration
        """
        if range_type == "letters":
            # Generate letter range (a-z)
            if not isinstance(start, str) or not isinstance(end, str):
                raise ValueError("Letter range requires string start and end values")

            start_char = start.lower()
            end_char = end.lower()

            if start_char > end_char:
                raise ValueError(f"Invalid letter range: {start} > {end}")

            for char in string.ascii_lowercase:
                if start_char <= char <= end_char:
                    yield char.upper() if capitalize else char

        elif range_type == "numbers":
            # Generate number range (0-999)
            if not isinstance(start, int) or not isinstance(end, int):
                raise ValueError("Number range requires integer start and end values")

            if start > end:
                raise ValueError(f"Invalid number range: {start} > {end}")

            # Calculate padding width based on end value
            pad_width = len(str(end)) if zero_pad else 0

            for num in range(start, end + 1):
                if zero_pad:
                    yield str(num).zfill(pad_width)
                else:
                    yield str(num)

        else:
            raise ValueError(f"Invalid range_type: {range_type}")

    def calculate_total_count(self, ranges: list[dict]) -> int:
        """
        Calculate total number of locations that will be generated.

        Args:
            ranges: List of range specifications

        Returns:
            Total count of locations (product of all range sizes)
        """
        if not ranges:
            return 1  # Single layout type

        total = 1
        for range_spec in ranges:
            if range_spec["range_type"] == "letters":
                start_char = range_spec["start"].lower()
                end_char = range_spec["end"].lower()
                count = ord(end_char) - ord(start_char) + 1
            else:  # numbers
                count = range_spec["end"] - range_spec["start"] + 1

            total *= count

        return total

    def generate_all_names(
        self,
        prefix: str,
        ranges: list[dict],
        separators: list[str],
    ) -> list[str]:
        """
        Generate all location names based on configuration.

        Args:
            prefix: Prefix for all location names
            ranges: List of range specifications
            separators: List of separators between ranges

        Returns:
            List of all generated location names
        """
        if not ranges:
            # Single layout: just return prefix
            return [prefix]

        # Generate all range values
        range_values = []
        for range_spec in ranges:
            values = list(
                self.generate_range(
                    range_type=range_spec["range_type"],
                    start=range_spec["start"],
                    end=range_spec["end"],
                    capitalize=range_spec.get("capitalize", False),
                    zero_pad=range_spec.get("zero_pad", False),
                )
            )
            range_values.append(values)

        # Generate all combinations using Cartesian product
        all_names = []
        for combination in itertools.product(*range_values):
            # Build name: prefix + range[0] + sep[0] + range[1] + sep[1] + ...
            name_parts = [prefix]
            for i, value in enumerate(combination):
                name_parts.append(value)
                if i < len(separators):
                    name_parts.append(separators[i])

            # Join all parts (remove empty separator at the end if present)
            name = "".join(name_parts)
            all_names.append(name)

        return all_names

    def generate_preview(
        self,
        prefix: str,
        ranges: list[dict],
        separators: list[str],
    ) -> dict:
        """
        Generate a preview of locations without full generation.

        Returns first 5 names, last name, and total count for performance.

        Args:
            prefix: Prefix for all location names
            ranges: List of range specifications
            separators: List of separators between ranges

        Returns:
            Dictionary with sample_names (list), last_name (str), total_count (int)
        """
        all_names = self.generate_all_names(prefix, ranges, separators)
        total_count = len(all_names)

        # Get first 5 and last name
        sample_names = all_names[:5]
        last_name = all_names[-1] if all_names else ""

        return {
            "sample_names": sample_names,
            "last_name": last_name,
            "total_count": total_count,
        }

    def validate_configuration(
        self,
        config: dict,
    ) -> tuple[bool, list[str], list[str]]:
        """
        Validate layout configuration against business rules.

        Args:
            config: Layout configuration dictionary

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Validate total count <= 500
        total_count = self.calculate_total_count(config.get("ranges", []))
        if total_count > 500:
            errors.append(
                f"Configuration would create {total_count} locations, "
                f"exceeding maximum of 500"
            )

        # Check for duplicate names in database
        all_names = self.generate_all_names(
            config["prefix"],
            config.get("ranges", []),
            config.get("separators", []),
        )

        existing_names = (
            self.db.query(StorageLocation.name)
            .filter(StorageLocation.name.in_(all_names))
            .all()
        )

        if existing_names:
            duplicate_names = [name[0] for name in existing_names]
            errors.append(
                f"The following location names already exist: {', '.join(duplicate_names[:5])}"
                + ("..." if len(duplicate_names) > 5 else "")
            )

        # Validate parent_id exists if provided
        parent_id = config.get("parent_id")
        if parent_id:
            parent = self.db.query(StorageLocation).filter_by(id=parent_id).first()
            if not parent:
                errors.append(f"Parent location with ID {parent_id} not found")

        # Add warning for large batches
        if 100 < total_count <= 500:
            warnings.append(
                f"Creating {total_count} locations cannot be undone. "
                f"Please review the preview carefully."
            )

        is_valid = len(errors) == 0

        return is_valid, errors, warnings

    def bulk_create_locations(
        self,
        config: dict,
    ) -> list[StorageLocation]:
        """
        Create storage locations in bulk based on layout configuration.

        This method performs an all-or-nothing transaction: either all locations
        are created successfully, or the entire operation is rolled back.

        Args:
            config: Layout configuration dictionary with all parameters

        Returns:
            List of created StorageLocation objects

        Raises:
            ValueError: If configuration validation fails
            IntegrityError: If database constraints are violated
        """
        # Validate configuration first
        is_valid, errors, _ = self.validate_configuration(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        # Generate all location names
        all_names = self.generate_all_names(
            config["prefix"],
            config.get("ranges", []),
            config.get("separators", []),
        )

        # Prepare layout_config for storage (audit trail)
        layout_config = {
            "layout_type": config["layout_type"],
            "prefix": config["prefix"],
            "ranges": config.get("ranges", []),
            "separators": config.get("separators", []),
        }

        # Create location objects
        created_locations = []
        parent_id = config.get("parent_id")
        location_type = config["location_type"]

        try:
            for name in all_names:
                location = StorageLocation(
                    name=name,
                    type=location_type,
                    parent_id=parent_id,
                    description=f"Auto-generated {config['layout_type']} layout location",
                )

                # Store the layout configuration as JSONB
                # Note: SQLite stores this as JSON text, but SQLAlchemy handles conversion
                location.layout_config = layout_config

                self.db.add(location)
                created_locations.append(location)

            # Commit all at once (transactional)
            self.db.commit()

            # Refresh to get generated IDs and timestamps
            for location in created_locations:
                self.db.refresh(location)

            return created_locations

        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            raise e
