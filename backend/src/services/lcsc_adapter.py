"""
LCSC provider adapter implementation.

Implements the ProviderAdapter interface for LCSC (Shenzhen Licheng Technology Co., Ltd.),
using web scraping to search their public website.
"""

import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup

from .provider_adapter import ProviderAdapter

logger = logging.getLogger(__name__)

# Try to import Playwright for JavaScript rendering
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.info(
        "Playwright not available. LCSC search will use basic HTML scraping (may return limited results). "
        "Install with: uv pip install -e '.[scraping]' && playwright install chromium"
    )


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
        Search LCSC by scraping their public website.
        Uses Playwright for JavaScript rendering if available, otherwise falls back to basic HTML scraping.

        Args:
            query: Search query (part number, description, etc.)
            limit: Maximum number of results to return

        Returns:
            List of part dictionaries with standardized fields
        """
        # Try Playwright first if available
        if PLAYWRIGHT_AVAILABLE:
            try:
                return await self._search_with_playwright(query, limit)
            except Exception as e:
                logger.warning(
                    f"Playwright search failed, falling back to basic scraping: {e}"
                )

        # Fallback to basic HTML scraping
        return await self._search_basic(query, limit)

    async def _search_with_playwright(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search LCSC using Playwright for JavaScript rendering.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        await self._rate_limit()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()

                # Navigate to search page
                search_url = f"https://www.lcsc.com/search?q={query}"
                await page.goto(search_url, wait_until="networkidle", timeout=15000)

                # LCSC loads results via Vue.js/API - wait for the data table to populate
                # Wait for table rows to appear (they don't have data-track in practice)
                try:
                    await page.wait_for_selector("tbody tr", timeout=10000)
                    logger.info("Product table loaded successfully")
                except Exception as e:
                    logger.warning(f"Timeout waiting for product table: {e}")
                    # Try anyway - sometimes content loads but selector times out
                    pass

                # Get page content after JS rendering
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                results = []
                # LCSC uses table tbody tr for product rows
                # Get more rows than needed since many are headers/non-products
                all_rows = soup.select("tbody tr")
                logger.debug(f"Found {len(all_rows)} total table rows")

                for row in all_rows:
                    # Stop if we have enough results
                    if len(results) >= limit:
                        break

                    try:
                        # Extract LCSC part number from link (e.g., C8734)
                        part_link = row.select_one('a[href*="/product-detail/C"]')
                        if not part_link:
                            continue

                        href = part_link.get("href", "")
                        part_number_match = re.search(r"C\d+", href)
                        if not part_number_match:
                            continue

                        lcsc_part_number = part_number_match.group(0)

                        # Extract MPN (manufacturer part number)
                        # MPN is in a link with highlighted text (has <span> with background-color)
                        mpn_elem = row.select_one("a.font-Bold-600.v2-a")
                        if mpn_elem:
                            # Get text, removing HTML highlighting
                            mpn_text = mpn_elem.get_text(strip=True)
                            mpn = mpn_text if mpn_text != lcsc_part_number else ""
                        else:
                            mpn = ""

                        # Extract manufacturer
                        mfr_link = row.select_one('a[href*="/brand-detail/"]')
                        manufacturer = mfr_link.get_text(strip=True) if mfr_link else ""

                        # Note: Description and package data from search results is unreliable
                        # due to dynamic table structure. Get from detail page instead.
                        description = ""
                        footprint = ""

                        # Extract image
                        img_elem = row.select_one("div.v-image__image")
                        image_url = ""
                        if img_elem:
                            style = img_elem.get("style", "")
                            img_match = re.search(
                                r'url\(["\']?([^"\']+)["\']?\)', style
                            )
                            if img_match:
                                image_url = img_match.group(1)

                        results.append(
                            {
                                "part_number": lcsc_part_number,
                                "name": mpn or lcsc_part_number,
                                "description": description,
                                "manufacturer": manufacturer,
                                "datasheet_url": "",  # Datasheet URL only available from detail page
                                "image_urls": [image_url] if image_url else [],
                                "footprint": footprint,
                                "provider_url": f"https://www.lcsc.com/product-detail/{lcsc_part_number}.html",
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse product row: {e}")
                        continue

                logger.info(
                    f"Playwright search for '{query}' returned {len(results)} results"
                )
                return results[:limit]

            finally:
                await browser.close()

    async def _extract_specifications_with_playwright(
        self, part_number: str, product_url: str
    ) -> dict:
        """
        Extract specifications using Playwright to render JavaScript content.

        Args:
            part_number: LCSC part number
            product_url: Full product URL

        Returns:
            Dictionary of specifications
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()

                # Navigate to product page
                await page.goto(product_url, wait_until="networkidle", timeout=15000)

                # Wait for specifications table to load
                try:
                    await page.wait_for_selector(
                        "div.common-table-v7 tbody tr", timeout=10000
                    )
                except Exception:
                    logger.warning(f"Timeout waiting for specs table on {part_number}")

                # Get rendered HTML
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                specifications = {}

                # Find the "Products Specifications" heading
                spec_heading = None
                headings = soup.select(
                    "h2, h3, .table-title, .section-title, div.font-Bold-600"
                )
                for heading in headings:
                    heading_text = heading.get_text(strip=True)
                    if "Product" in heading_text and "Specification" in heading_text:
                        spec_heading = heading
                        break

                if spec_heading:
                    # Get all tables after the heading
                    spec_tables = spec_heading.find_all_next(
                        "div", class_="common-table-v7", limit=10
                    )

                    for table in spec_tables:
                        spec_rows = table.select("tbody tr")

                        for row in spec_rows:
                            cells = row.select("td")
                            if len(cells) >= 2:
                                spec_name = cells[0].get_text(strip=True)
                                spec_value = cells[1].get_text(strip=True)

                                # Skip pricing rows (1+, 10+, etc.)
                                if "+" in spec_name and "$" in spec_value:
                                    continue

                                # Skip general info and non-technical fields
                                if spec_name in [
                                    "Category",
                                    "Manufacturer",
                                    "Package",
                                    "ECCN",
                                    "CNHTS",
                                    "USHTS",
                                    "TARIC",
                                    "CAHTS",
                                    "BRHTS",
                                    "INHTS",
                                    "MXHTS",
                                    "Datasheet",
                                    "Minimum",
                                    "Multiple",
                                    "Standard Packaging",
                                    "Sales Unit",
                                    "EDA Models",
                                    "RoHS",
                                ]:
                                    continue

                                # Store valid specifications
                                if spec_name and spec_value:
                                    specifications[spec_name] = spec_value

                return specifications

            finally:
                await browser.close()

    async def _search_basic(self, query: str, limit: int = 10) -> list[dict]:
        """
        Basic HTML scraping fallback (without JavaScript rendering).
        Note: LCSC uses JavaScript to load search results, so this may return no results.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results (likely empty due to JS requirement)
        """
        try:
            await self._rate_limit()

            search_url = "https://www.lcsc.com/search"
            params = {"q": query}

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    search_url, params=params, headers=headers, timeout=10.0
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                results = []

                product_items = soup.select(
                    ".product-item, .search-product-item, [data-product-code]"
                )[:limit]

                for item in product_items:
                    try:
                        part_number = self._extract_part_number_from_item(item)
                        if not part_number:
                            continue

                        name_elem = item.select_one(
                            ".product-model, .product-name, h3, h4"
                        )
                        name = (
                            name_elem.get_text(strip=True) if name_elem else part_number
                        )

                        desc_elem = item.select_one(
                            ".product-intro, .product-description, p"
                        )
                        description = (
                            desc_elem.get_text(strip=True) if desc_elem else ""
                        )

                        mfr_elem = item.select_one(".product-brand, .manufacturer")
                        manufacturer = mfr_elem.get_text(strip=True) if mfr_elem else ""

                        pkg_elem = item.select_one(".product-package, .package")
                        footprint = pkg_elem.get_text(strip=True) if pkg_elem else ""

                        img_elem = item.select_one("img")
                        image_url = img_elem.get("src", "") if img_elem else ""
                        if image_url and not image_url.startswith("http"):
                            image_url = f"https://www.lcsc.com{image_url}"

                        results.append(
                            {
                                "part_number": part_number,
                                "name": name,
                                "description": description,
                                "manufacturer": manufacturer,
                                "datasheet_url": "",  # Datasheet URL only available from detail page
                                "image_urls": [image_url] if image_url else [],
                                "footprint": footprint,
                                "provider_url": f"https://www.lcsc.com/product-detail/{part_number}.html",
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse product item: {e}")
                        continue

                if not results:
                    logger.warning(
                        f"Basic HTML scraping found no results for '{query}' - Install Playwright for better results: "
                        "uv pip install -e '.[scraping]' && playwright install chromium"
                    )

                return results[:limit]

        except Exception as e:
            logger.error(f"LCSC basic search failed for query '{query}': {str(e)}")
            return []

    def _extract_part_number_from_item(self, item) -> str:
        """Extract LCSC part number from product item in various ways."""
        # Try data attribute first
        part_number = item.get("data-product-code")
        if part_number:
            return part_number

        # Try nested element with data attribute
        nested = item.select_one("[data-product-code]")
        if nested:
            part_number = nested.get("data-product-code")
            if part_number:
                return part_number

        # Fallback: extract from text
        return self._extract_part_number(item)

    def _extract_part_number(self, item) -> str:
        """Try to extract LCSC part number from various possible locations."""
        # Look for C followed by digits in text
        text = item.get_text()
        match = re.search(r"C\d+", text)
        return match.group(0) if match else ""

    async def get_part_details(self, part_number: str) -> dict:
        """
        Get detailed information about a specific LCSC part by scraping the product page.

        Args:
            part_number: LCSC part number (e.g., "C529355")

        Returns:
            Dictionary with detailed part information

        Raises:
            Exception: If part not found or scraping error
        """
        logger.warning(f"[LCSC] Getting part details for {part_number}")
        try:
            await self._rate_limit()

            # LCSC product detail URL
            product_url = f"https://www.lcsc.com/product-detail/{part_number}.html"
            logger.warning(f"[LCSC] Fetching URL: {product_url}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(product_url, headers=headers, timeout=10.0)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Check if this is a 404 page
                title = soup.select_one("title")
                if title and "Page Not Found" in title.get_text():
                    logger.warning(f"Part {part_number} not found on LCSC")
                    raise Exception(f"Part {part_number} not found")

                # Extract data using actual LCSC HTML structure
                result = {
                    "part_number": part_number,
                    "name": "",
                    "description": "",
                    "manufacturer": "",
                    "datasheet_url": "",
                    "image_urls": [],
                    "footprint": "",
                    "provider_url": product_url,
                    "specifications": {},
                    "pricing": [],
                    "stock": 0,
                    "category": "",
                }

                # Extract product title (e.g., "ST STM32G431CBT6")
                title_elem = soup.select_one("h1.font-Bold-600.fz-20")
                if title_elem:
                    result["name"] = title_elem.get_text(strip=True)

                # Extract table information
                info_table = soup.select("table.tableInfoWrap tr")
                for row in info_table:
                    cells = row.select("td")
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)

                        if label == "Manufacturer":
                            result["manufacturer"] = value
                        elif label == "Mfr. Part #":
                            result["name"] = value
                        elif label == "Package":
                            result["footprint"] = value
                        elif label == "Description":
                            result["description"] = value

                # Extract datasheet URL
                datasheet_link = soup.select_one('a[href*="/datasheet/"]')
                if datasheet_link:
                    href = datasheet_link.get("href", "")
                    if href:
                        result["datasheet_url"] = (
                            f"https://www.lcsc.com{href}"
                            if href.startswith("/")
                            else href
                        )

                # Extract images from background-image style
                image_divs = soup.select("div.v-image__image")
                for img_div in image_divs:
                    style = img_div.get("style", "")
                    if "background-image: url(" in style:
                        # Extract URL from CSS url() function
                        match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                        if match:
                            img_url = match.group(1)
                            if img_url and img_url not in result["image_urls"]:
                                result["image_urls"].append(img_url)

                # Extract stock quantity
                stock_elem = soup.select_one("span.fz-20.font-Bold-600")
                if stock_elem:
                    stock_text = stock_elem.get_text(strip=True)
                    # Remove "In-Stock:" prefix and commas
                    stock_text = (
                        stock_text.replace("In-Stock:", "").replace(",", "").strip()
                    )
                    try:
                        result["stock"] = int(stock_text)
                    except (ValueError, AttributeError):
                        pass

                # Extract pricing from price table
                price_table = soup.select("table.priceTable tbody tr")
                for row in price_table:
                    cells = row.select("td")
                    if len(cells) >= 2:
                        qty_text = cells[0].get_text(strip=True)
                        price_text = cells[1].get_text(strip=True)

                        # Parse quantity (e.g., "1+", "10+", "1,000+")
                        qty_match = re.match(r"([\d,]+)\+", qty_text)
                        if qty_match:
                            quantity = int(qty_match.group(1).replace(",", ""))

                            # Parse price (e.g., "$ 3.0856")
                            price_match = re.search(r"\$?\s*([\d.]+)", price_text)
                            if price_match:
                                price = float(price_match.group(1))
                                result["pricing"].append(
                                    {
                                        "quantity": quantity,
                                        "price": price,
                                        "currency": "USD",
                                    }
                                )

                # Extract specifications using Playwright (JavaScript-rendered content)
                if PLAYWRIGHT_AVAILABLE:
                    try:
                        specs = await self._extract_specifications_with_playwright(
                            part_number, product_url
                        )
                        result["specifications"] = specs
                        logger.warning(
                            f"Extracted {len(specs)} specifications via Playwright for {part_number}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract specifications with Playwright: {e}"
                        )
                else:
                    logger.warning(
                        f"Playwright not available - skipping specifications for {part_number}"
                    )

                # Extract category from breadcrumbs
                breadcrumbs = soup.select("ul.v2-breadcrumbs a")
                if breadcrumbs:
                    # Last breadcrumb before product is usually the category
                    category_parts = [
                        bc.get_text(strip=True)
                        for bc in breadcrumbs
                        if bc.get_text(strip=True) not in ["Home", "Products"]
                    ]
                    if category_parts:
                        result["category"] = " / ".join(category_parts)

                logger.info(f"Successfully scraped details for {part_number}")
                return result

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
