"""
Mock data seeding script using Faker for testing the PartsHub database.
"""

import random
from decimal import Decimal

from faker import Faker
from sqlalchemy.orm import Session

from ..database import Base, engine, get_db

# Import all models to ensure they are registered
from ..models import (
    Category,
    Component,
    ComponentLocation,
    StorageLocation,
    Tag,
)

fake = Faker()


# Electronic component data for realistic seeding
COMPONENT_TYPES = {
    "resistor": {
        "components": [
            {"name": "10Ω 0805 1%", "part_number": "RC0805FR-0710RL", "manufacturer": "Yageo", "value": "10Ω", "package": "0805"},
            {"name": "100Ω 0603 5%", "part_number": "RC0603JR-07100RL", "manufacturer": "Yageo", "value": "100Ω", "package": "0603"},
            {"name": "1kΩ 1206 1%", "part_number": "ERJ-8ENF1001V", "manufacturer": "Panasonic", "value": "1kΩ", "package": "1206"},
            {"name": "10kΩ 0805 5%", "part_number": "CRCW080510K0JNEA", "manufacturer": "Vishay", "value": "10kΩ", "package": "0805"},
            {"name": "4.7kΩ THT 5%", "part_number": "CFR-25JB-52-4K7", "manufacturer": "Yageo", "value": "4.7kΩ", "package": "THT"},
            {"name": "47kΩ 0603 1%", "part_number": "RK73H1JTTD4702F", "manufacturer": "KOA Speer", "value": "47kΩ", "package": "0603"},
        ],
        "specs": lambda: {
            "tolerance": random.choice(["±1%", "±5%", "±10%"]),
            "power_rating": random.choice(["1/8W", "1/4W", "1/2W", "1W"]),
            "temperature_coefficient": random.choice(["±50ppm/°C", "±100ppm/°C"]),
        }
    },
    "capacitor": {
        "components": [
            {"name": "100nF 0805 X7R", "part_number": "GRM21BR71H104KA01L", "manufacturer": "Murata", "value": "100nF", "package": "0805"},
            {"name": "10µF 1206 X5R", "part_number": "C3216X5R1A106K160AB", "manufacturer": "TDK", "value": "10µF", "package": "1206"},
            {"name": "1µF 0603 X7R", "part_number": "CL10A105KB8NNNC", "manufacturer": "Samsung", "value": "1µF", "package": "0603"},
            {"name": "22pF 0603 C0G", "part_number": "C0603C220J5GACTU", "manufacturer": "Kemet", "value": "22pF", "package": "0603"},
            {"name": "100µF Electrolytic", "part_number": "UWT1V101MCL1GS", "manufacturer": "Nichicon", "value": "100µF", "package": "Radial"},
            {"name": "1nF 0805 X7R", "part_number": "GRM21BR71H102KA01L", "manufacturer": "Murata", "value": "1nF", "package": "0805"},
        ],
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
        "components": [
            {"name": "LM358 Op-Amp", "part_number": "LM358N", "manufacturer": "Texas Instruments", "value": "LM358", "package": "DIP-8"},
            {"name": "74HC595 Shift Register", "part_number": "SN74HC595N", "manufacturer": "Texas Instruments", "value": "74HC595", "package": "DIP-16"},
            {"name": "ATmega328P MCU", "part_number": "ATMEGA328P-PU", "manufacturer": "Microchip", "value": "ATmega328P", "package": "DIP-28"},
            {"name": "ESP32-WROOM-32", "part_number": "ESP32-WROOM-32", "manufacturer": "Espressif", "value": "ESP32", "package": "SMD"},
            {"name": "LM2596 Buck Converter", "part_number": "LM2596S-ADJ", "manufacturer": "Texas Instruments", "value": "LM2596", "package": "TO-263"},
            {"name": "555 Timer IC", "part_number": "NE555P", "manufacturer": "Texas Instruments", "value": "NE555", "package": "DIP-8"},
            {"name": "Arduino Nano MCU", "part_number": "A000005", "manufacturer": "Arduino", "value": "ATmega328P", "package": "Module"},
            {"name": "STM32F103C8T6", "part_number": "STM32F103C8T6", "manufacturer": "STMicro", "value": "STM32F103", "package": "LQFP-48"},
        ],
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

        # Generate component data - handle new structure
        if "components" in type_data:
            # Use real component data
            component_data = random.choice(type_data["components"])
            name = component_data["name"]
            part_number = component_data["part_number"]
            manufacturer = component_data["manufacturer"]
            value = component_data["value"]
            package = component_data["package"]
        else:
            # Fallback to old structure
            value = random.choice(type_data["values"])
            package = random.choice(type_data["packages"])
            manufacturer = random.choice(type_data["manufacturers"])
            name = f"{component_type.title()} {value}"
            part_number = f"{manufacturer[:3].upper()}-{fake.bothify('###??##')}"

        # Generate quantities
        quantity_on_hand = random.randint(0, 500)
        minimum_stock = random.randint(5, 50)

        # Generate financial data
        unit_price = Decimal(str(round(random.uniform(0.01, 25.00), 4)))
        total_value = unit_price * quantity_on_hand if quantity_on_hand > 0 else None

        component = Component(
            name=name,
            part_number=part_number,
            local_part_id=f"{component_type[:3].upper()}-{fake.bothify('###')}" if random.random() < 0.7 else None,
            barcode_id=fake.bothify('PH######') if random.random() < 0.5 else None,
            manufacturer_part_number=part_number if random.random() < 0.8 else None,
            provider_sku=fake.bothify('SK-######') if random.random() < 0.6 else None,
            manufacturer=manufacturer,
            component_type=component_type,
            value=value,
            package=package,
            average_purchase_price=unit_price,
            total_purchase_value=total_value,
            category_id=random.choice(categories).id,
            specifications=type_data["specs"](),
            notes=fake.sentence() if random.random() < 0.3 else None,
            custom_fields={
                "supplier": fake.company(),
                "datasheet_url": fake.url(),
                "last_ordered": fake.date_this_year().isoformat(),
            } if random.random() < 0.5 else None
        )

        db.add(component)
        db.flush()  # Ensure component has an ID

        # Create ComponentLocation record with the quantity data
        from ..models.component_location import ComponentLocation
        location = ComponentLocation(
            component_id=component.id,
            storage_location_id=random.choice(locations).id,
            quantity_on_hand=quantity_on_hand,
            quantity_ordered=random.randint(0, 100),
            minimum_stock=minimum_stock
        )
        db.add(location)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1} components...")
            db.commit()

    db.commit()
    print(f"✓ Created {count} components")


def create_tags(db: Session) -> dict:
    """Create realistic electronic component tags."""
    print("Creating tags...")

    # Define system and user tags
    tag_data = [
        {"name": "SMD", "description": "Surface Mount Device", "color": "#4CAF50", "is_system": True},
        {"name": "Through-Hole", "description": "Through-hole component", "color": "#2196F3", "is_system": True},
        {"name": "High-Power", "description": "High power rating components", "color": "#FF5722", "is_system": False},
        {"name": "Precision", "description": "High precision components", "color": "#9C27B0", "is_system": False},
        {"name": "Automotive", "description": "Automotive grade components", "color": "#FF9800", "is_system": False},
        {"name": "Low-ESR", "description": "Low Equivalent Series Resistance", "color": "#00BCD4", "is_system": False},
        {"name": "Military-Grade", "description": "Military specification components", "color": "#795548", "is_system": False},
        {"name": "RoHS", "description": "RoHS compliant", "color": "#8BC34A", "is_system": True},
        {"name": "Lead-Free", "description": "Lead-free soldering", "color": "#4CAF50", "is_system": True},
        {"name": "Temperature-Stable", "description": "Temperature stable components", "color": "#607D8B", "is_system": False},
        {"name": "Low-Noise", "description": "Low noise characteristics", "color": "#9E9E9E", "is_system": False},
        {"name": "Fast-Switching", "description": "Fast switching components", "color": "#E91E63", "is_system": False},
    ]

    tag_map = {}
    for tag_info in tag_data:
        tag = Tag(
            name=tag_info["name"],
            description=tag_info["description"],
            color=tag_info["color"],
            is_system_tag=tag_info["is_system"]
        )
        db.add(tag)
        db.flush()  # Get the ID
        tag_map[tag.name] = tag

    db.commit()
    print(f"✓ Created {len(tag_map)} tags")
    return tag_map


def assign_tags_to_components(db: Session, tag_map: dict):
    """Assign random tags to existing components."""
    print("Assigning tags to components...")

    components = db.query(Component).all()
    tags = list(tag_map.values())

    # Define component type to likely tags mapping
    component_tag_mapping = {
        "resistor": ["SMD", "Through-Hole", "Precision", "Temperature-Stable"],
        "capacitor": ["SMD", "Through-Hole", "Low-ESR", "Temperature-Stable", "Automotive"],
        "inductor": ["SMD", "Through-Hole", "High-Power", "Low-Noise"],
        "diode": ["SMD", "Through-Hole", "Fast-Switching", "Automotive"],
        "transistor": ["SMD", "Through-Hole", "Fast-Switching", "Low-Noise"],
        "ic": ["SMD", "Military-Grade", "Automotive", "Low-Noise"],
        "connector": ["Through-Hole", "Military-Grade", "Automotive"],
    }

    for component in components:
        # Get likely tags for this component type
        likely_tags = component_tag_mapping.get(component.component_type, [])

        # Add some system tags
        component_tags = ["RoHS", "Lead-Free"]

        # Add type-specific tags with probability
        for tag_name in likely_tags:
            if random.random() < 0.6:  # 60% chance
                component_tags.append(tag_name)

        # Add some random tags
        if random.random() < 0.3:  # 30% chance to add extra random tag
            extra_tag = random.choice([tag.name for tag in tags if tag.name not in component_tags])
            component_tags.append(extra_tag)

        # Assign tags to component
        for tag_name in component_tags:
            if tag_name in tag_map:
                component.tags.append(tag_map[tag_name])

    db.commit()
    print(f"✓ Assigned tags to {len(components)} components")


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

        # Create tags
        tag_map = create_tags(db)

        # Create components
        create_components(db, category_map, location_map, component_count)

        # Assign tags to components
        assign_tags_to_components(db, tag_map)

        print("✅ Database seeding completed successfully!")
        print(f"   - Categories: {len(category_map)}")
        print(f"   - Storage Locations: {len(location_map)}")
        print(f"   - Tags: {len(tag_map)}")
        print(f"   - Components: {component_count}")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(150)  # Create 150 components
