"""
ComponentService with CRUD and search operations for components.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session, selectinload

from ..database.search import hybrid_search_components
from ..models import (
    Category,
    Component,
    ComponentLocation,
    KiCadLibraryData,
    StockTransaction,
    StorageLocation,
    Tag,
)

logger = logging.getLogger(__name__)

# Import EasyEDA service for LCSC KiCad conversion
try:
    from .easyeda_service import EasyEDAService

    EASYEDA_INTEGRATION_AVAILABLE = True
except ImportError:
    EASYEDA_INTEGRATION_AVAILABLE = False


class ComponentService:
    """Service layer for component operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_component(self, component_data: dict[str, Any]) -> Component:
        """Create a new component."""
        # Generate ID if not provided
        if "id" not in component_data:
            component_data["id"] = str(uuid.uuid4())

        # Extract fields that should not be set directly on Component
        tag_ids = component_data.pop("tags", [])
        storage_location_id = component_data.pop("storage_location_id", None)
        quantity_on_hand = component_data.pop("quantity_on_hand", 0)
        quantity_ordered = component_data.pop("quantity_ordered", 0)
        minimum_stock = component_data.pop("minimum_stock", 0)

        # Create component instance (without quantity fields)
        component = Component(**component_data)

        self.db.add(component)
        self.db.flush()  # Flush to get component ID

        # Create ComponentLocation record if storage location is specified
        if storage_location_id:
            # Verify storage location exists
            storage_location = (
                self.db.query(StorageLocation)
                .filter(StorageLocation.id == storage_location_id)
                .first()
            )
            if storage_location:
                component_location = ComponentLocation(
                    component_id=component.id,
                    storage_location_id=storage_location_id,
                    quantity_on_hand=quantity_on_hand,
                    quantity_ordered=quantity_ordered,
                    minimum_stock=minimum_stock,
                )
                self.db.add(component_location)

        # Handle tag associations
        if tag_ids:
            tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            component.tags = tags

        self.db.commit()
        self.db.refresh(component)

        # Create initial stock transaction if quantity > 0
        if quantity_on_hand > 0:
            initial_transaction = StockTransaction.create_add_transaction(
                component=component,
                quantity=quantity_on_hand,
                reason="Initial stock entry",
                reference_type="initial_stock",
            )
            self.db.add(initial_transaction)
            self.db.commit()

        # Auto-generate KiCad data for imported components
        if component_data.get("import_source") == "external_provider":
            self._auto_generate_kicad_data(component)

        return component

    def _auto_generate_kicad_data(
        self, component: Component
    ) -> KiCadLibraryData | None:
        """
        Automatically generate KiCad data for a component if it has sufficient information.

        Args:
            component: Component instance to generate KiCad data for

        Returns:
            KiCadLibraryData instance if generated, None otherwise
        """
        # Check if component has part number or manufacturer part number
        if not (component.part_number or component.manufacturer_part_number):
            return None

        # Check if KiCad data already exists
        existing_kicad_data = (
            self.db.query(KiCadLibraryData).filter_by(component_id=component.id).first()
        )
        if existing_kicad_data:
            return existing_kicad_data

        try:
            # Note: EasyEDA conversion removed from auto-generation due to async requirements
            # EasyEDA conversion will be handled via API endpoints for on-demand conversion

            # Generate basic KiCad data
            kicad_data = self._generate_provider_kicad_data(component)

            if kicad_data:
                self.db.add(kicad_data)
                self.db.commit()
                return kicad_data

        except Exception as e:
            # Log error but don't fail component creation
            print(
                f"Failed to auto-generate KiCad data for component {component.id}: {e}"
            )

        return None

    async def _try_easyeda_conversion(
        self, component: Component
    ) -> KiCadLibraryData | None:
        """
        Try to convert component using EasyEDA for LCSC components.

        Args:
            component: Component to convert

        Returns:
            KiCadLibraryData instance with converted files or None
        """
        if not EASYEDA_INTEGRATION_AVAILABLE:
            return None

        # Check if this is an LCSC component
        lcsc_id = self._extract_lcsc_id(component)
        if not lcsc_id:
            return None

        try:
            # Initialize EasyEDA service
            EasyEDAService()

            # Convert component using EasyEDA
            # Note: This would require an async context, so it's commented out for now
            # conversion_result = await easyeda_service.convert_lcsc_component(lcsc_id)
            return (
                None  # Temporarily disabled until proper async handling is implemented
            )

            # if not conversion_result or 'conversions' not in conversion_result:
            #     return None

            # # Create KiCad data from conversion results
            # kicad_data = KiCadLibraryData(component_id=component.id)

            # conversions = conversion_result['conversions']

            # # Set symbol data if available
            # if 'symbol' in conversions:
            #     symbol_info = conversions['symbol']
            #     kicad_data.custom_symbol_file_path = symbol_info.get('file_path')
            #     kicad_data.symbol_library = symbol_info.get('library_name', 'EasyEDA_Symbols')
            #     kicad_data.symbol_name = symbol_info.get('symbol_name', component.name or 'EasyEDA_Component')
            #     kicad_data.symbol_source = kicad_data.symbol_source.PROVIDER
            #     kicad_data.symbol_updated_at = kicad_data.symbol_updated_at

            # # Set footprint data if available
            # if 'footprint' in conversions:
            #     footprint_info = conversions['footprint']
            #     kicad_data.custom_footprint_file_path = footprint_info.get('file_path')
            #     kicad_data.footprint_library = footprint_info.get('library_name', 'EasyEDA_Footprints')
            #     kicad_data.footprint_name = footprint_info.get('footprint_name', component.name or 'EasyEDA_Component')
            #     kicad_data.footprint_source = kicad_data.footprint_source.PROVIDER
            #     kicad_data.footprint_updated_at = kicad_data.footprint_updated_at

            # # Set 3D model data if available
            # if 'model_3d' in conversions:
            #     model_info = conversions['model_3d']
            #     kicad_data.custom_3d_model_file_path = model_info.get('file_path')
            #     kicad_data.model_3d_path = model_info.get('file_path')
            #     kicad_data.model_3d_source = kicad_data.model_3d_source.PROVIDER
            #     kicad_data.model_3d_updated_at = kicad_data.model_3d_updated_at

            # # Set provider data using the set_provider_data method
            # kicad_data.set_provider_data(
            #     symbol_lib=kicad_data.symbol_library,
            #     symbol_name=kicad_data.symbol_name,
            #     footprint_lib=kicad_data.footprint_library,
            #     footprint_name=kicad_data.footprint_name,
            #     model_3d_path=kicad_data.model_3d_path
            # )

            # print(f"Successfully converted LCSC component {lcsc_id} using EasyEDA")
            # return kicad_data

        except Exception as e:
            print(f"EasyEDA conversion failed for {lcsc_id}: {e}")
            return None

    def _extract_lcsc_id(self, component: Component) -> str | None:
        """
        Extract LCSC component ID from component data.

        Args:
            component: Component to check

        Returns:
            LCSC ID string or None if not found
        """
        # Check provider info for LCSC ID
        provider_info = getattr(component, "provider_info", {})
        if isinstance(provider_info, dict):
            provider_id = provider_info.get("provider_id", "")
            if provider_id and provider_id.startswith("LCSC-C"):
                return provider_id.replace("LCSC-", "")

        # Check part numbers for LCSC format
        for field in ["part_number", "manufacturer_part_number", "provider_sku"]:
            value = getattr(component, field, "")
            if value and isinstance(value, str):
                value = value.upper().strip()
                if value.startswith("C") and len(value) >= 6 and value[1:].isdigit():
                    return value

        # Check notes for LCSC ID
        notes = getattr(component, "notes", "")
        if notes and "LCSC:" in notes.upper():
            import re

            match = re.search(r"LCSC:\s*(C\d+)", notes.upper())
            if match:
                return match.group(1)

        return None

    def _generate_provider_kicad_data(
        self, component: Component
    ) -> KiCadLibraryData | None:
        """
        Generate KiCad data based on provider component information.

        Args:
            component: Component to generate KiCad data for

        Returns:
            KiCadLibraryData instance or None if generation failed
        """
        # Generate symbol library and name based on component type
        symbol_library = self._determine_symbol_library(component)
        symbol_name = self._determine_symbol_name(component)

        # Generate footprint library and name based on package
        footprint_library = self._determine_footprint_library(component)
        footprint_name = self._determine_footprint_name(component)

        # Create KiCad data with provider source
        kicad_data = KiCadLibraryData(
            component_id=component.id,
            symbol_library=symbol_library,
            symbol_name=symbol_name,
            footprint_library=footprint_library,
            footprint_name=footprint_name,
        )

        # Set as provider data if we have any data from provider
        if symbol_library and symbol_name:
            kicad_data.set_provider_data(
                symbol_lib=symbol_library,
                symbol_name=symbol_name,
                footprint_lib=footprint_library,
                footprint_name=footprint_name,
            )

        return kicad_data

    def _determine_symbol_library(self, component: Component) -> str | None:
        """Determine appropriate symbol library based on component type."""
        if not component.component_type:
            return None

        component_type = component.component_type.lower()

        # Map component types to symbol libraries
        symbol_library_map = {
            "resistor": "Device",
            "capacitor": "Device",
            "inductor": "Device",
            "diode": "Diode",
            "transistor": "Transistor",
            "ic": "Analog",
            "microcontroller": "MCU",
            "connector": "Connector",
            "crystal": "Device",
            "switch": "Switch",
            "relay": "Relay",
        }

        for key, library in symbol_library_map.items():
            if key in component_type:
                return library

        # Default fallback
        return "Device"

    def _determine_symbol_name(self, component: Component) -> str | None:
        """Determine appropriate symbol name based on component characteristics."""
        if not component.component_type:
            return None

        component_type = component.component_type.lower()

        # Basic symbol mapping
        if "resistor" in component_type:
            return "R"
        elif "capacitor" in component_type:
            return "C"
        elif "inductor" in component_type:
            return "L"
        elif "diode" in component_type:
            return "D"
        elif "transistor" in component_type:
            if "npn" in component_type.lower():
                return "Q_NPN_BCE"
            elif "pnp" in component_type.lower():
                return "Q_PNP_BCE"
            else:
                return "Q_NPN_BCE"  # Default

        # For complex components, use manufacturer part number or generic name
        if component.manufacturer_part_number:
            return component.manufacturer_part_number.replace("-", "_").replace(
                " ", "_"
            )
        elif component.part_number:
            return component.part_number.replace("-", "_").replace(" ", "_")

        return "Generic"

    def _determine_footprint_library(self, component: Component) -> str | None:
        """Determine appropriate footprint library based on package."""
        package = None

        # Try to get package from component package field first
        if component.package:
            package = component.package.lower()
        # Try to get package from specifications
        elif component.specifications and "package" in component.specifications:
            package = str(component.specifications["package"]).lower()
        elif component.specifications and "Package" in component.specifications:
            package = str(component.specifications["Package"]).lower()

        if not package:
            return None

        # Map package types to footprint libraries
        if any(
            term in package for term in ["0402", "0603", "0805", "1206", "smd", "chip"]
        ):
            return "Resistor_SMD"
        elif any(term in package for term in ["sot", "sc70", "sot23"]):
            return "Package_TO_SOT_SMD"
        elif any(term in package for term in ["qfp", "lqfp"]):
            return "Package_QFP"
        elif any(term in package for term in ["bga"]):
            return "Package_BGA"
        elif any(term in package for term in ["dip", "pdip"]):
            return "Package_DIP"
        elif any(term in package for term in ["soic", "so"]):
            return "Package_SO"

        # Default fallback
        return "Package_SMD"

    def _determine_footprint_name(self, component: Component) -> str | None:
        """Determine appropriate footprint name based on package."""
        package = None

        # Try to get package from component package field first
        if component.package:
            package = component.package
        # Try to get package from specifications
        elif component.specifications and "package" in component.specifications:
            package = str(component.specifications["package"])
        elif component.specifications and "Package" in component.specifications:
            package = str(component.specifications["Package"])

        if not package:
            return None

        # Clean up package name for footprint
        footprint_name = package.upper().replace(" ", "_").replace("-", "_")

        # Add standard prefixes based on component type
        if component.component_type:
            component_type = component.component_type.lower()
            if any(
                term in component_type for term in ["resistor", "capacitor", "inductor"]
            ):
                return f"R_{footprint_name}"

        return footprint_name

    def get_component(self, component_id: str) -> Component | None:
        """Get a component by ID with all relationships loaded."""
        return (
            self.db.query(Component)
            .options(
                selectinload(Component.category),
                selectinload(Component.locations).selectinload(
                    ComponentLocation.storage_location
                ),
                selectinload(Component.tags),
                selectinload(Component.attachments),
                selectinload(Component.kicad_data),
                selectinload(Component.custom_field_values).selectinload(
                    Component.custom_field_values.property.mapper.class_.field
                ),
            )
            .filter(Component.id == component_id)
            .first()
        )

    def update_component(
        self, component_id: str, update_data: dict[str, Any]
    ) -> Component | None:
        """Update a component."""
        component = (
            self.db.query(Component).filter(Component.id == component_id).first()
        )
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
        component = (
            self.db.query(Component).filter(Component.id == component_id).first()
        )
        if not component:
            return False

        self.db.delete(component)
        self.db.commit()
        return True

    def list_components(
        self,
        search: str | None = None,
        category: str | None = None,
        category_id: str | None = None,
        storage_location: str | None = None,
        component_type: str | None = None,
        stock_status: str | None = None,  # low, out, available
        tags: list[str] | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
        nl_query: str | None = None,
    ) -> tuple[list[Component], dict[str, Any] | None]:
        """
        List components with filtering and pagination.

        Search functionality includes intelligent ranking that prioritizes results by field relevance:
        1. Component name matches (highest priority)
        2. Component type matches
        3. Part number matches
        4. Value matches
        5. Package matches
        6. Manufacturer matches
        7. Tag matches
        8. Notes matches (lowest priority)

        When using default sorting (sort_by="name", sort_order="asc") with a search term,
        results are automatically ranked by field priority to ensure the most relevant
        components appear first (e.g., searching "cap" returns capacitors before components
        that only mention "capital" in their notes).

        Args:
            nl_query: Natural language query string (e.g., "find resistors with low stock").
                     When provided, parsed parameters override manual parameters unless
                     manual parameters are explicitly set. Returns metadata about parsing.

        Returns:
            Tuple of (components_list, nl_metadata). nl_metadata is None if nl_query not used.
        """
        nl_metadata = None

        # Process natural language query if provided
        if nl_query:
            try:
                from .natural_language_search_service import (
                    NaturalLanguageSearchService,
                )

                nl_service = NaturalLanguageSearchService()
                parsed_result = nl_service.parse_query(nl_query)

                logger.info(
                    f"NL query parsed: '{nl_query}' -> "
                    f"Intent: {parsed_result.get('intent')}, "
                    f"Confidence: {parsed_result.get('confidence'):.2f}, "
                    f"Fallback: {parsed_result.get('fallback_to_fts5')}"
                )

                # Build metadata for response
                nl_metadata = {
                    "query": nl_query,
                    "confidence": parsed_result.get("confidence", 0.0),
                    "parsed_entities": parsed_result.get("parsed_entities", {}),
                    "fallback_to_fts5": parsed_result.get("fallback_to_fts5", True),
                    "intent": parsed_result.get("intent", "unknown"),
                }

                # Merge parsed parameters with manual parameters
                # Priority: Manual filters > NL parsed filters
                # Only use NL params if manual params are not set
                if search is None and "search" in parsed_result:
                    search = parsed_result["search"]
                if component_type is None and "component_type" in parsed_result:
                    component_type = parsed_result["component_type"]
                if stock_status is None and "stock_status" in parsed_result:
                    stock_status = parsed_result["stock_status"]
                if storage_location is None and "storage_location" in parsed_result:
                    storage_location = parsed_result["storage_location"]
                if category is None and "category" in parsed_result:
                    category = parsed_result["category"]

                # Log low confidence queries for analysis
                if parsed_result.get("confidence", 0.0) < 0.5:
                    logger.warning(
                        f"Low confidence NL query: '{nl_query}' "
                        f"(confidence: {parsed_result.get('confidence'):.2f})"
                    )

            except Exception as e:
                # Never fail the entire request if NL parsing fails
                logger.error(
                    f"NL query parsing failed for '{nl_query}': {e}", exc_info=True
                )
                # Set metadata to indicate parsing error
                nl_metadata = {
                    "query": nl_query,
                    "confidence": 0.0,
                    "parsed_entities": {},
                    "fallback_to_fts5": True,
                    "intent": "error",
                    "error": str(e),
                }

        query = self.db.query(Component).options(
            selectinload(Component.category),
            selectinload(Component.locations).selectinload(
                ComponentLocation.storage_location
            ),
            selectinload(Component.tags),
            selectinload(Component.attachments),
        )

        # Apply filters
        if search:
            # Use hybrid search (FTS5 + rapidfuzz) for better recall and typo tolerance
            component_ids = hybrid_search_components(
                search, session=self.db, limit=1000, fuzzy_threshold=5
            )
            if component_ids:
                query = query.filter(Component.id.in_(component_ids))
            else:
                # No results from search - return empty result
                query = query.filter(Component.id.is_(None))

        if category:
            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        if category_id:
            query = query.filter(Component.category_id == category_id)

        if storage_location:
            query = (
                query.join(ComponentLocation)
                .join(StorageLocation)
                .filter(
                    StorageLocation.location_hierarchy.ilike(f"%{storage_location}%")
                )
            )

        if component_type:
            query = query.filter(Component.component_type.ilike(f"%{component_type}%"))

        # Stock status filtering with proper multi-location support
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

        if tags:
            query = query.join(Component.tags).filter(Tag.name.in_(tags))

        # Apply sorting
        if sort_order.lower() == "desc":
            if sort_by == "name":
                query = query.order_by(desc(Component.name))
            elif sort_by == "created_at":
                query = query.order_by(desc(Component.created_at))
            elif sort_by == "updated_at":
                query = query.order_by(desc(Component.updated_at))
            # Note: quantity sorting removed - quantity_on_hand is now a hybrid property
            # and cannot be used directly in SQL ORDER BY
        else:
            if sort_by == "name":
                query = query.order_by(Component.name)
            elif sort_by == "created_at":
                query = query.order_by(Component.created_at)
            elif sort_by == "updated_at":
                query = query.order_by(Component.updated_at)
            # Note: quantity sorting removed - quantity_on_hand is now a hybrid property
            # and cannot be used directly in SQL ORDER BY

        # Get results before pagination for search ranking
        if search and sort_by == "name" and sort_order == "asc":
            # Get all matching results for ranking, then apply pagination
            all_results = query.all()
            ranked_results = self._rank_search_results(all_results, search.lower())
            # Apply pagination to ranked results
            return ranked_results[offset : offset + limit], nl_metadata
        else:
            # Apply pagination
            query = query.offset(offset).limit(limit)
            return query.all(), nl_metadata

    def count_components(
        self,
        search: str | None = None,
        category: str | None = None,
        category_id: str | None = None,
        storage_location: str | None = None,
        component_type: str | None = None,
        stock_status: str | None = None,
        tags: list[str] | None = None,
    ) -> int:
        """Count components with filtering (for pagination)."""
        query = self.db.query(Component)

        # Apply the same filters as list_components
        if search:
            # Use hybrid search (FTS5 + rapidfuzz) - same as list_components
            component_ids = hybrid_search_components(
                search, session=self.db, limit=10000, fuzzy_threshold=5
            )
            if component_ids:
                query = query.filter(Component.id.in_(component_ids))
            else:
                # No results from search - return empty result
                query = query.filter(Component.id.is_(None))

        if category:
            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))

        if category_id:
            query = query.filter(Component.category_id == category_id)

        if storage_location:
            query = (
                query.join(ComponentLocation)
                .join(StorageLocation)
                .filter(
                    StorageLocation.location_hierarchy.ilike(f"%{storage_location}%")
                )
            )

        if component_type:
            query = query.filter(Component.component_type.ilike(f"%{component_type}%"))

        # Stock status filtering with proper multi-location support
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

        if tags:
            query = query.join(Component.tags).filter(Tag.name.in_(tags))

        return query.count()

    def search_components(
        self,
        query: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Component]:
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
            if "category_id" in filters:
                # Get category name from ID for list_components compatibility
                from ..models import Category

                category_obj = (
                    self.db.query(Category)
                    .filter(Category.id == filters["category_id"])
                    .first()
                )
                if category_obj:
                    category = category_obj.name

            if "package" in filters:
                component_type = filters["package"]

            if "manufacturer" in filters:
                manufacturer = filters["manufacturer"]

        # Build additional search constraints for manufacturer
        components_query = self.db.query(Component).options(
            selectinload(Component.category),
            selectinload(Component.locations).selectinload(
                ComponentLocation.storage_location
            ),
            selectinload(Component.tags),
            selectinload(Component.kicad_data),
        )

        # Apply search term filter with weighted ranking
        if search_term:
            search_term_like = f"%{search_term}%"
            components_query = components_query.filter(
                or_(
                    Component.name.ilike(search_term_like),
                    Component.part_number.ilike(search_term_like),
                    Component.local_part_id.ilike(search_term_like),
                    Component.barcode_id.ilike(search_term_like),
                    Component.manufacturer_part_number.ilike(search_term_like),
                    Component.provider_sku.ilike(search_term_like),
                    Component.manufacturer.ilike(search_term_like),
                    Component.component_type.ilike(search_term_like),
                    Component.value.ilike(search_term_like),
                    Component.package.ilike(search_term_like),
                    Component.notes.ilike(search_term_like),
                )
            ).order_by(
                # Prioritize exact matches first, then partial matches by field importance
                case(
                    (Component.name.ilike(search_term_like), 1),
                    (Component.component_type.ilike(search_term_like), 2),
                    (Component.part_number.ilike(search_term_like), 3),
                    (Component.value.ilike(search_term_like), 4),
                    (Component.package.ilike(search_term_like), 5),
                    (Component.manufacturer.ilike(search_term_like), 6),
                    else_=7,  # notes get lowest priority
                ),
                Component.name,
            )

        # Apply category filter
        if category:
            components_query = components_query.join(Category).filter(
                Category.name.ilike(f"%{category}%")
            )

        # Apply component type/package filter
        if component_type:
            # Check both component_type field and specifications.package
            components_query = components_query.filter(
                or_(
                    Component.component_type.ilike(f"%{component_type}%"),
                    Component.specifications.op("->>")("package").ilike(
                        f"%{component_type}%"
                    ),
                    Component.specifications.op("->>")("Package").ilike(
                        f"%{component_type}%"
                    ),
                )
            )

        # Apply manufacturer filter
        if manufacturer:
            components_query = components_query.filter(
                Component.manufacturer.ilike(f"%{manufacturer}%")
            )

        # Apply pagination
        components_query = components_query.offset(offset).limit(limit)

        return components_query.all()

    def _rank_search_results(
        self, components: list[Component], search_term: str
    ) -> list[Component]:
        """
        Rank search results by field relevance priority.
        Higher priority fields get ranked first.
        """

        def get_search_score(component: Component) -> int:
            """Calculate search score based on field matches. Lower score = higher priority."""
            search_lower = search_term.lower()

            # Check each field and return priority score (lower = better)
            if component.name and search_lower in component.name.lower():
                return 1  # Highest priority: name match
            elif (
                component.local_part_id
                and search_lower in component.local_part_id.lower()
            ):
                return 2  # Local part ID match (user-friendly identifier)
            elif (
                component.component_type
                and search_lower in component.component_type.lower()
            ):
                return 3  # Component type match
            elif (
                component.manufacturer_part_number
                and search_lower in component.manufacturer_part_number.lower()
            ):
                return 4  # Manufacturer part number match
            elif (
                component.part_number and search_lower in component.part_number.lower()
            ):
                return 5  # Legacy part number match
            elif component.barcode_id and search_lower in component.barcode_id.lower():
                return 6  # Barcode ID match
            elif component.value and search_lower in component.value.lower():
                return 7  # Value match
            elif component.package and search_lower in component.package.lower():
                return 8  # Package match
            elif (
                component.manufacturer
                and search_lower in component.manufacturer.lower()
            ):
                return 9  # Manufacturer match
            elif (
                component.provider_sku
                and search_lower in component.provider_sku.lower()
            ):
                return 10  # Provider SKU match
            elif component.tags and any(
                search_lower in tag.name.lower() for tag in component.tags
            ):
                return 11  # Tag match
            elif component.notes and search_lower in component.notes.lower():
                return 12  # Lowest priority: notes match
            else:
                return 13  # No direct match (shouldn't happen given the filter)

        # Sort by search score (priority), then by name
        return sorted(
            components,
            key=lambda c: (get_search_score(c), c.name.lower() if c.name else ""),
        )

    def update_stock(
        self,
        component_id: str,
        transaction_type: str,
        quantity_change: int,
        reason: str,
        reference_id: str | None = None,
        reference_type: str | None = None,
    ) -> StockTransaction | None:
        """Update component stock and create audit transaction."""
        component = (
            self.db.query(Component).filter(Component.id == component_id).first()
        )
        if not component:
            return None

        # Validate stock wouldn't go negative
        if (
            transaction_type == "remove"
            and component.quantity_on_hand + quantity_change < 0
        ):
            raise ValueError("Insufficient stock for removal")

        # Create transaction record
        previous_quantity = component.quantity_on_hand

        if transaction_type == "add":
            transaction = StockTransaction.create_add_transaction(
                component=component,
                quantity=abs(quantity_change),
                reason=reason,
                reference_id=reference_id,
                reference_type=reference_type,
            )
            component.quantity_on_hand += abs(quantity_change)
        elif transaction_type == "remove":
            transaction = StockTransaction.create_remove_transaction(
                component=component,
                quantity=abs(quantity_change),
                reason=reason,
                reference_id=reference_id,
                reference_type=reference_type,
            )
            component.quantity_on_hand -= abs(quantity_change)
        elif transaction_type == "adjust":
            new_quantity = previous_quantity + quantity_change
            transaction = StockTransaction.create_adjustment_transaction(
                component=component,
                new_quantity=new_quantity,
                reason=reason,
                reference_id=reference_id,
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
        self, component_id: str, limit: int = 50
    ) -> list[StockTransaction]:
        """Get stock transaction history for a component."""
        return (
            self.db.query(StockTransaction)
            .filter(StockTransaction.component_id == component_id)
            .order_by(desc(StockTransaction.created_at))
            .limit(limit)
            .all()
        )

    def get_low_stock_components(self, limit: int = 100) -> list[Component]:
        """Get components with low stock."""
        return (
            self.db.query(Component)
            .options(selectinload(Component.storage_location))
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(
                Component.minimum_stock > 0
            )  # Only components with minimum stock set
            .order_by(
                Component.quantity_on_hand / func.nullif(Component.minimum_stock, 0)
            )
            .limit(limit)
            .all()
        )

    def get_component_statistics(self) -> dict[str, int]:
        """Get component statistics."""
        total_components = self.db.query(Component).count()
        low_stock_count = (
            self.db.query(Component)
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(Component.minimum_stock > 0)
            .count()
        )
        out_of_stock_count = (
            self.db.query(Component).filter(Component.quantity_on_hand == 0).count()
        )

        return {
            "total_components": total_components,
            "low_stock_components": low_stock_count,
            "out_of_stock_components": out_of_stock_count,
            "available_components": total_components - out_of_stock_count,
        }

    def count_components_with_kicad_data(self) -> int:
        """Count components that have KiCad data."""
        from ..models import KiCadLibraryData

        return (
            self.db.query(Component)
            .join(KiCadLibraryData, Component.id == KiCadLibraryData.component_id)
            .count()
        )
