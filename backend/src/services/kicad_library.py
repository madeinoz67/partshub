"""
KiCad library management service.
Manages component symbols, footprints, and library metadata.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..models import Component
from ..database import get_session

logger = logging.getLogger(__name__)


class KiCadSymbol:
    """Represents a KiCad component symbol"""

    def __init__(self, name: str, reference: str, value: str, pins: List[Dict]):
        self.name = name
        self.reference = reference  # e.g., "U", "R", "C"
        self.value = value
        self.pins = pins  # List of pin definitions
        self.properties = {}
        self.graphics = []

    def add_property(self, name: str, value: str, visible: bool = False):
        """Add a property to the symbol"""
        self.properties[name] = {
            "value": value,
            "visible": visible
        }

    def to_kicad_format(self) -> str:
        """Convert symbol to KiCad format string"""
        # This is a simplified implementation
        # In production, you would generate the complete KiCad symbol format
        symbol_lines = [
            f'  (symbol "{self.name}" (in_bom yes) (on_board yes)',
            f'    (property "Reference" "{self.reference}" (id 0) (at 0 3.81 0)',
            '      (effects (font (size 1.27 1.27)))',
            '    )',
            f'    (property "Value" "{self.value}" (id 1) (at 0 -3.81 0)',
            '      (effects (font (size 1.27 1.27)))',
            '    )'
        ]

        # Add custom properties
        for prop_name, prop_data in self.properties.items():
            visibility = "" if prop_data["visible"] else " hide"
            symbol_lines.extend([
                f'    (property "{prop_name}" "{prop_data["value"]}" (id {len(symbol_lines)}) (at 0 0 0)',
                f'      (effects (font (size 1.27 1.27)){visibility})',
                '    )'
            ])

        # Add pins (simplified)
        for i, pin in enumerate(self.pins):
            pin_number = pin.get("number", str(i + 1))
            pin_name = pin.get("name", f"Pin{pin_number}")
            pin_type = pin.get("type", "passive")

            symbol_lines.extend([
                f'      (pin {pin_type} line (at -7.62 {2.54 * (i - len(self.pins) // 2)} 0) (length 2.54)',
                f'        (name "{pin_name}" (effects (font (size 1.27 1.27))))',
                f'        (number "{pin_number}" (effects (font (size 1.27 1.27))))',
                '      )'
            ])

        symbol_lines.append('  )')
        return '\n'.join(symbol_lines)


class KiCadFootprint:
    """Represents a KiCad component footprint"""

    def __init__(self, name: str, description: str, tags: List[str]):
        self.name = name
        self.description = description
        self.tags = tags
        self.pads = []
        self.graphics = []
        self.properties = {}

    def add_pad(self, number: str, pad_type: str, shape: str, position: tuple, size: tuple):
        """Add a pad to the footprint"""
        self.pads.append({
            "number": number,
            "type": pad_type,  # "smd", "thru_hole"
            "shape": shape,    # "rect", "circle", "roundrect"
            "position": position,  # (x, y)
            "size": size,      # (width, height)
        })

    def to_kicad_format(self) -> str:
        """Convert footprint to KiCad format string"""
        footprint_lines = [
            f'(footprint "{self.name}" (version 20221018) (generator "PartsHub")',
            f'  (layer "F.Cu")',
            f'  (descr "{self.description}")',
            f'  (tags "{" ".join(self.tags)}")',
            ''
        ]

        # Add reference text
        footprint_lines.extend([
            '  (fp_text reference "REF**" (at 0 -3) (layer "F.SilkS")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )'
        ])

        # Add value text
        footprint_lines.extend([
            f'  (fp_text value "{self.name}" (at 0 3) (layer "F.Fab")',
            '    (effects (font (size 1 1) (thickness 0.15)))',
            '  )'
        ])

        # Add pads
        for pad in self.pads:
            x, y = pad["position"]
            w, h = pad["size"]
            footprint_lines.append(
                f'  (pad "{pad["number"]}" {pad["type"]} {pad["shape"]} '
                f'(at {x} {y}) (size {w} {h}) '
                f'(layers "F.Cu" "F.Paste" "F.Mask"))'
            )

        footprint_lines.append(')')
        return '\n'.join(footprint_lines)


class KiCadLibraryManager:
    """Manages KiCad symbols and footprints for components"""

    def __init__(self):
        self.symbol_templates = self._load_symbol_templates()
        self.footprint_templates = self._load_footprint_templates()

    def _load_symbol_templates(self) -> Dict[str, Dict]:
        """Load symbol templates for different component types"""
        return {
            "resistor": {
                "reference": "R",
                "pins": [
                    {"number": "1", "name": "~", "type": "passive"},
                    {"number": "2", "name": "~", "type": "passive"}
                ],
                "graphics": "resistor_symbol"
            },
            "capacitor": {
                "reference": "C",
                "pins": [
                    {"number": "1", "name": "+", "type": "passive"},
                    {"number": "2", "name": "-", "type": "passive"}
                ],
                "graphics": "capacitor_symbol"
            },
            "inductor": {
                "reference": "L",
                "pins": [
                    {"number": "1", "name": "~", "type": "passive"},
                    {"number": "2", "name": "~", "type": "passive"}
                ],
                "graphics": "inductor_symbol"
            },
            "ic": {
                "reference": "U",
                "pins": [],  # Will be generated based on pin count
                "graphics": "ic_symbol"
            },
            "diode": {
                "reference": "D",
                "pins": [
                    {"number": "1", "name": "A", "type": "passive"},
                    {"number": "2", "name": "K", "type": "passive"}
                ],
                "graphics": "diode_symbol"
            },
            "transistor": {
                "reference": "Q",
                "pins": [
                    {"number": "1", "name": "C", "type": "passive"},
                    {"number": "2", "name": "B", "type": "input"},
                    {"number": "3", "name": "E", "type": "passive"}
                ],
                "graphics": "transistor_symbol"
            }
        }

    def _load_footprint_templates(self) -> Dict[str, Dict]:
        """Load footprint templates for different package types"""
        return {
            "0603": {
                "type": "smd",
                "size": (1.6, 0.8),
                "pads": [
                    {"number": "1", "position": (-0.8, 0), "size": (0.8, 0.8)},
                    {"number": "2", "position": (0.8, 0), "size": (0.8, 0.8)}
                ]
            },
            "0805": {
                "type": "smd",
                "size": (2.0, 1.25),
                "pads": [
                    {"number": "1", "position": (-1.0, 0), "size": (1.2, 1.2)},
                    {"number": "2", "position": (1.0, 0), "size": (1.2, 1.2)}
                ]
            },
            "1206": {
                "type": "smd",
                "size": (3.2, 1.6),
                "pads": [
                    {"number": "1", "position": (-1.6, 0), "size": (1.6, 1.6)},
                    {"number": "2", "position": (1.6, 0), "size": (1.6, 1.6)}
                ]
            },
            "dip8": {
                "type": "thru_hole",
                "size": (7.62, 6.35),
                "pads": [
                    {"number": str(i+1), "position": (-3.81, 3.81 - i*2.54), "size": (1.5, 1.5)}
                    for i in range(4)
                ] + [
                    {"number": str(i+5), "position": (3.81, -1.27 + i*2.54), "size": (1.5, 1.5)}
                    for i in range(4)
                ]
            }
        }

    def create_symbol_for_component(self, component: Component) -> KiCadSymbol:
        """Create a KiCad symbol for a component"""
        try:
            # Determine component type from category or specifications
            component_type = self._determine_component_type(component)

            # Get template
            template = self.symbol_templates.get(component_type, self.symbol_templates["ic"])

            # Create symbol
            symbol_name = f"{component.part_number}_{component.manufacturer if component.manufacturer else 'Unknown'}"
            symbol = KiCadSymbol(
                name=symbol_name,
                reference=template["reference"],
                value=component.part_number,
                pins=template["pins"].copy()
            )

            # Add component properties
            # Note: datasheet_url would come from attachments relationship
            # For now, we'll leave Datasheet empty or get from specifications

            if component.manufacturer:
                symbol.add_property("Manufacturer", component.manufacturer)

            if component.notes:
                symbol.add_property("Description", component.notes)

            # Add specifications as properties
            if component.specifications:
                for key, value in component.specifications.items():
                    symbol.add_property(key, str(value))

            logger.debug(f"Created symbol for component: {component.part_number}")
            return symbol

        except Exception as e:
            logger.error(f"Error creating symbol for component {component.part_number}: {e}")
            raise

    def create_footprint_for_component(self, component: Component) -> KiCadFootprint:
        """Create a KiCad footprint for a component"""
        try:
            # Determine package type
            package = self._determine_package_type(component)

            # Get template
            template = self.footprint_templates.get(package.lower(), self.footprint_templates["0805"])

            # Create footprint
            footprint_name = f"{component.part_number}_{package}"
            footprint = KiCadFootprint(
                name=footprint_name,
                description=f"{component.notes or component.part_number} - {package}",
                tags=[package, component.manufacturer if component.manufacturer else ""]
            )

            # Add pads based on template
            for pad_data in template["pads"]:
                footprint.add_pad(
                    number=pad_data["number"],
                    pad_type=template["type"],
                    shape="roundrect" if template["type"] == "smd" else "circle",
                    position=pad_data["position"],
                    size=pad_data["size"]
                )

            logger.debug(f"Created footprint for component: {component.part_number}")
            return footprint

        except Exception as e:
            logger.error(f"Error creating footprint for component {component.part_number}: {e}")
            raise

    def _determine_component_type(self, component: Component) -> str:
        """Determine component type from category and specifications"""
        if component.category:
            category_name = component.category.name.lower()
            if "resistor" in category_name:
                return "resistor"
            elif "capacitor" in category_name:
                return "capacitor"
            elif "inductor" in category_name:
                return "inductor"
            elif "diode" in category_name:
                return "diode"
            elif "transistor" in category_name:
                return "transistor"
            elif any(term in category_name for term in ["microcontroller", "ic", "processor"]):
                return "ic"

        # Check specifications
        if component.specifications:
            specs_str = str(component.specifications).lower()
            if "resistor" in specs_str or "ohm" in specs_str:
                return "resistor"
            elif "capacitor" in specs_str or "farad" in specs_str:
                return "capacitor"

        # Default to IC
        return "ic"

    def _determine_package_type(self, component: Component) -> str:
        """Determine package type from specifications"""
        if component.specifications:
            for key, value in component.specifications.items():
                key_lower = key.lower()
                value_str = str(value).lower()

                if "package" in key_lower or "footprint" in key_lower:
                    # Common package patterns
                    if any(pkg in value_str for pkg in ["0603", "0805", "1206", "1210"]):
                        return next(pkg for pkg in ["0603", "0805", "1206", "1210"] if pkg in value_str)
                    elif "dip" in value_str:
                        return "dip8"  # Default DIP package
                    elif "lqfp" in value_str:
                        return "lqfp64"  # Default LQFP package

        # Default package
        return "0805"

    async def get_component_library_data(self, component_id: str) -> Dict[str, Any]:
        """Get KiCad library data for a specific component"""
        session = get_session()
        try:
            component = session.query(Component).filter_by(id=component_id).first()

            if not component:
                return {"error": "Component not found"}

            # Create symbol and footprint
            symbol = self.create_symbol_for_component(component)
            footprint = self.create_footprint_for_component(component)

            return {
                "component_id": component.id,
                "part_number": component.part_number,
                "symbol": {
                    "name": symbol.name,
                    "reference": symbol.reference,
                    "kicad_format": symbol.to_kicad_format()
                },
                "footprint": {
                    "name": footprint.name,
                    "description": footprint.description,
                    "kicad_format": footprint.to_kicad_format()
                }
            }

        except Exception as e:
            logger.error(f"Error getting library data for component {component_id}: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def get_available_templates(self) -> Dict[str, Any]:
        """Get available symbol and footprint templates"""
        return {
            "symbols": list(self.symbol_templates.keys()),
            "footprints": list(self.footprint_templates.keys())
        }

    def sync_libraries(
        self,
        library_path: str,
        category_filters: Optional[List[str]] = None,
        include_symbols: bool = True,
        include_footprints: bool = True,
        include_3d_models: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Synchronize components to KiCad library files"""
        import os
        from sqlalchemy.orm import selectinload

        session = get_session()
        try:
            # Query components with filters
            query = session.query(Component).options(
                selectinload(Component.category),
                selectinload(Component.kicad_data)
            )

            if category_filters:
                from ..models import Category
                query = query.join(Category).filter(Category.name.in_(category_filters))

            if limit:
                query = query.limit(limit)

            components = query.all()

            # Create library directory
            os.makedirs(library_path, exist_ok=True)

            # Generate library files
            symbols_generated = 0
            footprints_generated = 0

            if include_symbols:
                symbol_lib_path = os.path.join(library_path, "PartsHub.kicad_sym")
                symbols_generated = self._generate_symbol_library_file(components, symbol_lib_path)

            if include_footprints:
                footprint_lib_path = os.path.join(library_path, "PartsHub.pretty")
                os.makedirs(footprint_lib_path, exist_ok=True)
                footprints_generated = self._generate_footprint_library_files(components, footprint_lib_path)

            logger.info(f"Synchronized {len(components)} components to {library_path}")

            return {
                "success": True,
                "components_exported": len(components),
                "symbols_created": symbols_generated,
                "footprints_created": footprints_generated,
                "library_path": library_path,
                "message": f"Successfully synchronized {len(components)} components to KiCad libraries"
            }

        except Exception as e:
            logger.error(f"Error synchronizing libraries: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Library synchronization failed: {e}"
            }
        finally:
            session.close()

    def _generate_symbol_library_file(self, components: List[Component], output_path: str) -> int:
        """Generate KiCad symbol library file"""
        symbol_content = [
            '(kicad_symbol_lib (version 20231120) (generator "PartsHub")',
            ""
        ]

        symbols_created = 0
        for component in components:
            try:
                symbol = self.create_symbol_for_component(component)
                symbol_content.append(symbol.to_kicad_format())
                symbol_content.append("")
                symbols_created += 1
            except Exception as e:
                logger.warning(f"Failed to generate symbol for {component.part_number}: {e}")
                continue

        symbol_content.append(")")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(symbol_content))

        return symbols_created

    def _generate_footprint_library_files(self, components: List[Component], output_dir: str) -> int:
        """Generate KiCad footprint library files"""
        footprints_created = 0

        for component in components:
            try:
                footprint = self.create_footprint_for_component(component)
                footprint_filename = f"{footprint.name}.kicad_mod"
                footprint_path = os.path.join(output_dir, footprint_filename)

                with open(footprint_path, 'w', encoding='utf-8') as f:
                    f.write(footprint.to_kicad_format())

                footprints_created += 1
            except Exception as e:
                logger.warning(f"Failed to generate footprint for {component.part_number}: {e}")
                continue

        return footprints_created