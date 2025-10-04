# Data Model: Storage Location Layout Generator

**Feature**: 003-location-improvements-as
**Date**: 2025-10-02

## Entity Definitions

### 1. LayoutConfiguration (Request Schema)

**Purpose**: Defines parameters for generating storage locations with various layout types.

**Fields**:
- `layout_type`: LayoutType enum - Type of layout (single, row, grid, grid_3d)
- `prefix`: str - Prefix for all generated location names (max 50 chars)
- `ranges`: List[RangeSpecification] - Ordered list of ranges defining dimensions
- `separators`: List[str] - Separators between range components (empty for row, 1 for grid, 2 for 3d)
- `parent_id`: Optional[str] - UUID of parent location (if creating children)
- `location_type`: LocationType enum - Type for all generated locations (bin, drawer, shelf, etc.)
- `single_part_only`: bool - Whether locations can hold only one part (default: False)

**Validation Rules**:
- layout_type determines ranges length: single=0, row=1, grid=2, grid_3d=3
- separators length must be len(ranges) - 1 (except single which needs 0)
- prefix must not contain separator characters
- Total generated locations ≤ 500 (calculated from ranges)
- parent_id must exist if provided

**State Transitions**: N/A (stateless request model)

---

### 2. RangeSpecification (Component Schema)

**Purpose**: Defines a single dimension in multi-dimensional layout.

**Fields**:
- `range_type`: RangeType enum - Type of range (letters or numbers)
- `start`: Union[str, int] - Start value (single char for letters, int 0-999 for numbers)
- `end`: Union[str, int] - End value (single char for letters, int 0-999 for numbers)
- `capitalize`: Optional[bool] - Capitalize letters (letters only, default: False)
- `zero_pad`: Optional[bool] - Zero-pad numbers to match end length (numbers only, default: False)

**Validation Rules**:
- If range_type=letters: start/end must be single alphabetic characters, start ≤ end (a-z order)
- If range_type=numbers: start/end must be 0-999, start ≤ end
- capitalize only valid for letters range_type
- zero_pad only valid for numbers range_type

**Examples**:
```json
// Letters a-f
{"range_type": "letters", "start": "a", "end": "f", "capitalize": false}

// Numbers 1-10 with zero-padding
{"range_type": "numbers", "start": 1, "end": 10, "zero_pad": true}
// Generates: 01, 02, 03, ..., 10
```

---

### 3. PreviewResponse (Response Schema)

**Purpose**: Preview of locations to be generated without creating them.

**Fields**:
- `sample_names`: List[str] - First 5 generated names
- `last_name`: str - Last generated name
- `total_count`: int - Total number of locations that would be created
- `warnings`: List[str] - Warning messages (e.g., "Creating 150 locations cannot be undone")
- `errors`: List[str] - Validation errors preventing creation
- `is_valid`: bool - Whether configuration is valid for creation

**Business Rules**:
- sample_names limited to 5 items for performance
- warnings triggered when total_count > 100 (FR-009)
- errors include duplicate detection, range validation, limit exceeded
- is_valid = len(errors) == 0

---

### 4. BulkCreateResponse (Response Schema)

**Purpose**: Result of bulk location creation operation.

**Fields**:
- `created_ids`: List[str] - UUIDs of successfully created locations
- `created_count`: int - Number of locations created
- `success`: bool - Whether operation succeeded
- `errors`: Optional[List[str]] - Errors if operation failed

**Business Rules**:
- Transactional: created_count == len(created_ids) or both are 0 (rollback on failure)
- success = created_count > 0
- errors populated only if success = False

---

### 5. StorageLocation (Database Model Extension)

**Purpose**: Existing model extended to store layout generation metadata.

**New Field**:
- `layout_config`: Optional[JSONB] - Persisted layout configuration for audit

**JSONB Structure**:
```json
{
  "layout_type": "grid",
  "prefix": "box1-",
  "ranges": [
    {"type": "letters", "start": "a", "end": "f"},
    {"type": "numbers", "start": 1, "end": 5}
  ],
  "separators": ["-"],
  "parent_id": "uuid-here",
  "location_type": "bin",
  "single_part_only": false,
  "created_at": "2025-10-02T10:30:00Z"
}
```

**Relationships**:
- parent_id (existing): FK to storage_locations.id (self-referential)
- Components: Many-to-many through component_storage (existing)

**Indexes**:
- name (existing): UNIQUE index for duplicate prevention
- parent_id (existing): Index for hierarchy queries
- layout_config (new): GIN index for JSONB queries (optional, for future search)

---

## Enumerations

### LayoutType
```python
class LayoutType(str, Enum):
    SINGLE = "single"      # One location with name = prefix
    ROW = "row"           # 1D: prefix + range[0]
    GRID = "grid"         # 2D: prefix + range[0] + sep[0] + range[1]
    GRID_3D = "grid_3d"   # 3D: prefix + range[0] + sep[0] + range[1] + sep[1] + range[2]
```

### RangeType
```python
class RangeType(str, Enum):
    LETTERS = "letters"   # a-z ranges
    NUMBERS = "numbers"   # 0-999 ranges
```

### LocationType (existing, reused)
```python
class LocationType(str, Enum):
    BIN = "bin"
    DRAWER = "drawer"
    SHELF = "shelf"
    BOX = "box"
    CABINET = "cabinet"
    ROOM = "room"
```

---

## Relationships & Constraints

### LayoutConfiguration → RangeSpecification
- **Relationship**: Composition (1:N)
- **Cardinality**: 0-3 ranges depending on layout_type
- **Constraint**: len(ranges) must match layout_type requirements

### LayoutConfiguration → StorageLocation (parent_id)
- **Relationship**: Optional foreign key
- **Cardinality**: 0:1 (one optional parent)
- **Constraint**: parent_id must exist in storage_locations

### BulkCreate → StorageLocation
- **Relationship**: Creates N storage locations transactionally
- **Cardinality**: 1:N (1 config → N locations)
- **Constraint**: All-or-nothing transaction (rollback on any failure)

---

## Database Migration

### Migration: `add_layout_config_to_storage_locations`

```sql
-- Up migration
ALTER TABLE storage_locations
ADD COLUMN layout_config JSONB NULL;

-- Optional: Add GIN index for future JSONB queries
CREATE INDEX idx_storage_locations_layout_config
ON storage_locations USING GIN (layout_config);

-- Down migration
DROP INDEX IF EXISTS idx_storage_locations_layout_config;
ALTER TABLE storage_locations
DROP COLUMN layout_config;
```

**Impact Analysis**:
- Existing rows: layout_config will be NULL (backward compatible)
- No data migration needed
- Nullable column allows gradual adoption
- Index creation is non-blocking (CONCURRENTLY in PostgreSQL)

---

## Validation Matrix

| Field | Schema Validation | Business Logic Validation | Database Validation |
|-------|-------------------|---------------------------|---------------------|
| layout_type | Enum membership | Matches ranges/separators length | N/A |
| prefix | String, max 50 chars | No separator chars | N/A |
| ranges | List[RangeSpec], length 0-3 | Total product ≤ 500 | N/A |
| start/end | Type per range_type | start ≤ end | N/A |
| parent_id | Valid UUID format | Exists in DB | FK constraint |
| location names | Generated strings | No duplicates in batch | UNIQUE constraint |

---

## Example Scenarios

### Scenario 1: Row Layout (FR-002)
**Input**:
```json
{
  "layout_type": "row",
  "prefix": "box1-",
  "ranges": [
    {"range_type": "letters", "start": "a", "end": "f"}
  ],
  "separators": [],
  "location_type": "bin"
}
```

**Generated Names**: `box1-a`, `box1-b`, `box1-c`, `box1-d`, `box1-e`, `box1-f`
**Total Count**: 6

### Scenario 2: Grid Layout (FR-003)
**Input**:
```json
{
  "layout_type": "grid",
  "prefix": "shelf-",
  "ranges": [
    {"range_type": "letters", "start": "a", "end": "c"},
    {"range_type": "numbers", "start": 1, "end": 5, "zero_pad": false}
  ],
  "separators": ["-"],
  "location_type": "drawer"
}
```

**Generated Names**: `shelf-a-1`, `shelf-a-2`, ..., `shelf-c-5`
**Total Count**: 15 (3 letters × 5 numbers)

### Scenario 3: 3D Grid Layout (FR-004)
**Input**:
```json
{
  "layout_type": "grid_3d",
  "prefix": "warehouse-",
  "ranges": [
    {"range_type": "letters", "start": "a", "end": "b"},
    {"range_type": "numbers", "start": 1, "end": 3},
    {"range_type": "numbers", "start": 1, "end": 2}
  ],
  "separators": ["-", "."],
  "location_type": "bin"
}
```

**Generated Names**: `warehouse-a-1.1`, `warehouse-a-1.2`, `warehouse-a-2.1`, ..., `warehouse-b-3.2`
**Total Count**: 12 (2 letters × 3 numbers × 2 numbers)

---

## Performance Considerations

### Space Complexity
- **Preview generation**: O(5) - Only first 5 + last 1 stored
- **Bulk creation**: O(N) where N ≤ 500 - All locations in memory before commit
- **JSONB storage**: ~200-500 bytes per layout_config (negligible)

### Time Complexity
- **Range iteration**: O(N) where N = product of all ranges
- **Duplicate check**: O(M) where M = existing location count (indexed query)
- **Bulk insert**: O(N) with transaction overhead

### Query Optimization
- Use `storage_locations.name` index for duplicate detection
- Batch insert in single transaction (reduces commit overhead)
- JSONB index optional (future optimization for audit queries)

---

**Status**: ✅ Complete
**Validation**: All entities map to functional requirements FR-001 through FR-024
