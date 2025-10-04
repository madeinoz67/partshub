# Bulk Operations Guide

PartsHub's bulk operations feature allows admin users to perform actions on multiple components simultaneously, saving time when managing large inventories.

## Overview

Bulk operations enable you to:

- Add or remove tags from multiple components at once
- Assign components to projects in bulk
- Delete multiple components
- Manage meta-parts, purchase lists, stock levels, and attribution data

**⚠️ Admin Privileges Required**: All bulk operations require admin authentication. Non-admin users will not see bulk operation controls.

## Accessing Bulk Operations

### Using the Web Interface

1. **Navigate to Components Page**: Go to the Components section
2. **Select Components**: Use checkboxes to select one or more components
   - Click individual checkboxes for specific components
   - Use the header checkbox to select all components on the current page
3. **Open Bulk Menu**: Click the "Selected..." button above the table
4. **Choose Operation**: Select the desired operation from the dropdown menu

### Selection Features

**Cross-Page Selection**: Your selection persists as you navigate between pages. You can:
- Select 3 components on page 1
- Navigate to page 2
- Select 2 more components
- Perform a bulk operation on all 5 selected components

**Selection Counter**: The "Selected..." button displays the number of selected components (e.g., "Rows: 323 selected: 5")

**Disabled State**: When no components are selected, the "Selected..." button is visible but grayed out (disabled)

**Clear Selection**: Use "Deselect all" from the bulk operations menu to clear your selection

## Available Operations

### Add or Remove Tags

Manage tags across multiple components simultaneously.

**Steps**:

1. Select components
2. Click "Selected..." → "Add/remove tags..."
3. In the dialog:
   - **Adding Tags**: Enter comma-separated tag names in "Tags to be added" field
   - **Removing Tags**:
     - "Common tags" shows tags present on ALL selected components
     - "All tags" shows tags present on ANY selected component
     - Click tag badges to add them to the removal list
4. **Preview**: Review the "Preview" section to see resulting tags for each component
   - "Tags (user)" column shows user-added tags
   - "Tags (auto)" column shows automatically-generated tags
5. Click "Add/Remove Tags" to apply changes

**Example**: Add "resistor" and "SMD" tags to 10 selected components.

**Note**: If a component already has a tag you're adding, the operation is idempotent (the tag won't be duplicated).

### Add to Project

Assign multiple components to a project with specified quantities.

**Steps**:

1. Select components
2. Click "Selected..." → "Add to project..."
3. In the dialog:
   - Review the list of selected components
   - Adjust quantities using +/- buttons (default: 1)
   - Select target project from "To project" dropdown
4. Click "Add" to assign components to the project

**Example**: Add 5 different resistors to "Arduino Prototype" project, each with quantity 10.

### Delete Components

Permanently remove multiple components from inventory.

**Steps**:

1. Select components to delete
2. Click "Selected..." → "Delete..."
3. Confirm the deletion in the dialog
4. Components are permanently removed

**⚠️ Warning**: Deletion is permanent and cannot be undone. The operation uses atomic transactions (all-or-nothing), so if any component fails to delete, none will be deleted.

### Other Operations

The following operations are available from the bulk menu:

- **Add to meta-part**: Group components into a meta-part definition
- **Add to purchase list**: Add components to a purchasing queue
- **Set low-stock levels**: Configure stock alert thresholds for multiple components
- **Set part attribution**: Update attribution metadata in bulk
- **Download as CSV**: Export selected components as CSV

## Transaction Safety

### Atomic Operations

All bulk operations use **atomic transactions** (all-or-nothing):

- If ANY component fails during a bulk operation, ALL changes are rolled back
- No partial updates occur
- You receive a detailed error report showing which component(s) caused the failure

**Example**: If you try to add tags to 10 components and one component is locked by another user, the entire operation fails and none of the components receive the new tags.

### Concurrent Modification Detection

PartsHub detects when components are modified by other users during a bulk operation:

- Each component has a version number that increments on every update
- If another user modifies a component while you're performing a bulk operation, the version mismatch is detected
- The entire operation is rolled back with an error: "Component modified by another user"

## Performance

Bulk operations are optimized for performance:

- **Up to 100 components**: < 200ms response time
- **100-1000 components**: < 500ms response time
- **Over 1000 components**: Operations may be chunked for optimal performance

## Troubleshooting

### "Selected..." Button is Grayed Out

**Cause**: No components are selected

**Solution**: Select at least one component using the checkboxes

### "Admin privileges required" Error

**Cause**: You are not logged in as an admin user

**Solution**: Log in with an admin account. Contact your system administrator if you need admin access.

### "Component modified by another user" Error

**Cause**: Concurrent modification detected - another user changed a component while your bulk operation was in progress

**Solution**:
1. Refresh the component list to see the latest data
2. Reselect components
3. Retry the bulk operation

### Selection Lost After Navigation

**Cause**: Selection should persist across navigation. If it doesn't, check browser localStorage settings

**Solution**:
1. Ensure your browser allows localStorage
2. Try refreshing the page
3. If the issue persists, use "Deselect all" and reselect components

### Bulk Operation Failed Partially

**Cause**: This should not happen - bulk operations are atomic (all-or-nothing)

**Solution**: If you experience partial updates:
1. Check the component list to verify actual state
2. Report this as a bug - atomic transactions should prevent partial updates

## API Access

For programmatic access to bulk operations, see the [Bulk Operations API Documentation](../api/bulk-operations.md).

All bulk operation endpoints require:
- JWT authentication
- Admin role
- POST requests (except preview, which uses GET)

## Best Practices

1. **Review Before Executing**: Use the preview feature (for tags) to verify changes before applying
2. **Start Small**: Test bulk operations on a few components before applying to large sets
3. **Use Cross-Page Selection**: Don't feel limited to one page - select components across multiple pages
4. **Clear Selection**: Use "Deselect all" when done to avoid accidentally including components in future operations
5. **Check Success Notifications**: PartsHub displays success notifications after each bulk operation
6. **Maintain Selection**: Selection persists after successful operations, allowing follow-up actions (e.g., add tags, then assign to project)

## Security

- Only admin users can perform bulk operations
- All operations are logged for audit purposes
- JWT tokens are validated on every request
- Operations use HTTPS in production environments
