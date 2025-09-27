# KiCad Workflow Examples

This guide provides practical examples and workflows for integrating PartsHub with KiCad projects.

## Common Workflows

### 1. Creating a New PCB Project

#### Step 1: Search Components in PartsHub
```bash
# Search for microcontroller
curl "http://localhost:8000/api/v1/kicad/components?search=STM32F103&package=LQFP"

# Search for passives
curl "http://localhost:8000/api/v1/kicad/components?search=10k&package=0805"
```

#### Step 2: Generate Project-Specific Library
```bash
# Create library for specific components
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "library_path": "./my_project_libs",
    "categories": ["Microcontrollers", "Resistors", "Capacitors"],
    "include_symbols": true,
    "include_footprints": true,
    "include_3d_models": true
  }'
```

#### Step 3: Import Libraries to KiCad
1. Open KiCad Project Manager
2. Go to Preferences → Manage Symbol Libraries
3. Add `./my_project_libs/symbols/*.kicad_sym`
4. Go to Preferences → Manage Footprint Libraries
5. Add `./my_project_libs/footprints/*.pretty`

#### Step 4: Use Components in Schematic
- Components will appear with PartsHub data populated
- All specifications available as component fields
- Datasheets linked automatically

### 2. Updating Existing Project Libraries

#### Check Current Library Status
```bash
curl "http://localhost:8000/api/v1/kicad/libraries/status"
```

#### Incremental Update
```bash
# Only update modified components
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "library_path": "./existing_libs",
    "incremental": true,
    "last_sync": "2024-01-15T10:30:00Z"
  }'
```

### 3. BOM Generation from KiCad

#### Export BOM from KiCad
1. In Eeschema: Tools → Generate Bill of Materials
2. Select "CSV" format
3. Include Reference, Value, Footprint, Manufacturer, MPN fields

#### Cross-Reference with PartsHub Inventory
```bash
# Check component availability
curl -X POST http://localhost:8000/api/v1/components/check-availability \
  -H "Content-Type: application/json" \
  -d '{
    "components": [
      {"manufacturer": "Yageo", "part_number": "RC0805FR-0710KL", "quantity": 10},
      {"manufacturer": "STMicroelectronics", "part_number": "STM32F103C8T6", "quantity": 1}
    ]
  }'
```

### 4. Component Data Synchronization

#### From Provider to PartsHub to KiCad
```bash
# Step 1: Import component from LCSC
curl -X POST http://localhost:8000/api/v1/components/import-from-provider \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "provider": "lcsc",
    "provider_part_id": "C8734",
    "storage_location_id": "storage-uuid"
  }'

# Step 2: Auto-generate KiCad library entry
curl -X POST http://localhost:8000/api/v1/kicad/components/auto-generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "component_id": "new-component-uuid",
    "symbol_template": "microcontroller",
    "footprint_template": "LQFP-48"
  }'

# Step 3: Update KiCad libraries
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"library_path": "./libs", "incremental": true}'
```

## Advanced Examples

### 1. Custom Symbol Generation

#### Define Component with Custom Symbol
```json
{
  "name": "Custom Op-Amp",
  "part_number": "LM358",
  "manufacturer": "Texas Instruments",
  "package": "SOIC-8",
  "component_type": "op_amp",
  "kicad_data": {
    "symbol_library": "Custom_Symbols",
    "symbol_name": "OpAmp_Dual",
    "footprint_library": "Custom_Footprints.pretty",
    "footprint_name": "SOIC-8_3.9x4.9mm_P1.27mm",
    "kicad_fields_json": {
      "Pin1": "OUT1",
      "Pin2": "IN1-",
      "Pin3": "IN1+",
      "Pin4": "VCC-",
      "Pin5": "IN2+",
      "Pin6": "IN2-",
      "Pin7": "OUT2",
      "Pin8": "VCC+"
    }
  }
}
```

### 2. Batch Component Processing

#### Import Multiple Components with KiCad Data
```bash
# Upload CSV with KiCad mappings
curl -X POST http://localhost:8000/api/v1/components/bulk-import-kicad \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@components_with_kicad.csv" \
  -F "mapping={
    \"part_number\": 0,
    \"manufacturer\": 1,
    \"package\": 2,
    \"symbol_lib\": 3,
    \"footprint_lib\": 4,
    \"model_path\": 5
  }"
```

**CSV Format:**
```csv
part_number,manufacturer,package,symbol_lib,footprint_lib,model_path
RC0805FR-0710KL,Yageo,0805,Resistors,Resistors.pretty,resistors/R_0805.step
LM358P,TI,DIP-8,OpAmps,OpAmps.pretty,ics/DIP-8.step
```

### 3. Project-Based Library Management

#### Create Project-Specific Component Set
```python
# Python script example
import requests

def create_project_library(project_name, component_list):
    """Create KiCad library for specific project components"""

    # Get component details
    components = []
    for part_number, manufacturer in component_list:
        response = requests.get(
            f"http://localhost:8000/api/v1/components",
            params={"search": f"{manufacturer} {part_number}"}
        )
        components.extend(response.json()["components"])

    # Generate library
    library_request = {
        "library_path": f"./projects/{project_name}/kicad_libs",
        "component_ids": [c["id"] for c in components],
        "include_symbols": True,
        "include_footprints": True,
        "include_3d_models": True
    }

    response = requests.post(
        "http://localhost:8000/api/v1/kicad/libraries/sync",
        json=library_request,
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()

# Usage
project_components = [
    ("STM32F103C8T6", "STMicroelectronics"),
    ("RC0805FR-0710KL", "Yageo"),
    ("CC0805KRX7R9BB104", "Yageo")
]

result = create_project_library("led_controller_v1", project_components)
print(f"Generated library with {result['components_exported']} components")
```

### 4. Automated Library Updates

#### Setup Automated Sync Script
```bash
#!/bin/bash
# auto_sync_kicad.sh

# Configuration
PARTSHUB_URL="http://localhost:8000"
LIBRARY_PATH="/home/user/KiCad/libraries"
TOKEN_FILE="~/.partshub_token"

# Get authentication token
get_token() {
    curl -s -X POST "$PARTSHUB_URL/api/v1/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"username":"'"$PARTSHUB_USER"'","password":"'"$PARTSHUB_PASS"'"}' \
        | jq -r '.access_token' > "$TOKEN_FILE"
}

# Sync libraries
sync_libraries() {
    TOKEN=$(cat "$TOKEN_FILE")

    curl -X POST "$PARTSHUB_URL/api/v1/kicad/libraries/sync" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "library_path": "'"$LIBRARY_PATH"'",
            "incremental": true,
            "include_symbols": true,
            "include_footprints": true
        }' | jq '.'
}

# Main execution
echo "Starting KiCad library sync..."
get_token
sync_libraries
echo "Sync completed at $(date)"
```

#### Cron Job Setup
```bash
# Add to crontab (sync daily at 2 AM)
0 2 * * * /path/to/auto_sync_kicad.sh >> /var/log/kicad_sync.log 2>&1
```

## Integration Patterns

### 1. Design Review Workflow

#### Component Verification
```bash
# Verify all components in BOM exist in inventory
curl -X POST http://localhost:8000/api/v1/kicad/bom/verify \
  -H "Authorization: Bearer $TOKEN" \
  -F "bom_file=@project_bom.csv" \
  -F "check_availability=true"
```

#### Alternative Component Suggestions
```bash
# Get substitute components for out-of-stock parts
curl "http://localhost:8000/api/v1/components/{component_id}/substitutes"
```

### 2. Manufacturing Handoff

#### Generate Manufacturing BOM
```bash
# Export BOM with supplier information
curl "http://localhost:8000/api/v1/kicad/bom/manufacturing" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "bom_file": "project_bom.csv",
    "include_pricing": true,
    "include_availability": true,
    "preferred_suppliers": ["LCSC", "DigiKey", "Mouser"]
  }'
```

### 3. Version Control Integration

#### Git Hooks for Library Updates
```bash
# .git/hooks/post-merge
#!/bin/bash
# Update KiCad libraries after git merge

if git diff-tree --name-only HEAD~1 HEAD | grep -q "components/"; then
    echo "Components updated, syncing KiCad libraries..."
    ./scripts/sync_kicad_libraries.sh
fi
```

## Error Handling and Recovery

### Common Error Scenarios

#### 1. Component ID Mismatch
```bash
# Problem: KiCad component references don't match PartsHub
# Solution: Regenerate library with UUID mapping

curl -X POST http://localhost:8000/api/v1/kicad/libraries/fix-references \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "library_path": "./libs",
    "update_mode": "uuid_mapping"
  }'
```

#### 2. Missing Footprints
```bash
# Problem: Generated symbols have no footprints
# Solution: Generate missing footprints

curl -X POST http://localhost:8000/api/v1/kicad/footprints/generate-missing \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "component_ids": ["uuid1", "uuid2"],
    "use_generic_fallback": true
  }'
```

#### 3. Library Corruption
```bash
# Problem: KiCad library files corrupted
# Solution: Full regeneration with validation

curl -X POST http://localhost:8000/api/v1/kicad/libraries/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "library_path": "./libs",
    "validate_output": true,
    "backup_existing": true
  }'
```

## Performance Tips

### 1. Large Database Optimization
- Use category-based filtering
- Enable incremental sync
- Implement library caching
- Use parallel processing

### 2. Network Optimization
- Cache frequently accessed components
- Use compression for large transfers
- Implement retry logic for failed requests

### 3. Storage Optimization
- Regular cleanup of unused libraries
- Compress 3D model files
- Use symbolic links for shared models

---

For more detailed examples and troubleshooting, see the main [KiCad Integration Guide](kicad-integration.md).