"""
BOM (Bill of Materials) generation service with provider SKU integration.
Generates BOMs from project components and integrates with provider data.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any

from ..database import get_session
from ..models import Component, ComponentProviderData, Project, ProjectComponent
from .provider_service import ProviderService

logger = logging.getLogger(__name__)


class BOMExportFormat:
    """BOM export format enumeration"""
    CSV = "csv"
    JSON = "json"
    KICAD = "kicad"
    EXCEL = "excel"


class BOMItem:
    """Individual BOM item with provider integration"""
    def __init__(self, component: Component, quantity: int, provider_data: ComponentProviderData | None = None):
        self.component = component
        self.quantity = quantity
        self.provider_data = provider_data

    def to_dict(self) -> dict[str, Any]:
        """Convert BOM item to dictionary"""
        item = {
            "component_id": self.component.id,
            "part_number": self.component.part_number,
            "manufacturer": self.component.manufacturer,
            "description": self.component.notes,
            "category": self.component.category.name if self.component.category else None,
            "quantity": self.quantity,
            "unit_cost": None,
            "total_cost": None,
            "provider_sku": None,
            "provider_name": None,
            "provider_url": None,
            "availability": None,
            "specifications": self.component.specifications or {}
        }

        # Add provider data if available
        if self.provider_data:
            item.update({
                "provider_sku": self.provider_data.provider_part_id,
                "provider_name": self.provider_data.provider_id.split('_')[0] if '_' in self.provider_data.provider_id else self.provider_data.provider_id,
                "provider_url": self.provider_data.provider_url,
                "availability": self.provider_data.availability
            })

            # Extract pricing for unit cost
            if self.provider_data.pricing and isinstance(self.provider_data.pricing, dict):
                price_breaks = self.provider_data.pricing.get('price_breaks', [])
                if price_breaks:
                    # Find the best price for the required quantity
                    best_price = None
                    for price_break in price_breaks:
                        if isinstance(price_break, dict) and price_break.get('quantity', 0) <= self.quantity:
                            best_price = price_break.get('price')

                    if best_price:
                        item["unit_cost"] = best_price
                        item["total_cost"] = best_price * self.quantity

        return item


class BOMService:
    """Service for generating Bills of Materials with provider integration"""

    def __init__(self):
        self.provider_service = ProviderService()

    async def generate_project_bom(
        self,
        project_id: str,
        include_provider_data: bool = True,
        refresh_provider_data: bool = False
    ) -> list[BOMItem]:
        """
        Generate BOM for a specific project.

        Args:
            project_id: Project ID
            include_provider_data: Whether to include provider data
            refresh_provider_data: Whether to refresh provider data from APIs

        Returns:
            List of BOM items
        """
        session = get_session()
        try:
            # Get project and its components
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            project_components = session.query(ProjectComponent).filter(
                ProjectComponent.project_id == project_id
            ).all()

            bom_items = []

            for pc in project_components:
                component = pc.component
                provider_data = None

                if include_provider_data:
                    # Get existing provider data
                    provider_data = session.query(ComponentProviderData).filter(
                        ComponentProviderData.component_id == component.id
                    ).first()

                    # Refresh provider data if requested
                    if refresh_provider_data or not provider_data:
                        await self._refresh_component_provider_data(component.id)
                        # Re-query after refresh
                        provider_data = session.query(ComponentProviderData).filter(
                            ComponentProviderData.component_id == component.id
                        ).first()

                bom_item = BOMItem(component, pc.quantity, provider_data)
                bom_items.append(bom_item)

            logger.info(f"Generated BOM for project {project_id} with {len(bom_items)} items")
            return bom_items

        finally:
            session.close()

    async def generate_component_list_bom(
        self,
        component_quantities: list[tuple[str, int]],
        include_provider_data: bool = True
    ) -> list[BOMItem]:
        """
        Generate BOM from a list of component IDs and quantities.

        Args:
            component_quantities: List of (component_id, quantity) tuples
            include_provider_data: Whether to include provider data

        Returns:
            List of BOM items
        """
        session = get_session()
        try:
            bom_items = []

            for component_id, quantity in component_quantities:
                component = session.query(Component).filter(Component.id == component_id).first()
                if not component:
                    logger.warning(f"Component not found: {component_id}")
                    continue

                provider_data = None
                if include_provider_data:
                    provider_data = session.query(ComponentProviderData).filter(
                        ComponentProviderData.component_id == component_id
                    ).first()

                bom_item = BOMItem(component, quantity, provider_data)
                bom_items.append(bom_item)

            logger.info(f"Generated BOM from component list with {len(bom_items)} items")
            return bom_items

        finally:
            session.close()

    async def _refresh_component_provider_data(self, component_id: str):
        """Refresh provider data for a component"""
        session = get_session()
        try:
            component = session.query(Component).filter(Component.id == component_id).first()
            if not component:
                return

            # Search for component in providers
            search_results = await self.provider_service.search_components(
                query=component.part_number,
                limit=1
            )

            if search_results:
                result = search_results[0]

                # Update or create provider data
                provider_data = session.query(ComponentProviderData).filter(
                    ComponentProviderData.component_id == component_id
                ).first()

                if not provider_data:
                    provider_data = ComponentProviderData(component_id=component_id)
                    session.add(provider_data)

                provider_data.provider_id = result.provider_id
                provider_data.provider_part_id = result.provider_part_id
                provider_data.provider_url = result.provider_url
                provider_data.datasheet_url = result.datasheet_url
                provider_data.image_url = result.image_url
                provider_data.specifications = result.specifications
                provider_data.availability = result.availability
                provider_data.pricing = {
                    "price_breaks": result.price_breaks,
                    "currency": "USD"
                }
                provider_data.last_updated = datetime.utcnow()

                session.commit()
                logger.debug(f"Refreshed provider data for component {component_id}")

        except Exception as e:
            logger.error(f"Error refreshing provider data for component {component_id}: {e}")
            session.rollback()
        finally:
            session.close()

    def export_bom_csv(self, bom_items: list[BOMItem]) -> str:
        """Export BOM to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [
            "Part Number", "Manufacturer", "Description", "Category",
            "Quantity", "Unit Cost", "Total Cost", "Provider SKU",
            "Provider", "Availability", "Provider URL"
        ]
        writer.writerow(headers)

        # Write data rows
        for item in bom_items:
            data = item.to_dict()
            row = [
                data["part_number"],
                data["manufacturer"],
                data["description"],
                data["category"],
                data["quantity"],
                data["unit_cost"] or "",
                data["total_cost"] or "",
                data["provider_sku"] or "",
                data["provider_name"] or "",
                data["availability"] or "",
                data["provider_url"] or ""
            ]
            writer.writerow(row)

        return output.getvalue()

    def export_bom_json(self, bom_items: list[BOMItem]) -> str:
        """Export BOM to JSON format"""
        bom_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_items": len(bom_items),
            "items": [item.to_dict() for item in bom_items]
        }

        # Calculate totals
        total_cost = sum(
            item.to_dict().get("total_cost", 0) or 0
            for item in bom_items
        )
        bom_data["total_cost"] = total_cost

        return json.dumps(bom_data, indent=2)

    def export_bom_kicad(self, bom_items: list[BOMItem]) -> str:
        """Export BOM to KiCad format"""
        output = io.StringIO()

        # KiCad BOM header
        output.write("# Bill of Materials\n")
        output.write(f"# Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("#\n")

        # Tab-separated format for KiCad
        headers = [
            "Reference", "Value", "Footprint", "Datasheet",
            "Manufacturer", "MPN", "Supplier", "SPN", "Quantity"
        ]
        output.write("\t".join(headers) + "\n")

        for i, item in enumerate(bom_items):
            data = item.to_dict()
            row = [
                f"U{i+1}",  # Reference designator
                data["part_number"],  # Value
                "",  # Footprint (would need to be determined from specs)
                data.get("provider_url", ""),  # Datasheet
                data["manufacturer"],
                data["part_number"],  # MPN
                data.get("provider_name", ""),  # Supplier
                data.get("provider_sku", ""),  # SPN
                str(data["quantity"])
            ]
            output.write("\t".join(row) + "\n")

        return output.getvalue()

    def calculate_bom_cost(self, bom_items: list[BOMItem]) -> dict[str, Any]:
        """Calculate total BOM cost and statistics"""
        total_cost = 0
        total_items = len(bom_items)
        items_with_pricing = 0
        items_with_availability = 0

        for item in bom_items:
            data = item.to_dict()

            if data.get("total_cost"):
                total_cost += data["total_cost"]
                items_with_pricing += 1

            if data.get("availability") is not None:
                items_with_availability += 1

        return {
            "total_cost": total_cost,
            "total_items": total_items,
            "items_with_pricing": items_with_pricing,
            "items_with_availability": items_with_availability,
            "pricing_coverage": items_with_pricing / total_items if total_items > 0 else 0,
            "availability_coverage": items_with_availability / total_items if total_items > 0 else 0
        }

    async def export_bom(
        self,
        bom_items: list[BOMItem],
        export_format: str = BOMExportFormat.CSV
    ) -> tuple[str, str]:
        """
        Export BOM in specified format.

        Args:
            bom_items: List of BOM items
            export_format: Export format (csv, json, kicad)

        Returns:
            Tuple of (content, mime_type)
        """
        if export_format == BOMExportFormat.CSV:
            content = self.export_bom_csv(bom_items)
            mime_type = "text/csv"
        elif export_format == BOMExportFormat.JSON:
            content = self.export_bom_json(bom_items)
            mime_type = "application/json"
        elif export_format == BOMExportFormat.KICAD:
            content = self.export_bom_kicad(bom_items)
            mime_type = "text/plain"
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        return content, mime_type
