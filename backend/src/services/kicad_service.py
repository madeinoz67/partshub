"""
KiCad library export service.
Generates KiCad-compatible library files from component database.
"""

import os
import tempfile
import zipfile
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..models import Component, Category
from ..database import get_session

logger = logging.getLogger(__name__)


class KiCadExportService:
    """Service for exporting components to KiCad library format"""

    def __init__(self):
        self.library_version = "20231120"  # KiCad file format version
        self.creator = "PartsHub Electronic Parts Management System"

    def export_component_library(
        self,
        components: List[Component],
        library_name: str = "PartsHub_Library"
    ) -> bytes:
        """
        Export components to KiCad library format.

        Args:
            components: List of components to export
            library_name: Name of the KiCad library

        Returns:
            ZIP file bytes containing KiCad library files
        """
        try:
            # Create temporary directory for library files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Generate library files
                symbol_lib_path = os.path.join(temp_dir, f"{library_name}.kicad_sym")
                footprint_lib_dir = os.path.join(temp_dir, f"{library_name}.pretty")

                os.makedirs(footprint_lib_dir, exist_ok=True)

                # Generate symbol library
                self._generate_symbol_library(components, symbol_lib_path, library_name)

                # Generate footprint library
                self._generate_footprint_library(components, footprint_lib_dir, library_name)

                # Create ZIP archive
                zip_buffer = self._create_library_archive(temp_dir, library_name)

                logger.info(f"Generated KiCad library '{library_name}' with {len(components)} components")
                return zip_buffer

        except Exception as e:
            logger.error(f"Error exporting KiCad library: {e}")
            raise

    def _generate_symbol_library(self, components: List[Component], output_path: str, library_name: str):
        """Generate KiCad symbol library file"""

        symbol_content = [
            f'(kicad_symbol_lib (version {self.library_version}) (generator "{self.creator}")',
            ""
        ]

        for component in components:
            symbol = self._generate_component_symbol(component)
            symbol_content.extend(symbol)
            symbol_content.append("")

        symbol_content.append(")")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(symbol_content))

        logger.debug(f"Generated symbol library: {output_path}")

    def _generate_component_symbol(self, component: Component) -> List[str]:
        """Generate KiCad symbol for a single component"""

        # Sanitize symbol name for KiCad
        symbol_name = self._sanitize_name(f"{component.part_number}_{component.manufacturer if component.manufacturer else 'Unknown'}")

        # Basic symbol template - in production, this would be more sophisticated
        symbol = [
            f'  (symbol "{symbol_name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
            f'    (property "Reference" "U" (at 0 3.81 0)',
            '      (effects (font (size 1.27 1.27)))',
            '    )',
            f'    (property "Value" "{component.part_number}" (at 0 -3.81 0)',
            '      (effects (font (size 1.27 1.27)))',
            '    )',
            f'    (property "Footprint" "" (at 0 0 0)',
            '      (effects (font (size 1.27 1.27)) hide)',
            '    )',
            f'    (property "Datasheet" "{component.datasheet_url or ""}" (at 0 0 0)',
            '      (effects (font (size 1.27 1.27)) hide)',
            '    )',
        ]

        # Add custom properties from specifications
        if component.specifications:
            for key, value in component.specifications.items():
                safe_key = self._sanitize_name(key)
                symbol.append(f'    (property "{safe_key}" "{value}" (at 0 0 0)')
                symbol.append('      (effects (font (size 1.27 1.27)) hide)')
                symbol.append('    )')

        # Add basic symbol graphics (rectangle with pins)
        symbol.extend([
            '    (symbol "{}_0_1"'.format(symbol_name),
            '      (rectangle (start -7.62 2.54) (end 7.62 -2.54)',
            '        (stroke (width 0.254) (type default))',
            '        (fill (type background))',
            '      )',
            '    )',
            '    (symbol "{}_1_1"'.format(symbol_name),
            '      (pin passive line (at -10.16 0 0) (length 2.54)',
            '        (name "1" (effects (font (size 1.27 1.27))))',
            '        (number "1" (effects (font (size 1.27 1.27))))',
            '      )',
            '      (pin passive line (at 10.16 0 180) (length 2.54)',
            '        (name "2" (effects (font (size 1.27 1.27))))',
            '        (number "2" (effects (font (size 1.27 1.27))))',
            '      )',
            '    )',
            '  )'
        ])

        return symbol

    def _generate_footprint_library(self, components: List[Component], output_dir: str, library_name: str):
        """Generate KiCad footprint library"""

        for component in components:
            footprint_file = self._generate_component_footprint(component, output_dir)
            if footprint_file:
                logger.debug(f"Generated footprint: {footprint_file}")

    def _generate_component_footprint(self, component: Component, output_dir: str) -> Optional[str]:
        """Generate KiCad footprint for a single component"""

        # Extract package information from specifications
        package = "Unknown"
        if component.specifications and 'package' in component.specifications:
            package = component.specifications['package']
        elif component.specifications and 'Package' in component.specifications:
            package = component.specifications['Package']

        # Sanitize footprint name
        footprint_name = self._sanitize_name(f"{component.part_number}_{package}")
        footprint_path = os.path.join(output_dir, f"{footprint_name}.kicad_mod")

        # Basic footprint template
        footprint_content = [
            f'(footprint "{footprint_name}" (version {self.library_version}) (generator "{self.creator}")',
            f'  (layer "F.Cu")',
            f'  (descr "{component.notes or component.part_number}")',
            f'  (tags "{package} {component.manufacturer if component.manufacturer else ""}")',
            ''
        ]

        # Add basic footprint elements based on package type
        if package.upper() in ['0603', '0805', '1206', '1210']:
            # SMD resistor/capacitor footprint
            footprint_content.extend(self._generate_smd_footprint(package))
        elif 'LQFP' in package.upper():
            # LQFP package footprint
            footprint_content.extend(self._generate_lqfp_footprint(package))
        else:
            # Generic footprint
            footprint_content.extend(self._generate_generic_footprint())

        footprint_content.append(')')

        with open(footprint_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(footprint_content))

        return footprint_path

    def _generate_smd_footprint(self, package: str) -> List[str]:
        """Generate SMD footprint elements"""
        # Package dimensions (simplified)
        dimensions = {
            '0603': (1.6, 0.8, 0.8, 0.8),
            '0805': (2.0, 1.25, 1.2, 1.2),
            '1206': (3.2, 1.6, 1.6, 1.6),
            '1210': (3.2, 2.5, 1.6, 2.5)
        }

        length, width, pad_length, pad_width = dimensions.get(package, (2.0, 1.25, 1.2, 1.2))

        return [
            f'  (fp_text reference "REF**" (at 0 -{width/2 + 1}) (layer "F.SilkS")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            f'  (fp_text value "{package}" (at 0 {width/2 + 1}) (layer "F.Fab")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            f'  (fp_line (start -{length/2} -{width/2}) (end {length/2} -{width/2})',
            '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
            f'  (fp_line (start -{length/2} {width/2}) (end {length/2} {width/2})',
            '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
            f'  (pad "1" smd roundrect (at -{length/2} 0) (size {pad_length} {pad_width})',
            '    (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))',
            f'  (pad "2" smd roundrect (at {length/2} 0) (size {pad_length} {pad_width})',
            '    (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))',
        ]

    def _generate_lqfp_footprint(self, package: str) -> List[str]:
        """Generate LQFP footprint elements (simplified)"""
        return [
            '  (fp_text reference "U" (at 0 -6) (layer "F.SilkS")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            f'  (fp_text value "{package}" (at 0 6) (layer "F.Fab")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            '  (fp_rect (start -5 -5) (end 5 5)',
            '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
            '  (pad "1" smd rect (at -5.7 -3.75) (size 1.5 0.3)',
            '    (layers "F.Cu" "F.Paste" "F.Mask"))',
            '  (pad "2" smd rect (at -5.7 -3.25) (size 1.5 0.3)',
            '    (layers "F.Cu" "F.Paste" "F.Mask"))',
            '  # Additional pads would be generated based on pin count...',
        ]

    def _generate_generic_footprint(self) -> List[str]:
        """Generate generic footprint elements"""
        return [
            '  (fp_text reference "U" (at 0 -2) (layer "F.SilkS")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            '  (fp_text value "Generic" (at 0 2) (layer "F.Fab")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )',
            '  (fp_rect (start -2.5 -1) (end 2.5 1)',
            '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
            '  (pad "1" thru_hole circle (at -1.27 0) (size 1.5 1.5) (drill 0.8)',
            '    (layers "*.Cu" "*.Mask"))',
            '  (pad "2" thru_hole circle (at 1.27 0) (size 1.5 1.5) (drill 0.8)',
            '    (layers "*.Cu" "*.Mask"))',
        ]

    def _create_library_archive(self, temp_dir: str, library_name: str) -> bytes:
        """Create ZIP archive containing all library files"""

        zip_buffer = tempfile.NamedTemporaryFile()

        with zipfile.ZipFile(zip_buffer.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)

        # Read the ZIP file content
        with open(zip_buffer.name, 'rb') as f:
            zip_data = f.read()

        return zip_data

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for KiCad compatibility"""
        # Replace problematic characters
        sanitized = name.replace(' ', '_').replace('-', '_').replace('.', '_')
        # Remove any other special characters
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        return sanitized

    async def export_components_by_category(self, category_id: str) -> bytes:
        """Export all components in a specific category"""
        session = get_session()
        try:
            components = session.query(Component).filter_by(category_id=category_id).all()
            category = session.query(Category).filter_by(id=category_id).first()

            library_name = f"PartsHub_{category.name if category else 'Category'}"
            return self.export_component_library(components, library_name)
        finally:
            session.close()

    async def export_components_by_manufacturer(self, manufacturer_name: str) -> bytes:
        """Export all components from a specific manufacturer"""
        session = get_session()
        try:
            components = session.query(Component).filter_by(manufacturer=manufacturer_name).all()
            library_name = f"PartsHub_{manufacturer_name.replace(' ', '_') if manufacturer_name else 'Manufacturer'}"
            return self.export_component_library(components, library_name)
        finally:
            session.close()

    async def export_all_components(self) -> bytes:
        """Export all components in the database"""
        session = get_session()
        try:
            components = session.query(Component).all()
            return self.export_component_library(components, "PartsHub_Complete")
        finally:
            session.close()

    def get_export_info(self) -> Dict[str, Any]:
        """Get information about the KiCad export service"""
        return {
            "library_version": self.library_version,
            "creator": self.creator,
            "supported_formats": ["symbols", "footprints"],
            "package_types": ["SMD", "Through-hole", "LQFP", "Generic"]
        }

    def format_component_for_kicad(self, component: Component, include_full_specs: bool = False) -> Dict[str, Any]:
        """Format component data for KiCad API responses"""

        # Determine reference designator based on component type
        reference_map = {
            'resistor': 'R',
            'capacitor': 'C',
            'inductor': 'L',
            'ic': 'U',
            'microcontroller': 'U',
            'diode': 'D',
            'transistor': 'Q',
            'connector': 'J',
            'crystal': 'Y'
        }

        reference = reference_map.get(component.component_type.lower() if component.component_type else '', 'U')

        # Build footprint reference
        footprint = ""
        if component.kicad_data and component.kicad_data.has_footprint:
            footprint = component.kicad_data.get_footprint_reference()
        elif component.package:
            # Generate standard footprint name
            footprint = f"Resistors:{component.component_type}_{component.package}"

        # Prepare fields from specifications
        fields = {}
        if component.specifications:
            for key, value in component.specifications.items():
                # Convert specification keys to KiCad-friendly field names
                field_name = key.replace('_', ' ').title()
                fields[field_name] = str(value)

        # Add standard fields
        if component.manufacturer:
            fields["Manufacturer"] = component.manufacturer
        if component.part_number:
            fields["MPN"] = component.part_number

        # Get datasheet URL from attachments
        datasheet_url = None
        for attachment in component.attachments:
            if 'datasheet' in attachment.filename.lower() or attachment.attachment_type == 'datasheet':
                datasheet_url = f"http://localhost:8000/api/v1/components/{component.id}/attachments/{attachment.id}/download"
                break

        return {
            "component_id": component.id,
            "reference": reference,
            "value": component.value or component.name,
            "footprint": footprint,
            "symbol_library": component.kicad_data.symbol_library if component.kicad_data else None,
            "symbol_name": component.kicad_data.symbol_name if component.kicad_data else None,
            "footprint_library": component.kicad_data.footprint_library if component.kicad_data else None,
            "footprint_name": component.kicad_data.footprint_name if component.kicad_data else None,
            "model_3d_path": component.kicad_data.model_3d_path if component.kicad_data else None,
            "fields": fields,
            "specifications": component.specifications or {},
            "manufacturer": component.manufacturer,
            "part_number": component.part_number,
            "datasheet_url": datasheet_url
        }

    def get_symbol_data(self, component: Component) -> Dict[str, Any]:
        """Get KiCad symbol data for a component"""

        if not component.kicad_data or not component.kicad_data.has_symbol:
            raise ValueError("Component has no KiCad symbol data")

        return {
            "symbol_library": component.kicad_data.symbol_library,
            "symbol_name": component.kicad_data.symbol_name,
            "symbol_reference": component.kicad_data.get_symbol_reference(),
            "pin_count": None,  # Could be extracted from specifications
            "symbol_data": component.kicad_data.kicad_fields_json
        }

    def get_footprint_data(self, component: Component) -> Dict[str, Any]:
        """Get KiCad footprint data for a component"""

        if not component.kicad_data or not component.kicad_data.has_footprint:
            raise ValueError("Component has no KiCad footprint data")

        return {
            "footprint_library": component.kicad_data.footprint_library,
            "footprint_name": component.kicad_data.footprint_name,
            "footprint_reference": component.kicad_data.get_footprint_reference(),
            "pad_count": None,  # Could be extracted from specifications
            "footprint_data": component.kicad_data.kicad_fields_json
        }

    def get_standard_field_mappings(self) -> Dict[str, str]:
        """Get standard KiCad field mappings used by PartsHub"""
        return {
            "Reference": "Component reference designator",
            "Value": "Component value or part name",
            "Footprint": "PCB footprint reference",
            "Datasheet": "Component datasheet URL",
            "Manufacturer": "Component manufacturer",
            "MPN": "Manufacturer part number",
            "Tolerance": "Component tolerance specification",
            "Voltage": "Voltage rating",
            "Power": "Power rating",
            "Package": "Physical package type",
            "TempRange": "Operating temperature range"
        }