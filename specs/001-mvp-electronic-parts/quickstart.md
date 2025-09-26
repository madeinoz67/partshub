# QuickStart Guide: PartsHub MVP

## Overview

This quickstart guide provides integration test scenarios that validate the core user workflows for the PartsHub electronic parts management application. These scenarios serve as both documentation and automated test cases.

## Prerequisites

- PartsHub application running at `http://localhost:8000`
- Default admin user created with changed password
- Database initialized with basic categories and default storage locations

## Core User Scenarios

### Scenario 1: First-Time Setup and Component Addition

**Objective**: Validate new user setup and basic component management

**Test Steps**:

1. **Initial Login**
   ```bash
   # Access the application
   curl -X GET http://localhost:8000/
   # Should show login page for admin functions, search available anonymously
   ```

2. **Create Storage Locations**
   ```bash
   # Admin login and get token
   TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"new_password"}' \
     | jq -r '.access_token')

   # Create cabinet storage location
   curl -X POST http://localhost:8000/api/v1/storage-locations \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "workbench-cabinet",
       "description": "Main workbench storage cabinet",
       "location_type": "cabinet"
     }'

   # Bulk create drawer locations
   curl -X POST http://localhost:8000/api/v1/storage-locations/bulk-create \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prefix": "drawer-",
       "layout_type": "row",
       "parent_location_id": "{cabinet_id}",
       "location_type": "drawer",
       "range_1": {
         "type": "numbers",
         "start": "1",
         "end": "6"
       }
     }'
   ```

3. **Add First Component**
   ```bash
   # Add a 10kΩ resistor
   curl -X POST http://localhost:8000/api/v1/components \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Resistor 10kΩ 1% 0805",
       "part_number": "RC0805FR-0710KL",
       "manufacturer": "Yageo",
       "category_id": "{resistor_category_id}",
       "storage_location_id": "{drawer_1_id}",
       "component_type": "resistor",
       "value": "10kΩ",
       "tolerance": "±1%",
       "package": "0805",
       "quantity_on_hand": 100,
       "minimum_stock": 20,
       "notes": "General purpose precision resistor"
     }'
   ```

**Expected Results**:
- Storage locations created successfully with proper hierarchy
- Component added with all specifications
- Component appears in search results
- Dashboard shows updated statistics

### Scenario 2: Component Search and Inventory Management

**Objective**: Validate search functionality and stock operations

**Test Steps**:

1. **Search Components (Anonymous)**
   ```bash
   # Search for resistors
   curl -X GET "http://localhost:8000/api/v1/components?search=resistor&limit=10"

   # Search by value
   curl -X GET "http://localhost:8000/api/v1/components?search=10k"

   # Filter by category and manufacturer
   curl -X GET "http://localhost:8000/api/v1/components?manufacturer=Yageo&category_id={resistor_category_id}"
   ```

2. **Update Component Stock**
   ```bash
   # Use 10 resistors for a project
   curl -X POST http://localhost:8000/api/v1/components/{component_id}/stock \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "transaction_type": "remove",
       "quantity_change": -10,
       "reason": "Used in LED driver project"
     }'

   # Add new stock from purchase
   curl -X POST http://localhost:8000/api/v1/components/{component_id}/stock \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "transaction_type": "add",
       "quantity_change": 50,
       "reason": "Purchase order PO-2025-001"
     }'
   ```

3. **View Stock History**
   ```bash
   curl -X GET http://localhost:8000/api/v1/components/{component_id}/history
   ```

**Expected Results**:
- Search returns relevant components with proper filtering
- Stock updates reflect in component quantity
- Stock history shows all transactions with timestamps
- Low stock alert triggers if quantity falls below minimum

### Scenario 3: Project-Based Component Management

**Objective**: Validate project allocation and tracking

**Test Steps**:

1. **Create Project**
   ```bash
   curl -X POST http://localhost:8000/api/v1/projects \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "LED Driver Circuit v2.1",
       "description": "Improved LED driver with current sensing",
       "status": "active"
     }'
   ```

2. **Allocate Components to Project**
   ```bash
   # Allocate resistors
   curl -X POST http://localhost:8000/api/v1/projects/{project_id}/components \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "component_id": "{resistor_component_id}",
       "quantity_allocated": 5
     }'

   # Allocate capacitors
   curl -X POST http://localhost:8000/api/v1/projects/{project_id}/components \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "component_id": "{capacitor_component_id}",
       "quantity_allocated": 3
     }'
   ```

3. **Track Component Usage**
   ```bash
   # Mark components as used
   curl -X PUT http://localhost:8000/api/v1/projects/{project_id}/components/{allocation_id} \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "quantity_used": 3
     }'
   ```

**Expected Results**:
- Project created successfully
- Components allocated with proper quantity tracking
- Project view shows allocated vs used quantities
- Component availability updated to reflect allocations

### Scenario 4: Component Data Provider Integration

**Objective**: Validate external data provider functionality

**Test Steps**:

1. **Search Provider for Component Data**
   ```bash
   # Search LCSC for component
   curl -X GET http://localhost:8000/api/v1/providers/lcsc/search?query=STM32F103C8T6 \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Import Component from Provider**
   ```bash
   curl -X POST http://localhost:8000/api/v1/components/import-from-provider \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "lcsc",
       "provider_part_id": "C8734",
       "storage_location_id": "{ic_drawer_id}",
       "quantity_on_hand": 10,
       "minimum_stock": 2
     }'
   ```

3. **Verify Imported Data**
   ```bash
   # Check component details
   curl -X GET http://localhost:8000/api/v1/components/{imported_component_id}

   # Verify datasheet and specifications were populated
   curl -X GET http://localhost:8000/api/v1/components/{imported_component_id}/attachments
   ```

**Expected Results**:
- Provider search returns relevant components
- Component imported with specifications, datasheet, and image
- Provider data cached for future reference
- Component searchable by imported specifications

### Scenario 5: KiCad Integration

**Objective**: Validate KiCad library integration and synchronization

**Test Steps**:

1. **Search Components from KiCad**
   ```bash
   # KiCad searches for components
   curl -X GET "http://localhost:8000/api/v1/kicad/components?search=STM32&package=LQFP-48"
   ```

2. **Get Component Details for KiCad**
   ```bash
   curl -X GET http://localhost:8000/api/v1/kicad/components/{component_id}
   ```

3. **Retrieve Symbol and Footprint Data**
   ```bash
   # Get symbol information
   curl -X GET http://localhost:8000/api/v1/kicad/components/{component_id}/symbol

   # Get footprint information
   curl -X GET http://localhost:8000/api/v1/kicad/components/{component_id}/footprint
   ```

4. **Synchronize Library**
   ```bash
   curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
     -H "Content-Type: application/json" \
     -d '{
       "library_path": "/tmp/kicad-libs",
       "categories": ["ICs", "Resistors", "Capacitors"],
       "include_symbols": true,
       "include_footprints": true,
       "include_3d_models": false
     }'
   ```

**Expected Results**:
- KiCad-formatted component data returned
- Symbol and footprint references properly formatted
- Library synchronization creates appropriate files
- Component quantities updated based on KiCad usage

### Scenario 6: Bulk Operations and Storage Management

**Objective**: Validate bulk storage creation and component organization

**Test Steps**:

1. **Create Grid Storage Layout**
   ```bash
   # Create 5x5 grid of component boxes
   curl -X POST http://localhost:8000/api/v1/storage-locations/bulk-create \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prefix": "box",
       "layout_type": "grid",
       "parent_location_id": "{shelf_id}",
       "location_type": "box",
       "is_single_part_only": true,
       "range_1": {
         "type": "letters",
         "start": "A",
         "end": "E",
         "capitalize": true
       },
       "range_2": {
         "type": "numbers",
         "start": "1",
         "end": "5"
       },
       "separator": "-"
     }'
   ```

2. **Bulk Import Components**
   ```bash
   # Import from CSV file
   curl -X POST http://localhost:8000/api/v1/components/bulk-import \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_components.csv" \
     -F "mapping={\"name\":0,\"part_number\":1,\"manufacturer\":2,\"quantity\":3}"
   ```

3. **Generate Storage Reports**
   ```bash
   # Get storage utilization
   curl -X GET http://localhost:8000/api/v1/reports/storage-utilization

   # Get low stock report
   curl -X GET http://localhost:8000/api/v1/reports/low-stock
   ```

**Expected Results**:
- Grid layout creates 25 storage locations (A1-E5)
- Bulk import processes components correctly
- Storage utilization shows proper statistics
- Reports generate accurate data

### Scenario 7: Authentication and API Access

**Objective**: Validate authentication tiers and API token management

**Test Steps**:

1. **Anonymous Read Access**
   ```bash
   # Search without authentication (should work)
   curl -X GET http://localhost:8000/api/v1/components?search=resistor

   # Try to create component without auth (should fail)
   curl -X POST http://localhost:8000/api/v1/components \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Component"}'
   ```

2. **Admin Token Management**
   ```bash
   # Create API token
   curl -X POST http://localhost:8000/api/v1/admin/api-tokens \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "KiCad Integration Token",
       "description": "Token for KiCad plugin access",
       "scopes": ["components:read", "components:write"]
     }'

   # List API tokens
   curl -X GET http://localhost:8000/api/v1/admin/api-tokens \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **API Token Usage**
   ```bash
   # Use API token for component creation
   curl -X POST http://localhost:8000/api/v1/components \
     -H "X-API-Key: {api_token}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Component via API Token",
       "category_id": "{category_id}",
       "storage_location_id": "{location_id}"
     }'
   ```

**Expected Results**:
- Anonymous access works for read operations
- Authentication required for CRUD operations
- API tokens created and managed successfully
- API tokens provide appropriate access levels

## Performance Validation

### Response Time Tests

```bash
# Test search performance with large dataset
time curl -X GET "http://localhost:8000/api/v1/components?search=resistor&limit=100"

# Test dashboard loading
time curl -X GET http://localhost:8000/api/v1/dashboard/stats

# Test storage hierarchy loading
time curl -X GET "http://localhost:8000/api/v1/storage-locations?include_hierarchy=true"
```

**Performance Targets**:
- Component search: <500ms for queries across 10,000 components
- Dashboard statistics: <1 second
- Storage hierarchy: <300ms for up to 1,000 locations
- Component details: <200ms per component

## Data Integrity Validation

### Constraint Tests

```bash
# Test negative quantity prevention
curl -X POST http://localhost:8000/api/v1/components/{component_id}/stock \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "remove",
    "quantity_change": -1000
  }'
# Should return error if would result in negative quantity

# Test duplicate part number prevention
curl -X POST http://localhost:8000/api/v1/components \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Duplicate Test",
    "part_number": "RC0805FR-0710KL",
    "manufacturer": "Yageo",
    "category_id": "{category_id}",
    "storage_location_id": "{location_id}"
  }'
# Should return error for duplicate part number within manufacturer
```

## Cleanup

After testing, reset the system state:

```bash
# Clear test data (admin only)
curl -X DELETE http://localhost:8000/api/v1/admin/test-data \
  -H "Authorization: Bearer $TOKEN"

# Reset to initial state
curl -X POST http://localhost:8000/api/v1/admin/reset-demo-data \
  -H "Authorization: Bearer $TOKEN"
```

## Success Criteria

All scenarios must pass with:
- ✅ Correct HTTP status codes
- ✅ Valid response data structures
- ✅ Performance within targets
- ✅ Proper authentication enforcement
- ✅ Data integrity maintained
- ✅ No system errors or crashes

This quickstart guide serves as both user documentation and comprehensive integration test suite for the PartsHub MVP application.