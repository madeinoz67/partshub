"""
Component import service for importing components from external providers.
Handles bulk imports, data validation, and integration with local database.
"""

import logging
from typing import Any
from uuid import uuid4

from ..database import get_session
from ..models import Category, Component
from ..providers.base_provider import ComponentSearchResult
from .provider_service import ProviderService

logger = logging.getLogger(__name__)


class ImportService:
    """Service for importing components from external providers"""

    def __init__(self):
        self.provider_service = ProviderService()

    async def search_and_prepare_import(
        self, query: str, limit: int = 20, providers: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Search providers and prepare components for import.

        Args:
            query: Search term
            limit: Maximum results
            providers: Specific providers to search

        Returns:
            List of components ready for import with mapping information
        """
        try:
            # Search external providers
            search_results = await self.provider_service.search_components(
                query, limit, providers
            )

            if not search_results:
                logger.info(f"No components found for search: {query}")
                return []

            # Prepare import data with local mapping
            import_data = []
            for result in search_results:
                prepared = await self._prepare_component_for_import(result)
                if prepared:
                    import_data.append(prepared)

            logger.info(
                f"Prepared {len(import_data)} components for import from search: {query}"
            )
            return import_data

        except Exception as e:
            logger.error(f"Error preparing import for '{query}': {e}")
            return []

    async def _prepare_component_for_import(
        self, search_result: ComponentSearchResult
    ) -> dict[str, Any] | None:
        """
        Prepare a component search result for import into local database.

        Args:
            search_result: Component data from external provider

        Returns:
            Dictionary with import-ready component data
        """
        try:
            # Check if component already exists locally
            session = get_session()
            existing = (
                session.query(Component)
                .filter_by(
                    part_number=search_result.part_number,
                    manufacturer=search_result.manufacturer,
                )
                .first()
            )

            if existing:
                logger.debug(
                    f"Component {search_result.part_number} already exists locally"
                )
                return None

            # Prepare component data
            component_data = {
                "id": str(uuid4()),
                "part_number": search_result.part_number,
                "manufacturer": search_result.manufacturer,
                "description": search_result.description,
                "category": search_result.category,
                "specifications": search_result.specifications,
                "datasheet_url": search_result.datasheet_url,
                "image_url": search_result.image_url,
                "provider_info": {
                    "provider_id": search_result.provider_id,
                    "provider_url": search_result.provider_url,
                    "price_breaks": search_result.price_breaks,
                    "availability": search_result.availability,
                },
                "import_source": "external_provider",
                "quantity_on_hand": 0,
                "minimum_stock": 0,
                "location": None,  # User will need to specify
                "notes": f"Imported from {search_result.provider_id}",
            }

            return component_data

        except Exception as e:
            logger.error(f"Error preparing component {search_result.part_number}: {e}")
            return None

    async def import_components(
        self,
        components_data: list[dict[str, Any]],
        default_location_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Import components into the local database.

        Args:
            components_data: List of component data to import
            default_location_id: Default storage location for all components

        Returns:
            Import summary with success/failure counts
        """
        if not components_data:
            return {"imported": 0, "failed": 0, "skipped": 0, "errors": []}

        imported_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        session = get_session()

        try:
            for comp_data in components_data:
                try:
                    # Get or create category
                    category_id = await self._get_or_create_category_id(
                        comp_data.get("category")
                    )

                    # Prepare component for database
                    component = Component(
                        id=comp_data["id"],
                        part_number=comp_data["part_number"],
                        name=comp_data.get("description", comp_data["part_number"]),
                        manufacturer=comp_data["manufacturer"],
                        category_id=category_id,
                        specifications=comp_data["specifications"],
                        quantity_on_hand=comp_data.get("quantity_on_hand", 0),
                        minimum_stock=comp_data.get("minimum_stock", 0),
                        storage_location_id=default_location_id
                        or comp_data.get("location"),
                        notes=comp_data.get("notes", ""),
                    )

                    session.add(component)
                    imported_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to import {comp_data.get('part_number', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Commit all imports
            session.commit()

            logger.info(
                f"Import completed: {imported_count} imported, {failed_count} failed, {skipped_count} skipped"
            )

            return {
                "imported": imported_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "errors": errors,
            }

        except Exception as e:
            session.rollback()
            error_msg = f"Import transaction failed: {str(e)}"
            logger.error(error_msg)
            return {
                "imported": 0,
                "failed": len(components_data),
                "skipped": 0,
                "errors": [error_msg],
            }
        finally:
            session.close()

    async def _get_or_create_category_id(self, category_name: str | None) -> str | None:
        """Get or create category and return its ID"""
        if not category_name:
            return None

        session = get_session()
        try:
            # Try to find existing category
            category = session.query(Category).filter_by(name=category_name).first()

            if not category:
                # Create new category
                category = Category(
                    id=str(uuid4()),
                    name=category_name,
                    description=f"Auto-created during import: {category_name}",
                )
                session.add(category)
                session.commit()
                logger.debug(f"Created new category: {category_name}")

            return category.id

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating category {category_name}: {e}")
            return None
        finally:
            session.close()

    async def import_from_search(
        self,
        query: str,
        limit: int = 20,
        default_location_id: str | None = None,
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Search and import components in one operation.

        Args:
            query: Search term
            limit: Maximum components to import
            default_location_id: Default storage location
            providers: Specific providers to search

        Returns:
            Import summary
        """
        try:
            # Search and prepare components
            components_data = await self.search_and_prepare_import(
                query, limit, providers
            )

            if not components_data:
                return {
                    "imported": 0,
                    "failed": 0,
                    "skipped": 0,
                    "errors": ["No components found"],
                }

            # Import components
            result = await self.import_components(components_data, default_location_id)

            logger.info(f"Import from search '{query}' completed: {result}")
            return result

        except Exception as e:
            error_msg = f"Import from search failed for '{query}': {str(e)}"
            logger.error(error_msg)
            return {"imported": 0, "failed": 0, "skipped": 0, "errors": [error_msg]}

    async def get_provider_status(self) -> dict[str, Any]:
        """Get status of all component providers"""
        try:
            provider_info = self.provider_service.get_provider_info()
            provider_status = await self.provider_service.verify_providers()

            # Combine info and status
            status = {}
            for name, info in provider_info.items():
                status[name] = {**info, "connected": provider_status.get(name, False)}

            return status

        except Exception as e:
            logger.error(f"Error getting provider status: {e}")
            return {}
