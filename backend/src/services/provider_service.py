"""
Provider service for managing multiple component data providers.
Handles provider registration, searches across providers, and result aggregation.
"""

import asyncio
import logging
import re
from typing import Any

from ..providers.base_provider import ComponentDataProvider, ComponentSearchResult
from ..providers.lcsc_provider import LCSCProvider

logger = logging.getLogger(__name__)


class ProviderService:
    """Service for managing component data providers"""

    def __init__(self):
        self.providers: dict[str, ComponentDataProvider] = {}
        self.enabled_providers: set[str] = set()
        self._initialize_default_providers()

    def _initialize_default_providers(self):
        """Initialize default component providers"""
        try:
            # Add LCSC provider
            lcsc = LCSCProvider()
            self.register_provider("lcsc", lcsc)
            self.enable_provider("lcsc")

            logger.info("Initialized default providers: LCSC")

        except Exception as e:
            logger.error(f"Error initializing default providers: {e}")

    def register_provider(self, name: str, provider: ComponentDataProvider):
        """Register a new component data provider"""
        self.providers[name] = provider
        logger.info(f"Registered provider: {name}")

    def enable_provider(self, name: str):
        """Enable a provider for searches"""
        if name in self.providers:
            self.enabled_providers.add(name)
            logger.info(f"Enabled provider: {name}")
        else:
            logger.warning(f"Cannot enable unknown provider: {name}")

    def disable_provider(self, name: str):
        """Disable a provider from searches"""
        self.enabled_providers.discard(name)
        logger.info(f"Disabled provider: {name}")

    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled provider names"""
        return list(self.enabled_providers)

    async def search_all_providers(
        self,
        query: str,
        limit_per_provider: int = 10,
        providers: list[str] | None = None,
    ) -> dict[str, list[ComponentSearchResult]]:
        """
        Search across multiple providers in parallel.

        Args:
            query: Search term
            limit_per_provider: Maximum results per provider
            providers: Specific providers to search (default: all enabled)

        Returns:
            Dictionary mapping provider names to their search results
        """
        target_providers = providers or self.get_enabled_providers()
        if not target_providers:
            logger.warning("No providers available for search")
            return {}

        # Create search tasks for all providers
        tasks = []
        for provider_name in target_providers:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                task = self._search_provider_safe(
                    provider_name, provider, query, limit_per_provider
                )
                tasks.append(task)

        if not tasks:
            return {}

        # Execute searches in parallel
        logger.info(f"Searching {len(tasks)} providers for '{query}'")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        provider_results = {}
        for i, result in enumerate(results):
            provider_name = (
                target_providers[i] if i < len(target_providers) else f"provider_{i}"
            )
            if isinstance(result, Exception):
                logger.error(f"Provider {provider_name} search failed: {result}")
                provider_results[provider_name] = []
            else:
                provider_results[provider_name] = result

        return provider_results

    async def _search_provider_safe(
        self,
        provider_name: str,
        provider: ComponentDataProvider,
        query: str,
        limit: int,
    ) -> list[ComponentSearchResult]:
        """Safely search a provider with error handling"""
        try:
            results = await provider.search_components(query, limit)
            logger.debug(
                f"Provider {provider_name} returned {len(results)} results for '{query}'"
            )
            return results
        except Exception as e:
            logger.error(f"Error searching provider {provider_name}: {e}")
            return []

    def aggregate_search_results(
        self, provider_results: dict[str, list[ComponentSearchResult]]
    ) -> list[ComponentSearchResult]:
        """
        Aggregate and deduplicate search results from multiple providers.

        Args:
            provider_results: Results from each provider

        Returns:
            Combined and deduplicated results, sorted by relevance
        """
        all_results = []
        seen_parts = set()

        # Prioritize results from different providers
        for provider_name, results in provider_results.items():
            for result in results:
                # Create a key for deduplication based on part number and manufacturer
                part_key = f"{result.part_number.upper()}_{result.manufacturer.upper()}"

                if part_key not in seen_parts:
                    seen_parts.add(part_key)
                    # Add provider info to track source
                    result.provider_id = f"{provider_name}_{result.provider_id}"
                    all_results.append(result)

        # Sort by manufacturer and part number for consistent ordering
        all_results.sort(key=lambda x: (x.manufacturer, x.part_number))

        logger.info(
            f"Aggregated {len(all_results)} unique components from {len(provider_results)} providers"
        )
        return all_results

    async def search_components(
        self, query: str, limit: int = 50, providers: list[str] | None = None
    ) -> list[ComponentSearchResult]:
        """
        Search for components across all enabled providers.

        Args:
            query: Search term
            limit: Maximum total results to return
            providers: Specific providers to search (optional)

        Returns:
            Aggregated and deduplicated search results
        """
        limit_per_provider = min(limit, 20)  # Distribute limit across providers

        # Search all providers
        provider_results = await self.search_all_providers(
            query, limit_per_provider, providers
        )

        # Aggregate results
        results = self.aggregate_search_results(provider_results)

        # Apply final limit
        return results[:limit]

    async def get_component_details(
        self,
        part_number: str,
        manufacturer: str | None = None,
        provider: str | None = None,
    ) -> ComponentSearchResult | None:
        """
        Get detailed component information from providers.

        Args:
            part_number: Component part number
            manufacturer: Component manufacturer (optional)
            provider: Specific provider to query (optional)

        Returns:
            Detailed component information or None if not found
        """
        target_providers = [provider] if provider else self.get_enabled_providers()

        for provider_name in target_providers:
            if provider_name not in self.providers:
                continue

            try:
                provider_obj = self.providers[provider_name]
                result = await provider_obj.get_component_details(
                    part_number, manufacturer
                )
                if result:
                    result.provider_id = f"{provider_name}_{result.provider_id}"
                    return result
            except Exception as e:
                logger.error(f"Error getting details from {provider_name}: {e}")

        return None

    async def verify_providers(self) -> dict[str, bool]:
        """
        Verify connectivity for all registered providers.

        Returns:
            Dictionary mapping provider names to their connection status
        """
        verification_tasks = []
        provider_names = []

        for name, provider in self.providers.items():
            provider_names.append(name)
            verification_tasks.append(provider.verify_connection())

        if not verification_tasks:
            return {}

        results = await asyncio.gather(*verification_tasks, return_exceptions=True)

        status = {}
        for i, result in enumerate(results):
            provider_name = provider_names[i]
            if isinstance(result, Exception):
                status[provider_name] = False
                logger.error(f"Provider {provider_name} verification failed: {result}")
            else:
                status[provider_name] = result
                logger.info(
                    f"Provider {provider_name} verification: {'OK' if result else 'FAILED'}"
                )

        return status

    async def search_by_provider_sku(
        self, provider_sku: str, providers: list[str] | None = None
    ) -> dict[str, ComponentSearchResult | None]:
        """
        Search for components by provider-specific SKU across all providers.

        Args:
            provider_sku: Provider-specific SKU or part identifier
            providers: Specific providers to search (default: all enabled)

        Returns:
            Dictionary mapping provider names to their search results
        """
        target_providers = providers or self.get_enabled_providers()
        if not target_providers:
            logger.warning("No providers available for SKU search")
            return {}

        # Create search tasks for all providers
        tasks = []
        for provider_name in target_providers:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                task = self._search_provider_sku_safe(
                    provider_name, provider, provider_sku
                )
                tasks.append(task)

        if not tasks:
            return {}

        # Execute searches in parallel
        logger.info(f"Searching {len(tasks)} providers for SKU '{provider_sku}'")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        provider_results = {}
        for i, result in enumerate(results):
            provider_name = (
                target_providers[i] if i < len(target_providers) else f"provider_{i}"
            )
            if isinstance(result, Exception):
                logger.error(f"Provider {provider_name} SKU search failed: {result}")
                provider_results[provider_name] = None
            else:
                provider_results[provider_name] = result

        return provider_results

    async def _search_provider_sku_safe(
        self, provider_name: str, provider: ComponentDataProvider, provider_sku: str
    ) -> ComponentSearchResult | None:
        """Safely search a provider by SKU with error handling"""
        try:
            result = await provider.search_by_provider_sku(provider_sku)
            if result:
                logger.debug(
                    f"Provider {provider_name} found component for SKU '{provider_sku}'"
                )
                # Ensure provider info is tagged
                result.provider_id = f"{provider_name}_{result.provider_id}"
            return result
        except Exception as e:
            logger.error(f"Error searching provider {provider_name} by SKU: {e}")
            return None

    async def unified_search(
        self,
        query: str,
        search_type: str = "auto",  # "auto", "part_number", "provider_sku"
        limit: int = 50,
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Unified search that combines manufacturer part number and provider SKU searches.

        Args:
            query: Search term (part number or provider SKU)
            search_type: Type of search to perform
            limit: Maximum total results to return
            providers: Specific providers to search (optional)

        Returns:
            Combined search results with metadata
        """
        results = {
            "query": query,
            "search_type": search_type,
            "part_number_results": [],
            "provider_sku_results": {},
            "total_results": 0,
        }

        # Determine search strategy
        if search_type == "auto":
            # Auto-detect based on query pattern
            search_type = self._detect_search_type(query)

        # Perform searches based on type
        if search_type in ["auto", "part_number"]:
            # Search by part number/manufacturer
            pn_results = await self.search_components(query, limit, providers)
            results["part_number_results"] = pn_results
            results["total_results"] += len(pn_results)

        if search_type in ["auto", "provider_sku"]:
            # Search by provider SKU
            sku_results = await self.search_by_provider_sku(query, providers)
            # Filter out None results
            filtered_sku_results = {
                k: v for k, v in sku_results.items() if v is not None
            }
            results["provider_sku_results"] = filtered_sku_results
            results["total_results"] += len(filtered_sku_results)

        logger.info(
            f"Unified search for '{query}' ({search_type}) returned {results['total_results']} total results"
        )
        return results

    def _detect_search_type(self, query: str) -> str:
        """
        Auto-detect search type based on query pattern.

        Args:
            query: Search query

        Returns:
            Detected search type: "part_number" or "provider_sku"
        """
        query = query.strip().upper()

        # Check for common provider SKU patterns
        sku_patterns = [
            r"^C\d{5,7}$",  # LCSC: C123456
            r"^DK\d+$",  # Digi-Key: DK12345
            r"^M\d+$",  # Mouser: M12345
            r"^RS\d+$",  # RS Components: RS12345
        ]

        for pattern in sku_patterns:
            if re.match(pattern, query):
                return "provider_sku"

        # Default to part number search
        return "part_number"

    def get_provider_info(self) -> dict[str, Any]:
        """Get information about all registered providers"""
        info = {}
        for name, provider in self.providers.items():
            provider_info = provider.get_provider_info()
            provider_info["enabled"] = name in self.enabled_providers
            info[name] = provider_info

        return info
