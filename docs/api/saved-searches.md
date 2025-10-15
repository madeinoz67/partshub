# Saved Searches API Guide

Complete API reference for saved searches functionality in PartsHub.

## Overview

The Saved Searches API allows users to save complex component search queries for quick re-execution. This feature enables users to store frequently used search parameters and access them with a single API call.

**Base URL**: `/api/v1/saved-searches`

**Authentication**: All endpoints require JWT bearer token authentication

**Version**: Added in v0.5.0

## Key Features

- User-specific saved searches (isolated per user account)
- Save complex search parameters as JSON
- Execute saved searches with usage tracking
- Duplicate searches for variations
- Statistics and analytics on search usage
- Full CRUD operations

## Endpoints

### POST /api/v1/saved-searches

Create a new saved search for the authenticated user.

**Authentication**: Required (JWT token)

**Request Body**: `SavedSearchCreate`

```json
{
  "name": "Low Stock Resistors",
  "description": "All resistors with stock below 10 units",
  "search_parameters": {
    "search": "resistor",
    "category": "passive",
    "stock_status": "low"
  }
}
```

**Field Descriptions:**

- `name` (required): Search name, 1-100 characters
- `description` (optional): Longer description of search purpose
- `search_parameters` (required): JSON object containing search criteria

**Response**: `SavedSearchResponse` (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Low Stock Resistors",
  "description": "All resistors with stock below 10 units",
  "search_parameters": {
    "search": "resistor",
    "category": "passive",
    "stock_status": "low"
  },
  "created_at": "2025-10-14T10:30:00Z",
  "updated_at": "2025-10-14T10:30:00Z",
  "last_used_at": null
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `422 Unprocessable Entity`: Validation error (invalid name length, missing required fields)
- `500 Internal Server Error`: Database or server error

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Low Stock Resistors",
    "description": "All resistors with stock below 10 units",
    "search_parameters": {
      "search": "resistor",
      "category": "passive",
      "stock_status": "low"
    }
  }'
```

---

### GET /api/v1/saved-searches

List all saved searches for the authenticated user.

**Authentication**: Required (JWT token)

**Query Parameters:**

- `limit` (optional): Number of items to return (default: 50, min: 1, max: 100)
- `offset` (optional): Number of items to skip (default: 0, min: 0)
- `sort_by` (optional): Sort field - one of: `created_at`, `updated_at`, `last_used_at`, `name` (default: `updated_at`)

**Response**: Array of `SavedSearchResponse` (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Low Stock Resistors",
    "description": "All resistors with stock below 10 units",
    "search_parameters": {...},
    "created_at": "2025-10-14T10:30:00Z",
    "updated_at": "2025-10-14T10:30:00Z",
    "last_used_at": "2025-10-14T14:22:00Z"
  },
  ...
]
```

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `422 Unprocessable Entity`: Invalid query parameters

**Example:**

```bash
# Get first 20 searches sorted by last used date
curl -X GET "http://localhost:8000/api/v1/saved-searches?limit=20&sort_by=last_used_at" \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/v1/saved-searches/stats

Get statistics about the current user's saved searches.

**Authentication**: Required (JWT token)

**Response**: `SavedSearchStatistics` (200 OK)

```json
{
  "total_searches": 15,
  "used_searches": 8,
  "unused_searches": 7,
  "most_recent_search": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Low Stock Resistors",
    "last_used_at": "2025-10-14T14:22:00Z"
  }
}
```

**Field Descriptions:**

- `total_searches`: Total number of saved searches for user
- `used_searches`: Number of searches that have been executed at least once
- `unused_searches`: Number of searches never executed
- `most_recent_search`: Most recently used search (null if no searches used)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token

**Example:**

```bash
curl -X GET http://localhost:8000/api/v1/saved-searches/stats \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/v1/saved-searches/{search_id}

Get a specific saved search by ID.

**Authentication**: Required (JWT token)

**Path Parameters:**

- `search_id`: UUID of the saved search

**Response**: `SavedSearchResponse` (200 OK)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Search doesn't exist or doesn't belong to current user
- `422 Unprocessable Entity`: Invalid UUID format

**Example:**

```bash
curl -X GET http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

---

### PUT /api/v1/saved-searches/{search_id}

Update an existing saved search.

**Authentication**: Required (JWT token)

**Path Parameters:**

- `search_id`: UUID of the saved search

**Request Body**: `SavedSearchUpdate`

```json
{
  "name": "Critical Low Stock Resistors",
  "description": "Updated description",
  "search_parameters": {
    "search": "resistor",
    "category": "passive",
    "stock_status": "critical"
  }
}
```

**Note**: Only provided fields will be updated. All fields are optional.

**Response**: `SavedSearchResponse` (200 OK)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Search doesn't exist or doesn't belong to current user
- `422 Unprocessable Entity`: Invalid UUID format or validation error

**Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Critical Low Stock Resistors",
    "description": "Updated to show critical stock levels only"
  }'
```

---

### DELETE /api/v1/saved-searches/{search_id}

Delete a saved search permanently.

**Authentication**: Required (JWT token)

**Path Parameters:**

- `search_id`: UUID of the saved search

**Response**: 204 No Content (successful deletion)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Search doesn't exist or doesn't belong to current user
- `422 Unprocessable Entity`: Invalid UUID format

**Warning**: This operation cannot be undone. The search is permanently removed.

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v1/saved-searches/{search_id}/execute

Execute a saved search and return its parameters.

**Authentication**: Required (JWT token)

**Path Parameters:**

- `search_id`: UUID of the saved search

**Response**: `SavedSearchExecuteResponse` (200 OK)

```json
{
  "search_parameters": {
    "search": "resistor",
    "category": "passive",
    "stock_status": "low"
  }
}
```

**Side Effects:**

- Updates `last_used_at` timestamp on the search
- Increments internal usage counter (for statistics)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Search doesn't exist or doesn't belong to current user
- `422 Unprocessable Entity`: Invalid UUID format

**Usage Pattern:**

1. Call this endpoint to get search parameters
2. Apply parameters to component search UI (frontend automatically loads parameters into search fields)
3. Display results to user

**Frontend Integration:**

When a saved search is executed from the Saved Searches page, the user is redirected to `/components?savedSearchId={id}`. The ComponentList page automatically:

1. Detects the `savedSearchId` query parameter
2. Calls this execute endpoint to fetch search parameters
3. Populates the search fields with the returned parameters (search text, category filter, stock status filter)
4. Executes the search automatically
5. Displays a success notification

**Example:**

```bash
# Execute saved search
curl -X POST http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000/execute \
  -H "Authorization: Bearer <token>"

# Response includes parameters that frontend applies
# Frontend then navigates to /components?savedSearchId={id}
```

---

### POST /api/v1/saved-searches/{search_id}/duplicate

Duplicate an existing saved search with a new name.

**Authentication**: Required (JWT token)

**Path Parameters:**

- `search_id`: UUID of the saved search to duplicate

**Request Body**: `SavedSearchDuplicateRequest`

```json
{
  "name": "Copy of Low Stock Resistors"
}
```

**Note**: If name is not provided, defaults to "Copy of {original_name}"

**Response**: `SavedSearchResponse` (200 OK)

**Error Responses:**

- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Search doesn't exist or doesn't belong to current user
- `422 Unprocessable Entity`: Invalid UUID format or validation error

**Example:**

```bash
# Duplicate with custom name
curl -X POST http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000/duplicate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMD Resistors Low Stock"
  }'

# Duplicate with default name
curl -X POST http://localhost:8000/api/v1/saved-searches/550e8400-e29b-41d4-a716-446655440000/duplicate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Data Models

### SavedSearch (Database Model)

```python
{
  "id": "string (UUID)",
  "user_id": "string (UUID)",
  "name": "string (max 100 chars)",
  "description": "string | null",
  "search_parameters": "object (JSON)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "last_used_at": "datetime (ISO 8601) | null"
}
```

### Search Parameters Structure

The `search_parameters` field is a flexible JSON object that stores search criteria. The backend does not validate the structure - it's stored as-is and returned when executed.

**Currently Implemented Parameters (v0.5.0):**

```json
{
  "search": "string - search query text (optional)",
  "category": "string - category filter (optional)",
  "stock_status": "string - low | critical | available | out_of_stock | all (optional)"
}
```

**Future/Extensible Parameters:**

The JSON structure supports additional fields for future features:

```json
{
  "search": "string - search query text",
  "searchType": "unified | part_number | provider_sku",
  "category": "string - category filter",
  "stock_status": "string - stock status filter",
  "tags": "array of tag names",
  "manufacturer": "string - manufacturer filter",
  "location": "string - storage location filter",
  "limit": "number - result limit",
  "providers": "array of provider names",
  "sort_by": "string - sort field",
  "sort_order": "asc | desc"
}
```

**Implementation Notes:**

- Parameters are stored as a flexible JSON object
- Backend does not validate parameter structure
- Clients should ensure parameters are compatible with their search implementation
- Current frontend (v0.5.0) captures: `search`, `category`, and `stock_status`
- Additional parameters can be added without backend changes

## Common Workflows

### Save Current Search

```bash
# 1. User performs search
curl -X GET "http://localhost:8000/api/v1/components?search=resistor&limit=20"

# 2. User saves the search
curl -X POST http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "All Resistors",
    "search_parameters": {
      "search": "resistor",
      "category": "passive"
    }
  }'
```

### Execute Saved Search

```bash
# 1. List available searches
curl -X GET http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer <token>"

# 2. Execute specific search
curl -X POST http://localhost:8000/api/v1/saved-searches/{id}/execute \
  -H "Authorization: Bearer <token>"

# 3. Frontend navigates to /components?savedSearchId={id}
# 4. ComponentList automatically loads and applies parameters
```

### Create Search Variation

```bash
# 1. Duplicate existing search
curl -X POST http://localhost:8000/api/v1/saved-searches/{id}/duplicate \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "Variation Name"}'

# 2. Update duplicated search parameters
curl -X PUT http://localhost:8000/api/v1/saved-searches/{new_id} \
  -H "Authorization: Bearer <token>" \
  -d '{
    "search_parameters": {
      "search": "resistor",
      "stock_status": "critical"
    }
  }'
```

## Security & Access Control

### Authentication

All endpoints require a valid JWT bearer token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### User Isolation

- Saved searches are strictly isolated per user account
- Users can only access, modify, or delete their own saved searches
- Attempting to access another user's search returns 404 Not Found
- User ID is extracted from JWT token, not request parameters

### Data Privacy

- Search parameters are stored as-is without validation or sanitization
- Ensure sensitive data is not stored in search parameters
- Search names and descriptions are visible only to the owning user

## Performance Considerations

### Pagination

- Default limit: 50 searches
- Maximum limit: 100 searches
- Use `offset` for pagination through large result sets

### Sorting

Recommended sort strategies:

- `last_used_at DESC`: Show recently used searches first
- `name ASC`: Alphabetical organization
- `created_at DESC`: Show newest searches first

### Indexing

The following database indexes improve performance:

- `user_id` (indexed) - Fast user-specific queries
- `id` (primary key) - Fast single-search lookups

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message description"
}
```

### Common Error Scenarios

**401 Unauthorized:**
- Missing JWT token in Authorization header
- Invalid or expired JWT token
- Token signature verification failed

**404 Not Found:**
- Search ID doesn't exist in database
- Search belongs to a different user
- User attempting to access non-existent search

**422 Unprocessable Entity:**
- Invalid UUID format for search_id
- Name too long (>100 characters)
- Name too short (<1 character)
- Missing required fields
- Invalid sort_by parameter
- Invalid limit or offset values

**500 Internal Server Error:**
- Database connection failure
- Unexpected server error
- JSON serialization error

## Testing

### Manual Testing with curl

```bash
# Set environment variables
export TOKEN="your_jwt_token_here"
export API_URL="http://localhost:8000"

# Create
curl -X POST "$API_URL/api/v1/saved-searches" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Search","search_parameters":{"search":"test"}}'

# List
curl -X GET "$API_URL/api/v1/saved-searches" \
  -H "Authorization: Bearer $TOKEN"

# Execute
curl -X POST "$API_URL/api/v1/saved-searches/{id}/execute" \
  -H "Authorization: Bearer $TOKEN"

# Delete
curl -X DELETE "$API_URL/api/v1/saved-searches/{id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Integration Tests

See `backend/tests/integration/test_saved_searches_api.py` for comprehensive test coverage.

## Related Documentation

- [Saved Searches User Guide](../user/saved-searches.md) - End-user documentation
- [Saved Searches Frontend Integration](../frontend/saved-searches-integration.md) - Frontend implementation
- [Component Search API](../api.md) - Component search endpoint documentation
- [Authentication Guide](../backend/index.md) - JWT authentication details

## Changelog

### v0.5.0 (2025-10-14)

**Initial Release:**
- Complete CRUD operations for saved searches
- Execute endpoint with usage tracking
- Duplicate functionality
- Statistics endpoint
- User-isolated searches
- Pagination and sorting support
- Frontend integration with automatic parameter loading
- Navigation from Saved Searches page to Components page with query parameter
- Search field population on execution

---

**Version**: v0.5.0
**Last Updated**: 2025-10-15
