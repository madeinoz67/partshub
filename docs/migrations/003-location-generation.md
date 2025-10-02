# Migration Guide: Storage Location Layout Generator (v1.x.x)

## Overview
Version 1.x.x introduces the Storage Location Layout Generator, a powerful feature for creating multiple storage locations using configurable layouts.

## Database Migration
```bash
cd backend
uv run --project .. alembic upgrade head
```

This migration adds a new `layout_config` JSON column to the `storage_locations` table. The column is nullable and stores the layout generation configuration for bulk-created locations.

## New Features
- Bulk location generation with 4 layout types:
  - Single
  - Row
  - Grid
  - 3D Grid
- Real-time preview generation
- Configurable location naming
- Optional parent location assignment
- Single-part location restrictions

## Endpoint Changes
### New Endpoints
- `POST /api/storage-locations/generate-preview`
- `POST /api/storage-locations/bulk-create`

### Authentication
- Preview endpoint: No authentication required
- Bulk creation: JWT authentication required

## Frontend Changes
- New "Create Bulk Locations" button in Storage Locations page
- Location generation configuration dialog
- Real-time preview generation
- Improved location management workflow

## Configuration Examples

### Row Layout
```json
{
  "layout_type": "row",
  "prefix": "shelf-",
  "ranges": [
    {"range_type": "letters", "start": "a", "end": "f"}
  ],
  "location_type": "drawer"
}
```

### Grid Layout with Parent
```json
{
  "layout_type": "grid",
  "prefix": "bin-",
  "ranges": [
    {"range_type": "letters", "start": "a", "end": "c"},
    {"range_type": "numbers", "start": 1, "end": 5}
  ],
  "parent_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_type": "bin"
}
```

## Limitations
- Maximum 500 locations per request
- Unique location names required
- Parent locations must exist
- Requires JWT authentication for bulk creation

## Upgrade Steps
1. Backup database
2. Run database migration
3. Update backend server
4. Update frontend application
5. Clear frontend cache
6. Test location generation workflow

## No Breaking Changes
- Existing functionality preserved
- Optional new features
- Backwards compatible