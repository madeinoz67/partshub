"""
LCSC provider adapter implementation.

Implements the ProviderAdapter interface for LCSC (Shenzhen Licheng Technology Co., Ltd.),
providing access to their component search and resource APIs.
"""

import asyncio
import logging

import httpx

from .provider_adapter import ProviderAdapter

logger = logging.getLogger(__name__)


class LCSCAdapter(ProviderAdapter):
    """
    LCSC provider adapter for searching parts and retrieving resources.

    Implements rate limiting (10 req/sec), error handling, and pagination
    for the LCSC API.
    """

    def __init__(
        self, api_key: str | None = None, base_url: str = "https://api.lcsc.com"
    ):
        """
        Initialize LCSC adapter.

        Args:
            api_key: Optional API key for authenticated requests
            base_url: Base URL for LCSC API (configurable for testing)
        """
        self.api_key = api_key
        self.base_url = base_url
        self._last_request_time = 0.0
        self._rate_limit_delay = 0.1  # 10 requests per second = 0.1s between requests

    async def _rate_limit(self):
        """Enforce rate limiting to prevent API abuse."""
        import time

        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - time_since_last_request)

        self._last_request_time = time.time()

    async def _make_request(
        self, endpoint: str, params: dict | None = None, timeout: float = 10.0
    ) -> dict:
        """
        Make HTTP request to LCSC API with error handling.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.TimeoutException: If request times out
        """
        await self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, params=params or {}, headers=headers, timeout=timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"LCSC API error: {e.response.status_code} - {e.response.text}"
                )
                raise
            except httpx.TimeoutException:
                logger.error(f"LCSC API timeout for {url}")
                raise
            except Exception as e:
                logger.error(f"LCSC API request failed: {str(e)}")
                raise

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search LCSC for parts matching the query.

        Args:
            query: Search query (part number, description, etc.)
            limit: Maximum number of results to return

        Returns:
            List of part dictionaries with standardized fields

        Example response:
            [
                {
                    "part_number": "C2040",
                    "name": "STM32F103C8T6",
                    "description": "ARM Cortex-M3 MCU, 64KB Flash",
                    "manufacturer": "STMicroelectronics",
                    "datasheet_url": "https://lcsc.com/datasheet/...",
                    "image_urls": ["https://lcsc.com/images/..."],
                    "footprint": "LQFP-48",
                    "provider_url": "https://lcsc.com/product-detail/C2040.html"
                }
            ]
        """
        try:
            # Call LCSC search API
            response = await self._make_request(
                "/v1/products/search", params={"q": query, "limit": limit}
            )

            # Parse and normalize results
            results = []
            for item in response.get("data", {}).get("products", []):
                results.append(
                    {
                        "part_number": item.get("productCode", ""),
                        "name": item.get("productModel", ""),
                        "description": item.get("productIntroEn", ""),
                        "manufacturer": item.get("brandNameEn", ""),
                        "datasheet_url": item.get("pdfUrl", ""),
                        "image_urls": [item.get("productImages", "")]
                        if item.get("productImages")
                        else [],
                        "footprint": item.get("encapStandard", ""),
                        "provider_url": f"https://www.lcsc.com/product-detail/{item.get('productCode', '')}.html",
                    }
                )

            return results[:limit]

        except Exception as e:
            logger.error(f"LCSC search failed for query '{query}': {str(e)}")
            # Return empty results on failure to allow graceful degradation
            return []

    async def get_part_details(self, part_number: str) -> dict:
        """
        Get detailed information about a specific LCSC part.

        Args:
            part_number: LCSC part number (e.g., "C2040")

        Returns:
            Dictionary with detailed part information

        Raises:
            Exception: If part not found or API error
        """
        try:
            response = await self._make_request(f"/v1/products/{part_number}")

            data = response.get("data", {})
            return {
                "part_number": data.get("productCode", ""),
                "name": data.get("productModel", ""),
                "description": data.get("productIntroEn", ""),
                "manufacturer": data.get("brandNameEn", ""),
                "datasheet_url": data.get("pdfUrl", ""),
                "image_urls": [data.get("productImages", "")]
                if data.get("productImages")
                else [],
                "footprint": data.get("encapStandard", ""),
                "provider_url": f"https://www.lcsc.com/product-detail/{part_number}.html",
                "specifications": data.get("paramVOList", {}),
                "pricing": data.get("productPriceList", []),
                "stock": data.get("stockNumber", 0),
            }

        except Exception as e:
            logger.error(f"LCSC get_part_details failed for '{part_number}': {str(e)}")
            raise

    async def get_resources(self, part_number: str) -> list[dict]:
        """
        Get downloadable resources for an LCSC part.

        Args:
            part_number: LCSC part number

        Returns:
            List of resource dictionaries

        Example response:
            [
                {
                    "type": "datasheet",
                    "url": "https://lcsc.com/datasheet/...",
                    "file_name": "STM32F103C8T6.pdf",
                    "description": "Datasheet"
                },
                {
                    "type": "image",
                    "url": "https://lcsc.com/images/...",
                    "file_name": "C2040_image.jpg"
                }
            ]
        """
        try:
            # Get part details which includes resource URLs
            details = await self.get_part_details(part_number)

            resources = []

            # Add datasheet if available
            if details.get("datasheet_url"):
                resources.append(
                    {
                        "type": "datasheet",
                        "url": details["datasheet_url"],
                        "file_name": f"{part_number}_datasheet.pdf",
                        "description": "Product datasheet",
                    }
                )

            # Add images if available
            for idx, image_url in enumerate(details.get("image_urls", [])):
                if image_url:
                    resources.append(
                        {
                            "type": "image",
                            "url": image_url,
                            "file_name": f"{part_number}_image_{idx + 1}.jpg",
                            "description": f"Product image {idx + 1}",
                        }
                    )

            return resources

        except Exception as e:
            logger.error(f"LCSC get_resources failed for '{part_number}': {str(e)}")
            return []
