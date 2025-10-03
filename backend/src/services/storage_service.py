"""
StorageLocationService with hierarchy and bulk creation operations.
"""

import uuid
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from ..models import Component, ComponentLocation, StorageLocation


class StorageLocationService:
    """Service layer for storage location operations."""

    # Valid storage location types
    VALID_TYPES = {"container", "room", "building", "cabinet", "drawer", "shelf", "bin", "bag"}

    def __init__(self, db: Session):
        self.db = db

    def create_storage_location(self, location_data: dict[str, Any]) -> StorageLocation:
        """Create a new storage location."""
        # Generate ID if not provided
        if "id" not in location_data:
            location_data["id"] = str(uuid.uuid4())

        # Validate storage location type
        if "type" in location_data and location_data["type"] not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid storage location type '{location_data['type']}'. "
                f"Valid types are: {', '.join(sorted(self.VALID_TYPES))}"
            )

        # Check for duplicate name
        if "name" in location_data:
            existing = (
                self.db.query(StorageLocation)
                .filter(StorageLocation.name == location_data["name"])
                .first()
            )
            if existing:
                raise ValueError(
                    f"Storage location with name '{location_data['name']}' already exists"
                )

        # Validate parent exists if specified
        if "parent_id" in location_data and location_data["parent_id"]:
            parent = (
                self.db.query(StorageLocation)
                .filter(StorageLocation.id == location_data["parent_id"])
                .first()
            )
            if not parent:
                raise ValueError(
                    f"Parent location not found: {location_data['parent_id']}"
                )

        location = StorageLocation(**location_data)

        # Build hierarchy path
        if location.parent_id:
            parent = (
                self.db.query(StorageLocation)
                .filter(StorageLocation.id == location.parent_id)
                .first()
            )
            location.location_hierarchy = f"{parent.location_hierarchy}/{location.name}"
        else:
            location.location_hierarchy = location.name

        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def get_storage_location(
        self,
        location_id: str,
        include_children: bool = False,
        include_component_count: bool = False,
        include_full_hierarchy: bool = False,
    ) -> StorageLocation | None:
        """Get a storage location by ID with optional related data."""
        query = self.db.query(StorageLocation)

        if include_children:
            query = query.options(selectinload(StorageLocation.children))

        location = query.filter(StorageLocation.id == location_id).first()

        if not location:
            return None

        # Add computed properties if requested
        if include_component_count:
            location.component_count = location.get_component_count()

        if include_full_hierarchy:
            location.full_hierarchy_path = [
                {"id": loc.id, "name": loc.name} for loc in location.full_path[:-1]
            ]

        return location

    def update_storage_location(
        self, location_id: str, update_data: dict[str, Any]
    ) -> StorageLocation | None:
        """Update a storage location."""
        location = (
            self.db.query(StorageLocation)
            .filter(StorageLocation.id == location_id)
            .first()
        )
        if not location:
            return None

        # Validate storage location type if being updated
        if "type" in update_data and update_data["type"] not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid storage location type '{update_data['type']}'. "
                f"Valid types are: {', '.join(sorted(self.VALID_TYPES))}"
            )

        # Handle parent change
        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]

            # Prevent self-reference
            if new_parent_id == location_id:
                raise ValueError("Location cannot be its own parent")

            # Validate parent exists
            if new_parent_id:
                parent = (
                    self.db.query(StorageLocation)
                    .filter(StorageLocation.id == new_parent_id)
                    .first()
                )
                if not parent:
                    raise ValueError(f"Parent location not found: {new_parent_id}")

                # Prevent circular references
                if location.is_ancestor_of(parent):
                    raise ValueError("Circular reference detected")

        # Update fields
        for field, value in update_data.items():
            if hasattr(location, field):
                setattr(location, field, value)

        # Rebuild hierarchy if parent or name changed
        if "parent_id" in update_data or "name" in update_data:
            if location.parent_id:
                parent = (
                    self.db.query(StorageLocation)
                    .filter(StorageLocation.id == location.parent_id)
                    .first()
                )
                location.location_hierarchy = (
                    f"{parent.location_hierarchy}/{location.name}"
                )
            else:
                location.location_hierarchy = location.name

            # Update all children hierarchies recursively
            self._update_children_hierarchy(location)

        self.db.commit()
        self.db.refresh(location)
        return location

    def delete_storage_location(self, location_id: str) -> bool:
        """Delete a storage location."""
        location = (
            self.db.query(StorageLocation)
            .filter(StorageLocation.id == location_id)
            .first()
        )
        if not location:
            return False

        # Check if location has components
        component_count = (
            self.db.query(ComponentLocation)
            .filter(ComponentLocation.storage_location_id == location_id)
            .count()
        )
        if component_count > 0:
            raise ValueError(
                f"Cannot delete location with {component_count} components"
            )

        self.db.delete(location)
        self.db.commit()
        return True

    def list_storage_locations(
        self,
        search: str | None = None,
        location_type: str | None = None,
        include_component_count: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StorageLocation]:
        """List storage locations with filtering and pagination."""
        query = self.db.query(StorageLocation)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    StorageLocation.name.ilike(search_term),
                    StorageLocation.location_hierarchy.ilike(search_term),
                    StorageLocation.description.ilike(search_term),
                )
            )

        if location_type:
            query = query.filter(StorageLocation.type == location_type)

        # Apply pagination
        query = (
            query.order_by(StorageLocation.location_hierarchy)
            .offset(offset)
            .limit(limit)
        )
        locations = query.all()

        # Add component count if requested
        if include_component_count:
            for location in locations:
                location.component_count = location.get_component_count()

        return locations

    def get_location_components(
        self,
        location_id: str,
        include_children: bool = False,
        search: str | None = None,
        category: str | None = None,
        component_type: str | None = None,
        stock_status: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Component]:
        """Get components in a storage location."""
        from .component_service import ComponentService

        ComponentService(self.db)

        from ..models import ComponentLocation

        if include_children:
            # Get location and all its descendants
            location = (
                self.db.query(StorageLocation)
                .filter(StorageLocation.id == location_id)
                .first()
            )
            if not location:
                return []

            descendant_locations = location.get_all_descendants()
            location_ids = [location.id] + [loc.id for loc in descendant_locations]

            # Filter components by multiple locations via ComponentLocation
            query = (
                self.db.query(Component)
                .options(
                    selectinload(Component.category),
                    selectinload(Component.locations),
                    selectinload(Component.tags),
                )
                .join(ComponentLocation)
                .filter(ComponentLocation.storage_location_id.in_(location_ids))
            )
        else:
            # Just this location
            query = (
                self.db.query(Component)
                .options(
                    selectinload(Component.category),
                    selectinload(Component.locations),
                    selectinload(Component.tags),
                )
                .join(ComponentLocation)
                .filter(ComponentLocation.storage_location_id == location_id)
            )

        # Apply additional filters (reuse logic from ComponentService)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Component.name.ilike(search_term),
                    Component.part_number.ilike(search_term),
                    Component.manufacturer.ilike(search_term),
                )
            )

        if category:
            from ..models import Category

            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        if component_type:
            query = query.filter(Component.component_type.ilike(f"%{component_type}%"))

        if stock_status:
            from sqlalchemy import and_, func

            # Apply the same multi-location stock filtering logic as ComponentService
            if stock_status == "out":
                # Components with zero total quantity across all locations
                quantity_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.quantity_on_hand), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                query = query.filter(quantity_subquery == 0)
            elif stock_status == "low":
                # Components with quantity > 0 but <= total minimum stock across all locations
                quantity_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.quantity_on_hand), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                min_stock_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.minimum_stock), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                query = query.filter(
                    and_(
                        quantity_subquery > 0,
                        quantity_subquery <= min_stock_subquery,
                        min_stock_subquery > 0,
                    )
                )
            elif stock_status == "available":
                # Components with quantity > total minimum stock across all locations
                quantity_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.quantity_on_hand), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                min_stock_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.minimum_stock), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                query = query.filter(quantity_subquery > min_stock_subquery)

        # Apply sorting
        if sort_order.lower() == "desc":
            if sort_by == "name":
                query = query.order_by(Component.name.desc())
            elif sort_by == "quantity":
                # For multi-location model, we need to sort by calculated total quantity
                quantity_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.quantity_on_hand), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                query = query.order_by(quantity_subquery.desc())
        else:
            if sort_by == "name":
                query = query.order_by(Component.name)
            elif sort_by == "quantity":
                # For multi-location model, we need to sort by calculated total quantity
                quantity_subquery = (
                    self.db.query(
                        func.coalesce(func.sum(ComponentLocation.quantity_on_hand), 0)
                    )
                    .filter(ComponentLocation.component_id == Component.id)
                    .scalar_subquery()
                )
                query = query.order_by(quantity_subquery)

        # Apply pagination
        return query.offset(offset).limit(limit).all()

    def bulk_create_locations(
        self, locations_data: list[dict[str, Any]]
    ) -> list[StorageLocation]:
        """Create multiple storage locations in a single transaction."""
        if not locations_data:
            raise ValueError("No locations provided")

        # Check for duplicate names in the batch
        names_in_batch = [
            loc_data.get("name") for loc_data in locations_data if loc_data.get("name")
        ]
        if len(names_in_batch) != len(set(names_in_batch)):
            raise ValueError("Duplicate names found in batch")

        created_locations = []
        location_map = {}  # name -> location mapping for parent resolution

        try:
            # First pass: create locations without parent relationships
            for loc_data in locations_data:
                if "id" not in loc_data:
                    loc_data["id"] = str(uuid.uuid4())

                # Skip parent_id for now, handle parent_name if present
                create_data = {k: v for k, v in loc_data.items() if k != "parent_name"}
                if "parent_id" in create_data:
                    create_data.pop("parent_id")

                location = StorageLocation(**create_data)
                location.location_hierarchy = (
                    location.name
                )  # Temporary, will be updated

                self.db.add(location)
                location_map[location.name] = location
                created_locations.append(location)

            self.db.flush()  # Get IDs but don't commit yet

            # Second pass: resolve parent relationships and update hierarchies
            for i, loc_data in enumerate(locations_data):
                location = created_locations[i]

                # Handle parent_name reference
                if "parent_name" in loc_data:
                    parent_name = loc_data["parent_name"]
                    if parent_name is None:
                        continue  # Skip if parent_name is explicitly None
                    if parent_name in location_map:
                        parent = location_map[parent_name]
                        location.parent_id = parent.id
                        location.location_hierarchy = (
                            f"{parent.location_hierarchy}/{location.name}"
                        )
                    else:
                        raise ValueError(f"Parent location not found: {parent_name}")

            # Check for circular references
            for location in created_locations:
                if location.parent_id:
                    self._check_circular_reference(location, location_map)

            self.db.commit()

            # Refresh all locations
            for location in created_locations:
                self.db.refresh(location)

            return created_locations

        except Exception as e:
            self.db.rollback()
            raise e

    def _update_children_hierarchy(self, parent_location: StorageLocation):
        """Recursively update hierarchy paths for all children."""
        for child in parent_location.children:
            child.location_hierarchy = (
                f"{parent_location.location_hierarchy}/{child.name}"
            )
            self._update_children_hierarchy(child)

    def _check_circular_reference(
        self, location: StorageLocation, location_map: dict[str, StorageLocation]
    ):
        """Check for circular references in bulk creation."""
        visited = set()
        current = location

        while current and current.parent_id:
            if current.id in visited:
                raise ValueError(
                    f"Circular reference detected for location: {location.name}"
                )
            visited.add(current.id)

            # Find parent in location_map
            parent = None
            for loc in location_map.values():
                if loc.id == current.parent_id:
                    parent = loc
                    break
            current = parent
