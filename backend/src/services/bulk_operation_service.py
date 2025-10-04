"""
Bulk operation service for atomic component operations.

This service handles bulk operations on components with proper transaction
management, error handling, and rollback support. All operations are atomic
and follow all-or-nothing semantics.
"""

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.exc import StaleDataError

from ..models.component import Component
from ..models.project import Project, ProjectComponent
from ..models.tag import Tag
from ..schemas.bulk_operations import (
    BulkOperationError,
    BulkOperationResponse,
    ErrorType,
)


class BulkOperationService:
    """
    Service for performing bulk operations on components.

    All operations use atomic transactions with rollback on failure.
    Implements optimistic locking to detect concurrent modifications.
    """

    def __init__(self, db: Session):
        """
        Initialize bulk operation service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def bulk_add_tags(
        self, component_ids: list[str], tags: list[str]
    ) -> BulkOperationResponse:
        """
        Add tags to multiple components atomically.

        Creates new Tag records if they don't exist. All operations
        succeed or all are rolled back.

        Args:
            component_ids: List of component IDs to add tags to
            tags: List of tag names to add

        Returns:
            BulkOperationResponse with success status and affected count

        Raises:
            StaleDataError: If concurrent modification detected
        """
        errors = []
        affected_count = 0

        try:
            # Start atomic transaction
            # Fetch all components with tag relationships eagerly loaded
            components = (
                self.db.query(Component)
                .options(selectinload(Component.tags))
                .filter(Component.id.in_(component_ids))
                .all()
            )

            # Check for missing components
            found_ids = {c.id for c in components}
            missing_ids = set(component_ids) - found_ids
            for missing_id in missing_ids:
                errors.append(
                    BulkOperationError(
                        component_id=missing_id,
                        component_name="Unknown",
                        error_message=f"Component with ID {missing_id} not found",
                        error_type=ErrorType.NOT_FOUND,
                    )
                )

            if errors:
                # If any components not found, fail the entire operation
                return BulkOperationResponse(
                    success=False, affected_count=0, errors=errors
                )

            # Get or create tags
            tag_objects = []
            for tag_name in tags:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()  # Get the tag ID
                tag_objects.append(tag)

            # Add tags to each component
            for component in components:
                existing_tag_names = {t.name for t in component.tags}
                for tag in tag_objects:
                    if tag.name not in existing_tag_names:
                        component.tags.append(tag)
                        affected_count += 1

            # Commit transaction
            self.db.commit()

            return BulkOperationResponse(
                success=True, affected_count=len(components), errors=None
            )

        except StaleDataError:
            self.db.rollback()
            # Concurrent modification detected
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message="Concurrent modification detected. Please retry.",
                        error_type=ErrorType.CONCURRENT_MODIFICATION,
                    )
                ],
            )
        except Exception as e:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message=f"Operation failed: {str(e)}",
                        error_type=ErrorType.VALIDATION_ERROR,
                    )
                ],
            )

    async def bulk_remove_tags(
        self, component_ids: list[str], tags: list[str]
    ) -> BulkOperationResponse:
        """
        Remove tags from multiple components atomically.

        All operations succeed or all are rolled back.

        Args:
            component_ids: List of component IDs to remove tags from
            tags: List of tag names to remove

        Returns:
            BulkOperationResponse with success status and affected count

        Raises:
            StaleDataError: If concurrent modification detected
        """
        errors = []
        affected_count = 0

        try:
            # Fetch all components with tag relationships eagerly loaded
            components = (
                self.db.query(Component)
                .options(selectinload(Component.tags))
                .filter(Component.id.in_(component_ids))
                .all()
            )

            # Check for missing components
            found_ids = {c.id for c in components}
            missing_ids = set(component_ids) - found_ids
            for missing_id in missing_ids:
                errors.append(
                    BulkOperationError(
                        component_id=missing_id,
                        component_name="Unknown",
                        error_message=f"Component with ID {missing_id} not found",
                        error_type=ErrorType.NOT_FOUND,
                    )
                )

            if errors:
                return BulkOperationResponse(
                    success=False, affected_count=0, errors=errors
                )

            # Remove tags from each component
            tag_names_set = set(tags)
            for component in components:
                tags_to_remove = [t for t in component.tags if t.name in tag_names_set]
                for tag in tags_to_remove:
                    component.tags.remove(tag)
                    affected_count += 1

            # Commit transaction
            self.db.commit()

            return BulkOperationResponse(
                success=True, affected_count=len(components), errors=None
            )

        except StaleDataError:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message="Concurrent modification detected. Please retry.",
                        error_type=ErrorType.CONCURRENT_MODIFICATION,
                    )
                ],
            )
        except Exception as e:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message=f"Operation failed: {str(e)}",
                        error_type=ErrorType.VALIDATION_ERROR,
                    )
                ],
            )

    async def bulk_assign_project(
        self, component_ids: list[str], project_id: str, quantities: dict[str, int]
    ) -> BulkOperationResponse:
        """
        Assign multiple components to a project atomically.

        Creates or updates ProjectComponent records. All operations
        succeed or all are rolled back.

        Args:
            component_ids: List of component IDs to assign
            project_id: Project ID to assign components to
            quantities: Map of component_id to quantity allocated

        Returns:
            BulkOperationResponse with success status and affected count

        Raises:
            StaleDataError: If concurrent modification detected
        """
        errors = []

        try:
            # Verify project exists
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return BulkOperationResponse(
                    success=False,
                    affected_count=0,
                    errors=[
                        BulkOperationError(
                            component_id="N/A",
                            component_name="N/A",
                            error_message=f"Project with ID {project_id} not found",
                            error_type=ErrorType.NOT_FOUND,
                        )
                    ],
                )

            # Fetch all components
            components = (
                self.db.query(Component).filter(Component.id.in_(component_ids)).all()
            )

            # Check for missing components
            found_ids = {c.id for c in components}
            missing_ids = set(component_ids) - found_ids
            for missing_id in missing_ids:
                errors.append(
                    BulkOperationError(
                        component_id=missing_id,
                        component_name="Unknown",
                        error_message=f"Component with ID {missing_id} not found",
                        error_type=ErrorType.NOT_FOUND,
                    )
                )

            if errors:
                return BulkOperationResponse(
                    success=False, affected_count=0, errors=errors
                )

            # Assign components to project
            for component in components:
                quantity = quantities.get(component.id, 1)

                # Check if already assigned
                existing = (
                    self.db.query(ProjectComponent)
                    .filter(
                        ProjectComponent.project_id == project_id,
                        ProjectComponent.component_id == component.id,
                    )
                    .first()
                )

                if existing:
                    # Update existing allocation
                    existing.quantity_allocated = quantity
                else:
                    # Create new allocation
                    project_component = ProjectComponent(
                        project_id=project_id,
                        component_id=component.id,
                        quantity_allocated=quantity,
                    )
                    self.db.add(project_component)

            # Commit transaction
            self.db.commit()

            return BulkOperationResponse(
                success=True, affected_count=len(components), errors=None
            )

        except StaleDataError:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message="Concurrent modification detected. Please retry.",
                        error_type=ErrorType.CONCURRENT_MODIFICATION,
                    )
                ],
            )
        except Exception as e:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message=f"Operation failed: {str(e)}",
                        error_type=ErrorType.VALIDATION_ERROR,
                    )
                ],
            )

    async def bulk_delete(self, component_ids: list[str]) -> BulkOperationResponse:
        """
        Delete multiple components atomically.

        All deletions succeed or all are rolled back.

        Args:
            component_ids: List of component IDs to delete

        Returns:
            BulkOperationResponse with success status and affected count

        Raises:
            StaleDataError: If concurrent modification detected
        """
        errors = []

        try:
            # Fetch all components
            components = (
                self.db.query(Component).filter(Component.id.in_(component_ids)).all()
            )

            # Check for missing components
            found_ids = {c.id for c in components}
            missing_ids = set(component_ids) - found_ids
            for missing_id in missing_ids:
                errors.append(
                    BulkOperationError(
                        component_id=missing_id,
                        component_name="Unknown",
                        error_message=f"Component with ID {missing_id} not found",
                        error_type=ErrorType.NOT_FOUND,
                    )
                )

            if errors:
                return BulkOperationResponse(
                    success=False, affected_count=0, errors=errors
                )

            # Delete all components
            deleted_count = len(components)
            for component in components:
                self.db.delete(component)

            # Commit transaction
            self.db.commit()

            return BulkOperationResponse(
                success=True, affected_count=deleted_count, errors=None
            )

        except StaleDataError:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message="Concurrent modification detected. Please retry.",
                        error_type=ErrorType.CONCURRENT_MODIFICATION,
                    )
                ],
            )
        except Exception as e:
            self.db.rollback()
            return BulkOperationResponse(
                success=False,
                affected_count=0,
                errors=[
                    BulkOperationError(
                        component_id="unknown",
                        component_name="Unknown",
                        error_message=f"Operation failed: {str(e)}",
                        error_type=ErrorType.VALIDATION_ERROR,
                    )
                ],
            )
