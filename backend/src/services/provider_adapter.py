"""
Abstract base class for provider adapters.

Defines the interface that all provider adapters (LCSC, Mouser, DigiKey, etc.)
must implement for searching parts and retrieving resources.
"""

from abc import ABC, abstractmethod


class ProviderAdapter(ABC):
    """
    Abstract base class for external provider adapters.

    Each provider (LCSC, Mouser, DigiKey) implements this interface to provide
    standardized access to their APIs for part search and resource retrieval.
    """

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for parts matching the query string.

        Args:
            query: Search query (part number, description, etc.)
            limit: Maximum number of results to return

        Returns:
            List of dictionaries containing search results. Each dict should include:
            - part_number: Provider's part number
            - name: Component name/description
            - description: Detailed description
            - manufacturer: Manufacturer name (if available)
            - datasheet_url: URL to datasheet (if available)
            - image_urls: List of image URLs (if available)
            - footprint: Footprint/package name (if available)
            - provider_url: URL to part page on provider's website

        Raises:
            Exception: If API call fails or rate limit exceeded
        """
        pass

    @abstractmethod
    async def get_part_details(self, part_number: str) -> dict:
        """
        Get detailed information about a specific part.

        Args:
            part_number: Provider's part number

        Returns:
            Dictionary containing detailed part information with same structure
            as search results, but with additional fields:
            - specifications: Dict of technical specifications
            - pricing: List of price breaks (if available)
            - stock: Current stock level (if available)
            - related_parts: List of related/substitute parts (if available)

        Raises:
            Exception: If part not found or API call fails
        """
        pass

    @abstractmethod
    async def get_resources(self, part_number: str) -> list[dict]:
        """
        Get downloadable resources for a specific part.

        Args:
            part_number: Provider's part number

        Returns:
            List of dictionaries containing resource information:
            - type: Resource type (datasheet, image, footprint, symbol, model_3d)
            - url: Download URL
            - file_name: Suggested filename
            - file_size: File size in bytes (if available)
            - description: Resource description (optional)

        Raises:
            Exception: If part not found or API call fails
        """
        pass
