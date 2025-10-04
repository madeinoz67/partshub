# Bulk Operations API

The Bulk Operations API allows admin users to perform actions on multiple components simultaneously using atomic transactions.

## Base URL

All bulk operation endpoints are prefixed with:

```
/api/v1/components/bulk
```

## Authentication

**Required**: All endpoints require admin authentication via JWT bearer token.

```http
Authorization: Bearer <your-admin-jwt-token>
```

### Error Responses

- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: Valid token but user is not an admin
- **400 Bad Request**: Invalid request body or parameters
- **409 Conflict**: Concurrent modification detected (operation rolled back)

## Atomic Transactions

All bulk operations use **atomic transactions**:

- **All-or-nothing**: Either ALL components are updated successfully, or NONE are
- **Automatic rollback**: If any component fails, the entire operation is rolled back
- **Error reporting**: Detailed error information is returned on failure

## Endpoints

### POST /tags/add

Add tags to multiple components atomically.

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "tags": ["resistor", "SMD"]
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `tags` (array of strings, required): Tag names to add (min 1)

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Response** (409 Conflict - Concurrent Modification):

```json
{
  "success": false,
  "affected_count": 0,
  "errors": [
    {
      "component_id": 2,
      "component_name": "RES-10K-0805",
      "error_message": "Component modified by another user",
      "error_type": "concurrent_modification"
    }
  ]
}
```

**Behavior**:
- Creates new Tag records if they don't exist
- Idempotent: If a component already has a tag, it won't be duplicated
- All operations succeed or all are rolled back

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3],
    "tags": ["resistor", "SMD"]
  }'
```

---

### POST /tags/remove

Remove tags from multiple components atomically.

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "tags": ["obsolete", "temp"]
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `tags` (array of strings, required): Tag names to remove (min 1)

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Behavior**:
- Removes tag associations from components
- If a component doesn't have a specified tag, it's skipped (no error)
- All operations succeed or all are rolled back

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/remove \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3],
    "tags": ["obsolete"]
  }'
```

---

### GET /tags/preview

Preview the result of tag operations before applying them.

**Query Parameters**:
- `component_ids` (string, required): Comma-separated component IDs (e.g., "1,2,3")
- `tags_to_add` (string, optional): Comma-separated tags to add (e.g., "resistor,SMD")
- `tags_to_remove` (string, optional): Comma-separated tags to remove (e.g., "obsolete")

**Response** (200 OK):

```json
{
  "components": [
    {
      "component_id": 1,
      "component_name": "RES-10K-0805",
      "current_tags": ["resistor"],
      "resulting_tags": ["resistor", "SMD"]
    },
    {
      "component_id": 2,
      "component_name": "CAP-10UF-0603",
      "current_tags": ["capacitor", "obsolete"],
      "resulting_tags": ["capacitor", "SMD"]
    }
  ]
}
```

**Response Schema**:
- `components` (array): Preview for each component
  - `component_id` (integer): Component ID
  - `component_name` (string): Component name/part number
  - `current_tags` (array of strings): Tags before operation
  - `resulting_tags` (array of strings): Tags after operation

**Example**:

```bash
curl -X GET "http://localhost:8000/api/v1/components/bulk/tags/preview?component_ids=1,2,3&tags_to_add=SMD&tags_to_remove=obsolete" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### POST /projects/assign

Assign multiple components to a project atomically.

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "project_id": 5,
  "quantities": {
    "1": 10,
    "2": 5,
    "3": 20
  }
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `project_id` (integer, required): ID of target project
- `quantities` (object, required): Map of component_id → quantity

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Response** (404 Not Found - Project Doesn't Exist):

```json
{
  "detail": "Project with ID 5 not found"
}
```

**Behavior**:
- Creates or updates ProjectComponent records
- All operations succeed or all are rolled back

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/components/bulk/projects/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3],
    "project_id": 5,
    "quantities": {"1": 10, "2": 5, "3": 20}
  }'
```

---

### POST /delete

Delete multiple components atomically.

**Request Body**:

```json
{
  "component_ids": [1, 2, 3]
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs to delete

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Behavior**:
- Permanently deletes components and related records (tags, project associations)
- All deletions succeed or all are rolled back
- Cannot be undone

**⚠️ Warning**: This operation is destructive and permanent.

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/components/bulk/delete \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": [1, 2, 3]
  }'
```

---

### POST /meta-parts/add

Add components to a meta-part atomically.

**Status**: Stub implementation (future feature)

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "meta_part_name": "Generic Resistor Kit"
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `meta_part_name` (string, required): Name of the meta-part

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Note**: Currently returns success without performing actual operation (placeholder for future feature).

---

### POST /purchase-lists/add

Add components to a purchase list atomically.

**Status**: Stub implementation (future feature)

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "purchase_list_id": 7
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `purchase_list_id` (integer, required): ID of purchase list

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Note**: Currently returns success without performing actual operation (placeholder for future feature).

---

### POST /low-stock/set

Set low-stock alert thresholds for multiple components atomically.

**Status**: Stub implementation (future feature)

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "threshold": 10
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `threshold` (integer, required): Low-stock threshold (minimum: 0)

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Note**: Currently returns success without performing actual operation (placeholder for future feature).

---

### POST /attribution/set

Set attribution metadata for multiple components atomically.

**Status**: Stub implementation (future feature)

**Request Body**:

```json
{
  "component_ids": [1, 2, 3],
  "attribution_data": {
    "supplier": "Digi-Key",
    "purchase_date": "2025-01-15"
  }
}
```

**Request Schema**:
- `component_ids` (array of integers, required): 1-1000 component IDs
- `attribution_data` (object, required): Key-value pairs of attribution metadata

**Response** (200 OK):

```json
{
  "success": true,
  "affected_count": 3,
  "errors": null
}
```

**Note**: Currently returns success without performing actual operation (placeholder for future feature).

---

## Common Response Schema

### BulkOperationResponse

All bulk operation endpoints return this schema:

```json
{
  "success": boolean,
  "affected_count": integer,
  "errors": [BulkOperationError] | null
}
```

**Fields**:
- `success` (boolean): Whether ALL operations succeeded (all-or-nothing)
- `affected_count` (integer): Number of components affected (0 if failed)
- `errors` (array or null): List of errors if operation failed

### BulkOperationError

```json
{
  "component_id": integer,
  "component_name": string,
  "error_message": string,
  "error_type": string
}
```

**Error Types**:
- `not_found`: Component doesn't exist
- `concurrent_modification`: Component modified by another user (version mismatch)
- `validation_error`: Request validation failed
- `permission_denied`: Insufficient permissions

## Error Handling

### 400 Bad Request

Invalid request body or parameters:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "component_ids"],
      "msg": "ensure this value has at least 1 items",
      "input": []
    }
  ]
}
```

### 403 Forbidden

User is not an admin:

```json
{
  "detail": "Admin privileges required for bulk operations"
}
```

### 409 Conflict

Concurrent modification detected - entire operation rolled back:

```json
{
  "success": false,
  "affected_count": 0,
  "errors": [
    {
      "component_id": 5,
      "component_name": "RES-1K",
      "error_message": "Component modified by another user",
      "error_type": "concurrent_modification"
    }
  ]
}
```

## Rate Limiting

- Maximum 1000 components per request
- No artificial rate limiting (rely on atomic transaction timeouts)

## Performance Targets

- **< 100 components**: < 200ms response time (p95)
- **100-1000 components**: < 500ms response time (p95)
- **> 1000 components**: Not supported (split into multiple requests)

## Concurrency Control

All bulk operations use optimistic concurrency control:

1. Each component has a `version` field that increments on every update
2. During bulk operations, the current version is read
3. On commit, if another user has modified the component (version mismatch), the entire transaction is rolled back
4. Detailed error report identifies which component(s) had conflicts

## OpenAPI Specification

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

The complete OpenAPI 3.0 specification includes:
- Request/response schemas
- Authentication requirements
- Example requests and responses
- Error codes and descriptions

## Client Examples

### Python (requests)

```python
import requests

ADMIN_TOKEN = "your-admin-jwt-token"
BASE_URL = "http://localhost:8000/api/v1/components/bulk"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

# Add tags to components
response = requests.post(
    f"{BASE_URL}/tags/add",
    headers=headers,
    json={
        "component_ids": [1, 2, 3],
        "tags": ["resistor", "SMD"]
    }
)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        print(f"Successfully tagged {result['affected_count']} components")
    else:
        print(f"Operation failed: {result['errors']}")
else:
    print(f"HTTP Error {response.status_code}: {response.json()}")
```

### JavaScript (fetch)

```javascript
const ADMIN_TOKEN = "your-admin-jwt-token";
const BASE_URL = "http://localhost:8000/api/v1/components/bulk";

async function bulkAddTags(componentIds, tags) {
  const response = await fetch(`${BASE_URL}/tags/add`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ADMIN_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      component_ids: componentIds,
      tags: tags
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  const result = await response.json();
  if (!result.success) {
    console.error('Bulk operation failed:', result.errors);
  }
  return result;
}

// Usage
bulkAddTags([1, 2, 3], ['resistor', 'SMD'])
  .then(result => console.log(`Tagged ${result.affected_count} components`))
  .catch(error => console.error(error));
```

### cURL

```bash
# Add tags
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component_ids": [1,2,3], "tags": ["resistor", "SMD"]}'

# Preview tags
curl -X GET "http://localhost:8000/api/v1/components/bulk/tags/preview?component_ids=1,2,3&tags_to_add=resistor,SMD" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Assign to project
curl -X POST http://localhost:8000/api/v1/components/bulk/projects/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component_ids": [1,2,3], "project_id": 5, "quantities": {"1": 10, "2": 5, "3": 20}}'

# Delete components
curl -X POST http://localhost:8000/api/v1/components/bulk/delete \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component_ids": [1,2,3]}'
```

## Best Practices

1. **Check Preview First**: Use `/tags/preview` before applying tag operations
2. **Handle Errors**: Always check `success` field and handle `errors` array
3. **Batch Wisely**: Keep requests under 1000 components for optimal performance
4. **Retry on 409**: Concurrent modification errors can be retried safely
5. **Use HTTPS**: Always use HTTPS in production
6. **Secure Tokens**: Store JWT tokens securely (never in client-side code)
7. **Validate Input**: Validate component IDs exist before sending requests

## Migration from Individual Operations

If you're currently using individual component update endpoints:

**Before** (individual requests):
```bash
for id in 1 2 3; do
  curl -X PATCH http://localhost:8000/api/v1/components/$id \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"tags": ["resistor"]}'
done
```

**After** (bulk operation):
```bash
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component_ids": [1,2,3], "tags": ["resistor"]}'
```

Benefits:
- **Atomic**: All-or-nothing instead of partial updates
- **Faster**: Single request instead of multiple
- **Safer**: Automatic rollback on any failure
