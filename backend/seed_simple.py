"""
Simple database seeding script for testing
"""

import sys

sys.path.append('/app/src')

import random
from decimal import Decimal

from faker import Faker
from src.database import Base, engine, get_db
from src.models.category import Category
from src.models.component import Component
from src.models.storage_location import StorageLocation

fake = Faker()

def create_simple_seed():
    """Create simple test data"""
    print("🌱 Creating simple test data...")

    # Create tables
    print("📋 Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    try:
        # Create a simple category
        category = Category(
            name="Resistors",
            description="Basic resistor components"
        )
        db.add(category)
        db.flush()

        # Create a simple storage location
        location = StorageLocation(
            name="Main Storage",
            type="cabinet",
            description="Primary component storage"
        )
        db.add(location)
        db.flush()

        # Create some components
        for i in range(10):
            component = Component(
                name=f"Resistor {random.randint(1, 1000)}Ω",
                part_number=f"RES-{fake.bothify('###-??')}",
                manufacturer=random.choice(["Yageo", "Vishay", "Panasonic"]),
                component_type="resistor",
                value=f"{random.randint(10, 10000)}Ω",
                package=random.choice(["0603", "0805", "1206"]),
                quantity_on_hand=random.randint(0, 100),
                minimum_stock=10,
                average_purchase_price=Decimal(str(round(random.uniform(0.01, 1.0), 4))),
                category_id=category.id,
                storage_location_id=location.id
            )
            db.add(component)

        db.commit()
        print("✅ Created simple test data successfully!")
        print("   - 1 Category")
        print("   - 1 Storage Location")
        print("   - 10 Components")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_simple_seed()
