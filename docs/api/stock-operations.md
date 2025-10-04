# Stock Operations API Reference

## Overview

The Stock Operations API provides comprehensive functionality for managing component inventory across multiple storage locations. These endpoints are exclusively available to admin users and support critical inventory management tasks:

- Adding stock to a component
- Removing stock from a component
- Moving stock between locations
- Viewing and exporting stock history

### Authentication

**All stock operation endpoints require:**
- A valid JWT token
- User account with admin privileges

### General Behavior

- **Pessimistic Locking**: Each stock operation locks the affected location for 30 seconds
- **Atomic Transactions**: All operations are fully atomic - they either complete entirely or fail completely
- **Validation**: Comprehensive input validation prevents invalid stock modifications
- **Audit Trail**: Every operation is permanently logged in stock history

## Endpoint: Add Stock

**Endpoint**: `POST /api/v1/components/{component_id}/stock/add`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `component_id` | UUID | Yes | Unique identifier of the target component |
| `location_id` | UUID | Yes | Storage location where stock will be added |
| `quantity` | Integer | Yes | Number of units to add (minimum: 1) |
| `price_per_unit` | Decimal | Optional | Price for each unit (for per-component pricing) |
| `total_price` | Decimal | Optional | Total price for entire lot |
| `lot_id` | String | Optional | Lot/batch tracking identifier |
| `comments` | String | Optional | Additional notes about the stock addition |
| `reference_id` | String | Optional | Related order or purchase ID |
| `reference_type` | String | Optional | Type of reference (e.g., "purchase_order") |

### Request Examples

#### Manual Entry with Pricing
```json
{
  "location_id": "660e8400-e29b-41d4-a716-446655440001",
  "quantity": 100,
  "price_per_unit": 0.50,
  "lot_id": "LOT-2025-Q1-001",
  "comments": "Manual stock addition - quarterly restock"
}
```

#### Order Receiving
```json
{
  "location_id": "660e8400-e29b-41d4-a716-446655440001",
  "quantity": 50,
  "total_price": 25.00,
  "reference_id": "PO-2025-001",
  "reference_type": "purchase_order",
  "comments": "Received shipment against PO-2025-001"
}
```

### Responses

#### Success (200 OK)
```json
{
  "success": true,
  "message": "Stock added successfully",
  "transaction_id": "770e8400-e29b-41d4-a716-446655440002",
  "component_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_id": "660e8400-e29b-41d4-a716-446655440001",
  "quantity_added": 50,
  "previous_quantity": 100,
  "new_quantity": 150,
  "total_stock": 250
}
```

#### Error Responses

| Status Code | Description | Example |
|------------|-------------|---------|
| 400 | Validation Error | `{"detail": "Quantity must be positive (minimum: 1)"}` |
| 403 | Forbidden (Non-Admin) | `{"detail": "Admin privileges required"}` |
| 404 | Component Not Found | `{"detail": "Component not found"}` |
| 409 | Resource Locked | `{"detail": "Location is currently locked"}` |

## Endpoint: Remove Stock

**Endpoint**: `POST /api/v1/components/{component_id}/stock/remove`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location_id` | UUID | Yes | Storage location to remove stock from |
| `quantity` | Integer | Yes | Number of units to remove |
| `comments` | String | Optional | Reason for stock removal |

### Request Example
```json
{
  "location_id": "660e8400-e29b-41d4-a716-446655440001",
  "quantity": 25,
  "comments": "Used in project X"
}
```

### Responses

Similar to Add Stock endpoint, with auto-capping of removal quantity to available stock.

## Endpoint: Move Stock

**Endpoint**: `POST /api/v1/components/{component_id}/stock/move`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_location_id` | UUID | Yes | Location to move stock from |
| `destination_location_id` | UUID | Yes | Location to move stock to |
| `quantity` | Integer | Yes | Number of units to move |
| `comments` | String | Optional | Notes about stock movement |

### Request Example
```json
{
  "source_location_id": "660e8400-e29b-41d4-a716-446655440001",
  "destination_location_id": "770e8400-e29b-41d4-a716-446655440002",
  "quantity": 50,
  "comments": "Reorganizing inventory"
}
```

## Endpoint: Stock History

**Endpoints**:
- `GET /api/v1/components/{component_id}/stock/history`
- `GET /api/v1/components/{component_id}/stock/history/export`

### Query Parameters for History

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | Integer | Page number | 1 |
| `per_page` | Integer | Entries per page | 10 |
| `format` | String | Export format (for export endpoint) | CSV |

### Export Formats
- CSV
- XLSX (Excel)
- JSON

## Performance Targets

- Stock Operations: <200ms response time
- History Pagination: <50ms response time

## Error Handling

The API provides comprehensive error responses covering:
- Authentication errors
- Validation failures
- Quantity constraints
- Concurrent operation conflicts

**Best Practices**:
- Always check error responses
- Implement retry mechanisms for locked resources
- Validate input before submission