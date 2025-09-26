"""
Mock data seeding script using Faker for testing the PartsHub database.
"""

import random
from faker import Faker
from sqlalchemy.orm import Session
from decimal import Decimal

from ..database import Base, engine, get_db
# Import all models to ensure they are registered
from ..models import *


fake = Faker()


# Electronic component data for realistic seeding
COMPONENT_TYPES = {
    "resistor": {
        "values": ["10Ω", "100Ω", "1kΩ", "10kΩ", "100kΩ", "1MΩ", "4.7kΩ", "2.2kΩ", "47kΩ"],
        "packages": ["0603", "0805", "1206", "THT"],
        "manufacturers": ["Yageo", "Panasonic", "Vishay", "KOA Speer"],
        "specs": lambda: {
            "tolerance": random.choice(["±1%", "±5%", "±10%"]),
            "power_rating": random.choice(["1/8W", "1/4W", "1/2W", "1W"]),
            "temperature_coefficient": random.choice(["±50ppm/°C", "±100ppm/°C"]),
        }
    },
    "capacitor": {
        "values": ["1pF", "10pF", "100pF", "1nF", "10nF", "100nF", "1µF", "10µF", "100µF"],
        "packages": ["0603", "0805", "1206", "THT", "Radial"],
        "manufacturers": ["Murata", "TDK", "Samsung", "Kemet"],
        "specs": lambda: {
            "voltage_rating": random.choice(["16V", "25V", "50V", "100V", "250V"]),
            "tolerance": random.choice(["±5%", "±10%", "±20%"]),
            "dielectric": random.choice(["X7R", "X5R", "C0G", "Y5V"]),
        }
    },
    "inductor": {
        "values": ["1µH", "10µH", "100µH", "1mH", "10mH", "47µH", "22µH"],
        "packages": ["0603", "0805", "1206", "THT", "Shielded"],
        "manufacturers": ["Bourns", "Coilcraft", "TDK", "Murata"],
        "specs": lambda: {
            "current_rating": random.choice(["100mA", "500mA", "1A", "2A"]),
            "tolerance": random.choice(["±10%", "±20%", "±30%"]),
            "dc_resistance": f"{random.randint(10, 1000)}mΩ",
        }
    },
    "diode": {
        "values": ["1N4148", "1N5819", "BAT54", "LED Red", "LED Blue", "LED White"],
        "packages": ["SOD-123", "DO-41", "SOT-23", "0805", "THT"],
        "manufacturers": ["Diodes Inc", "ON Semi", "Vishay", "Nexperia"],
        "specs": lambda: {
            "forward_voltage": f"{random.uniform(0.3, 3.5):.1f}V",
            "current_rating": random.choice(["150mA", "1A", "3A", "10A"]),
            "reverse_voltage": random.choice(["50V", "100V", "200V", "400V"]),
        }
    },
    "transistor": {
        "values": ["2N3904", "2N3906", "BC547", "BC557", "MOSFET-N", "MOSFET-P"],
        "packages": ["SOT-23", "TO-92", "SOT-223", "TO-220"],
        "manufacturers": ["Fairchild", "ON Semi", "Infineon", "STMicro"],
        "specs": lambda: {
            "type": random.choice(["NPN", "PNP", "N-Channel", "P-Channel"]),
            "voltage_rating": random.choice(["30V", "60V", "100V", "200V"]),
            "current_rating": random.choice(["200mA", "500mA", "1A", "2A"]),
        }
    },
    "ic": {
        "values": ["LM358", "74HC595", "ATmega328P", "ESP32", "LM2596", "TL074"],
        "packages": ["DIP-8", "SOIC-8", "QFP-32", "QFN-32", "TQFP-100"],
        "manufacturers": ["Texas Instruments", "Microchip", "Espressif", "STMicro"],
        "specs": lambda: {
            "supply_voltage": random.choice(["3.3V", "5V", "12V", "±15V"]),
            "operating_temp": random.choice(["-40°C to +85°C", "0°C to +70°C"]),
            "package_type": random.choice(["DIP", "SMD", "BGA"]),
        }
    }
}

STORAGE_TYPES = [
    {"name": "Main Workshop", "type": "room", "parent": None},
    {"name": "Storage Room", "type": "room", "parent": None},
    {"name": "Electronics Cabinet A", "type": "cabinet", "parent": "Main Workshop"},
    {"name": "Electronics Cabinet B", "type": "cabinet", "parent": "Main Workshop"},
    {"name": "Component Drawers", "type": "cabinet", "parent": "Storage Room"},
]

CATEGORIES = [
    {"name": "Passive Components", "parent": None, "color": "#3498db"},
    {"name": "Active Components", "parent": None, "color": "#e74c3c"},
    {"name": "Mechanical", "parent": None, "color": "#95a5a6"},
    {"name": "Resistors", "parent": "Passive Components", "color": "#f39c12"},
    {"name": "Capacitors", "parent": "Passive Components", "color": "#9b59b6"},
    {"name": "Inductors", "parent": "Passive Components", "color": "#1abc9c"},
    {"name": "Semiconductors", "parent": "Active Components", "color": "#e67e22"},
    {"name": "Integrated Circuits", "parent": "Active Components", "color": "#34495e"},
    {"name": "Diodes", "parent": "Semiconductors", "color": "#f1c40f"},
    {"name": "Transistors", "parent": "Semiconductors", "color": "#2ecc71"},
]


def create_categories(db: Session):
    """Create category hierarchy."""
    print("Creating categories...")
    category_map = {}

    # Create categories in order (parents first)
    for cat_data in CATEGORIES:
        parent_id = None
        if cat_data["parent"]:
            parent_id = category_map[cat_data["parent"]].id

        category = Category(
            name=cat_data["name"],
            parent_id=parent_id,
            color=cat_data.get("color"),
            description=fake.sentence(),
            sort_order=random.randint(1, 100)
        )
        db.add(category)
        db.flush()  # Get the ID
        category_map[cat_data["name"]] = category

    db.commit()
    return category_map


def create_storage_locations(db: Session):
    """Create storage location hierarchy."""
    print("Creating storage locations...")
    location_map = {}

    # Create base locations
    for loc_data in STORAGE_TYPES:
        parent_id = None
        if loc_data["parent"]:
            parent_id = location_map[loc_data["parent"]].id

        location = StorageLocation(
            name=loc_data["name"],
            type=loc_data["type"],
            parent_id=parent_id,
            description=fake.sentence(),
            qr_code_id=f"QR-{fake.uuid4()[:8].upper()}"
        )
        db.add(location)
        db.flush()
        location_map[loc_data["name"]] = location

    # Add some drawers and bins
    cabinet_a = location_map["Electronics Cabinet A"]
    for i in range(1, 6):
        drawer = StorageLocation(
            name=f"Drawer {i}",
            type="drawer",
            parent_id=cabinet_a.id,
            description=f"Drawer {i} in Electronics Cabinet A",
            qr_code_id=f"QR-{fake.uuid4()[:8].upper()}"
        )
        db.add(drawer)
        db.flush()
        location_map[f"Drawer {i}"] = drawer

        # Add bins to each drawer
        for j in range(1, 4):
            bin_loc = StorageLocation(
                name=f"Bin {j}",
                type="bin",
                parent_id=drawer.id,
                description=f"Bin {j} in Drawer {i}",
                qr_code_id=f"QR-{fake.uuid4()[:8].upper()}"
            )
            db.add(bin_loc)
            db.flush()
            location_map[f"Drawer {i} Bin {j}"] = bin_loc

    db.commit()
    return location_map


def create_components(db: Session, category_map: dict, location_map: dict, count: int = 100):
    """Create mock electronic components."""
    print(f"Creating {count} components...")

    categories = list(category_map.values())
    locations = list(location_map.values())

    for i in range(count):
        # Pick a component type
        component_type = random.choice(list(COMPONENT_TYPES.keys()))
        type_data = COMPONENT_TYPES[component_type]

        # Generate component data
        value = random.choice(type_data["values"])
        package = random.choice(type_data["packages"])
        manufacturer = random.choice(type_data["manufacturers"])

        # Generate part number
        part_number = f"{manufacturer[:3].upper()}-{fake.bothify('###??##')}"

        # Generate quantities
        quantity_on_hand = random.randint(0, 500)
        minimum_stock = random.randint(5, 50)

        # Generate financial data
        unit_price = Decimal(str(round(random.uniform(0.01, 25.00), 4)))
        total_value = unit_price * quantity_on_hand if quantity_on_hand > 0 else None

        component = Component(
            name=f"{component_type.title()} {value}",
            part_number=part_number,
            manufacturer=manufacturer,
            component_type=component_type,
            value=value,
            package=package,
            quantity_on_hand=quantity_on_hand,
            quantity_ordered=random.randint(0, 100),
            minimum_stock=minimum_stock,
            average_purchase_price=unit_price,
            total_purchase_value=total_value,
            category_id=random.choice(categories).id,
            storage_location_id=random.choice(locations).id,
            specifications=type_data["specs"](),
            notes=fake.sentence() if random.random() < 0.3 else None,
            custom_fields={
                "supplier": fake.company(),
                "datasheet_url": fake.url(),
                "last_ordered": fake.date_this_year().isoformat(),
            } if random.random() < 0.5 else None
        )

        db.add(component)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1} components...")
            db.commit()

    db.commit()
    print(f"✓ Created {count} components")


def seed_database(component_count: int = 100):
    """Main seeding function."""
    print("🌱 Seeding PartsHub database with mock data...")

    # Create database tables first
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    try:
        # Create the hierarchy
        category_map = create_categories(db)
        location_map = create_storage_locations(db)

        # Create components
        create_components(db, category_map, location_map, component_count)

        print("✅ Database seeding completed successfully!")
        print(f"   - Categories: {len(category_map)}")
        print(f"   - Storage Locations: {len(location_map)}")
        print(f"   - Components: {component_count}")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(150)  # Create 150 components