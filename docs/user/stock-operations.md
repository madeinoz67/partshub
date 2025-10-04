# Stock Operations User Guide

## Overview

The Stock Operations feature allows admin users to manage component inventory efficiently and accurately. You can add, remove, and move stock between locations, track historical changes, and export detailed stock history.

## Requirements

- **User Role**: Admin
- **Permissions**: Full stock management capabilities

## Accessing Stock Operations

Stock operations are available directly in the component row expansion menu:

1. Navigate to the Components table
2. Click the expansion icon (➕) on any component row
3. Select one of these operations:
   - Add Stock
   - Remove Stock
   - Move Stock
   - View Stock History

## Adding Stock

### Workflow Overview

The "Add Stock" feature supports two primary methods:
1. Manual Entry
2. Receiving Against Order

### Manual Entry Tab

1. Click "Add Stock" in the component row expansion
2. Select "Enter manually" tab
3. Fill in required fields:
   - **Quantity**: Number of units being added
   - **Location**: Select existing or create new storage location
4. Optional pricing options:
   - **No Price**: Skip pricing information
   - **Per Component**: Enter price per individual unit
   - **Entire Lot**: Enter total lot price
5. Optional additional information:
   - **Lot ID**: Tracking identifier for the batch
   - **Comments**: Notes about stock addition

### Receiving Against Order Tab

1. Click "Add Stock" in the component row expansion
2. Select "Receive against an order" tab
3. Choose the relevant purchase order
4. System pre-fills:
   - Quantity
   - Total price
   - Reference information
5. Confirm or adjust details as needed

### Validation and Feedback

- Red highlights indicate validation errors
- Submit button remains disabled until all required fields are correctly filled
- Immediate success notification upon stock addition
- Total component quantity updates dynamically

## Removing Stock

### Workflow Overview

1. Click "Remove Stock" in the component row expansion
2. View available locations with current stock quantities
3. Select source location
4. Enter quantity to remove
5. Optional: Add comments explaining removal reason

### Key Behaviors

- **Auto-Capping**: If you enter a quantity larger than available stock, the system automatically adjusts to the maximum available quantity
- **Location Cleanup**: If all stock is removed from a location, that location entry is automatically deleted
- **Immediate Update**: Component and location quantities update instantly

## Moving Stock

### Workflow Overview

1. Click "Move Stock" in the component row expansion
2. Source location pre-selected based on current row
3. Choose destination:
   - Existing locations with the component
   - "Other locations that can accept this part"
4. Enter quantity to move
5. Optional: Add movement comments

### Key Behaviors

- **Atomic Transfer**: Stock moves completely or not at all
- **Pricing Inheritance**:
  - Moved stock preserves original lot and pricing information
  - If merging into an existing location, calculates weighted average price
- **Location Management**:
  - Can move to new or existing locations
  - Automatically handles source location cleanup if entire stock is moved

## Stock History

### Viewing History

1. Open component row expansion
2. Navigate to Stock History tab
3. View paginated table with:
   - Date
   - Operation Type (Add/Remove/Move)
   - Quantity (+/- indicators)
   - Location
   - Lot ID
   - Price
   - Comments
   - User who performed operation

### Sorting and Navigation

- Click column headers to sort
- 10 entries displayed per page
- Pagination controls for navigating multiple pages

## Exporting Stock History

### Export Options

1. Click "Export" button in Stock History view
2. Select export format:
   - CSV
   - Excel (XLSX)
   - JSON
3. File downloads immediately

### Export Restrictions

- Admin-only feature
- Exports full historical record

## Troubleshooting

### Common Issues

1. **Validation Errors**
   - Ensure all required fields are filled
   - Check quantity constraints
   - Verify location selection

2. **Lock Timeout Errors**
   - Another admin might be modifying the same stock
   - Wait 30 seconds and retry
   - Contact team if persistent issues occur

3. **Insufficient Quantity**
   - System auto-caps removals/moves
   - Confirm total available stock before operation

## System Limitations

- Maximum 1000 components per bulk operation
- Requires unique admin credentials
- Pricing optional but recommended for accurate inventory valuation

## Best Practices

- Always add descriptive comments
- Verify quantities before confirming
- Use lot tracking for precise inventory management
- Export history regularly for record-keeping

## Migration Guidance

1. Transition from manual stock tracking
2. Use inline forms for quick updates
3. Leverage comprehensive audit features
4. Train team on new inventory management workflow