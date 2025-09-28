"""
Abstract base class for component data providers.
Defines the interface for external component data sources.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ComponentSearchResult(BaseModel):
    """Search result from an external provider"""
    part_number: str
    manufacturer: str
    description: str
    category: str | None = None
    datasheet_url: str | None = None
    image_url: str | None = None
    specifications: dict[str, Any] = {}
    price_breaks: list[dict[str, Any]] = []  # [{"quantity": 1, "price": 0.10, "currency": "USD"}]
    availability: int | None = None
    provider_id: str
    provider_url: str | None = None
    provider_part_id: str | None = None  # Provider-specific SKU/part ID


class ComponentDataProvider(ABC):
    """Abstract base class for component data providers"""

    def __init__(self, name: str, api_key: str | None = None):
        self.name = name
        self.api_key = api_key
        self.base_url = ""
        self.rate_limit_delay = 1.0  # seconds between requests

    @abstractmethod
    async def search_components(self, query: str, limit: int = 10) -> list[ComponentSearchResult]:
        """
        Search for components by part number or description.

        Args:
            query: Search term (part number, manufacturer, description)
            limit: Maximum number of results to return

        Returns:
            List of component search results
        """
        pass

    @abstractmethod
    async def get_component_details(self, part_number: str, manufacturer: str | None = None) -> ComponentSearchResult | None:
        """
        Get detailed information for a specific component.

        Args:
            part_number: Component part number
            manufacturer: Optional manufacturer name for disambiguation

        Returns:
            Detailed component information or None if not found
        """
        pass

    async def search_by_provider_sku(self, provider_sku: str) -> ComponentSearchResult | None:
        """
        Search for a component by provider-specific SKU/part ID.

        Args:
            provider_sku: Provider-specific SKU or part identifier

        Returns:
            Component information or None if not found
        """
        # Default implementation falls back to regular search
        # Providers can override this for more efficient SKU-based lookups
        results = await self.search_components(provider_sku, limit=1)
        if results and results[0].provider_part_id == provider_sku:
            return results[0]
        return None

    async def verify_connection(self) -> bool:
        """
        Verify that the provider connection is working.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple search to verify connectivity
            await self.search_components("test", limit=1)
            return True
        except Exception:
            return False

    def get_provider_info(self) -> dict[str, Any]:
        """
        Get provider information and capabilities.

        Returns:
            Dictionary with provider details
        """
        return {
            "name": self.name,
            "base_url": self.base_url,
            "supports_search": True,
            "supports_details": True,
            "rate_limit_delay": self.rate_limit_delay,
            "requires_api_key": bool(self.api_key)
        }
