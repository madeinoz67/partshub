#!/usr/bin/env python3
"""
Quick seed script to create basic test data for PartsHub.
"""

import uuid

from src.database import Base, SessionLocal, engine
from src.models import (
    Category,
    Component,
    ComponentLocation,
    StorageLocation,
    Tag,
    User,
    component_tags,
)


def create_test_data():
    """Create basic test data for the application."""

    # Create tables
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
            description="Fixed resistors and resistor networks"
        )
        category_capacitors = Category(
            id=str(uuid.uuid4()),
            name="Capacitors",
            description="Electrolytic, ceramic, and film capacitors"
        )
        category_ics = Category(
            id=str(uuid.uuid4()),
            name="Integrated Circuits",
            description="Microcontrollers, processors, and logic ICs"
        )

        db.add_all([category_resistors, category_capacitors, category_ics])
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
        location_drawer2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer A2",
            description="IC storage drawer",
            type="drawer",
            parent_id=location_main.id,
            location_hierarchy="Main Lab/Drawer A2"
        )

        db.add_all([location_main, location_drawer1, location_drawer2])
        db.commit()

        # Create components
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
            minimum_stock=50,
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
            minimum_stock=100,
            notes="X7R ceramic capacitor"
        )

        # Microcontroller
        mcu_esp32 = Component(
            id=str(uuid.uuid4()),
            name="ESP32-S3 Microcontroller",
            part_number="ESP32-S3-WROOM-1",
            local_part_id="U001",
            manufacturer="Espressif",
            manufacturer_part_number="ESP32-S3-WROOM-1-N16R8",
            category_id=category_ics.id,
            component_type="microcontroller",
            value="ESP32-S3",
            package="Module",
            minimum_stock=5,
            notes="WiFi/Bluetooth enabled MCU with 16MB Flash, 8MB RAM"
        )

        db.add_all([resistor_1k, cap_100n, mcu_esp32])
        db.commit()

        # Create component locations with stock
        print("📍 Setting up component locations...")

        resistor_location = ComponentLocation(
            component_id=resistor_1k.id,
            storage_location_id=location_drawer1.id,
            quantity_on_hand=150,
            quantity_ordered=0,
            minimum_stock=50,
            location_notes="Main stock location"
        )

        cap_location = ComponentLocation(
            component_id=cap_100n.id,
            storage_location_id=location_drawer1.id,
            quantity_on_hand=250,
            quantity_ordered=0,
            minimum_stock=100,
            location_notes="Bulk ceramic caps"
        )

        mcu_location = ComponentLocation(
            component_id=mcu_esp32.id,
            storage_location_id=location_drawer2.id,
            quantity_on_hand=12,
            quantity_ordered=0,
            minimum_stock=5,
            location_notes="Development boards"
        )

        db.add_all([resistor_location, cap_location, mcu_location])
        db.commit()

        # Create tags
        print("🏷️ Creating tags...")

        tag_smd = Tag(id=str(uuid.uuid4()), name="SMD")
        tag_common = Tag(id=str(uuid.uuid4()), name="Common")
        tag_dev = Tag(id=str(uuid.uuid4()), name="Development")

        db.add_all([tag_smd, tag_common, tag_dev])
        db.commit()

        # Tag components using the association table
        component_tag_data = [
            {"component_id": resistor_1k.id, "tag_id": tag_smd.id},
            {"component_id": resistor_1k.id, "tag_id": tag_common.id},
            {"component_id": cap_100n.id, "tag_id": tag_smd.id},
            {"component_id": cap_100n.id, "tag_id": tag_common.id},
            {"component_id": mcu_esp32.id, "tag_id": tag_dev.id},
        ]

        for tag_data in component_tag_data:
            db.execute(component_tags.insert().values(**tag_data))
        db.commit()

        # Create a test user
        print("👤 Creating test user...")
        test_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            full_name="Administrator",
            hashed_password="$2b$12$test",  # This is just for testing
            is_active=True,
            is_admin=True
        )

        db.add(test_user)
        db.commit()

        print("✅ Test data created successfully!")
        print(f"   - {db.query(Category).count()} categories")
        print(f"   - {db.query(StorageLocation).count()} storage locations")
        print(f"   - {db.query(Component).count()} components")
        print(f"   - {db.query(Tag).count()} tags")
        print(f"   - {db.query(User).count()} users")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
