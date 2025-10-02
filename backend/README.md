# PartsHub Backend

## Storage Location Layout Generator

### Overview
The Storage Location Layout Generator allows bulk creation of storage locations using configurable layouts. Supports row, grid, and 3D grid generation with extensive customization.

### API Endpoints

#### Generate Location Preview
`POST /api/storage-locations/generate-preview`

Preview storage locations before creation. No authentication required.

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/storage-locations/generate-preview \
     -H "Content-Type: application/json" \
     -d '{
         "layout_type": "grid",
         "prefix": "shelf-",
         "ranges": [
             {"range_type": "letters", "start": "a", "end": "c"},
             {"range_type": "numbers", "start": 1, "end": 5}
         ],
         "separators": ["-"],
         "location_type": "drawer",
         "single_part_only": false
     }'
```

#### Bulk Create Locations
`POST /api/storage-locations/bulk-create`

Create multiple storage locations. Requires JWT authentication.

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/storage-locations/bulk-create \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
         "layout_type": "grid",
         "prefix": "bin-",
         "ranges": [
             {"range_type": "letters", "start": "a", "end": "c"},
             {"range_type": "numbers", "start": 1, "end": 5}
         ],
         "separators": ["-"],
         "location_type": "bin",
         "parent_id": "550e8400-e29b-41d4-a716-446655440000",
         "single_part_only": true
     }'
```

### Layout Types
- `single`: No range generation
- `row`: Linear generation along single range
- `grid`: Generation along two ranges
- `grid_3d`: Generation across three ranges

### Configuration Parameters
- `layout_type`: Type of layout generation
- `prefix`: Common prefix for all locations
- `ranges`: 1-3 range specifications
- `separators`: Optional separators between range components
- `location_type`: Type of storage location
- `parent_id`: Optional parent location UUID
- `single_part_only`: Restrict location to single-part storage

### Limitations
- Maximum 500 locations per request
- Requires unique location names
- Parent locations must exist

### Functional Requirements
- Supports various location generation strategies
- Real-time preview generation
- Transaction-based creation (all-or-nothing)
- Comprehensive error handling

### See Also
- [Quickstart Guide](/specs/003-location-improvements-as/quickstart.md)
- [Location Layout Contracts](/specs/003-location-improvements-as/contracts/location-layout-api.yaml)