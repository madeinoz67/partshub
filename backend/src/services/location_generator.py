"""
Location generator service for creating storage locations with various layouts.

This service implements the business logic for generating storage location names
based on configurable layouts (single, row, grid, 3D grid) using range specifications.
"""

import itertools
import string
from collections.abc import Generator

from ..schemas.location_layout import LayoutConfiguration, RangeSpecification, RangeType


class LocationGeneratorService:
    """
    Service for generating storage location names from layout configurations.

    This service is stateless and focuses solely on name generation logic.
    Validation and database operations are handled by separate services.
    """

    def generate_range(
        self,
        range_spec: RangeSpecification,
    ) -> Generator[str, None, None]:
        """
        Generate a range of values based on range specification.

        Args:
            range_spec: Range specification with type, start, end, and options

        Yields:
            Generated values as strings

        Raises:
            ValueError: If invalid range configuration
        """
        if range_spec.range_type == RangeType.LETTERS:
            # Generate letter range (a-z)
            start_char = range_spec.start.lower()
            end_char = range_spec.end.lower()

            capitalize = range_spec.capitalize or False

            for char in string.ascii_lowercase:
                if start_char <= char <= end_char:
                    yield char.upper() if capitalize else char

        elif range_spec.range_type == RangeType.NUMBERS:
            # Generate number range (0-999)
            zero_pad = range_spec.zero_pad or False

            # Calculate padding width based on end value
            pad_width = len(str(range_spec.end)) if zero_pad else 0

            for num in range(range_spec.start, range_spec.end + 1):
                if zero_pad:
                    yield str(num).zfill(pad_width)
                else:
                    yield str(num)

    def calculate_total_count(self, config: LayoutConfiguration) -> int:
        """
        Calculate total number of locations that will be generated.

        Args:
            config: Layout configuration with ranges

        Returns:
            Total count of locations (product of all range sizes)
        """
        if not config.ranges:
            return 1  # Single layout type

        total = 1
        for range_spec in config.ranges:
            if range_spec.range_type == RangeType.LETTERS:
                # Calculate letter range size
                start = range_spec.start.lower()
                end = range_spec.end.lower()
                count = ord(end) - ord(start) + 1
            else:
                # Calculate number range size
                count = range_spec.end - range_spec.start + 1

            total *= count

        return total

    def generate_names(self, config: LayoutConfiguration) -> list[str]:
        """
        Generate all location names based on configuration.

        Args:
            config: Layout configuration with prefix, ranges, and separators

        Returns:
            List of all generated location names
        """
        if not config.ranges:
            # Single layout: just return prefix
            return [config.prefix]

        # Generate all range values
        range_values = []
        for range_spec in config.ranges:
            values = list(self.generate_range(range_spec))
            range_values.append(values)

        # Generate all combinations using Cartesian product
        all_names = []
        for combination in itertools.product(*range_values):
            # Build name: prefix + range[0] + sep[0] + range[1] + sep[1] + ...
            name_parts = [config.prefix]
            for i, value in enumerate(combination):
                name_parts.append(value)
                if i < len(config.separators):
                    name_parts.append(config.separators[i])

            # Join all parts
            name = "".join(name_parts)
            all_names.append(name)

        return all_names
