#!/usr/bin/env python3
"""
Add dummy data to test multi-location inventory functionality.
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

import uuid

from src.database import get_session
from src.models import Component, ComponentLocation, StorageLocation


def add_multi_location_data():
    """Add test data for multi-location inventory."""
    db = get_session()

    try:
        # Get existing components
        components = db.query(Component).all()
        print(f"Found {len(components)} existing components")

        # Get existing storage locations
        existing_locations = db.query(StorageLocation).all()
        print(f"Found {len(existing_locations)} existing storage locations")

        # Create additional storage locations
        new_locations = [
            StorageLocation(
                id=str(uuid.uuid4()),
                name="Shelf B2",
                type="shelf",
                location_hierarchy="Shelf B2",
                description="Secondary storage shelf B2"
            ),
            StorageLocation(
                id=str(uuid.uuid4()),
                name="Drawer C3",
                type="drawer",
                location_hierarchy="Cabinet C > Drawer C3",
                description="Small parts drawer C3"
            ),
            StorageLocation(
                id=str(uuid.uuid4()),
                name="Bin A5",
                type="bin",
                location_hierarchy="Rack A > Bin A5",
                description="Overflow bin A5"
            )
        ]

        for location in new_locations:
            db.add(location)

        db.commit()
        print(f"Added {len(new_locations)} new storage locations")

        # Add multi-location entries for existing components
        if len(components) >= 1:
            # First component: spread across 3 locations
            comp1 = components[0]
            print(f"Adding multi-location data for: {comp1.name}")

            # Add to Shelf B2
            loc1 = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=comp1.id,
                storage_location_id=new_locations[0].id,
                quantity_on_hand=25,
                quantity_ordered=10,
                minimum_stock=5,
                location_notes="Overflow storage",
                unit_cost_at_location=0.018
            )
            db.add(loc1)

            # Add to Drawer C3
            loc2 = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=comp1.id,
                storage_location_id=new_locations[1].id,
                quantity_on_hand=15,
                quantity_ordered=0,
                minimum_stock=10,
                location_notes="Easy access for prototyping",
                unit_cost_at_location=0.022
            )
            db.add(loc2)

        if len(components) >= 2:
            # Second component: in 2 locations
            comp2 = components[1]
            print(f"Adding multi-location data for: {comp2.name}")

            # Add to Bin A5
            loc3 = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=comp2.id,
                storage_location_id=new_locations[2].id,
                quantity_on_hand=8,
                quantity_ordered=20,
                minimum_stock=5,
                location_notes="Backup stock",
                unit_cost_at_location=0.55
            )
            db.add(loc3)

        if len(components) >= 3:
            # Third component: create a low stock scenario
            comp3 = components[2]
            print(f"Adding multi-location data for: {comp3.name}")

            # Add to Shelf B2 with low stock
            loc4 = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=comp3.id,
                storage_location_id=new_locations[0].id,
                quantity_on_hand=2,  # Low stock
                quantity_ordered=50,
                minimum_stock=10,
                location_notes="Running low - reorder placed",
                unit_cost_at_location=1.25
            )
            db.add(loc4)

            # Add empty location (out of stock)
            loc5 = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=comp3.id,
                storage_location_id=new_locations[1].id,
                quantity_on_hand=0,  # Out of stock
                quantity_ordered=0,
                minimum_stock=5,
                location_notes="Depleted - awaiting restock"
            )
            db.add(loc5)

        db.commit()
        print("✅ Successfully added multi-location inventory data!")

        # Display summary
        print("\n📊 Multi-location inventory summary:")
        for i, comp in enumerate(components[:3]):
            locations = db.query(ComponentLocation).filter(ComponentLocation.component_id == comp.id).all()
            total_qty = sum(loc.quantity_on_hand for loc in locations)
            total_min = sum(loc.minimum_stock for loc in locations)
            print(f"  {comp.name}:")
            print(f"    - {len(locations)} locations")
            print(f"    - {total_qty} total quantity")
            print(f"    - {total_min} total minimum stock")
            for loc in locations:
                location_name = db.query(StorageLocation).filter(StorageLocation.id == loc.storage_location_id).first().name
                print(f"      • {location_name}: {loc.quantity_on_hand} on hand")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_multi_location_data()
