# Quickstart: Storage Location Layout Generator

**Feature**: 003-location-improvements-as
**Purpose**: Validate that the feature works end-to-end by executing all user scenarios from the spec.

## Prerequisites

- Backend server running: `make dev` or `cd backend && uv run --project .. uvicorn src.main:app`
- Frontend server running: `cd frontend && npm run dev`
- Database initialized with migrations: `cd backend && uv run --project .. alembic upgrade head`
- Authenticated user account (or ability to create one)

## Test Scenarios (From Spec)

### Scenario 1: Row Layout Creation (FR-002)

**User Story**: Create 6 storage bins with letter sequence naming.

**Steps**:
1. Navigate to Storage Locations page
2. Click "Create" button
3. Select "Row" layout tab
4. Enter configuration:
   - Prefix: `box1-`
   - Range Type: Letters
   - Start: `a`
   - End: `f`
   - Location Type: Bin
5. Observe preview: Shows `box1-a, box1-b, box1-c, box1-d, box1-e` (first 5) and `box1-f` (last)
6. Click "Create Locations"
7. Verify success notification: "6 locations created"
8. Verify locations appear in tree: `box1-a` through `box1-f`

**Expected Result**: ✅ 6 bin locations created with letter-based naming

**API Equivalent**:
```bash
# Preview
curl -X POST http://localhost:8000/api/storage-locations/generate-preview \
  -H "Content-Type: application/json" \
  -d '{
    "layout_type": "row",
    "prefix": "box1-",
    "ranges": [{"range_type": "letters", "start": "a", "end": "f"}],
    "separators": [],
    "location_type": "bin",
    "single_part_only": false
  }'

# Create (requires auth token)
curl -X POST http://localhost:8000/api/storage-locations/bulk-create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "layout_type": "row",
    "prefix": "box1-",
    "ranges": [{"range_type": "letters", "start": "a", "end": "f"}],
    "separators": [],
    "location_type": "bin",
    "single_part_only": false
  }'
```

---

### Scenario 2: Grid Layout with Preview (FR-003, FR-013)

**User Story**: Create 30 drawer locations in a 6×5 grid pattern.

**Steps**:
1. Click "Create" button
2. Select "Grid" layout tab
3. Enter configuration:
   - Prefix: `drawer-`
   - Row Range: Letters `a` to `f` (6 rows)
   - Column Range: Numbers `1` to `5` (5 columns)
   - Separator: `-`
   - Location Type: Drawer
4. Observe preview:
   - Sample names: `drawer-a-1, drawer-a-2, drawer-a-3, drawer-a-4, drawer-a-5`
   - Last name: `drawer-f-5`
   - Total count: `30`
5. Click "Create Locations"
6. Verify all 30 locations created

**Expected Result**: ✅ 30 drawer locations in grid pattern (a1-f5)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/storage-locations/bulk-create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "layout_type": "grid",
    "prefix": "drawer-",
    "ranges": [
      {"range_type": "letters", "start": "a", "end": "f"},
      {"range_type": "numbers", "start": 1, "end": 5}
    ],
    "separators": ["-"],
    "location_type": "drawer",
    "single_part_only": false
  }'
```

---

### Scenario 3: 3D Grid Layout (FR-004)

**User Story**: Create warehouse locations with aisle-shelf-bin structure.

**Steps**:
1. Click "Create" button
2. Select "3D Grid" layout tab
3. Enter configuration:
   - Prefix: `warehouse-`
   - Aisle Range: Letters `a` to `c` (3 aisles)
   - Shelf Range: Numbers `1` to `4` (4 shelves)
   - Bin Range: Numbers `1` to `3` (3 bins)
   - Separator 1: `-`
   - Separator 2: `.`
   - Location Type: Bin
4. Observe preview:
   - Sample: `warehouse-a-1.1, warehouse-a-1.2, warehouse-a-1.3, warehouse-a-2.1, warehouse-a-2.2`
   - Last: `warehouse-c-4.3`
   - Total: `36` (3×4×3)
5. Click "Create Locations"
6. Verify 36 locations created

**Expected Result**: ✅ 36 bin locations in 3D grid (a-1.1 to c-4.3)

---

### Scenario 4: Warning for Large Batch (FR-009)

**User Story**: User warned when creating 100+ locations.

**Steps**:
1. Click "Create" button
2. Configure grid:
   - Prefix: `big-`
   - Rows: `a` to `f` (6)
   - Columns: `1` to `25` (25)
   - Total: 150 locations
3. Observe preview shows warning:
   - ⚠️ "Creating 150 locations cannot be undone. Locations cannot be deleted."
4. Preview is valid (is_valid: true)
5. User can proceed to create

**Expected Result**: ✅ Warning shown but creation allowed

---

### Scenario 5: Error for Exceeding Limit (FR-008)

**User Story**: User prevented from creating >500 locations.

**Steps**:
1. Click "Create" button
2. Configure grid:
   - Prefix: `toolarge-`
   - Rows: `a` to `z` (26)
   - Columns: `1` to `30` (30)
   - Total: 780 locations
3. Observe preview shows error:
   - ❌ "Total location count (780) exceeds maximum limit of 500"
   - is_valid: false
4. "Create Locations" button disabled

**Expected Result**: ✅ Creation blocked, clear error message

---

### Scenario 6: Invalid Range Validation (FR-019)

**User Story**: User corrected when start > end.

**Steps**:
1. Click "Create" button
2. Enter row configuration:
   - Prefix: `invalid-`
   - Range: Letters `z` to `a` (reversed)
3. Observe validation error:
   - ❌ "Start value must be less than or equal to end value"
   - Preview shows 0 locations
4. Correct to `a` to `z`
5. Preview updates to show valid configuration

**Expected Result**: ✅ Inline validation prevents invalid ranges

---

### Scenario 7: Duplicate Prevention (FR-007)

**User Story**: User prevented from creating locations with existing names.

**Steps**:
1. Create initial locations:
   - Prefix: `test-`
   - Range: `a` to `c`
   - Success: 3 locations created
2. Attempt to create same locations again:
   - Same configuration
3. Observe error:
   - ❌ "Duplicate location names: test-a, test-b, test-c"
   - created_count: 0
4. No locations created (transaction rolled back)

**Expected Result**: ✅ Duplicates prevented, clear error message

---

### Scenario 8: Parent Location Assignment (FR-014)

**User Story**: Create child locations under a parent.

**Steps**:
1. Create parent location:
   - Layout: Single
   - Name: `cabinet-1`
   - Type: Cabinet
2. Create child locations:
   - Layout: Row
   - Prefix: `drawer-`
   - Range: `a` to `d`
   - **Parent: Select `cabinet-1`**
   - Type: Drawer
3. Verify locations created under parent in hierarchy tree
4. Expand `cabinet-1` → see `drawer-a, drawer-b, drawer-c, drawer-d`

**Expected Result**: ✅ Child locations correctly nested under parent

---

### Scenario 9: Single-Part Only Flag (FR-015)

**User Story**: Mark locations for single-part storage.

**Steps**:
1. Create locations with single-part flag:
   - Prefix: `singlepart-`
   - Range: `a` to `c`
   - ✅ Check "Mark as single-part only"
2. Create locations
3. Verify locations have single-part designation
   - (Implementation detail: check via GET endpoint or database)

**Expected Result**: ✅ single_part_only flag persisted correctly

---

### Scenario 10: Zero-Padding for Numbers (FR-011)

**User Story**: Create numbered locations with zero-padding.

**Steps**:
1. Create locations:
   - Prefix: `bin-`
   - Range: Numbers `1` to `15`
   - ✅ Enable "Zero-pad numbers"
2. Observe preview:
   - Sample: `bin-01, bin-02, bin-03, bin-04, bin-05`
   - Last: `bin-15`
3. Create locations
4. Verify zero-padded names

**Expected Result**: ✅ Numbers formatted as `01, 02, ..., 15`

---

### Scenario 11: Letter Capitalization (FR-010)

**User Story**: Create locations with uppercase letters.

**Steps**:
1. Create locations:
   - Prefix: `BIN-`
   - Range: Letters `a` to `c`
   - ✅ Enable "Capitalize letters"
2. Observe preview:
   - Sample: `BIN-A, BIN-B, BIN-C`
3. Create locations
4. Verify capitalized letters

**Expected Result**: ✅ Letters formatted as uppercase

---

## Integration Test Checklist

Run these tests to verify complete functionality:

### Backend Tests
```bash
cd backend

# Run contract tests (should PASS after implementation)
uv run --project .. pytest tests/contract/test_location_generation_api.py -v

# Run integration tests
uv run --project .. pytest tests/integration/test_location_generation.py -v

# Run unit tests
uv run --project .. pytest tests/unit/test_location_generator.py -v

# Check coverage (minimum 80%)
uv run --project .. pytest --cov=src --cov-report=term-missing
```

### Frontend Tests
```bash
cd frontend

# Run component tests
npm test -- LocationLayoutDialog.test.ts

# Run E2E tests (if implemented)
npm run test:e2e
```

### Manual Verification

- [ ] All 11 scenarios above pass
- [ ] Locations appear in hierarchy tree immediately after creation
- [ ] Preview updates in <300ms after input change (debounced)
- [ ] Preview API responds in <200ms for 500-location config
- [ ] Bulk create completes in <2s for 500 locations
- [ ] Authentication required for bulk create (401 without token)
- [ ] Anonymous users cannot access create dialog (read-only)
- [ ] Error messages are clear and actionable
- [ ] Success notification shows created count
- [ ] Transaction rollback works (duplicates create 0 locations)

---

## Performance Validation

### Preview Endpoint Performance
```bash
# Measure preview response time for 500-location config
time curl -X POST http://localhost:8000/api/storage-locations/generate-preview \
  -H "Content-Type: application/json" \
  -d '{
    "layout_type": "grid",
    "prefix": "perf-",
    "ranges": [
      {"range_type": "letters", "start": "a", "end": "z"},
      {"range_type": "numbers", "start": 1, "end": 19}
    ],
    "separators": ["-"],
    "location_type": "bin",
    "single_part_only": false
  }'

# Expected: <200ms response time
```

### Bulk Create Performance
```bash
# Measure bulk create time for 500 locations
time curl -X POST http://localhost:8000/api/storage-locations/bulk-create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "layout_type": "grid",
    "prefix": "bulk-",
    "ranges": [
      {"range_type": "letters", "start": "a", "end": "z"},
      {"range_type": "numbers", "start": 1, "end": 19}
    ],
    "separators": ["-"],
    "location_type": "bin",
    "single_part_only": false
  }'

# Expected: <2s total time
```

---

## Database Audit Verification

Verify layout_config is persisted correctly:

```sql
-- Check layout_config field exists and contains valid JSON
SELECT
  id,
  name,
  layout_config->>'layout_type' as layout_type,
  layout_config->>'prefix' as prefix,
  layout_config
FROM storage_locations
WHERE layout_config IS NOT NULL
LIMIT 10;

-- Verify parent-child relationships
SELECT
  parent.name as parent_name,
  child.name as child_name
FROM storage_locations parent
JOIN storage_locations child ON child.parent_id = parent.id
WHERE parent.name = 'cabinet-1';
```

---

## Success Criteria

All scenarios pass ✅ AND:
- [ ] Zero test failures
- [ ] 80%+ code coverage
- [ ] All API endpoints documented in OpenAPI
- [ ] Preview response time <200ms
- [ ] Bulk create time <2s for 500 locations
- [ ] No duplicate locations created
- [ ] Transaction rollback works correctly
- [ ] Authentication enforced for mutations
- [ ] Anonymous users have read-only access
- [ ] Layout config audit trail persisted

**Status**: Ready for implementation (TDD cycle)
