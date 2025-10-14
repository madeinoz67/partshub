# Saved Searches Guide

Save and reuse your component search queries to streamline your inventory management workflow.

## Overview

Saved Searches allow you to store frequently used search parameters and quickly re-execute them with a single click. This feature is particularly useful for:

- Monitoring specific component categories
- Tracking low-stock items
- Finding components by manufacturer
- Reusing complex multi-criteria searches

## Quick Start

### Saving a Search

1. Go to the Component Search page
2. Enter your search criteria and click "Search"
3. After results appear, click the **"Save Search"** button
4. Enter a descriptive name (required)
5. Optionally add a description to help remember what this search is for
6. Click "Save Search"

A success notification will confirm your search has been saved.

### Using a Saved Search

1. Click the **"Saved Searches"** dropdown button on the search page
2. Select a saved search from the list
3. The search parameters automatically load and execute

Your search results will appear instantly with the saved criteria applied.

### Managing Saved Searches

Navigate to the Saved Searches management page (or use the "View all" link in the dropdown) to:

- View all your saved searches
- Sort by name, creation date, or last used date
- Execute any saved search
- Edit search names and descriptions
- Duplicate searches for variations
- Delete searches you no longer need

## Features

### Search Parameters Saved

When you save a search, the following parameters are captured:

- **Search Query** - The text search term
- **Search Type** - unified, part_number, or provider_sku
- **Result Limit** - Number of results to display
- **Provider Filters** - Selected component providers

### Statistics Dashboard

The Saved Searches management page displays useful statistics:

- **Total Searches** - How many searches you've saved
- **Used Searches** - Searches you've executed at least once
- **Unused Searches** - Searches you haven't used yet
- **Most Used Searches** - Your top 5 most frequently used searches with quick-access execute buttons

### Sorting and Pagination

The full management view includes:

- Sort by name (A-Z or Z-A)
- Sort by creation date (newest or oldest first)
- Sort by last used date (most recent first)
- Pagination controls for large lists (20 searches per page)

## Common Use Cases

### Monitoring Low Stock

Create a saved search for components with low stock levels and check it regularly:

1. Search for components with your low-stock criteria
2. Save as "Low Stock Check"
3. Execute periodically to monitor inventory

### Manufacturer-Specific Searches

Save searches for your frequently ordered manufacturers:

1. Search for a specific manufacturer
2. Save as "Manufacturer Name - Components"
3. Quickly access all components from that manufacturer

### Project Component Tracking

Save searches for components related to specific projects:

1. Use tags or descriptions that match your project
2. Save as "Project Name - Components"
3. Easily find all relevant parts when working on the project

### Category Management

Create saved searches for each component category:

1. Search for resistors, capacitors, ICs, etc.
2. Save with descriptive category names
3. Quick access to browse component types

## Tips and Best Practices

### Naming Conventions

Use clear, descriptive names for your saved searches:

- Good: "Resistors - 1% Tolerance - Low Stock"
- Good: "STMicroelectronics - All ICs"
- Avoid: "Search 1", "Test", "Temp"

### Adding Descriptions

Include context in the description field:

- Why you created this search
- What you're monitoring
- When to use this search
- Special criteria or filters applied

### Regular Cleanup

Periodically review and delete:

- Searches you no longer use
- Duplicate searches
- Test searches

### Duplicating for Variations

Instead of creating similar searches from scratch:

1. Find an existing search that's close to what you need
2. Click the "Duplicate" button
3. Give it a new name
4. Execute and adjust criteria as needed
5. Save the updated search

## Managing Your Searches

### Editing

You can edit the **name** and **description** of saved searches, but not the search parameters themselves. To change search parameters:

1. Execute the saved search
2. Modify the search criteria
3. Save as a new search

### Deleting

To delete a saved search:

1. Click the delete icon next to the search
2. Confirm the deletion in the dialog
3. The search is permanently removed

Warning: Deletion cannot be undone. Consider duplicating important searches before experimenting with variations.

### Execution Updates

Each time you execute a saved search, the system updates:

- **Last Used Date** - Timestamp of most recent execution
- **Usage Statistics** - Tracked for "Most Used" rankings

## Keyboard Navigation

All saved search components support keyboard navigation:

- **Tab** - Move between interactive elements
- **Enter/Space** - Activate buttons and execute searches
- **Escape** - Close dialogs

## Mobile Support

Saved searches work seamlessly on mobile devices:

- Responsive dropdown interface
- Touch-optimized buttons
- Full management page accessible on mobile

## Troubleshooting

### Save Button Not Appearing

The "Save Search" button only appears after you've performed a search with results. If you don't see it:

1. Ensure you've clicked the "Search" button
2. Verify that search results are displayed
3. Check that you're logged in (if authentication is required)

### Saved Search Not Loading

If a saved search won't execute:

1. Check your internet connection
2. Try refreshing the page
3. Verify the search still exists in your saved list
4. Check browser console for error messages

### Missing Saved Searches

If your saved searches disappeared:

1. Verify you're logged in with the correct account
2. Check if filters or sorting are hiding the search
3. Try refreshing the page
4. Contact support if searches are truly missing

## Privacy and Data

### User-Specific Searches

Saved searches are specific to your user account. Other users cannot:

- See your saved searches
- Execute your saved searches
- Modify or delete your saved searches

### Data Storage

Saved search data includes:

- Search name and description
- Search parameters (as JSON)
- Metadata (creation date, last used date, usage count)
- User association

No actual search results are stored - only the parameters needed to re-run the search.

## Future Enhancements

Planned improvements to saved searches include:

- **Shared Searches** - Share searches with team members
- **Search Folders** - Organize searches into categories
- **Search Tags** - Tag searches for better organization
- **Export/Import** - Export searches as JSON files
- **Search Templates** - Pre-defined search templates for common tasks
- **Scheduled Searches** - Auto-execute searches on a schedule
- **Search Alerts** - Get notified when search results change

## Related Documentation

- [Component Search](features.md#search-and-filtering-capabilities) - Learn about search capabilities
- [Bulk Operations](bulk-operations.md) - Perform actions on multiple components
- [Stock Operations](stock-operations.md) - Manage component inventory

## Support

For additional help with saved searches:

1. Check the [Features Guide](features.md) for related functionality
2. Review the [Getting Started Guide](getting-started.md) for general PartsHub usage
3. Submit questions or issues through the GitHub repository

---

**Version**: Added in PartsHub v0.5.0
**Last Updated**: 2025-10-14
