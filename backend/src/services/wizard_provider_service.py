"""
Wizard provider service for managing external component providers.

Provides high-level operations for listing providers, searching across
providers, and dynamically instantiating provider adapters for the wizard feature.
"""

import importlib
import logging

from sqlalchemy.orm import Session

from ..models.wizard_provider import Provider

logger = logging.getLogger(__name__)


class WizardProviderService:
    """
    Service for managing component data providers in the wizard feature.

    Handles provider listing, adapter instantiation, and delegating
    search operations to the appropriate provider adapter.
    """

    @staticmethod
    async def list_providers(db: Session) -> list[Provider]:
        """
        Get all active providers.

        Args:
            db: Database session

        Returns:
            List of Provider objects
        """
        return db.query(Provider).filter(Provider.status == "active").all()

    @staticmethod
    async def get_provider(db: Session, provider_id: int) -> Provider:
        """
        Get a specific provider by ID.

        Args:
            db: Database session
            provider_id: Provider ID

        Returns:
            Provider object

        Raises:
            ValueError: If provider not found
        """
        provider = db.query(Provider).filter(Provider.id == provider_id).first()

        if not provider:
            raise ValueError(f"Provider with ID {provider_id} not found")

        return provider

    @staticmethod
    def _instantiate_adapter(provider: Provider):
        """
        Dynamically instantiate the provider adapter class.

        Args:
            provider: Provider object with adapter_class attribute

        Returns:
            Instance of the provider adapter

        Raises:
            ImportError: If adapter class cannot be imported
            AttributeError: If adapter class not found in module
        """
        try:
            # Import adapter class from services module
            # Example: adapter_class = "LCSCAdapter" -> src.services.lcsc_adapter.LCSCAdapter
            module_name = provider.adapter_class.lower().replace("adapter", "_adapter")
            module_path = f"src.services.{module_name}"

            module = importlib.import_module(module_path)
            adapter_class = getattr(module, provider.adapter_class)

            # Instantiate adapter with provider's base_url
            return adapter_class(base_url=provider.base_url)

        except (ImportError, AttributeError) as e:
            logger.error(
                f"Failed to instantiate adapter '{provider.adapter_class}': {str(e)}"
            )
            raise ImportError(
                f"Could not load adapter class '{provider.adapter_class}': {str(e)}"
            )

    @staticmethod
    async def search_provider(
        db: Session, provider_id: int, query: str, limit: int = 10
    ) -> dict:
        """
        Search a specific provider for parts matching the query.

        Args:
            db: Database session
            provider_id: Provider ID to search
            query: Search query string
            limit: Maximum number of results

        Returns:
            Dictionary containing:
            - provider_id: Provider ID
            - provider_name: Provider name
            - results: List of part dictionaries from adapter.search()

        Raises:
            ValueError: If provider not found
            ImportError: If adapter cannot be instantiated
            Exception: If search fails
        """
        # Get provider
        provider = await WizardProviderService.get_provider(db, provider_id)

        if not provider.is_active:
            raise ValueError(f"Provider '{provider.name}' is not active")

        # Instantiate adapter
        adapter = WizardProviderService._instantiate_adapter(provider)

        # Execute search
        try:
            results = await adapter.search(query, limit)

            return {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "results": results,
            }

        except Exception as e:
            logger.error(
                f"Search failed for provider '{provider.name}' with query '{query}': {str(e)}"
            )
            # Re-raise for controller to handle
            raise

    @staticmethod
    async def get_part_details(db: Session, provider_id: int, part_number: str) -> dict:
        """
        Get detailed information about a part from a specific provider.

        Args:
            db: Database session
            provider_id: Provider ID
            part_number: Provider's part number

        Returns:
            Dictionary with part details from adapter.get_part_details()

        Raises:
            ValueError: If provider not found
            Exception: If retrieval fails
        """
        provider = await WizardProviderService.get_provider(db, provider_id)
        adapter = WizardProviderService._instantiate_adapter(provider)

        return await adapter.get_part_details(part_number)

    @staticmethod
    async def get_part_resources(
        db: Session, provider_id: int, part_number: str
    ) -> list[dict]:
        """
        Get downloadable resources for a part from a specific provider.

        Args:
            db: Database session
            provider_id: Provider ID
            part_number: Provider's part number

        Returns:
            List of resource dictionaries from adapter.get_resources()

        Raises:
            ValueError: If provider not found
            Exception: If retrieval fails
        """
        provider = await WizardProviderService.get_provider(db, provider_id)
        adapter = WizardProviderService._instantiate_adapter(provider)

        return await adapter.get_resources(part_number)
