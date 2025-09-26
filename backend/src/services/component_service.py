"""
ComponentService with CRUD and search operations for components.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc
from ..models import Component, StockTransaction, TransactionType, Category, StorageLocation, Tag
import uuid


class ComponentService:
    """Service layer for component operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_component(self, component_data: Dict[str, Any]) -> Component:
        """Create a new component."""
        # Generate ID if not provided
        if "id" not in component_data:
            component_data["id"] = str(uuid.uuid4())

        # Extract tags before creating component
        tag_ids = component_data.pop("tags", [])

        # Create component instance
        component = Component(**component_data)

        self.db.add(component)
        self.db.flush()  # Flush to get component ID

        # Handle tag associations
        if tag_ids:
            tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            component.tags = tags

        self.db.commit()
        self.db.refresh(component)

        # Create initial stock transaction if quantity > 0
        if component.quantity_on_hand > 0:
            initial_transaction = StockTransaction.create_add_transaction(
                component=component,
                quantity=component.quantity_on_hand,
                reason="Initial stock entry",
                reference_type="initial_stock"
            )
            self.db.add(initial_transaction)
            self.db.commit()

        return component

    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID with all relationships loaded."""
        return (
            self.db.query(Component)
            .options(
                selectinload(Component.category),
                selectinload(Component.storage_location),
                selectinload(Component.tags),
                selectinload(Component.attachments),
                selectinload(Component.custom_field_values).selectinload(Component.custom_field_values.property.mapper.class_.field)
            )
            .filter(Component.id == component_id)
            .first()
        )

    def update_component(self, component_id: str, update_data: Dict[str, Any]) -> Optional[Component]:
        """Update a component."""
        component = self.db.query(Component).filter(Component.id == component_id).first()
        if not component:
            return None

        # Extract tags before updating component
        tag_ids = update_data.pop("tags", None)

        # Update fields
        for field, value in update_data.items():
            if hasattr(component, field):
                setattr(component, field, value)

        # Handle tag associations if provided
        if tag_ids is not None:
            if tag_ids:
                tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                component.tags = tags
            else:
                component.tags = []

        self.db.commit()
        self.db.refresh(component)
        return component

    def delete_component(self, component_id: str) -> bool:
        """Delete a component."""
        component = self.db.query(Component).filter(Component.id == component_id).first()
        if not component:
            return False

        self.db.delete(component)
        self.db.commit()
        return True

    def list_components(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        storage_location: Optional[str] = None,
        component_type: Optional[str] = None,
        stock_status: Optional[str] = None,  # low, out, available
        tags: Optional[List[str]] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Component]:
        """List components with filtering and pagination."""
        query = self.db.query(Component).options(
            selectinload(Component.category),
            selectinload(Component.storage_location),
            selectinload(Component.tags)
        )

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Component.name.ilike(search_term),
                    Component.part_number.ilike(search_term),
                    Component.manufacturer.ilike(search_term),
                    Component.notes.ilike(search_term),
                    Component.tags.any(Tag.name.ilike(search_term))
                )
            )

        if category:
            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        if storage_location:
            query = query.join(StorageLocation).filter(
                StorageLocation.location_hierarchy.ilike(f"%{storage_location}%")
            )

        if component_type:
            query = query.filter(Component.component_type.ilike(f"%{component_type}%"))

        if stock_status:
            if stock_status == "low":
                query = query.filter(Component.quantity_on_hand <= Component.minimum_stock)
            elif stock_status == "out":
                query = query.filter(Component.quantity_on_hand == 0)
            elif stock_status == "available":
                query = query.filter(Component.quantity_on_hand > 0)

        if tags:
            query = query.join(Component.tags).filter(Tag.name.in_(tags))

        # Apply sorting
        if sort_order.lower() == "desc":
            if sort_by == "name":
                query = query.order_by(desc(Component.name))
            elif sort_by == "quantity":
                query = query.order_by(desc(Component.quantity_on_hand))
            elif sort_by == "created_at":
                query = query.order_by(desc(Component.created_at))
        else:
            if sort_by == "name":
                query = query.order_by(Component.name)
            elif sort_by == "quantity":
                query = query.order_by(Component.quantity_on_hand)
            elif sort_by == "created_at":
                query = query.order_by(Component.created_at)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        return query.all()

    def count_components(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        storage_location: Optional[str] = None,
        component_type: Optional[str] = None,
        stock_status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Count components with filtering (for pagination)."""
        query = self.db.query(Component)

        # Apply the same filters as list_components
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Component.name.ilike(search_term),
                    Component.part_number.ilike(search_term),
                    Component.manufacturer.ilike(search_term),
                    Component.notes.ilike(search_term),
                    Component.tags.any(Tag.name.ilike(search_term))
                )
            )

        if category:
            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        if storage_location:
            query = query.join(StorageLocation).filter(
                StorageLocation.location_hierarchy.ilike(f"%{storage_location}%")
            )

        if component_type:
            query = query.filter(Component.component_type.ilike(f"%{component_type}%"))

        if stock_status:
            if stock_status == "low":
                query = query.filter(Component.quantity_on_hand <= Component.minimum_stock)
            elif stock_status == "out":
                query = query.filter(Component.quantity_on_hand == 0)
            elif stock_status == "available":
                query = query.filter(Component.quantity_on_hand > 0)

        if tags:
            query = query.join(Component.tags).filter(Tag.name.in_(tags))

        return query.count()

    def search_components(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Component]:
        """
        Search components with filters - compatible with KiCad API.

        Args:
            query: Search term for component name, part number, manufacturer
            filters: Dictionary of additional filters (package, category_id, manufacturer)
            limit: Maximum number of results
            offset: Results offset for pagination

        Returns:
            List of Component objects matching the search criteria
        """
        # Use the existing list_components method with appropriate parameter mapping
        search_term = query
        category = None
        component_type = None
        manufacturer = None

        if filters:
            # Map KiCad API filters to list_components parameters
            if 'category_id' in filters:
                # Get category name from ID for list_components compatibility
                from ..models import Category
                category_obj = self.db.query(Category).filter(Category.id == filters['category_id']).first()
                if category_obj:
                    category = category_obj.name

            if 'package' in filters:
                component_type = filters['package']

            if 'manufacturer' in filters:
                manufacturer = filters['manufacturer']

        # Build additional search constraints for manufacturer
        components_query = self.db.query(Component).options(
            selectinload(Component.category),
            selectinload(Component.storage_location),
            selectinload(Component.tags),
            selectinload(Component.kicad_data)
        )

        # Apply search term filter
        if search_term:
            search_term_like = f"%{search_term}%"
            components_query = components_query.filter(
                or_(
                    Component.name.ilike(search_term_like),
                    Component.part_number.ilike(search_term_like),
                    Component.manufacturer.ilike(search_term_like),
                    Component.notes.ilike(search_term_like)
                )
            )

        # Apply category filter
        if category:
            components_query = components_query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        # Apply component type/package filter
        if component_type:
            # Check both component_type field and specifications.package
            components_query = components_query.filter(
                or_(
                    Component.component_type.ilike(f"%{component_type}%"),
                    Component.specifications.op('->>')('package').ilike(f"%{component_type}%"),
                    Component.specifications.op('->>')('Package').ilike(f"%{component_type}%")
                )
            )

        # Apply manufacturer filter
        if manufacturer:
            components_query = components_query.filter(Component.manufacturer.ilike(f"%{manufacturer}%"))

        # Apply pagination
        components_query = components_query.offset(offset).limit(limit)

        return components_query.all()

    def update_stock(
        self,
        component_id: str,
        transaction_type: str,
        quantity_change: int,
        reason: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None
    ) -> Optional[StockTransaction]:
        """Update component stock and create audit transaction."""
        component = self.db.query(Component).filter(Component.id == component_id).first()
        if not component:
            return None

        # Validate stock wouldn't go negative
        if transaction_type == "remove" and component.quantity_on_hand + quantity_change < 0:
            raise ValueError("Insufficient stock for removal")

        # Create transaction record
        previous_quantity = component.quantity_on_hand

        if transaction_type == "add":
            transaction = StockTransaction.create_add_transaction(
                component=component,
                quantity=abs(quantity_change),
                reason=reason,
                reference_id=reference_id,
                reference_type=reference_type
            )
            component.quantity_on_hand += abs(quantity_change)
        elif transaction_type == "remove":
            transaction = StockTransaction.create_remove_transaction(
                component=component,
                quantity=abs(quantity_change),
                reason=reason,
                reference_id=reference_id,
                reference_type=reference_type
            )
            component.quantity_on_hand -= abs(quantity_change)
        elif transaction_type == "adjust":
            new_quantity = previous_quantity + quantity_change
            transaction = StockTransaction.create_adjustment_transaction(
                component=component,
                new_quantity=new_quantity,
                reason=reason,
                reference_id=reference_id
            )
            component.quantity_on_hand = new_quantity
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        # Update component quantities
        transaction.new_quantity = component.quantity_on_hand

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_stock_history(
        self,
        component_id: str,
        limit: int = 50
    ) -> List[StockTransaction]:
        """Get stock transaction history for a component."""
        return (
            self.db.query(StockTransaction)
            .filter(StockTransaction.component_id == component_id)
            .order_by(desc(StockTransaction.created_at))
            .limit(limit)
            .all()
        )

    def get_low_stock_components(self, limit: int = 100) -> List[Component]:
        """Get components with low stock."""
        return (
            self.db.query(Component)
            .options(selectinload(Component.storage_location))
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(Component.minimum_stock > 0)  # Only components with minimum stock set
            .order_by(
                (Component.quantity_on_hand / func.nullif(Component.minimum_stock, 0))
            )
            .limit(limit)
            .all()
        )

    def get_component_statistics(self) -> Dict[str, int]:
        """Get component statistics."""
        total_components = self.db.query(Component).count()
        low_stock_count = (
            self.db.query(Component)
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(Component.minimum_stock > 0)
            .count()
        )
        out_of_stock_count = self.db.query(Component).filter(Component.quantity_on_hand == 0).count()

        return {
            "total_components": total_components,
            "low_stock_components": low_stock_count,
            "out_of_stock_components": out_of_stock_count,
            "available_components": total_components - out_of_stock_count
        }


    def count_components_with_kicad_data(self) -> int:
        """Count components that have KiCad data."""
        from ..models import KiCadLibraryData
        return (
            self.db.query(Component)
            .join(KiCadLibraryData, Component.id == KiCadLibraryData.component_id)
            .count()
        )