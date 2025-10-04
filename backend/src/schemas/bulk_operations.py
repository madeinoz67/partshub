"""
Pydantic schemas for bulk operations on components.

These schemas define request/response models for bulk operations including:
- Bulk tag addition/removal
- Bulk project assignment
- Bulk component deletion
- Other bulk operations (meta-parts, purchase lists, low stock, attribution)
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_serializer


class ErrorType(str, Enum):
    """Error types for bulk operations."""

    NOT_FOUND = "not_found"
    CONCURRENT_MODIFICATION = "concurrent_modification"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"


class BulkOperationError(BaseModel):
    """
    Error details for a single component in a bulk operation.

    Provides detailed information about why a specific component
    failed during a bulk operation.
    """

    component_id: str = Field(..., description="ID of the component that failed")
    component_name: str = Field(..., description="Name of the component for display")
    error_message: str = Field(..., description="Human-readable error message")
    error_type: ErrorType = Field(..., description="Type of error that occurred")


class BulkOperationResponse(BaseModel):
    """
    Response schema for bulk operations.

    Provides success status, count of affected components,
    and detailed error information if any operations failed.
    """

    success: bool = Field(
        ..., description="Whether the operation completed successfully"
    )
    affected_count: int = Field(
        ..., description="Number of components successfully affected"
    )
    errors: list[BulkOperationError] | None = Field(
        None, description="List of errors if any operations failed"
    )

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize model, excluding None values."""
        result = {"success": self.success, "affected_count": self.affected_count}
        if self.errors is not None:
            result["errors"] = self.errors
        return result


class BulkAddTagsRequest(BaseModel):
    """Request schema for bulk tag addition."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs to add tags to",
    )
    tags: list[str] = Field(..., min_length=1, description="List of tag names to add")

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]


class BulkRemoveTagsRequest(BaseModel):
    """Request schema for bulk tag removal."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs to remove tags from",
    )
    tags: list[str] = Field(
        ..., min_length=1, description="List of tag names to remove"
    )

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]


class BulkAssignProjectRequest(BaseModel):
    """Request schema for bulk project assignment."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs to assign to project",
    )
    project_id: str | int = Field(
        ..., description="ID of the project to assign components to"
    )
    quantities: dict[str, int] = Field(
        ..., description="Map of component_id to quantity allocated"
    )

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]

    @field_validator("project_id")
    @classmethod
    def convert_project_id_to_str(cls, v: str | int) -> str:
        """Convert project ID to string."""
        return str(v)

    @field_validator("quantities")
    @classmethod
    def validate_quantities(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate that all quantities are positive integers."""
        for component_id, quantity in v.items():
            if quantity <= 0:
                raise ValueError(
                    f"Quantity for component {component_id} must be positive"
                )
        return v


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk component deletion."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs to delete",
    )

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]


class BulkMetaPartRequest(BaseModel):
    """Request schema for bulk meta-part operations."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs",
    )
    meta_part_id: str | int = Field(..., description="ID of the meta-part")

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]

    @field_validator("meta_part_id")
    @classmethod
    def convert_meta_part_id_to_str(cls, v: str | int) -> str:
        """Convert meta-part ID to string."""
        return str(v)


class BulkPurchaseListRequest(BaseModel):
    """Request schema for bulk purchase list operations."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs",
    )
    purchase_list_id: str | int = Field(..., description="ID of the purchase list")

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]

    @field_validator("purchase_list_id")
    @classmethod
    def convert_purchase_list_id_to_str(cls, v: str | int) -> str:
        """Convert purchase list ID to string."""
        return str(v)


class BulkLowStockRequest(BaseModel):
    """Request schema for bulk low stock threshold setting."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs",
    )
    minimum_stock: int = Field(..., ge=0, description="Minimum stock threshold")

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]


class BulkAttributionRequest(BaseModel):
    """Request schema for bulk attribution setting."""

    component_ids: list[str | int] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of component IDs",
    )
    attribution: dict[str, Any] = Field(..., description="Attribution metadata to set")

    @field_validator("component_ids")
    @classmethod
    def convert_component_ids_to_str(cls, v: list[str | int]) -> list[str]:
        """Convert all component IDs to strings."""
        return [str(id) for id in v]


class ComponentTagPreview(BaseModel):
    """Preview of a component's tags after bulk operation."""

    component_id: str = Field(..., description="Component ID")
    component_name: str = Field(..., description="Component name")
    current_tags: list[str] = Field(..., description="Current tag names")
    resulting_tags: list[str] = Field(..., description="Tags after operation")


class TagPreviewResponse(BaseModel):
    """Response schema for tag operation preview."""

    components: list[ComponentTagPreview] = Field(
        ..., description="Preview of each component's tags"
    )
