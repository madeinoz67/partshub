#!/usr/bin/env python3
"""
Demo seed script for PartsHub - creates realistic demonstration data.
Uses the component service to properly create data with all relationships.
"""

import time

import requests

BASE_URL = "http://localhost:8000/api/v1"

def wait_for_server():
    """Wait for the server to be ready."""
    print("🔄 Waiting for server to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{BASE_URL}/components?limit=1", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            time.sleep(1)
    print("❌ Server not responding")
    return False

def create_categories():
    """Create component categories."""
    print("📁 Creating categories...")

    categories = [
        {
            "name": "Resistors",
            "description": "Fixed resistors, variable resistors, and resistor networks",
            "sort_order": 1
        },
        {
            "name": "Capacitors",
            "description": "Ceramic, electrolytic, tantalum, and film capacitors",
            "sort_order": 2
        },
        {
            "name": "Integrated Circuits",
            "description": "Microcontrollers, processors, analog ICs, and logic gates",
            "sort_order": 3
        },
        {
            "name": "Semiconductors",
            "description": "Diodes, transistors, MOSFETs, and voltage regulators",
            "sort_order": 4
        },
        {
            "name": "Inductors & Transformers",
            "description": "Power inductors, RF coils, and transformers",
            "sort_order": 5
        },
        {
            "name": "Connectors",
            "description": "Headers, sockets, terminal blocks, and cable connectors",
            "sort_order": 6
        }
    ]

    created_categories = {}
    for cat in categories:
        try:
            response = requests.post(f"{BASE_URL}/categories", json=cat)
            if response.status_code == 201:
                result = response.json()
                created_categories[cat["name"]] = result["id"]
                print(f"  ✅ Created category: {cat['name']}")
            else:
                print(f"  ❌ Failed to create {cat['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {cat['name']}: {e}")

    return created_categories

def create_storage_locations():
    """Create storage location hierarchy."""
    print("📦 Creating storage locations...")

    locations = [
        {
            "name": "Electronics Lab",
            "description": "Main electronics laboratory",
            "type": "room"
        },
        {
            "name": "Component Cabinet A",
            "description": "Primary component storage cabinet",
            "type": "cabinet"
        },
        {
            "name": "SMD Drawer",
            "description": "Surface mount components drawer",
            "type": "drawer"
        },
        {
            "name": "Through-Hole Drawer",
            "description": "Through-hole components drawer",
            "type": "drawer"
        },
        {
            "name": "IC Storage",
            "description": "Integrated circuit storage area",
            "type": "shelf"
        },
        {
            "name": "Development Boards",
            "description": "Arduino, Raspberry Pi, and dev boards",
            "type": "shelf"
        }
    ]

    created_locations = {}
    for loc in locations:
        try:
            response = requests.post(f"{BASE_URL}/storage-locations", json=loc)
            if response.status_code == 201:
                result = response.json()
                created_locations[loc["name"]] = result["id"]
                print(f"  ✅ Created location: {loc['name']}")
            else:
                print(f"  ❌ Failed to create {loc['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {loc['name']}: {e}")

    return created_locations

def create_tags():
    """Create component tags."""
    print("🏷️ Creating tags...")

    tags = [
        {"name": "SMD", "description": "Surface Mount Device"},
        {"name": "Through-Hole", "description": "Through-hole component"},
        {"name": "Common", "description": "Commonly used component"},
        {"name": "High-Power", "description": "High power rating"},
        {"name": "Precision", "description": "High precision component"},
        {"name": "Development", "description": "Development and prototyping"},
        {"name": "Arduino", "description": "Arduino compatible"},
        {"name": "Low-Power", "description": "Low power consumption"},
        {"name": "RF", "description": "Radio frequency applications"}
    ]

    created_tags = {}
    for tag in tags:
        try:
            response = requests.post(f"{BASE_URL}/tags", json=tag)
            if response.status_code == 201:
                result = response.json()
                created_tags[tag["name"]] = result["id"]
                print(f"  ✅ Created tag: {tag['name']}")
            else:
                print(f"  ❌ Failed to create {tag['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {tag['name']}: {e}")

    return created_tags

def create_demo_components(categories: dict[str, str], locations: dict[str, str], tags: dict[str, str]):
    """Create demonstration components."""
    print("🔧 Creating demo components...")

    # Get a default storage location
    default_location = list(locations.values())[0] if locations else None

    components = [
        # Resistors
        {
            "name": "1kΩ Resistor",
            "part_number": "RC0603FR-071KL",
            "local_part_id": "R001",
            "manufacturer": "Yageo",
            "manufacturer_part_number": "RC0603FR-071KL",
            "category_id": categories.get("Resistors"),
            "storage_location_id": default_location,
            "component_type": "resistor",
            "value": "1kΩ",
            "package": "0603",
            "quantity_on_hand": 250,
            "minimum_stock": 50,
            "notes": "1% tolerance, 1/10W power rating",
            "specifications": {
                "tolerance": "±1%",
                "power_rating": "0.1W",
                "temperature_coefficient": "±100ppm/°C"
            }
        },
        {
            "name": "10kΩ Resistor",
            "part_number": "RC0603FR-0710KL",
            "local_part_id": "R002",
            "manufacturer": "Yageo",
            "manufacturer_part_number": "RC0603FR-0710KL",
            "category_id": categories.get("Resistors"),
            "storage_location_id": default_location,
            "component_type": "resistor",
            "value": "10kΩ",
            "package": "0603",
            "quantity_on_hand": 180,
            "minimum_stock": 50,
            "notes": "1% tolerance, 1/10W power rating"
        },
        {
            "name": "470Ω Resistor",
            "part_number": "MFR-25FRF52-470R",
            "local_part_id": "R003",
            "manufacturer": "Yageo",
            "component_type": "resistor",
            "value": "470Ω",
            "package": "Through-Hole",
            "category_id": categories.get("Resistors"),
            "storage_location_id": default_location,
            "quantity_on_hand": 100,
            "minimum_stock": 25,
            "notes": "1/4W metal film resistor, through-hole"
        },

        # Capacitors
        {
            "name": "100nF Ceramic Capacitor",
            "part_number": "GCM188R71H104KA57D",
            "local_part_id": "C001",
            "manufacturer": "Murata",
            "manufacturer_part_number": "GCM188R71H104KA57D",
            "category_id": categories.get("Capacitors"),
            "storage_location_id": default_location,
            "component_type": "capacitor",
            "value": "100nF",
            "package": "0603",
            "quantity_on_hand": 500,
            "minimum_stock": 100,
            "notes": "X7R dielectric, 50V rated",
            "specifications": {
                "capacitance": "100nF",
                "voltage_rating": "50V",
                "dielectric": "X7R",
                "tolerance": "±10%"
            }
        },
        {
            "name": "10µF Electrolytic Capacitor",
            "part_number": "EEE-HA1H100WR",
            "local_part_id": "C002",
            "manufacturer": "Panasonic",
            "component_type": "capacitor",
            "value": "10µF",
            "package": "Radial",
            "category_id": categories.get("Capacitors"),
            "storage_location_id": default_location,
            "quantity_on_hand": 75,
            "minimum_stock": 20,
            "notes": "50V aluminum electrolytic, radial package"
        },
        {
            "name": "22pF Ceramic Capacitor",
            "part_number": "GCM1885C1H220JA16D",
            "local_part_id": "C003",
            "manufacturer": "Murata",
            "component_type": "capacitor",
            "value": "22pF",
            "package": "0603",
            "category_id": categories.get("Capacitors"),
            "storage_location_id": default_location,
            "quantity_on_hand": 200,
            "minimum_stock": 50,
            "notes": "C0G/NP0 dielectric, ultra-stable"
        },

        # Integrated Circuits
        {
            "name": "ESP32-S3 Microcontroller",
            "part_number": "ESP32-S3-WROOM-1-N16R8",
            "local_part_id": "U001",
            "manufacturer": "Espressif",
            "manufacturer_part_number": "ESP32-S3-WROOM-1-N16R8",
            "category_id": categories.get("Integrated Circuits"),
            "storage_location_id": default_location,
            "component_type": "microcontroller",
            "value": "ESP32-S3",
            "package": "Module",
            "quantity_on_hand": 15,
            "minimum_stock": 5,
            "notes": "WiFi/Bluetooth enabled MCU with 16MB Flash, 8MB PSRAM",
            "specifications": {
                "cpu_cores": "2x Xtensa LX7",
                "flash_memory": "16MB",
                "ram": "8MB PSRAM",
                "wifi": "802.11 b/g/n",
                "bluetooth": "5.0"
            }
        },
        {
            "name": "ATmega328P Microcontroller",
            "part_number": "ATMEGA328P-PU",
            "local_part_id": "U002",
            "manufacturer": "Microchip",
            "manufacturer_part_number": "ATMEGA328P-PU",
            "category_id": categories.get("Integrated Circuits"),
            "storage_location_id": default_location,
            "component_type": "microcontroller",
            "value": "ATmega328P",
            "package": "DIP-28",
            "quantity_on_hand": 25,
            "minimum_stock": 10,
            "notes": "Arduino Uno compatible microcontroller"
        },
        {
            "name": "LM358 Op-Amp",
            "part_number": "LM358P",
            "local_part_id": "U003",
            "manufacturer": "Texas Instruments",
            "component_type": "op-amp",
            "value": "LM358",
            "package": "DIP-8",
            "category_id": categories.get("Integrated Circuits"),
            "storage_location_id": default_location,
            "quantity_on_hand": 40,
            "minimum_stock": 15,
            "notes": "Dual operational amplifier"
        },

        # Semiconductors
        {
            "name": "1N4007 Diode",
            "part_number": "1N4007-TP",
            "local_part_id": "D001",
            "manufacturer": "Micro Commercial Co",
            "component_type": "diode",
            "value": "1N4007",
            "package": "DO-41",
            "category_id": categories.get("Semiconductors"),
            "storage_location_id": default_location,
            "quantity_on_hand": 200,
            "minimum_stock": 50,
            "notes": "1A 1000V rectifier diode"
        },
        {
            "name": "2N3904 NPN Transistor",
            "part_number": "2N3904-AP",
            "local_part_id": "Q001",
            "manufacturer": "Central Semiconductor",
            "component_type": "transistor",
            "value": "2N3904",
            "package": "TO-92",
            "category_id": categories.get("Semiconductors"),
            "storage_location_id": default_location,
            "quantity_on_hand": 150,
            "minimum_stock": 30,
            "notes": "General purpose NPN switching transistor"
        },

        # Development boards
        {
            "name": "Arduino Uno R3",
            "part_number": "A000066",
            "local_part_id": "DEV001",
            "manufacturer": "Arduino",
            "component_type": "development_board",
            "value": "Arduino Uno R3",
            "package": "PCB",
            "category_id": categories.get("Integrated Circuits"),
            "storage_location_id": default_location,
            "quantity_on_hand": 8,
            "minimum_stock": 3,
            "notes": "Original Arduino Uno development board"
        },
        {
            "name": "Raspberry Pi 4 Model B",
            "part_number": "RPI4-MODBP-4GB",
            "local_part_id": "DEV002",
            "manufacturer": "Raspberry Pi Foundation",
            "component_type": "single_board_computer",
            "value": "RPi 4B 4GB",
            "package": "PCB",
            "category_id": categories.get("Integrated Circuits"),
            "storage_location_id": default_location,
            "quantity_on_hand": 5,
            "minimum_stock": 2,
            "notes": "4GB RAM model single board computer"
        }
    ]

    created_components = []
    for comp in components:
        try:
            # Clean up None values
            clean_comp = {k: v for k, v in comp.items() if v is not None}

            response = requests.post(f"{BASE_URL}/components", json=clean_comp)
            if response.status_code == 201:
                result = response.json()
                created_components.append(result)
                print(f"  ✅ Created component: {comp['name']}")
            else:
                print(f"  ❌ Failed to create {comp['name']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {comp['name']}: {e}")

    return created_components

def create_demo_projects():
    """Create demonstration projects."""
    print("📋 Creating demo projects...")

    projects = [
        {
            "name": "LED Matrix Display",
            "description": "8x8 RGB LED matrix with ESP32 control",
            "status": "active",
            "notes": "Using WS2812B addressable LEDs"
        },
        {
            "name": "IoT Temperature Monitor",
            "description": "Wireless temperature and humidity monitoring system",
            "status": "planning",
            "notes": "ESP32 + DHT22 sensor with web dashboard"
        },
        {
            "name": "Arduino Robot Car",
            "description": "Remote controlled robot car with obstacle avoidance",
            "status": "completed",
            "notes": "Uses ultrasonic sensors and servo motors"
        }
    ]

    for project in projects:
        try:
            response = requests.post(f"{BASE_URL}/projects", json=project)
            if response.status_code == 201:
                response.json()
                print(f"  ✅ Created project: {project['name']}")
            else:
                print(f"  ❌ Failed to create {project['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating {project['name']}: {e}")

def main():
    """Main demo seed function."""
    print("🌱 Creating PartsHub demonstration data...")
    print("=" * 50)

    if not wait_for_server():
        return

    # Create base data
    categories = create_categories()
    locations = create_storage_locations()
    tags = create_tags()

    # Create components
    components = create_demo_components(categories, locations, tags)

    # Create projects
    create_demo_projects()

    print("\n" + "=" * 50)
    print("✅ Demo data creation complete!")
    print(f"📊 Created {len(categories)} categories")
    print(f"📦 Created {len(locations)} storage locations")
    print(f"🏷️ Created {len(tags)} tags")
    print(f"🔧 Created {len(components)} components")
    print("📋 Created demo projects")
    print("\n🚀 Your PartsHub demo is ready!")
    print("   Visit: http://localhost:3000")
    print("   Admin login: admin / roUy5jBBQ4aRFEelXjjjAw")

if __name__ == "__main__":
    main()
