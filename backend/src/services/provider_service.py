"""
Provider service for managing multiple component data providers.
Handles provider registration, searches across providers, and result aggregation.
"""

import asyncio
from typing import List, Dict, Optional, Any
from collections import defaultdict
import logging

from ..providers.base_provider import ComponentDataProvider, ComponentSearchResult
from ..providers.lcsc_provider import LCSCProvider

logger = logging.getLogger(__name__)


class ProviderService:
    """Service for managing component data providers"""

    def __init__(self):
        self.providers: Dict[str, ComponentDataProvider] = {}
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

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names"""
        return list(self.enabled_providers)

    async def search_all_providers(
        self,
        query: str,
        limit_per_provider: int = 10,
        providers: Optional[List[str]] = None
    ) -> Dict[str, List[ComponentSearchResult]]:
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
                task = self._search_provider_safe(provider_name, provider, query, limit_per_provider)
                tasks.append(task)

        if not tasks:
            return {}

        # Execute searches in parallel
        logger.info(f"Searching {len(tasks)} providers for '{query}'")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        provider_results = {}
        for i, result in enumerate(results):
            provider_name = target_providers[i] if i < len(target_providers) else f"provider_{i}"
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
        limit: int
    ) -> List[ComponentSearchResult]:
        """Safely search a provider with error handling"""
        try:
            results = await provider.search_components(query, limit)
            logger.debug(f"Provider {provider_name} returned {len(results)} results for '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error searching provider {provider_name}: {e}")
            return []

    def aggregate_search_results(
        self,
        provider_results: Dict[str, List[ComponentSearchResult]]
    ) -> List[ComponentSearchResult]:
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

        logger.info(f"Aggregated {len(all_results)} unique components from {len(provider_results)} providers")
        return all_results

    async def search_components(
        self,
        query: str,
        limit: int = 50,
        providers: Optional[List[str]] = None
    ) -> List[ComponentSearchResult]:
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
        provider_results = await self.search_all_providers(query, limit_per_provider, providers)

        # Aggregate results
        results = self.aggregate_search_results(provider_results)

        # Apply final limit
        return results[:limit]

    async def get_component_details(
        self,
        part_number: str,
        manufacturer: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Optional[ComponentSearchResult]:
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
                result = await provider_obj.get_component_details(part_number, manufacturer)
                if result:
                    result.provider_id = f"{provider_name}_{result.provider_id}"
                    return result
            except Exception as e:
                logger.error(f"Error getting details from {provider_name}: {e}")

        return None

    async def verify_providers(self) -> Dict[str, bool]:
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
                logger.info(f"Provider {provider_name} verification: {'OK' if result else 'FAILED'}")

        return status

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about all registered providers"""
        info = {}
        for name, provider in self.providers.items():
            provider_info = provider.get_provider_info()
            provider_info["enabled"] = name in self.enabled_providers
            info[name] = provider_info

        return info