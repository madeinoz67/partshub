"""
LCSC (JLCPCB) component data provider implementation.
Integrates with LCSC's public API for component search and data.
"""

import logging
import re
from typing import Any

from .base_provider import ComponentDataProvider, ComponentSearchResult

logger = logging.getLogger(__name__)

# Import EasyEDA service for KiCad conversion
try:
    from ..services.easyeda_service import EasyEDAService

    EASYEDA_SERVICE_AVAILABLE = True
except ImportError:
    EASYEDA_SERVICE_AVAILABLE = False
    logger.warning("EasyEDA service not available for LCSC provider")


class LCSCProvider(ComponentDataProvider):
    """LCSC component data provider"""

    def __init__(self, api_key: str | None = None):
        super().__init__("LCSC", api_key)
        self.base_url = "https://wmsc.lcsc.com/wmsc"
        self.rate_limit_delay = 0.5  # LCSC allows higher rates

        # Initialize EasyEDA service for KiCad data
        self.easyeda_service = EasyEDAService() if EASYEDA_SERVICE_AVAILABLE else None

    async def search_components(
        self, query: str, limit: int = 10
    ) -> list[ComponentSearchResult]:
        """
        Search LCSC for components matching the query.

        Uses the LCSCAdapter for actual web scraping implementation.
        """
        try:
            # Import adapter here to avoid circular dependency
            from ..services.lcsc_adapter import LCSCAdapter

            adapter = LCSCAdapter()
            results = await adapter.search(query, limit)

            # Convert adapter results to ComponentSearchResult format
            component_results = []
            for result in results:
                component_results.append(
                    ComponentSearchResult(
                        part_number=result.get("part_number", ""),
                        manufacturer=result.get("manufacturer", ""),
                        description=result.get("description", ""),
                        category=result.get("category", ""),
                        datasheet_url=result.get("datasheet_url"),
                        image_url=result.get("image_urls", [None])[0],
                        specifications=result.get("specifications", {}),
                        price_breaks=result.get("pricing", []),
                        availability=result.get("stock", 0),
                        provider_id=result.get("part_number", ""),
                        provider_url=result.get("provider_url", ""),
                        provider_part_id=result.get("part_number", ""),
                    )
                )

            logger.info(
                f"LCSC search for '{query}' returned {len(component_results)} results"
            )
            return component_results

        except Exception as e:
            logger.error(f"LCSC search failed for '{query}': {e}")
            return []

    async def get_component_details(
        self, part_number: str, manufacturer: str | None = None
    ) -> ComponentSearchResult | None:
        """Get detailed component information from LCSC"""
        try:
            # Import adapter here to avoid circular dependency
            from ..services.lcsc_adapter import LCSCAdapter

            adapter = LCSCAdapter()
            result = await adapter.get_part_details(part_number)

            if not result:
                return None

            return ComponentSearchResult(
                part_number=result.get("part_number", ""),
                manufacturer=result.get("manufacturer", ""),
                description=result.get("description", ""),
                category=result.get("category", ""),
                datasheet_url=result.get("datasheet_url"),
                image_url=result.get("image_urls", [None])[0],
                specifications=result.get("specifications", {}),
                price_breaks=result.get("pricing", []),
                availability=result.get("stock", 0),
                provider_id=result.get("part_number", ""),
                provider_url=result.get("provider_url", ""),
                provider_part_id=result.get("part_number", ""),
            )

        except Exception as e:
            logger.error(f"LCSC details failed for '{part_number}': {e}")
            return None

    async def search_by_provider_sku(
        self, provider_sku: str
    ) -> ComponentSearchResult | None:
        """
        Search for a component by LCSC-specific SKU/part ID.
        LCSC SKUs typically follow patterns like C123456, C12345, etc.
        """
        try:
            # Detect LCSC SKU format
            if not self._is_lcsc_sku_format(provider_sku):
                # Not an LCSC SKU format, fall back to regular search
                return await super().search_by_provider_sku(provider_sku)

            # Use get_component_details which will scrape the actual product page
            result = await self.get_component_details(provider_sku)

            if result:
                logger.info(f"Found component for LCSC SKU: {provider_sku}")
            else:
                logger.info(f"No component found for LCSC SKU: {provider_sku}")

            return result

        except Exception as e:
            logger.error(f"LCSC SKU search failed for '{provider_sku}': {e}")
            return None

    def _is_lcsc_sku_format(self, sku: str) -> bool:
        """
        Check if the given string matches LCSC SKU format.
        LCSC SKUs typically start with 'C' followed by 5-7 digits.
        """
        if not sku:
            return False

        # LCSC SKU patterns: C12345, C123456, C1234567
        pattern = r"^C\d{5,7}$"
        return bool(re.match(pattern, sku.upper()))

    async def get_easyeda_data(self, lcsc_id: str) -> dict[str, Any] | None:
        """
        Get EasyEDA component data for KiCad conversion.

        Args:
            lcsc_id: LCSC component ID (e.g., "C123456")

        Returns:
            EasyEDA component data or None if not available
        """
        if not self.easyeda_service:
            logger.warning("EasyEDA service not available for component data")
            return None

        try:
            # Clean LCSC ID format
            clean_lcsc_id = lcsc_id.upper()
            if not clean_lcsc_id.startswith("C"):
                clean_lcsc_id = f"C{clean_lcsc_id}"

            logger.info(f"Fetching EasyEDA data for LCSC component: {clean_lcsc_id}")

            # Get EasyEDA component information
            easyeda_info = await self.easyeda_service.get_easyeda_component_info(
                clean_lcsc_id
            )

            if easyeda_info:
                logger.info(f"Successfully retrieved EasyEDA data for {clean_lcsc_id}")
                return easyeda_info
            else:
                logger.info(f"No EasyEDA data found for {clean_lcsc_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to get EasyEDA data for {lcsc_id}: {e}")
            return None

    async def convert_to_kicad(
        self, lcsc_id: str, output_dir: str | None = None
    ) -> dict[str, Any] | None:
        """
        Convert LCSC component to KiCad format using EasyEDA data.

        Args:
            lcsc_id: LCSC component ID (e.g., "C123456")
            output_dir: Directory to save converted files (optional)

        Returns:
            Conversion results or None if failed
        """
        if not self.easyeda_service:
            logger.warning("EasyEDA service not available for KiCad conversion")
            return None

        try:
            # Clean LCSC ID format
            clean_lcsc_id = lcsc_id.upper()
            if not clean_lcsc_id.startswith("C"):
                clean_lcsc_id = f"C{clean_lcsc_id}"

            logger.info(f"Converting LCSC component to KiCad: {clean_lcsc_id}")

            # Convert using EasyEDA service
            conversion_result = await self.easyeda_service.convert_lcsc_component(
                clean_lcsc_id, output_dir
            )

            if conversion_result:
                logger.info(f"Successfully converted {clean_lcsc_id} to KiCad format")
                return conversion_result
            else:
                logger.info(f"No conversion possible for {clean_lcsc_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to convert {lcsc_id} to KiCad: {e}")
            return None

    def get_provider_info(self) -> dict[str, Any]:
        """
        Get provider information and capabilities including EasyEDA support.

        Returns:
            Dictionary with provider details
        """
        base_info = super().get_provider_info()

        # Add EasyEDA capability information
        base_info.update(
            {
                "supports_easyeda": EASYEDA_SERVICE_AVAILABLE
                and self.easyeda_service is not None,
                "supports_kicad_conversion": EASYEDA_SERVICE_AVAILABLE
                and self.easyeda_service is not None,
                "easyeda_service_status": self.easyeda_service.get_conversion_status()
                if self.easyeda_service
                else None,
            }
        )

        return base_info

    async def get_component_with_kicad_data(
        self, lcsc_id: str, include_conversion: bool = False
    ) -> dict[str, Any] | None:
        """
        Get component details with EasyEDA/KiCad data.

        Args:
            lcsc_id: LCSC component ID
            include_conversion: Whether to include converted KiCad files

        Returns:
            Component data with KiCad information
        """
        try:
            # Get basic component details
            component = await self.search_by_provider_sku(lcsc_id)
            if not component:
                logger.info(f"Component {lcsc_id} not found")
                return None

            result = {
                "component": component,
                "easyeda_data": None,
                "kicad_conversion": None,
            }

            # Get EasyEDA data
            easyeda_data = await self.get_easyeda_data(lcsc_id)
            if easyeda_data:
                result["easyeda_data"] = easyeda_data

                # Optionally include KiCad conversion
                if include_conversion:
                    conversion_result = await self.convert_to_kicad(lcsc_id)
                    if conversion_result:
                        result["kicad_conversion"] = conversion_result

            return result

        except Exception as e:
            logger.error(f"Failed to get component with KiCad data for {lcsc_id}: {e}")
            return None
