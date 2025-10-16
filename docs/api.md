# PartsHub API Documentation

## Overview

PartsHub provides a RESTful API for electronic component inventory management. The API supports:

- **Natural Language Search**: Search components using plain English queries
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

## Natural Language Search

**Latest Feature**: Search for components using conversational queries like "find resistors with low stock" or "capacitors in location A1".

### Key Features
- ✅ **Plain English queries**: Use natural language instead of complex filters
- ✅ **Confidence scoring**: Visual feedback on how well the query was understood
- ✅ **Smart fallback**: Automatically uses full-text search for ambiguous queries
- ✅ **Multi-entity support**: Combine multiple filters in one query
- ✅ **Intent classification**: Understands different query types (search, filter, etc.)
- ✅ **No external dependencies**: Pattern-based parsing with no API calls required

### Endpoint

```
GET /api/v1/components?nl_query={query}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nl_query` | string | No | Natural language query string |
| `limit` | integer | No | Number of results (1-100, default: 50) |
| `offset` | integer | No | Pagination offset (default: 0) |
| `sort_by` | string | No | Sort field (default: "updated_at") |
| `sort_order` | string | No | Sort order "asc" or "desc" (default: "desc") |

**Note:** Manual filter parameters (category, stock_status, component_type, etc.) can be combined with `nl_query`. Manual parameters always take priority over parsed parameters.

### Response Structure

```json
{
  "components": [
    {
      "id": "uuid",
      "name": "10kΩ Resistor",
      "component_type": "resistor",
      "stock_status": "low",
      "quantity_on_hand": 5,
      "storage_location": {
        "id": "uuid",
        "name": "A1",
        "location_hierarchy": "Cabinet > Drawer A > Bin 1"
      },
      ...
    }
  ],
  "total": 42,
  "page": 1,
  "total_pages": 3,
  "limit": 20,
  "nl_metadata": {
    "query": "resistors with low stock in A1",
    "confidence": 0.87,
    "parsed_entities": {
      "component_type": "resistor",
      "stock_status": "low",
      "location": "A1"
    },
    "fallback_to_fts5": false,
    "intent": "search_by_type"
  }
}
```

### NL Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original natural language query |
| `confidence` | float | Parsing confidence (0.0-1.0) |
| `parsed_entities` | object | Extracted filter parameters |
| `fallback_to_fts5` | boolean | Whether FTS5 fallback was used |
| `intent` | string | Classified query intent |
| `error` | string | Error message if parsing failed (optional) |

### Supported Query Patterns

#### 1. Search by Component Type
```bash
# Find all resistors
curl -X GET "http://localhost:8000/api/v1/components?nl_query=find%20resistors"

# List capacitors
curl -X GET "http://localhost:8000/api/v1/components?nl_query=show%20capacitors"
```

#### 2. Filter by Stock Status
```bash
# Components with low stock
curl -X GET "http://localhost:8000/api/v1/components?nl_query=low%20stock%20items"

# Out of stock parts
curl -X GET "http://localhost:8000/api/v1/components?nl_query=out%20of%20stock%20parts"
```

#### 3. Filter by Location
```bash
# Components in location A1
curl -X GET "http://localhost:8000/api/v1/components?nl_query=components%20in%20A1"

# Parts stored in Bin-23
curl -X GET "http://localhost:8000/api/v1/components?nl_query=parts%20in%20Bin-23"
```

#### 4. Filter by Value/Specifications
```bash
# 10k resistors
curl -X GET "http://localhost:8000/api/v1/components?nl_query=10k%20resistors"

# 100μF capacitors
curl -X GET "http://localhost:8000/api/v1/components?nl_query=100uF%20capacitors"

# 0805 SMD components
curl -X GET "http://localhost:8000/api/v1/components?nl_query=0805%20SMD%20components"
```

#### 5. Filter by Price
```bash
# Components under $5
curl -X GET "http://localhost:8000/api/v1/components?nl_query=components%20under%20%245"

# Cheap resistors
curl -X GET "http://localhost:8000/api/v1/components?nl_query=cheap%20resistors"
```

#### 6. Multi-Entity Queries
```bash
# 10k SMD resistors with low stock
curl -X GET "http://localhost:8000/api/v1/components?nl_query=10k%20SMD%20resistors%20with%20low%20stock"

# Capacitors in A1 under $1
curl -X GET "http://localhost:8000/api/v1/components?nl_query=capacitors%20in%20A1%20under%20%241"

# Available 5V regulators
curl -X GET "http://localhost:8000/api/v1/components?nl_query=available%205V%20regulators"
```

### Recognized Entities

The system can extract these entity types from natural language queries:

| Entity Type | Examples |
|-------------|----------|
| Component Type | resistor, capacitor, led, transistor, ic, diode, connector |
| Stock Status | low stock, out of stock, available, unused, need reorder |
| Location | A1, Bin-23, Shelf-A, in Cabinet-1 |
| Resistance | 10kΩ, 4.7k, 100Ω, 1M |
| Capacitance | 100μF, 10nF, 1pF |
| Voltage | 5V, 3.3V, 12V |
| Package | 0805, 1206, DIP8, SOT-23, SMD, THT |
| Manufacturer | Texas Instruments, Murata, Vishay |
| Price | under $5, less than $10, between $1 and $5, cheap |

### Intent Types

| Intent | Description | Example |
|--------|-------------|---------|
| `search_by_type` | Finding components by type | "find resistors" |
| `filter_by_stock` | Filtering by stock status | "low stock items" |
| `filter_by_location` | Filtering by location | "parts in A1" |
| `filter_by_value` | Filtering by specifications | "10k resistors" |
| `filter_by_price` | Filtering by price | "cheap capacitors" |

### Confidence Levels

- **High (0.8-1.0)**: Green indicator, query well understood
- **Medium (0.5-0.79)**: Orange indicator, partial understanding
- **Low (<0.5)**: Red indicator, falls back to full-text search

### Example Workflow

```bash
# 1. Simple query
curl -X GET "http://localhost:8000/api/v1/components?nl_query=resistors" \
  -H "accept: application/json"

# Response includes metadata
{
  "components": [...],
  "total": 150,
  "nl_metadata": {
    "query": "resistors",
    "confidence": 0.75,
    "parsed_entities": {"component_type": "resistor"},
    "fallback_to_fts5": false,
    "intent": "search_by_type"
  }
}

# 2. Complex multi-entity query
curl -X GET "http://localhost:8000/api/v1/components?nl_query=10k%20SMD%20resistors%20with%20low%20stock%20in%20A1" \
  -H "accept: application/json"

# Response with multiple extracted entities
{
  "components": [...],
  "total": 5,
  "nl_metadata": {
    "query": "10k SMD resistors with low stock in A1",
    "confidence": 0.92,
    "parsed_entities": {
      "component_type": "resistor",
      "stock_status": "low",
      "location": "A1",
      "resistance": "10kΩ",
      "package": "SMD"
    },
    "fallback_to_fts5": false,
    "intent": "search_by_type"
  }
}

# 3. Combining NL query with manual filters
curl -X GET "http://localhost:8000/api/v1/components?nl_query=low%20stock%20parts&category=passive" \
  -H "accept: application/json"

# Manual 'category' parameter overrides any parsed category
```

### Error Handling

**Empty Query:**
```json
{
  "components": [],
  "total": 0,
  "nl_metadata": {
    "query": "",
    "confidence": 0.0,
    "fallback_to_fts5": true,
    "parsed_entities": {}
  }
}
```

**Low Confidence (FTS5 Fallback):**
```json
{
  "components": [...],
  "total": 10,
  "nl_metadata": {
    "query": "show me stuff",
    "confidence": 0.30,
    "fallback_to_fts5": true,
    "parsed_entities": {},
    "intent": "search_by_type"
  }
}
```

### Performance

- **Parsing:** <50ms (typical: 10-30ms)
- **Search:** 50-500ms depending on result set size
- **No external API calls:** All processing done locally

**📖 Complete Documentation**: [Natural Language Search Guide](features/search.md)

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
