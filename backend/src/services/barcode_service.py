"""
Barcode scanning service for component identification.
Supports various barcode formats and integrates with component database.
"""

import base64
import io
import logging
from typing import Any

from PIL import Image

from ..database import get_session
from ..models import Component

logger = logging.getLogger(__name__)

# Note: pyzbar installation varies by environment:
# - macOS: brew install zbar; pip install pyzbar
# - Docker: apt-get install libzbar0; pip install pyzbar
# For now, we'll provide a mock implementation with graceful fallback
try:
    from pyzbar import pyzbar

    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    # pyzbar not available - using mock barcode scanning


class BarcodeResult:
    """Barcode scan result"""

    def __init__(self, data: str, format_type: str, confidence: float = 1.0):
        self.data = data
        self.format = format_type
        self.confidence = confidence


class BarcodeService:
    """Service for barcode scanning and component identification"""

    def __init__(self):
        self.supported_formats = [
            "CODE128",
            "CODE39",
            "EAN13",
            "EAN8",
            "UPCA",
            "UPCE",
            "QRCODE",
            "DATAMATRIX",
            "PDF417",
        ]

    def scan_barcode_from_base64(self, image_data: str) -> list[BarcodeResult]:
        """
        Scan barcode from base64 encoded image.

        Args:
            image_data: Base64 encoded image string

        Returns:
            List of detected barcodes
        """
        try:
            # Remove data URL prefix if present
            if image_data.startswith("data:image"):
                image_data = image_data.split(",")[1]

            # Decode base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            return self.scan_barcode_from_image(image)

        except Exception as e:
            logger.error(f"Error scanning barcode from base64: {e}")
            return []

    def scan_barcode_from_image(self, image: Image.Image) -> list[BarcodeResult]:
        """
        Scan barcode from PIL Image.

        Args:
            image: PIL Image object

        Returns:
            List of detected barcodes
        """
        if not PYZBAR_AVAILABLE:
            return self._mock_barcode_scan(image)

        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Scan for barcodes
            barcodes = pyzbar.decode(image)

            results = []
            for barcode in barcodes:
                try:
                    # Decode barcode data
                    data = barcode.data.decode("utf-8")
                    format_type = barcode.type

                    result = BarcodeResult(
                        data=data,
                        format_type=format_type,
                        confidence=1.0,  # pyzbar doesn't provide confidence scores
                    )
                    results.append(result)

                    logger.debug(f"Detected {format_type} barcode: {data}")

                except Exception as e:
                    logger.warning(f"Error decoding barcode: {e}")

            logger.info(f"Scanned image and found {len(results)} barcodes")
            return results

        except Exception as e:
            logger.error(f"Error scanning barcode from image: {e}")
            return []

    def _mock_barcode_scan(self, image: Image.Image) -> list[BarcodeResult]:
        """
        Mock barcode scanning for development/testing.
        Returns simulated barcode results.
        """
        logger.warning(
            "Using mock barcode scanning - install pyzbar for real functionality"
        )

        # Simulate some common component barcodes based on image characteristics
        mock_results = []

        # Simple heuristic based on image size and properties
        width, height = image.size

        if width > 400 and height > 300:
            # Simulate finding a QR code with component data
            mock_results.append(
                BarcodeResult(
                    data="STM32F407VGT6|STMicroelectronics|ARM Cortex-M4 MCU",
                    format_type="QRCODE",
                    confidence=0.95,
                )
            )

        if width > 200 and height < 100:
            # Simulate finding a linear barcode with part number
            mock_results.append(
                BarcodeResult(data="LM358P", format_type="CODE128", confidence=0.90)
            )

        return mock_results

    async def identify_component_from_barcode(
        self, barcode_data: str
    ) -> dict[str, Any] | None:
        """
        Identify component from barcode data.

        Args:
            barcode_data: Decoded barcode string

        Returns:
            Component information if found, None otherwise
        """
        try:
            session = get_session()

            # Try different strategies to match barcode data to components
            component = None

            # Strategy 1: Direct part number match
            component = (
                session.query(Component).filter_by(part_number=barcode_data).first()
            )

            # Strategy 2: Parse structured barcode data (e.g., "PART|MANUFACTURER|DESCRIPTION")
            if not component and "|" in barcode_data:
                parts = barcode_data.split("|")
                if len(parts) >= 2:
                    part_number, manufacturer = parts[0], parts[1]
                    component = (
                        session.query(Component)
                        .join(Component.manufacturer)
                        .filter(
                            Component.part_number == part_number,
                            Component.manufacturer.has(name=manufacturer),
                        )
                        .first()
                    )

            # Strategy 3: Search in part number or description
            if not component:
                component = (
                    session.query(Component)
                    .filter(
                        (Component.part_number.ilike(f"%{barcode_data}%"))
                        | (Component.notes.ilike(f"%{barcode_data}%"))
                    )
                    .first()
                )

            if component:
                component_data = {
                    "id": component.id,
                    "part_number": component.part_number,
                    "manufacturer": component.manufacturer,
                    "description": component.notes,
                    "category": component.category.name if component.category else None,
                    "quantity_on_hand": component.quantity_on_hand,
                    "minimum_stock": component.minimum_stock,
                    "storage_location": component.storage_location.name
                    if component.storage_location
                    else None,
                    "specifications": component.specifications,
                    "barcode_match": barcode_data,
                }

                logger.info(
                    f"Identified component from barcode '{barcode_data}': {component.part_number}"
                )
                return component_data

            logger.info(f"No component found for barcode: {barcode_data}")
            return None

        except Exception as e:
            logger.error(
                f"Error identifying component from barcode '{barcode_data}': {e}"
            )
            return None
        finally:
            session.close()

    async def process_barcode_scan(self, image_data: str) -> dict[str, Any]:
        """
        Process barcode scan from image and identify components.

        Args:
            image_data: Base64 encoded image data

        Returns:
            Scan results with component matches
        """
        try:
            # Scan image for barcodes
            barcode_results = self.scan_barcode_from_base64(image_data)

            if not barcode_results:
                return {
                    "success": False,
                    "message": "No barcodes detected in image",
                    "barcodes": [],
                    "components": [],
                }

            # Try to identify components for each barcode
            components = []
            processed_barcodes = []

            for barcode in barcode_results:
                processed_barcode = {
                    "data": barcode.data,
                    "format": barcode.format,
                    "confidence": barcode.confidence,
                }

                # Try to identify component
                component = await self.identify_component_from_barcode(barcode.data)
                if component:
                    components.append(component)
                    processed_barcode["component_found"] = True
                else:
                    processed_barcode["component_found"] = False

                processed_barcodes.append(processed_barcode)

            result = {
                "success": True,
                "message": f"Detected {len(barcode_results)} barcode(s), found {len(components)} component(s)",
                "barcodes": processed_barcodes,
                "components": components,
            }

            logger.info(f"Barcode scan processed: {result['message']}")
            return result

        except Exception as e:
            error_msg = f"Error processing barcode scan: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "barcodes": [],
                "components": [],
            }

    def get_supported_formats(self) -> list[str]:
        """Get list of supported barcode formats"""
        return self.supported_formats.copy()

    def get_service_info(self) -> dict[str, Any]:
        """Get barcode service information"""
        import os
        import platform

        # Detect environment and provide installation guidance
        system = platform.system().lower()
        is_docker = (
            os.path.exists("/.dockerenv")
            or os.environ.get("DOCKER_CONTAINER") == "true"
        )

        installation_info = {}
        if not PYZBAR_AVAILABLE:
            if is_docker:
                installation_info = {
                    "environment": "docker",
                    "install_commands": [
                        "apt-get update",
                        "apt-get install -y libzbar0",
                        "pip install pyzbar",
                    ],
                }
            elif system == "darwin":  # macOS
                installation_info = {
                    "environment": "macos",
                    "install_commands": ["brew install zbar", "pip install pyzbar"],
                }
            elif system == "linux":
                installation_info = {
                    "environment": "linux",
                    "install_commands": [
                        "sudo apt-get install libzbar0",  # Ubuntu/Debian
                        "pip install pyzbar",
                    ],
                }
            else:
                installation_info = {
                    "environment": system,
                    "install_commands": ["pip install pyzbar"],
                }

        return {
            "pyzbar_available": PYZBAR_AVAILABLE,
            "supported_formats": self.supported_formats,
            "mock_mode": not PYZBAR_AVAILABLE,
            "environment": {
                "system": system,
                "is_docker": is_docker,
                "installation": installation_info,
            },
        }
