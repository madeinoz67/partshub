# PartsHub API Documentation

## Overview

PartsHub provides a RESTful API for electronic component inventory management. The API supports:

- **Saved Searches**: Save and reuse component search queries
- **Storage Location Layout Generation**: Bulk creation of organized storage hierarchies
- **Component Bulk Operations**: Admin-only atomic operations on multiple components
- **Stock Operations**: Add, remove, and move inventory with transaction tracking
- **Component CRUD**: Individual component management
- **Projects, Tags, and more**: Full inventory system capabilities

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: Most endpoints require JWT bearer token authentication

**Interactive Docs**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Saved Searches

**New in v0.5.0**: Save complex component search queries for quick re-execution.

### Key Features
- ✅ **User-specific searches**: Each user has isolated saved searches
- ✅ **Flexible parameters**: Save any component search criteria as JSON
- ✅ **Usage tracking**: Track when searches are executed
- ✅ **Statistics**: View usage analytics and most-used searches
- ✅ **Duplicate & modify**: Create search variations easily

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/saved-searches` | POST | Create new saved search |
| `/saved-searches` | GET | List user's saved searches (with pagination) |
| `/saved-searches/stats` | GET | Get usage statistics |
| `/saved-searches/{id}` | GET | Get specific saved search |
| `/saved-searches/{id}` | PUT | Update saved search |
| `/saved-searches/{id}` | DELETE | Delete saved search |
| `/saved-searches/{id}/execute` | POST | Execute search (updates last_used_at) |
| `/saved-searches/{id}/duplicate` | POST | Duplicate search with new name |

**📖 Complete Documentation**:
- [Saved Searches API Guide](api/saved-searches.md)
- [Saved Searches User Guide](user/saved-searches.md)
- [Frontend Integration Guide](frontend/saved-searches-integration.md)

**Quick Example**:
```bash
# Create a saved search
curl -X POST http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Low Stock Resistors",
    "description": "All resistors with stock below 10",
    "search_parameters": {
      "search": "resistor",
      "searchType": "unified",
      "limit": 20,
      "stock_status": "low"
    }
  }'

# Execute a saved search
curl -X POST http://localhost:8000/api/v1/saved-searches/{id}/execute \
  -H "Authorization: Bearer $TOKEN"
```

---

## Bulk Operations (Admin Only)

**New in v0.1.2**: Admin users can perform atomic operations on multiple components simultaneously.

### Key Features
- ✅ **Atomic transactions**: All-or-nothing (automatic rollback on any failure)
- ✅ **Concurrent modification detection**: Version-based optimistic locking
- ✅ **Admin-only access**: JWT authentication with admin role required
- ✅ **Batch operations**: Up to 1000 components per request
- ✅ **Performance optimized**: <200ms for <100 components, <500ms for 100-1000

### Available Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/components/bulk/tags/add` | POST | Add tags to multiple components | ✅ Implemented |
| `/components/bulk/tags/remove` | POST | Remove tags from multiple components | ✅ Implemented |
| `/components/bulk/tags/preview` | GET | Preview tag changes before applying | ✅ Implemented |
| `/components/bulk/projects/assign` | POST | Assign components to project | ✅ Implemented |
| `/components/bulk/delete` | POST | Delete multiple components | ✅ Implemented |
| `/components/bulk/meta-parts/add` | POST | Add to meta-part | 🚧 Stub |
| `/components/bulk/purchase-lists/add` | POST | Add to purchase list | 🚧 Stub |
| `/components/bulk/low-stock/set` | POST | Set low-stock thresholds | 🚧 Stub |
| `/components/bulk/attribution/set` | POST | Set attribution metadata | 🚧 Stub |

**📖 Complete Documentation**:
- [Bulk Operations API Guide](api/bulk-operations.md)
- [Stock Operations API Guide](api/stock-operations.md)

**Quick Example**:
```bash
# Add tags to multiple components
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component_ids": [1,2,3], "tags": ["resistor", "SMD"]}'
```

---

## Storage Location Layout Generation Endpoints

### POST /api/v1/storage-locations/generate-preview

**Description**: Generate a preview of locations without creating them.

**Authentication**: None required (read-only operation)

**Request Body**: LayoutConfiguration
- `layout_type`: "single" | "row" | "grid" | "grid_3d"
- `prefix`: Location name prefix (max 50 chars)
- `ranges`: Array of RangeSpecification objects
- `separators`: Array of separator strings (length = ranges.length - 1)
- `parent_id`: Optional UUID of parent location
- `location_type`: "bin" | "drawer" | "shelf" | "box" | "cabinet" | "room"
- `single_part_only`: Boolean (default: false)

**Response 200**: PreviewResponse
- `sample_names`: First 5 location names
- `last_name`: Last location name
- `total_count`: Total locations that would be created
- `warnings`: Array of warning messages (e.g., large batch)
- `errors`: Array of validation errors
- `is_valid`: Boolean (can proceed with creation)

**Response 422**: Validation error

### POST /api/v1/storage-locations/bulk-create-layout

**Description**: Create locations in bulk from layout configuration.

**Authentication**: **Required** (JWT token)

**Request Body**: LayoutConfiguration (same as preview)

**Response 201**: BulkCreateResponse
- `created_ids`: Array of UUIDs for created locations
- `created_count`: Number of locations created
- `success`: Boolean
- `errors`: Array of error messages (if failed)

**Response 401**: Unauthorized (no valid token)
**Response 422**: Validation error

## Data Models

### RangeSpecification
```json
{
    "range_type": "letters" | "numbers",
    "start": "string" | integer,
    "end": "string" | integer,
    "capitalize": boolean (optional),
    "zero_pad": boolean (optional)
}
```

### Example Layout Configurations

#### Single Layout (single location)
```json
{
    "layout_type": "single",
    "prefix": "warehouse-",
    "ranges": [
        {"range_type": "letters", "start": "a", "end": "a"}
    ],
    "separators": [],
    "location_type": "room"
}
```

#### Row Layout (a-f bins)
```json
{
    "layout_type": "row",
    "prefix": "box1-",
    "ranges": [{
        "range_type": "letters",
        "start": "a",
        "end": "f",
        "capitalize": true,
        "zero_pad": false
    }],
    "separators": [],
    "location_type": "bin"
}
```

#### Grid Layout (drawer grid)
```json
{
    "layout_type": "grid",
    "prefix": "drawer-",
    "ranges": [
        {"range_type": "letters", "start": "a", "end": "f"},
        {"range_type": "numbers", "start": 1, "end": 5", "zero_pad": true}
    ],
    "separators": ["-"],
    "location_type": "drawer"
}
```

#### 3D Grid Layout (complex warehouse shelving)
```json
{
    "layout_type": "grid_3d",
    "prefix": "warehouse-rack",
    "ranges": [
        {"range_type": "letters", "start": "a", "end": "c"},     // Rows
        {"range_type": "numbers", "start": 1, "end": 5"},        // Columns
        {"range_type": "letters", "start": "a", "end": "d"}      // Levels
    ],
    "separators": ["-", "-"],
    "location_type": "shelf"
}
```

### Validation and Limitations

!!! warning "Layout Generation Limits"
    - Maximum of 500 locations can be generated in a single request
    - Warning issued when generating more than 100 locations
    - Duplicate location names are prevented
    - Parent-child hierarchy must be valid
    - Location names are validated against existing records

### Error Handling

When validation fails, the API returns detailed error messages:

- `422 Unprocessable Entity`: Invalid configuration
- Errors include specific validation details (range mismatches, duplicate names, etc.)
- Some non-blocking issues return warnings in the preview response
