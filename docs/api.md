# PartsHub API Documentation

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