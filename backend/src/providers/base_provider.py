"""
Abstract base class for component data providers.
Defines the interface for external component data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ComponentSearchResult(BaseModel):
    """Search result from an external provider"""
    part_number: str
    manufacturer: str
    description: str
    category: Optional[str] = None
    datasheet_url: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Dict[str, Any] = {}
    price_breaks: List[Dict[str, Any]] = []  # [{"quantity": 1, "price": 0.10, "currency": "USD"}]
    availability: Optional[int] = None
    provider_id: str
    provider_url: Optional[str] = None


class ComponentDataProvider(ABC):
    """Abstract base class for component data providers"""

    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.base_url = ""
        self.rate_limit_delay = 1.0  # seconds between requests

    @abstractmethod
    async def search_components(self, query: str, limit: int = 10) -> List[ComponentSearchResult]:
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
    async def get_component_details(self, part_number: str, manufacturer: Optional[str] = None) -> Optional[ComponentSearchResult]:
        """
        Get detailed information for a specific component.

        Args:
            part_number: Component part number
            manufacturer: Optional manufacturer name for disambiguation

        Returns:
            Detailed component information or None if not found
        """
        pass

    async def verify_connection(self) -> bool:
        """
        Verify that the provider connection is working.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple search to verify connectivity
            results = await self.search_components("test", limit=1)
            return True
        except Exception:
            return False

    def get_provider_info(self) -> Dict[str, Any]:
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