"""
Database initialization with default categories and admin user.
"""

from sqlalchemy.orm import Session

from ..database import Base, engine
from ..models import Category, StorageLocation, Tag


def create_default_categories(db: Session):
    """Create default component categories."""
    categories_data = [
        # Root categories
        {"name": "Passive", "description": "Passive electronic components"},
        {"name": "Active", "description": "Active electronic components"},
        {"name": "Electromechanical", "description": "Electromechanical components"},
        {"name": "Hardware", "description": "Hardware and mechanical parts"},
        # Passive subcategories
        {
            "name": "Resistors",
            "parent": "Passive",
            "description": "Fixed and variable resistors",
        },
        {
            "name": "Capacitors",
            "parent": "Passive",
            "description": "Electrolytic, ceramic, tantalum capacitors",
        },
        {
            "name": "Inductors",
            "parent": "Passive",
            "description": "Inductors and transformers",
        },
        {
            "name": "Crystals",
            "parent": "Passive",
            "description": "Crystals and oscillators",
        },
        # Active subcategories
        {
            "name": "Semiconductors",
            "parent": "Active",
            "description": "Diodes, transistors, ICs",
        },
        {
            "name": "Integrated Circuits",
            "parent": "Active",
            "description": "Digital and analog ICs",
        },
        {
            "name": "Microcontrollers",
            "parent": "Active",
            "description": "MCUs and development boards",
        },
        {
            "name": "Sensors",
            "parent": "Active",
            "description": "Temperature, pressure, motion sensors",
        },
        # Electromechanical subcategories
        {
            "name": "Connectors",
            "parent": "Electromechanical",
            "description": "Headers, sockets, terminals",
        },
        {
            "name": "Switches",
            "parent": "Electromechanical",
            "description": "Buttons, toggles, rotary switches",
        },
        {
            "name": "Relays",
            "parent": "Electromechanical",
            "description": "Electromechanical relays",
        },
        {
            "name": "Displays",
            "parent": "Electromechanical",
            "description": "LEDs, LCDs, OLEDs",
        },
        # Hardware subcategories
        {
            "name": "Enclosures",
            "parent": "Hardware",
            "description": "Project boxes and enclosures",
        },
        {"name": "PCBs", "parent": "Hardware", "description": "Printed circuit boards"},
        {"name": "Cables", "parent": "Hardware", "description": "Wires and cables"},
        {
            "name": "Fasteners",
            "parent": "Hardware",
            "description": "Screws, standoffs, spacers",
        },
    ]

    # Create parent categories first
    category_map = {}

    # First pass: create parent categories
    for cat_data in categories_data:
        if "parent" not in cat_data:
            category = Category(
                name=cat_data["name"], description=cat_data["description"]
            )
            db.add(category)
            db.flush()  # Get the ID
            category_map[cat_data["name"]] = category

    # Second pass: create child categories
    for cat_data in categories_data:
        if "parent" in cat_data:
            parent_name = cat_data["parent"]
            if parent_name in category_map:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    parent_id=category_map[parent_name].id,
                )
                db.add(category)
                db.flush()
                category_map[cat_data["name"]] = category

    db.commit()
    return category_map


def create_default_storage_locations(db: Session):
    """Create default storage locations."""
    locations_data = [
        # Root locations
        {
            "name": "Workshop",
            "type": "room",
            "description": "Main electronics workshop",
        },
        {
            "name": "Storage Room",
            "type": "room",
            "description": "Component storage area",
        },
        # Workshop locations
        {
            "name": "Main Workbench",
            "parent": "Workshop",
            "type": "container",
            "description": "Primary work area",
        },
        {
            "name": "Electronics Cabinet",
            "parent": "Workshop",
            "type": "cabinet",
            "description": "Component storage cabinet",
        },
        # Cabinet organization
        {
            "name": "Drawer 1 - Resistors",
            "parent": "Electronics Cabinet",
            "type": "drawer",
            "description": "Resistor storage",
        },
        {
            "name": "Drawer 2 - Capacitors",
            "parent": "Electronics Cabinet",
            "type": "drawer",
            "description": "Capacitor storage",
        },
        {
            "name": "Drawer 3 - ICs",
            "parent": "Electronics Cabinet",
            "type": "drawer",
            "description": "Integrated circuit storage",
        },
        {
            "name": "Shelf A - Development Boards",
            "parent": "Electronics Cabinet",
            "type": "shelf",
            "description": "Arduino, Raspberry Pi, etc.",
        },
        # Storage room
        {
            "name": "Bulk Storage",
            "parent": "Storage Room",
            "type": "container",
            "description": "Bulk component storage",
        },
        {
            "name": "Archive Cabinet",
            "parent": "Storage Room",
            "type": "cabinet",
            "description": "Obsolete and archive components",
        },
    ]

    location_map = {}

    # First pass: create parent locations
    for loc_data in locations_data:
        if "parent" not in loc_data:
            location = StorageLocation(
                name=loc_data["name"],
                type=loc_data["type"],
                description=loc_data["description"],
            )
            # Manually set hierarchy for root locations
            location.location_hierarchy = loc_data["name"]
            db.add(location)
            db.flush()
            location_map[loc_data["name"]] = location

    # Second pass: create child locations
    for loc_data in locations_data:
        if "parent" in loc_data:
            parent_name = loc_data["parent"]
            if parent_name in location_map:
                parent = location_map[parent_name]
                location = StorageLocation(
                    name=loc_data["name"],
                    type=loc_data["type"],
                    description=loc_data["description"],
                    parent_id=parent.id,
                )
                # Build hierarchy path
                location.location_hierarchy = (
                    f"{parent.location_hierarchy}/{loc_data['name']}"
                )
                db.add(location)
                db.flush()
                location_map[loc_data["name"]] = location

    db.commit()
    return location_map


def create_default_tags(db: Session):
    """Create default component tags."""
    tags_data = [
        {"name": "SMD", "description": "Surface mount device", "color": "#3B82F6"},
        {
            "name": "Through-hole",
            "description": "Through-hole component",
            "color": "#10B981",
        },
        {
            "name": "High-precision",
            "description": "High precision component",
            "color": "#8B5CF6",
        },
        {
            "name": "Low-power",
            "description": "Low power consumption",
            "color": "#F59E0B",
        },
        {"name": "Automotive", "description": "Automotive grade", "color": "#EF4444"},
        {
            "name": "Military",
            "description": "Military specification",
            "color": "#6B7280",
        },
        {"name": "RoHS", "description": "RoHS compliant", "color": "#059669"},
        {
            "name": "Obsolete",
            "description": "Obsolete or discontinued",
            "color": "#DC2626",
        },
        {
            "name": "Prototype",
            "description": "Prototype or development",
            "color": "#7C3AED",
        },
        {"name": "Production", "description": "Production ready", "color": "#0891B2"},
    ]

    for tag_data in tags_data:
        tag = Tag(
            name=tag_data["name"],
            description=tag_data["description"],
            color=tag_data["color"],
            is_system_tag=True,
        )
        db.add(tag)

    db.commit()


def initialize_database():
    """Initialize database with all tables and default data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    print("Adding default data...")
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_categories = db.query(Category).first()
        if not existing_categories:
            print("Creating default categories...")
            create_default_categories(db)

            print("Creating default storage locations...")
            create_default_storage_locations(db)

            print("Creating default tags...")
            create_default_tags(db)

            print("Database initialization complete!")
        else:
            print("Database already initialized.")

    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
