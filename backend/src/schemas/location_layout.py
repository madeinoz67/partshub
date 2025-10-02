"""
Pydantic schemas for Storage Location Layout Generator.

This module defines all request/response schemas for the layout generation feature,
including comprehensive validation logic for multi-dimensional location layouts.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class LayoutType(str, Enum):
    """
    Type of layout for location generation.

    Determines the dimensionality and naming pattern:
    - SINGLE: One location with name = prefix
    - ROW: 1D array (prefix + range[0])
    - GRID: 2D array (prefix + range[0] + sep[0] + range[1])
    - GRID_3D: 3D array (prefix + range[0] + sep[0] + range[1] + sep[1] + range[2])
    """

    SINGLE = "single"
    ROW = "row"
    GRID = "grid"
    GRID_3D = "grid_3d"


class RangeType(str, Enum):
    """
    Type of range for dimension specification.

    - LETTERS: Alphabetic ranges (a-z), supports capitalization
    - NUMBERS: Numeric ranges (0-999), supports zero-padding
    """

    LETTERS = "letters"
    NUMBERS = "numbers"


class RangeSpecification(BaseModel):
    """
    Defines a single dimension in a multi-dimensional layout.

    Examples:
        Letters a-f: {"range_type": "letters", "start": "a", "end": "f", "capitalize": False}
        Numbers 1-10 with padding: {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": True}
    """

    range_type: RangeType = Field(..., description="Type of range (letters or numbers)")
    start: str | int = Field(
        ..., description="Start value (single char for letters, int 0-999 for numbers)"
    )
    end: str | int = Field(
        ..., description="End value (single char for letters, int 0-999 for numbers)"
    )
    capitalize: bool | None = Field(
        None, description="Capitalize letters (letters only, default: False)"
    )
    zero_pad: bool | None = Field(
        None,
        description="Zero-pad numbers to match end length (numbers only, default: False)",
    )

    @field_validator("start", "end")
    @classmethod
    def validate_range_values(cls, v, info):
        """Validate range values based on range_type."""
        # We need to access range_type from the model, but it might not be set yet
        # This validation will be completed in model_validator
        return v

    @model_validator(mode="after")
    def validate_range_specification(self):
        """
        Validate range specification based on range_type.

        Rules:
        - If letters: start/end must be single alphabetic characters, start <= end
        - If numbers: start/end must be 0-999, start <= end
        - capitalize only valid for letters
        - zero_pad only valid for numbers
        """
        if self.range_type == RangeType.LETTERS:
            # Validate letter range
            if not isinstance(self.start, str) or not isinstance(self.end, str):
                raise ValueError("start and end must be strings for letters range")

            if len(self.start) != 1 or len(self.end) != 1:
                raise ValueError(
                    "start and end must be single characters for letters range"
                )

            if not self.start.isalpha() or not self.end.isalpha():
                raise ValueError(
                    "start and end must be alphabetic characters for letters range"
                )

            # Normalize to lowercase for comparison
            start_lower = self.start.lower()
            end_lower = self.end.lower()

            if start_lower > end_lower:
                raise ValueError(
                    f"start '{self.start}' must be <= end '{self.end}' in alphabetic order"
                )

            # Validate that zero_pad is not used with letters
            if self.zero_pad is not None:
                raise ValueError("zero_pad is only valid for numbers range")

        elif self.range_type == RangeType.NUMBERS:
            # Validate number range
            if not isinstance(self.start, int) or not isinstance(self.end, int):
                raise ValueError("start and end must be integers for numbers range")

            if self.start < 0 or self.start > 999:
                raise ValueError("start must be between 0 and 999 for numbers range")

            if self.end < 0 or self.end > 999:
                raise ValueError("end must be between 0 and 999 for numbers range")

            if self.start > self.end:
                raise ValueError(f"start {self.start} must be <= end {self.end}")

            # Validate that capitalize is not used with numbers
            if self.capitalize is not None:
                raise ValueError("capitalize is only valid for letters range")

        return self


class LayoutConfiguration(BaseModel):
    """
    Configuration for generating storage locations with various layout types.

    Defines parameters for bulk location creation including layout type, naming,
    ranges, and metadata.
    """

    layout_type: LayoutType = Field(
        ..., description="Type of layout (single, row, grid, grid_3d)"
    )
    prefix: str = Field(
        ..., max_length=50, description="Prefix for all generated location names"
    )
    ranges: list[RangeSpecification] = Field(
        ..., description="Ordered list of ranges defining dimensions"
    )
    separators: list[str] = Field(
        ..., description="Separators between range components"
    )
    parent_id: str | None = Field(
        None, description="UUID of parent location (if creating children)"
    )
    location_type: str = Field(
        ..., description="Type for all generated locations (bin, drawer, shelf, etc.)"
    )
    single_part_only: bool = Field(
        False, description="Whether locations can hold only one part"
    )

    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v):
        """Ensure prefix is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("prefix cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_layout_configuration(self):
        """
        Validate layout configuration constraints.

        Rules:
        - layout_type determines ranges length: single=0, row=1, grid=2, grid_3d=3
        - separators length must be len(ranges) - 1 (except single which needs 0)
        - prefix must not contain separator characters
        - Total generated locations <= 500
        """
        # Validate ranges length based on layout_type
        expected_ranges = {
            LayoutType.SINGLE: 0,
            LayoutType.ROW: 1,
            LayoutType.GRID: 2,
            LayoutType.GRID_3D: 3,
        }

        expected_count = expected_ranges[self.layout_type]
        if len(self.ranges) != expected_count:
            raise ValueError(
                f"layout_type '{self.layout_type.value}' requires {expected_count} ranges, "
                f"but {len(self.ranges)} were provided"
            )

        # Validate separators length
        expected_separators = max(0, len(self.ranges) - 1)
        if len(self.separators) != expected_separators:
            raise ValueError(
                f"Expected {expected_separators} separators for {len(self.ranges)} ranges, "
                f"but {len(self.separators)} were provided"
            )

        # Note: Max 500 validation is handled in business logic (PreviewService/BulkCreateService)
        # to allow preview endpoint to return 200 with validation errors instead of 422

        return self

    def _calculate_total_locations(self) -> int:
        """
        Calculate total number of locations that will be generated.

        Returns:
            Total count as product of all ranges
        """
        if self.layout_type == LayoutType.SINGLE:
            return 1

        total = 1
        for range_spec in self.ranges:
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


class PreviewResponse(BaseModel):
    """
    Preview of locations to be generated without creating them.

    Provides sample names, total count, and validation feedback.
    """

    sample_names: list[str] = Field(
        ..., description="First 5 generated names (or fewer if total < 5)"
    )
    last_name: str = Field(..., description="Last generated name")
    total_count: int = Field(
        ..., description="Total number of locations that would be created"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warning messages (e.g., 'Creating 150 locations cannot be undone')",
    )
    errors: list[str] = Field(
        default_factory=list, description="Validation errors preventing creation"
    )
    is_valid: bool = Field(
        default=True,
        description="Whether configuration is valid for creation (computed from errors)",
    )

    @model_validator(mode="after")
    def compute_is_valid(self):
        """Compute is_valid from errors list."""
        self.is_valid = len(self.errors) == 0
        return self


class BulkCreateResponse(BaseModel):
    """
    Result of bulk location creation operation.

    Provides created location IDs and operation status.
    """

    created_ids: list[str] = Field(
        default_factory=list, description="UUIDs of successfully created locations"
    )
    created_count: int = Field(..., description="Number of locations created")
    success: bool = Field(..., description="Whether operation succeeded")
    errors: list[str] | None = Field(None, description="Errors if operation failed")

    @model_validator(mode="after")
    def validate_bulk_create(self):
        """
        Validate bulk create response consistency.

        Rules:
        - Transactional: created_count == len(created_ids) or both are 0 (rollback on failure)
        - success = created_count > 0
        - errors populated only if success = False
        """
        # Validate transactional consistency
        if self.created_count != len(self.created_ids):
            raise ValueError(
                f"created_count ({self.created_count}) must equal length of created_ids ({len(self.created_ids)})"
            )

        # Validate success flag
        expected_success = self.created_count > 0
        if self.success != expected_success:
            raise ValueError(
                f"success must be {expected_success} when created_count is {self.created_count}"
            )

        # Validate errors
        if not self.success and (self.errors is None or len(self.errors) == 0):
            raise ValueError("errors must be provided when success is False")

        if self.success and self.errors is not None and len(self.errors) > 0:
            raise ValueError("errors must not be provided when success is True")

        return self
