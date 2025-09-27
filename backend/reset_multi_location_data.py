#!/usr/bin/env python3
"""
Reset and recreate clean multi-location inventory data without duplicates.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from src.database import get_session
from src.models import Component, ComponentLocation, StorageLocation, Category
import uuid

def reset_multi_location_data():
    """Reset and recreate clean multi-location inventory data."""
    db = get_session()

    try:
        # First, clean up any existing ComponentLocation records for components 1-3
        components = db.query(Component).limit(3).all()
        component_ids = [comp.id for comp in components]

        print(f"Cleaning up existing ComponentLocation records for {len(components)} components...")
        deleted_count = db.query(ComponentLocation).filter(ComponentLocation.component_id.in_(component_ids)).delete()
        print(f"Deleted {deleted_count} existing ComponentLocation records")

        # Get existing storage locations
        existing_locations = db.query(StorageLocation).all()
        print(f"Found {len(existing_locations)} existing storage locations")

        # Create new storage locations if they don't exist
        location_names = ["Shelf B2", "Drawer C3", "Bin A5"]
        new_locations = []

        for name in location_names:
            existing = db.query(StorageLocation).filter(StorageLocation.name == name).first()
            if not existing:
                if name == "Shelf B2":
                    location = StorageLocation(
                        id=str(uuid.uuid4()),
                        name=name,
                        type="shelf",
                        location_hierarchy=name,
                        description="Secondary storage shelf B2"
                    )
                elif name == "Drawer C3":
                    location = StorageLocation(
                        id=str(uuid.uuid4()),
                        name=name,
                        type="drawer",
                        location_hierarchy=f"Cabinet C > {name}",
                        description="Small parts drawer C3"
                    )
                elif name == "Bin A5":
                    location = StorageLocation(
                        id=str(uuid.uuid4()),
                        name=name,
                        type="bin",
                        location_hierarchy=f"Rack A > {name}",
                        description="Overflow bin A5"
                    )

                db.add(location)
                new_locations.append(location)
                print(f"Created new location: {name}")
            else:
                new_locations.append(existing)
                print(f"Using existing location: {name}")

        db.commit()

        # Note: quantity_on_hand, quantity_ordered, and minimum_stock are computed properties
        # that automatically sum values from ComponentLocation records

        # Create ONE ComponentLocation record per component-location pair

        # Component 1 (10kΩ Resistor): Spread across 3 locations
        if len(components) >= 1:
            comp1 = components[0]
            print(f"Adding multi-location data for: {comp1.name}")

            # Primary location gets most stock
            primary_location = existing_locations[0] if existing_locations else None
            if primary_location:
                primary_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp1.id,
                    storage_location_id=primary_location.id,
                    quantity_on_hand=60,
                    quantity_ordered=0,
                    minimum_stock=10,
                    location_notes="Primary stock location"
                )
                db.add(primary_loc)

            # Secondary location (Shelf B2)
            shelf_b2 = next((loc for loc in new_locations if loc.name == "Shelf B2"), None)
            if shelf_b2:
                shelf_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp1.id,
                    storage_location_id=shelf_b2.id,
                    quantity_on_hand=25,
                    quantity_ordered=10,
                    minimum_stock=5,
                    location_notes="Overflow storage",
                    unit_cost_at_location=0.018
                )
                db.add(shelf_loc)

            # Tertiary location (Drawer C3)
            drawer_c3 = next((loc for loc in new_locations if loc.name == "Drawer C3"), None)
            if drawer_c3:
                drawer_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp1.id,
                    storage_location_id=drawer_c3.id,
                    quantity_on_hand=15,
                    quantity_ordered=0,
                    minimum_stock=0,
                    location_notes="Easy access for prototyping",
                    unit_cost_at_location=0.022
                )
                db.add(drawer_loc)

        # Component 2 (100µF Capacitor): In 2 locations
        if len(components) >= 2:
            comp2 = components[1]
            print(f"Adding multi-location data for: {comp2.name}")

            # Primary location
            primary_location = existing_locations[0] if existing_locations else None
            if primary_location:
                primary_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp2.id,
                    storage_location_id=primary_location.id,
                    quantity_on_hand=42,
                    quantity_ordered=0,
                    minimum_stock=5,
                    location_notes="Main stock"
                )
                db.add(primary_loc)

            # Secondary location (Bin A5)
            bin_a5 = next((loc for loc in new_locations if loc.name == "Bin A5"), None)
            if bin_a5:
                bin_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp2.id,
                    storage_location_id=bin_a5.id,
                    quantity_on_hand=8,
                    quantity_ordered=20,
                    minimum_stock=5,
                    location_notes="Backup stock",
                    unit_cost_at_location=0.55
                )
                db.add(bin_loc)

        # Component 3 (1kΩ Resistor): Create low stock scenario with one depleted location
        if len(components) >= 3:
            comp3 = components[2]
            print(f"Adding multi-location data for: {comp3.name}")

            # Primary location with most stock
            primary_location = existing_locations[0] if existing_locations else None
            if primary_location:
                primary_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp3.id,
                    storage_location_id=primary_location.id,
                    quantity_on_hand=198,
                    quantity_ordered=0,
                    minimum_stock=15,
                    location_notes="Main inventory"
                )
                db.add(primary_loc)

            # Low stock location (Shelf B2)
            shelf_b2 = next((loc for loc in new_locations if loc.name == "Shelf B2"), None)
            if shelf_b2:
                low_stock_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp3.id,
                    storage_location_id=shelf_b2.id,
                    quantity_on_hand=2,
                    quantity_ordered=50,
                    minimum_stock=10,
                    location_notes="Running low - reorder placed",
                    unit_cost_at_location=1.25
                )
                db.add(low_stock_loc)

            # DEPLETED location (Drawer C3) - THIS IS THE KEY TEST CASE
            drawer_c3 = next((loc for loc in new_locations if loc.name == "Drawer C3"), None)
            if drawer_c3:
                depleted_loc = ComponentLocation(
                    id=str(uuid.uuid4()),
                    component_id=comp3.id,
                    storage_location_id=drawer_c3.id,
                    quantity_on_hand=0,  # ZERO STOCK - should still be visible
                    quantity_ordered=0,
                    minimum_stock=5,
                    location_notes="Depleted - awaiting restock"
                )
                db.add(depleted_loc)

        # Component totals will be automatically calculated from ComponentLocation records:
        # Component 1: 100 total (60 + 25 + 15), min_stock: 15 (10 + 5 + 0)
        # Component 2: 50 total (42 + 8), min_stock: 10 (5 + 5)
        # Component 3: 200 total (198 + 2 + 0), min_stock: 30 (15 + 10 + 5)

        db.commit()
        print("✅ Successfully reset and recreated clean multi-location inventory data!")

        # Display summary
        print("\n📊 Clean multi-location inventory summary:")
        for i, comp in enumerate(components):
            locations = db.query(ComponentLocation).filter(ComponentLocation.component_id == comp.id).all()
            total_qty = sum(loc.quantity_on_hand for loc in locations)
            total_min = sum(loc.minimum_stock for loc in locations)
            print(f"  {comp.name}:")
            print(f"    - {len(locations)} locations")
            print(f"    - {total_qty} total quantity (component.quantity_on_hand: {comp.quantity_on_hand})")
            print(f"    - {total_min} total minimum stock (component.minimum_stock: {comp.minimum_stock})")
            for loc in locations:
                location_name = db.query(StorageLocation).filter(StorageLocation.id == loc.storage_location_id).first().name
                status = "⚠️ DEPLETED" if loc.quantity_on_hand == 0 else "✅"
                print(f"      {status} {location_name}: {loc.quantity_on_hand} on hand (notes: {loc.location_notes})")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_multi_location_data()