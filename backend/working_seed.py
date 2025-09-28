#!/usr/bin/env python3
"""
Working seed script for PartsHub.
Creates tables first, then adds test data.
"""

import uuid

from src.database import Base, SessionLocal, engine
from src.models import *


def create_working_test_data():
    """Create working test data for the application."""

    # Create all tables
    print("🏗️ Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create database session
    db = SessionLocal()

    try:
        print("🌱 Creating test data...")

        # Create categories
        print("📁 Creating categories...")
        category_resistors = Category(
            id=str(uuid.uuid4()),
            name="Resistors",
            description="Fixed resistors and resistor networks",
            sort_order=1
        )
        category_capacitors = Category(
            id=str(uuid.uuid4()),
            name="Capacitors",
            description="Electrolytic, ceramic, and film capacitors",
            sort_order=2
        )

        db.add_all([category_resistors, category_capacitors])
        db.commit()

        # Create storage locations
        print("📦 Creating storage locations...")
        location_main = StorageLocation(
            id=str(uuid.uuid4()),
            name="Main Lab",
            description="Primary component storage",
            type="room",
            location_hierarchy="Main Lab"
        )
        location_drawer1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer A1",
            description="Small components drawer",
            type="drawer",
            parent_id=location_main.id,
            location_hierarchy="Main Lab/Drawer A1"
        )

        db.add_all([location_main, location_drawer1])
        db.commit()

        # Create components (without minimum_stock as it's a calculated property)
        print("🔧 Creating components...")

        # Resistor
        resistor_1k = Component(
            id=str(uuid.uuid4()),
            name="1kΩ Resistor",
            part_number="R1K0-0603",
            local_part_id="R001",
            manufacturer="Yageo",
            manufacturer_part_number="RC0603FR-071KL",
            category_id=category_resistors.id,
            component_type="resistor",
            value="1kΩ",
            package="0603",
            notes="Standard 1% tolerance resistor"
        )

        # Capacitor
        cap_100n = Component(
            id=str(uuid.uuid4()),
            name="100nF Ceramic Capacitor",
            part_number="C100N-0603",
            local_part_id="C001",
            manufacturer="Murata",
            manufacturer_part_number="GCM188R71H104KA57D",
            category_id=category_capacitors.id,
            component_type="capacitor",
            value="100nF",
            package="0603",
            notes="X7R ceramic capacitor"
        )

        db.add_all([resistor_1k, cap_100n])
        db.commit()

        # Create component locations with stock
        print("📍 Setting up component locations...")

        resistor_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=resistor_1k.id,
            storage_location_id=location_drawer1.id,
            quantity_on_hand=150,
            quantity_ordered=0,
            minimum_stock=50,
            location_notes="Main stock location"
        )

        cap_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=cap_100n.id,
            storage_location_id=location_drawer1.id,
            quantity_on_hand=250,
            quantity_ordered=0,
            minimum_stock=100,
            location_notes="Bulk ceramic caps"
        )

        db.add_all([resistor_location, cap_location])
        db.commit()

        # Create tags
        print("🏷️ Creating tags...")

        tag_smd = Tag(
            id=str(uuid.uuid4()),
            name="SMD",
            description="Surface Mount Device",
            is_system_tag=False
        )
        tag_common = Tag(
            id=str(uuid.uuid4()),
            name="Common",
            description="Commonly used component",
            is_system_tag=False
        )

        db.add_all([tag_smd, tag_common])
        db.commit()

        # Tag components
        resistor_1k.tags.append(tag_smd)
        resistor_1k.tags.append(tag_common)
        cap_100n.tags.append(tag_smd)
        cap_100n.tags.append(tag_common)

        db.commit()

        print("✅ Test data created successfully!")
        print(f"   - {db.query(Category).count()} categories")
        print(f"   - {db.query(StorageLocation).count()} storage locations")
        print(f"   - {db.query(Component).count()} components")
        print(f"   - {db.query(ComponentLocation).count()} component locations")
        print(f"   - {db.query(Tag).count()} tags")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_working_test_data()
