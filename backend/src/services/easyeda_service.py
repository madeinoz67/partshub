"""
EasyEDA to KiCad conversion service for handling LCSC/JLCPCB component data.
Integrates with easyeda2kicad.py library to convert EasyEDA format files to KiCad.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

try:
    from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
    from easyeda2kicad.kicad.export_kicad_3d import Exporter3D
    from easyeda2kicad.kicad.export_kicad_footprint import ExporterFootprint
    from easyeda2kicad.kicad.export_kicad_symbol import ExporterSymbol
    EASYEDA_AVAILABLE = True
except ImportError:
    EASYEDA_AVAILABLE = False
    logging.warning("easyeda2kicad library not available. EasyEDA conversion will be disabled.")


logger = logging.getLogger(__name__)


class EasyEDAConversionError(Exception):
    """Exception raised when EasyEDA conversion fails."""
    pass


class EasyEDAService:
    """Service for converting EasyEDA components to KiCad format."""

    def __init__(self):
        self.api = EasyedaApi() if EASYEDA_AVAILABLE else None
        self.temp_dir = Path(tempfile.gettempdir()) / "partshub_easyeda"
        self.temp_dir.mkdir(exist_ok=True)

    async def convert_lcsc_component(
        self,
        lcsc_id: str,
        output_dir: str | None = None
    ) -> dict[str, Any]:
        """
        Convert an LCSC component to KiCad format.

        Args:
            lcsc_id: LCSC component ID (e.g., "C123456")
            output_dir: Directory to save converted files (optional)

        Returns:
            Dictionary containing conversion results and file paths
        """
        if not EASYEDA_AVAILABLE:
            raise EasyEDAConversionError("easyeda2kicad library not available")

        if not self.api:
            raise EasyEDAConversionError("EasyEDA API not initialized")

        # Clean LCSC ID format
        clean_lcsc_id = lcsc_id.upper()
        if not clean_lcsc_id.startswith('C'):
            clean_lcsc_id = f"C{clean_lcsc_id}"

        logger.info(f"Converting LCSC component: {clean_lcsc_id}")

        try:
            # Create temporary output directory
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = self.temp_dir / f"lcsc_{clean_lcsc_id}"
            output_path.mkdir(exist_ok=True, parents=True)

            # Get component info from EasyEDA API
            component_info = await self._get_component_info(clean_lcsc_id)
            if not component_info:
                raise EasyEDAConversionError(f"Component {clean_lcsc_id} not found in EasyEDA")

            # Convert symbol, footprint, and 3D model
            conversion_results = {}

            # Convert symbol
            symbol_result = await self._convert_symbol(component_info, output_path)
            if symbol_result:
                conversion_results['symbol'] = symbol_result

            # Convert footprint
            footprint_result = await self._convert_footprint(component_info, output_path)
            if footprint_result:
                conversion_results['footprint'] = footprint_result

            # Convert 3D model
            model_3d_result = await self._convert_3d_model(component_info, output_path)
            if model_3d_result:
                conversion_results['model_3d'] = model_3d_result

            logger.info(f"Successfully converted {clean_lcsc_id}: {list(conversion_results.keys())}")
            return {
                'lcsc_id': clean_lcsc_id,
                'component_info': component_info,
                'conversions': conversion_results,
                'output_dir': str(output_path)
            }

        except Exception as e:
            logger.error(f"Failed to convert {clean_lcsc_id}: {e}")
            raise EasyEDAConversionError(f"Conversion failed: {e}")

    async def _get_component_info(self, lcsc_id: str) -> dict[str, Any] | None:
        """Get component information from EasyEDA API."""
        try:
            # Use easyeda2kicad API to get component info
            component_info = self.api.get_component_info_by_lcsc_id(lcsc_id)
            return component_info
        except Exception as e:
            logger.error(f"Failed to get component info for {lcsc_id}: {e}")
            return None

    async def _convert_symbol(
        self,
        component_info: dict[str, Any],
        output_path: Path
    ) -> dict[str, Any] | None:
        """Convert EasyEDA symbol to KiCad format."""
        try:
            if 'symbol' not in component_info or not component_info['symbol']:
                logger.debug("No symbol data available for component")
                return None

            # Create symbol exporter
            exporter = ExporterSymbol()

            # Extract symbol data
            symbol_data = component_info['symbol']

            # Convert to KiCad format
            symbol_file = output_path / f"{component_info.get('name', 'component')}.kicad_sym"

            # Use easyeda2kicad to convert symbol
            kicad_symbol = exporter.export(symbol_data)

            # Save to file
            with open(symbol_file, 'w', encoding='utf-8') as f:
                f.write(kicad_symbol)

            return {
                'file_path': str(symbol_file),
                'library_name': component_info.get('symbol_lib', 'EasyEDA_Symbols'),
                'symbol_name': component_info.get('name', 'EasyEDA_Component')
            }

        except Exception as e:
            logger.error(f"Symbol conversion failed: {e}")
            return None

    async def _convert_footprint(
        self,
        component_info: dict[str, Any],
        output_path: Path
    ) -> dict[str, Any] | None:
        """Convert EasyEDA footprint to KiCad format."""
        try:
            if 'footprint' not in component_info or not component_info['footprint']:
                logger.debug("No footprint data available for component")
                return None

            # Create footprint exporter
            exporter = ExporterFootprint()

            # Extract footprint data
            footprint_data = component_info['footprint']

            # Convert to KiCad format
            footprint_file = output_path / f"{component_info.get('name', 'component')}.kicad_mod"

            # Use easyeda2kicad to convert footprint
            kicad_footprint = exporter.export(footprint_data)

            # Save to file
            with open(footprint_file, 'w', encoding='utf-8') as f:
                f.write(kicad_footprint)

            return {
                'file_path': str(footprint_file),
                'library_name': component_info.get('footprint_lib', 'EasyEDA_Footprints'),
                'footprint_name': component_info.get('name', 'EasyEDA_Component')
            }

        except Exception as e:
            logger.error(f"Footprint conversion failed: {e}")
            return None

    async def _convert_3d_model(
        self,
        component_info: dict[str, Any],
        output_path: Path
    ) -> dict[str, Any] | None:
        """Convert EasyEDA 3D model to KiCad format."""
        try:
            if '3d_model' not in component_info or not component_info['3d_model']:
                logger.debug("No 3D model data available for component")
                return None

            # Create 3D model exporter
            exporter = Exporter3D()

            # Extract 3D model data
            model_3d_data = component_info['3d_model']

            # Convert to KiCad format (typically STEP or WRL)
            model_file = output_path / f"{component_info.get('name', 'component')}.step"

            # Use easyeda2kicad to convert 3D model
            kicad_model = exporter.export(model_3d_data)

            # Save to file
            with open(model_file, 'wb') as f:
                f.write(kicad_model)

            return {
                'file_path': str(model_file),
                'model_name': component_info.get('name', 'EasyEDA_Component')
            }

        except Exception as e:
            logger.error(f"3D model conversion failed: {e}")
            return None

    async def get_easyeda_component_info(self, lcsc_id: str) -> dict[str, Any] | None:
        """
        Get component information from EasyEDA without conversion.

        Args:
            lcsc_id: LCSC component ID

        Returns:
            Component information dictionary or None
        """
        if not EASYEDA_AVAILABLE or not self.api:
            return None

        clean_lcsc_id = lcsc_id.upper()
        if not clean_lcsc_id.startswith('C'):
            clean_lcsc_id = f"C{clean_lcsc_id}"

        try:
            component_info = await self._get_component_info(clean_lcsc_id)
            return component_info
        except Exception as e:
            logger.error(f"Failed to get EasyEDA component info for {clean_lcsc_id}: {e}")
            return None

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary conversion files older than specified hours.

        Args:
            older_than_hours: Remove files older than this many hours
        """
        try:
            import time
            cutoff_time = time.time() - (older_than_hours * 3600)

            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")

    def get_conversion_status(self) -> dict[str, Any]:
        """Get status of EasyEDA conversion capability."""
        return {
            'easyeda_available': EASYEDA_AVAILABLE,
            'api_initialized': self.api is not None,
            'temp_dir': str(self.temp_dir),
            'temp_dir_exists': self.temp_dir.exists()
        }
