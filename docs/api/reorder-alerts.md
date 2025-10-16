# Reorder Alerts API Documentation

**New in v0.5.0**: Automatic low-stock alerting with database triggers and comprehensive lifecycle management.

## Overview

The Reorder Alerts API provides automatic stock monitoring and alerting capabilities for PartsHub. When component stock falls below configured thresholds, the system automatically creates alerts via SQLite database triggers - providing zero-latency notification without polling or background jobs.

## Key Features

- **Zero-latency alert generation** - Database triggers create alerts instantly when stock falls below threshold
- **Per-location threshold configuration** - Set different reorder points for each storage location
- **Alert lifecycle management** - Track alerts from creation through dismissal, ordering, or resolution
- **Severity calculation** - Automatic criticality assessment based on shortage percentage
- **Bulk threshold updates** - Configure multiple locations simultaneously
- **Real-time reporting** - Low stock reports and statistics independent of alert status
- **Admin-only operations** - All endpoints require admin JWT authentication

## Base URL

```
http://localhost:8000/api/v1/reorder-alerts
```

## Authentication

All reorder alert endpoints require **admin authentication** via JWT bearer token:

```bash
Authorization: Bearer <admin-token>
```

## Alert Lifecycle

Alerts follow a defined workflow from creation to resolution:

```
┌─────────┐
│ CREATED │ (by database trigger when stock < threshold)
└────┬────┘
     │
     ▼
┌────────┐
│ ACTIVE │ ────┐
└────┬───┘     │
     │         │
     ├─────────┼──► DISMISSED (user action - no reorder needed)
     │         │
     ├─────────┼──► ORDERED (user action - order placed with supplier)
     │         │
     └─────────┴──► RESOLVED (auto-resolved when stock rises above threshold)
```

## Severity Levels

Alerts are automatically assigned severity based on shortage percentage:

| Severity | Condition | Description |
|----------|-----------|-------------|
| **critical** | > 80% shortage | Urgent reorder needed |
| **high** | > 50% shortage | High priority reorder |
| **medium** | > 20% shortage | Moderate priority |
| **low** | ≤ 20% shortage | Low priority |

**Calculation**: `shortage_percentage = (shortage_amount / reorder_threshold) * 100`

---

## Endpoints

### Alert Retrieval

#### List Active Alerts

Get all currently active alerts (not dismissed, ordered, or resolved).

```http
GET /api/v1/reorder-alerts/
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `component_id` | UUID | No | Filter by component UUID |
| `location_id` | UUID | No | Filter by storage location UUID |
| `min_shortage` | integer | No | Minimum shortage amount (≥0) |

**Response 200:**

```json
{
  "alerts": [
    {
      "id": 42,
      "component_location_id": "12",
      "component_id": "660e8400-e29b-41d4-a716-446655440001",
      "component_name": "10kΩ Resistor 0805",
      "component_part_number": "RC0805FR-0710KL",
      "location_id": "770e8400-e29b-41d4-a716-446655440001",
      "location_name": "Bin A1",
      "status": "active",
      "severity": "critical",
      "current_quantity": 5,
      "reorder_threshold": 50,
      "shortage_amount": 45,
      "shortage_percentage": 90.0,
      "created_at": "2025-10-15T10:30:00Z",
      "updated_at": "2025-10-15T10:30:00Z",
      "dismissed_at": null,
      "ordered_at": null,
      "resolved_at": null,
      "notes": null
    }
  ],
  "total_count": 1
}
```

**Example:**

```bash
# Get all active alerts
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get alerts for specific component with minimum shortage
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/?component_id=660e8400-e29b-41d4-a716-446655440001&min_shortage=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

#### Get Alert History

Retrieve historical alerts (dismissed, ordered, or resolved).

```http
GET /api/v1/reorder-alerts/history
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `component_id` | UUID | No | - | Filter by component UUID |
| `limit` | integer | No | 50 | Max records (1-500) |

**Response 200:**

Same structure as active alerts, ordered by `updated_at` descending (newest first).

**Example:**

```bash
# Get last 100 historical alerts
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/history?limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get history for specific component
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/history?component_id=660e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

#### Get Single Alert

Retrieve a specific alert by ID.

```http
GET /api/v1/reorder-alerts/{alert_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `alert_id` | integer | Alert primary key ID |

**Response 200:**

```json
{
  "id": 42,
  "component_location_id": "12",
  "component_id": "660e8400-e29b-41d4-a716-446655440001",
  "component_name": "10kΩ Resistor 0805",
  "component_part_number": "RC0805FR-0710KL",
  "location_id": "770e8400-e29b-41d4-a716-446655440001",
  "location_name": "Bin A1",
  "status": "active",
  "severity": "critical",
  "current_quantity": 5,
  "reorder_threshold": 50,
  "shortage_amount": 45,
  "shortage_percentage": 90.0,
  "created_at": "2025-10-15T10:30:00Z",
  "updated_at": "2025-10-15T10:30:00Z",
  "dismissed_at": null,
  "ordered_at": null,
  "resolved_at": null,
  "notes": null
}
```

**Errors:**

- `404 Not Found` - Alert does not exist
- `403 Forbidden` - User is not admin

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/42" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Alert Lifecycle Management

#### Dismiss Alert

Dismiss an active alert (mark as not requiring reorder).

```http
POST /api/v1/reorder-alerts/{alert_id}/dismiss
```

**Request Body:**

```json
{
  "notes": "Component being phased out - no reorder needed"
}
```

**When to Dismiss:**
- Component is being discontinued
- Manual reorder decision made via other channels
- Alert is no longer relevant

**Response 200:**

Returns updated alert with `status: "dismissed"` and `dismissed_at` timestamp.

**Errors:**

- `400 Bad Request` - Alert is not active
- `404 Not Found` - Alert does not exist
- `403 Forbidden` - User is not admin

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/reorder-alerts/42/dismiss" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Switching to alternative part - no reorder needed"}'
```

---

#### Mark Alert as Ordered

Mark an active alert as ordered (restock order placed).

```http
POST /api/v1/reorder-alerts/{alert_id}/mark-ordered
```

**Request Body:**

```json
{
  "notes": "PO-2025-042 placed with Mouser - Expected delivery 2025-11-01 - Qty: 1000"
}
```

**Recommended Notes:**
- Purchase order number
- Supplier name
- Expected delivery date
- Order quantity

**Response 200:**

Returns updated alert with `status: "ordered"` and `ordered_at` timestamp.

**Errors:**

- `400 Bad Request` - Alert is not active
- `404 Not Found` - Alert does not exist
- `403 Forbidden` - User is not admin

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/reorder-alerts/42/mark-ordered" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "PO-2025-042 - Mouser - ETA: 2025-11-01 - Ordered 1000 units"
  }'
```

---

### Threshold Management

#### Update Reorder Threshold

Configure reorder threshold for a component at a specific location.

```http
PUT /api/v1/reorder-alerts/thresholds/{component_id}/{location_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_id` | UUID | Component UUID |
| `location_id` | UUID | Storage location UUID |

**Request Body:**

```json
{
  "threshold": 50,
  "enabled": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `threshold` | integer | Yes | Reorder threshold quantity (≥0) |
| `enabled` | boolean | Yes | Enable/disable reorder monitoring |

**Response 200:**

```json
{
  "component_location_id": "12",
  "component_id": "660e8400-e29b-41d4-a716-446655440001",
  "location_id": "770e8400-e29b-41d4-a716-446655440001",
  "reorder_threshold": 50,
  "reorder_enabled": true,
  "current_quantity": 35,
  "needs_reorder": false
}
```

**Behavior:**
- If `enabled: true` and stock is currently below threshold, an alert will be automatically created by database triggers
- Uses pessimistic locking to prevent concurrent threshold modifications

**Errors:**

- `400 Bad Request` - Invalid threshold (must be ≥0)
- `404 Not Found` - ComponentLocation does not exist
- `409 Conflict` - Concurrent modification (lock timeout)
- `403 Forbidden` - User is not admin

**Example:**

```bash
# Enable reorder monitoring with threshold of 50
curl -X PUT "http://localhost:8000/api/v1/reorder-alerts/thresholds/660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 50, "enabled": true}'

# Disable reorder monitoring
curl -X PUT "http://localhost:8000/api/v1/reorder-alerts/thresholds/660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 0, "enabled": false}'
```

---

#### Bulk Update Thresholds

Configure reorder thresholds for multiple component locations simultaneously.

```http
POST /api/v1/reorder-alerts/thresholds/bulk
```

**Request Body:**

```json
{
  "updates": [
    {
      "component_id": "660e8400-e29b-41d4-a716-446655440001",
      "location_id": "770e8400-e29b-41d4-a716-446655440001",
      "threshold": 50,
      "enabled": true
    },
    {
      "component_id": "660e8400-e29b-41d4-a716-446655440002",
      "location_id": "770e8400-e29b-41d4-a716-446655440001",
      "threshold": 100,
      "enabled": true
    }
  ]
}
```

**Response 200:**

```json
{
  "success_count": 1,
  "error_count": 1,
  "errors": [
    {
      "component_id": "660e8400-e29b-41d4-a716-446655440002",
      "location_id": "770e8400-e29b-41d4-a716-446655440001",
      "error": "ComponentLocation not found"
    }
  ]
}
```

**Behavior:**
- Failed updates are reported individually without affecting successful updates
- No atomic transaction - partial success is possible
- Each update is processed independently

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/reorder-alerts/thresholds/bulk" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "component_id": "660e8400-e29b-41d4-a716-446655440001",
        "location_id": "770e8400-e29b-41d4-a716-446655440001",
        "threshold": 50,
        "enabled": true
      },
      {
        "component_id": "660e8400-e29b-41d4-a716-446655440003",
        "location_id": "770e8400-e29b-41d4-a716-446655440002",
        "threshold": 25,
        "enabled": true
      }
    ]
  }'
```

---

### Reports

#### Low Stock Report

Get real-time low stock report (current state independent of alert status).

```http
GET /api/v1/reorder-alerts/reports/low-stock
```

**Response 200:**

```json
{
  "items": [
    {
      "component_location_id": "12",
      "component_id": "660e8400-e29b-41d4-a716-446655440001",
      "component_name": "10kΩ Resistor 0805",
      "location_id": "770e8400-e29b-41d4-a716-446655440001",
      "location_name": "Bin A1",
      "current_quantity": 5,
      "reorder_threshold": 50,
      "shortage_amount": 45
    }
  ],
  "total_count": 1
}
```

**Use Case:**
- Dashboard widgets
- Scheduled reports
- Current inventory health check (independent of alert workflow)

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/reports/low-stock" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

#### Alert Statistics

Get aggregate alert statistics and metrics.

```http
GET /api/v1/reorder-alerts/reports/statistics
```

**Response 200:**

```json
{
  "by_status": {
    "active": 12,
    "dismissed": 5,
    "ordered": 8,
    "resolved": 45
  },
  "active_alerts": {
    "count": 12,
    "avg_shortage": 35.5,
    "max_shortage": 120
  }
}
```

**Use Case:**
- Dashboard summary widgets
- Inventory health monitoring
- Alert workflow analytics

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/reports/statistics" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Database Triggers

Reorder alerts are managed by SQLite database triggers for zero-latency operation:

### Trigger: Create Alert on Stock Drop

**Name:** `reorder_alert_create_on_stock_drop`

**When:** After UPDATE on `component_locations` table

**Condition:**
- `reorder_enabled = 1`
- `new.quantity < new.reorder_threshold`
- No existing active alert for this location

**Action:** Creates new alert with status `'active'`

### Trigger: Resolve Alert on Stock Increase

**Name:** `reorder_alert_resolve_on_stock_increase`

**When:** After UPDATE on `component_locations` table

**Condition:**
- Active alert exists
- `new.quantity >= new.reorder_threshold`

**Action:** Updates alert status to `'resolved'` with `resolved_at` timestamp

### Trigger: Update Alert on Quantity Change

**Name:** `reorder_alert_update_on_quantity_change`

**When:** After UPDATE on `component_locations` table

**Condition:**
- Active alert exists
- Quantity changed but still below threshold

**Action:** Updates `current_quantity`, `shortage_amount`, and `updated_at`

---

## Common Workflows

### 1. Enable Reorder Monitoring for Location

```bash
# Set threshold and enable monitoring
curl -X PUT "http://localhost:8000/api/v1/reorder-alerts/thresholds/$COMPONENT_ID/$LOCATION_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 50, "enabled": true}'

# If current stock is below threshold, alert is automatically created
```

### 2. Process Active Alerts

```bash
# List all active alerts
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Mark as ordered after placing supplier order
curl -X POST "http://localhost:8000/api/v1/reorder-alerts/42/mark-ordered" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "PO-2025-042 - Mouser - ETA: 2025-11-01 - Qty: 1000"
  }'

# When stock arrives and is added, alert auto-resolves
```

### 3. Bulk Configure Thresholds

```bash
# Configure multiple locations at once
curl -X POST "http://localhost:8000/api/v1/reorder-alerts/thresholds/bulk" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"component_id": "uuid1", "location_id": "loc1", "threshold": 50, "enabled": true},
      {"component_id": "uuid2", "location_id": "loc1", "threshold": 100, "enabled": true},
      {"component_id": "uuid3", "location_id": "loc2", "threshold": 25, "enabled": true}
    ]
  }'
```

### 4. Dashboard Monitoring

```bash
# Get current low stock items
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/reports/low-stock" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get aggregate statistics
curl -X GET "http://localhost:8000/api/v1/reorder-alerts/reports/statistics" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Error Handling

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Successful operation |
| `400 Bad Request` | Invalid request (alert not active, invalid threshold, etc.) |
| `403 Forbidden` | User is not admin |
| `404 Not Found` | Alert or ComponentLocation not found |
| `409 Conflict` | Concurrent modification (pessimistic lock timeout) |
| `422 Unprocessable Entity` | Validation error (invalid UUID format, etc.) |

### Example Error Response

```json
{
  "detail": "Alert 42 is not active - current status: ordered"
}
```

---

## Performance Characteristics

- **Alert creation:** <1ms (database trigger execution)
- **List active alerts:** 50-200ms (depending on result set size)
- **Update threshold:** 100-300ms (includes pessimistic locking)
- **Bulk threshold update:** 50-100ms per item
- **Reports:** 100-500ms (depending on data volume)

---

## Integration Examples

### Python (requests)

```python
import requests

ADMIN_TOKEN = "your-admin-token"
BASE_URL = "http://localhost:8000/api/v1/reorder-alerts"
HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# List active alerts
response = requests.get(f"{BASE_URL}/", headers=HEADERS)
alerts = response.json()["alerts"]

# Configure threshold
threshold_data = {"threshold": 50, "enabled": True}
response = requests.put(
    f"{BASE_URL}/thresholds/{component_id}/{location_id}",
    headers=HEADERS,
    json=threshold_data
)

# Mark alert as ordered
order_data = {"notes": "PO-2025-042 - Mouser - ETA: 2025-11-01"}
response = requests.post(
    f"{BASE_URL}/42/mark-ordered",
    headers=HEADERS,
    json=order_data
)
```

### JavaScript (fetch)

```javascript
const ADMIN_TOKEN = "your-admin-token";
const BASE_URL = "http://localhost:8000/api/v1/reorder-alerts";
const headers = {
  "Authorization": `Bearer ${ADMIN_TOKEN}`,
  "Content-Type": "application/json"
};

// Get low stock report
const response = await fetch(`${BASE_URL}/reports/low-stock`, { headers });
const data = await response.json();
console.log(`${data.total_count} items need reorder`);

// Dismiss alert
await fetch(`${BASE_URL}/42/dismiss`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    notes: "Component being discontinued"
  })
});
```

---

## See Also

- [Reorder Alerts User Guide](../user/reorder-alerts.md) - User-facing documentation
- [Stock Operations API](stock-operations.md) - Related stock management endpoints
- [Bulk Operations API](bulk-operations.md) - Bulk component operations
