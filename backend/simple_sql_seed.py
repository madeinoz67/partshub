#!/usr/bin/env python3
"""
Simple SQL-based seed script for PartsHub.
"""

import sqlite3
import uuid
from datetime import datetime

def create_test_data():
    """Create basic test data using direct SQL."""

    # Connect to the database
    conn = sqlite3.connect('data/partshub.db')
    cursor = conn.cursor()

    try:
        print("🌱 Creating test data...")

        # Generate UUIDs
        category_resistor_id = str(uuid.uuid4())
        category_capacitor_id = str(uuid.uuid4())
        location_main_id = str(uuid.uuid4())
        location_drawer1_id = str(uuid.uuid4())
        component1_id = str(uuid.uuid4())
        component2_id = str(uuid.uuid4())
        tag1_id = str(uuid.uuid4())
        tag2_id = str(uuid.uuid4())

        # Current timestamp
        now = datetime.now().isoformat()

        # Insert categories
        print("📁 Creating categories...")
        cursor.execute("""
            INSERT INTO categories (id, name, description, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category_resistor_id, "Resistors", "Fixed resistors", 1, now, now))

        cursor.execute("""
            INSERT INTO categories (id, name, description, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category_capacitor_id, "Capacitors", "Capacitors", 2, now, now))

        # Insert storage locations
        print("📦 Creating storage locations...")
        cursor.execute("""
            INSERT INTO storage_locations (id, name, description, type, location_hierarchy, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (location_main_id, "Main Lab", "Primary storage", "room", "Main Lab", now, now))

        cursor.execute("""
            INSERT INTO storage_locations (id, name, description, type, parent_id, location_hierarchy, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (location_drawer1_id, "Drawer A1", "Components drawer", "drawer", location_main_id, "Main Lab/Drawer A1", now, now))

        # Insert components
        print("🔧 Creating components...")
        cursor.execute("""
            INSERT INTO components (id, name, part_number, local_part_id, manufacturer, category_id,
                                  component_type, value, package, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (component1_id, "1kΩ Resistor", "R1K0-0603", "R001", "Yageo", category_resistor_id,
              "resistor", "1kΩ", "0603", "Standard 1% tolerance", now, now))

        cursor.execute("""
            INSERT INTO components (id, name, part_number, local_part_id, manufacturer, category_id,
                                  component_type, value, package, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (component2_id, "100nF Capacitor", "C100N-0603", "C001", "Murata", category_capacitor_id,
              "capacitor", "100nF", "0603", "X7R ceramic capacitor", now, now))

        # Insert component locations (stock information)
        print("📍 Creating component locations...")
        location1_id = str(uuid.uuid4())
        location2_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO component_locations (id, component_id, storage_location_id, quantity_on_hand,
                                           quantity_ordered, minimum_stock, location_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (location1_id, component1_id, location_drawer1_id, 150, 0, 50, "Main stock", now, now))

        cursor.execute("""
            INSERT INTO component_locations (id, component_id, storage_location_id, quantity_on_hand,
                                           quantity_ordered, minimum_stock, location_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (location2_id, component2_id, location_drawer1_id, 250, 0, 100, "Bulk caps", now, now))

        # Insert tags
        print("🏷️ Creating tags...")
        cursor.execute("""
            INSERT INTO tags (id, name, description, is_system_tag, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tag1_id, "SMD", "Surface Mount Device", 0, now, now))

        cursor.execute("""
            INSERT INTO tags (id, name, description, is_system_tag, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tag2_id, "Common", "Commonly used component", 0, now, now))

        # Tag components
        cursor.execute("""
            INSERT INTO component_tags (component_id, tag_id)
            VALUES (?, ?)
        """, (component1_id, tag1_id))

        cursor.execute("""
            INSERT INTO component_tags (component_id, tag_id)
            VALUES (?, ?)
        """, (component1_id, tag2_id))

        cursor.execute("""
            INSERT INTO component_tags (component_id, tag_id)
            VALUES (?, ?)
        """, (component2_id, tag1_id))

        # Commit all changes
        conn.commit()

        # Check what we created
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM storage_locations")
        location_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM components")
        component_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]

        print("✅ Test data created successfully!")
        print(f"   - {category_count} categories")
        print(f"   - {location_count} storage locations")
        print(f"   - {component_count} components")
        print(f"   - {tag_count} tags")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_data()