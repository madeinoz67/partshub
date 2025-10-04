# Quickstart: Component Bulk Operations

## Prerequisites
- PartsHub backend running on http://localhost:8000
- PartsHub frontend running on http://localhost:3000
- Admin user account with JWT token
- At least 10 components in the database

## Test Scenario 1: Bulk Add Tags (3 components)

### Setup
1. Login as admin user
2. Navigate to Components page
3. Ensure at least 3 components visible

### Steps
```bash
# 1. Get admin JWT token
export ADMIN_TOKEN="<your-admin-jwt-token>"

# 2. Get list of components
curl -X GET http://localhost:8000/api/components \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.[] | {id, part_number}' | head -3

# 3. Select 3 component IDs (replace with actual IDs)
export COMP_IDS="1,2,3"

# 4. Preview tag addition
curl -X GET "http://localhost:8000/api/components/bulk/tags/preview?component_ids=$COMP_IDS&add_tags=resistor,SMD" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.'

# 5. Add tags via bulk operation
curl -X POST http://localhost:8000/api/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3],
    "tags": ["resistor", "SMD"]
  }' \
  | jq '.'

# Expected Response:
# {
#   "success": true,
#   "affected_count": 3,
#   "errors": null
# }

# 6. Verify tags were added
curl -X GET "http://localhost:8000/api/components/1" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.tags'
```

### Frontend Verification
1. Open http://localhost:3000/components
2. Select 3 components using checkboxes
3. Click "Selected..." button
4. Choose "Add/remove tags..."
5. Enter "resistor, SMD" in "Tags to be added" field
6. Verify preview shows both tags will be added
7. Click "Add/Remove Tags"
8. Verify success notification
9. Verify tags appear on selected components
10. Verify selection is maintained after operation

**Expected**: All 3 components now have "resistor" and "SMD" user tags. Selection persists.

## Test Scenario 2: Bulk Assign to Project (5 components)

### Setup
1. Create a test project if needed
2. Have 5 components selected

### Steps
```bash
# 1. Create test project (if needed)
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "For bulk operations testing"
  }' \
  | jq '.'

export PROJECT_ID=<project_id_from_response>

# 2. Assign 5 components to project
curl -X POST http://localhost:8000/api/components/bulk/projects/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3, 4, 5],
    "project_id": '$PROJECT_ID',
    "quantities": {
      "1": 1,
      "2": 1,
      "3": 1,
      "4": 1,
      "5": 1
    }
  }' \
  | jq '.'

# Expected Response:
# {
#   "success": true,
#   "affected_count": 5,
#   "errors": null
# }

# 3. Verify project assignment
curl -X GET "http://localhost:8000/api/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.components | length'

# Expected: 5
```

### Frontend Verification
1. Select 5 components
2. Click "Selected..." → "Add to project..."
3. Select "Test Project" from dropdown
4. Adjust quantities if needed (default 1)
5. Click "Add"
6. Verify success notification
7. Verify all 5 components show "Test Project" association
8. Verify selection is maintained

**Expected**: All 5 components assigned to project with quantity 1. Selection persists.

## Test Scenario 3: Bulk Delete (8 components)

### Setup
1. Create 8 test components for deletion
2. Ensure admin privileges

### Steps
```bash
# 1. Create 8 test components
for i in {1..8}; do
  curl -X POST http://localhost:8000/api/components \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"part_number\": \"TEST-DELETE-$i\",
      \"description\": \"Test component for bulk delete\",
      \"stock\": 0
    }"
done

# 2. Get IDs of test components
curl -X GET "http://localhost:8000/api/components?part_number=TEST-DELETE" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '[.[] | .id]'

export DELETE_IDS="[1,2,3,4,5,6,7,8]"  # Replace with actual IDs

# 3. Bulk delete
curl -X POST http://localhost:8000/api/components/bulk/delete \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"component_ids\": $DELETE_IDS
  }" \
  | jq '.'

# Expected Response:
# {
#   "success": true,
#   "affected_count": 8,
#   "errors": null
# }

# 4. Verify deletion
curl -X GET "http://localhost:8000/api/components?part_number=TEST-DELETE" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq 'length'

# Expected: 0
```

### Frontend Verification
1. Select 8 test components
2. Click "Selected..." → "Delete..."
3. Confirm deletion in dialog
4. Verify success notification
5. Verify components removed from table
6. Verify selection cleared after deletion

**Expected**: All 8 components deleted. Selection cleared.

## Test Scenario 4: Selection Persistence Across Pages

### Setup
1. Have 20+ components across multiple pages
2. Page size = 10 components

### Steps (Frontend Only)
1. Navigate to Components page (page 1)
2. Select 3 components on page 1
3. Click page 2
4. Verify 3 components still shown as selected in count
5. Select 2 components on page 2
6. Verify count shows 5 selected
7. Click page 1
8. Verify original 3 components still have checkmarks
9. Click "Selected..." → "Deselect all"
10. Verify all selections cleared
11. Verify count shows 0 selected

**Expected**: Selection persists across page navigation. Deselect all clears global selection.

## Test Scenario 5: Disabled State with 0 Components Selected

### Steps (Frontend Only)
1. Navigate to Components page (as admin)
2. Ensure no components selected
3. Verify "Selected..." button is visible but grayed out
4. Click "Selected..." button (should not open menu)
5. Select 1 component
6. Verify "Selected..." button becomes enabled (not grayed)
7. Click "Selected..." button
8. Verify dropdown menu opens

**Expected**: Button disabled when 0 selected, enabled when ≥1 selected.

## Test Scenario 6: Rollback on Partial Failure

### Setup
1. Have 5 components in database
2. One component to be modified concurrently

### Steps
```bash
# 1. Start bulk operation in one terminal
export COMP_IDS="[1,2,3,4,5]"
curl -X POST http://localhost:8000/api/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"component_ids\": $COMP_IDS,
    \"tags\": [\"test-rollback\"]
  }" &

# 2. Immediately modify component 3 in another terminal (concurrent modification)
curl -X PATCH http://localhost:8000/api/components/3 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Modified concurrently"}' &

# Wait for both requests

# 3. Check bulk operation response
# Expected Response:
# {
#   "success": false,
#   "affected_count": 0,
#   "errors": [
#     {
#       "component_id": 3,
#       "component_name": "...",
#       "error_message": "Component modified by another user",
#       "error_type": "concurrent_modification"
#     }
#   ]
# }

# 4. Verify no components have the tag (rollback successful)
for id in 1 2 3 4 5; do
  curl -X GET "http://localhost:8000/api/components/$id" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    | jq '.tags[] | select(.name == "test-rollback")'
done

# Expected: No output (tag not added to any component)
```

**Expected**: Concurrent modification detected, all changes rolled back, detailed error report shown.

## Non-Admin User Test

### Setup
1. Login as non-admin user
2. Navigate to Components page

### Steps (Frontend Only)
1. Verify no checkboxes visible on component rows
2. Verify no "Selected..." button visible
3. Verify no header checkbox visible

### Steps (API)
```bash
# 1. Get non-admin token
export USER_TOKEN="<non-admin-jwt-token>"

# 2. Attempt bulk operation
curl -X POST http://localhost:8000/api/components/bulk/tags/add \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3],
    "tags": ["test"]
  }'

# Expected Response: 403 Forbidden
# {
#   "detail": "Admin privileges required for bulk operations"
# }
```

**Expected**: Non-admin users cannot access bulk operations (403 error). UI hidden for non-admins.

## Performance Validation

### Load Test (100 components)
```bash
# 1. Create 100 test components
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/api/components \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"part_number\": \"PERF-TEST-$i\",
      \"description\": \"Performance test component\",
      \"stock\": 10
    }" > /dev/null
done

# 2. Get IDs
PERF_IDS=$(curl -s -X GET "http://localhost:8000/api/components?part_number=PERF-TEST" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '[.[] | .id]')

# 3. Measure bulk tag operation time
time curl -X POST http://localhost:8000/api/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"component_ids\": $PERF_IDS,
    \"tags\": [\"performance-test\"]
  }"

# Expected: <200ms (per performance goal)
```

### Load Test (1000 components)
```bash
# Similar to above, with 1000 components
# Expected: <500ms (per performance goal)
```

## Cleanup
```bash
# Delete all test data
curl -X DELETE "http://localhost:8000/api/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

curl -X POST http://localhost:8000/api/components/bulk/delete \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"component_ids\": [list of all test component IDs]
  }"
```

## Success Criteria
- ✅ All 6 test scenarios pass
- ✅ Non-admin users blocked from bulk operations
- ✅ Selection persists across page navigation
- ✅ Atomic transactions work (all-or-nothing)
- ✅ Concurrent modification detected and rolled back
- ✅ Performance goals met (<200ms for <100, <500ms for 100-1000)
- ✅ Admin-only UI controls work correctly
- ✅ All OpenAPI contracts validated
