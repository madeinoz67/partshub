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
2. Enter your search criteria (search text, category filter, stock status)
3. Click "Search" to see results
4. After results appear, click the **"Save Search"** button
5. Enter a descriptive name (required)
6. Optionally add a description to help remember what this search is for
7. Review the search parameters that will be saved
8. Click "Save Search"

A success notification will confirm your search has been saved.

### Using a Saved Search

#### From the Saved Searches Page:

1. Navigate to the **Saved Searches** page from the main menu
2. Click the "Execute" button next to any saved search
3. You'll be automatically redirected to the Components page
4. Search parameters will be loaded and the search will execute automatically
5. A notification will confirm the saved search was loaded

#### From the Component List Page:

1. Click the **"Saved Searches"** dropdown button on the component list page
2. Select a saved search from the dropdown list
3. The search parameters automatically load and execute

Your search results will appear instantly with the saved criteria applied.

### Managing Saved Searches

Navigate to the **Saved Searches** management page to:

- View all your saved searches
- See usage statistics (total, used, unused searches)
- View your most recently used searches
- Sort by name, creation date, or last used date
- Execute any saved search
- Edit search names and descriptions
- Duplicate searches for variations
- Delete searches you no longer need

## Features

### Search Parameters Saved

When you save a search, the following parameters are captured (as of v0.5.0):

- **Search Query** - The text search term entered in the search field
- **Category Filter** - Selected component category (e.g., "passive", "active", "mechanical")
- **Stock Status Filter** - Stock level filter (e.g., "low", "critical", "available", "out_of_stock")

Note: Only non-empty parameters are saved. If you leave a field blank, it won't be included in the saved search.

### Search Parameter Visibility

When you execute a saved search:

- Search parameters automatically populate the search form fields
- You can see exactly what filters are active
- You can modify the parameters and perform a new search
- You can save the modified search as a new saved search

### Statistics Dashboard

The Saved Searches management page displays useful statistics:

- **Total Searches** - How many searches you've saved
- **Used Searches** - Searches you've executed at least once
- **Unused Searches** - Searches you haven't used yet
- **Most Recent Search** - Your most recently executed search with quick-access execute button

### Sorting and Pagination

The full management view includes:

- Sort by name (A-Z or Z-A)
- Sort by creation date (newest or oldest first)
- Sort by last used date (most recent first)
- Pagination controls for large lists (20 searches per page)

## Common Use Cases

### Monitoring Low Stock

Create a saved search for components with low stock levels and check it regularly:

1. Set the stock status filter to "low"
2. Optionally add a search term or category
3. Click "Search"
4. Save as "Low Stock Check"
5. Execute periodically to monitor inventory

### Category Browsing

Save searches for each component category you work with frequently:

1. Select a category filter (e.g., "passive components")
2. Click "Search"
3. Save as "Passive Components"
4. Quickly access all components in that category

### Combining Filters

Create searches with multiple criteria:

1. Enter search text: "resistor"
2. Select category: "passive"
3. Select stock status: "available"
4. Click "Search"
5. Save as "Available Resistors"
6. Quickly find in-stock resistors when needed

### Project Component Tracking

Save searches for components related to specific projects:

1. Enter a search term that matches your project
2. Apply relevant category or stock filters
3. Save as "Project Name - Components"
4. Easily find all relevant parts when working on the project

### Category Management

Create saved searches for each component category:

1. Search for resistors, capacitors, ICs, etc.
2. Save with descriptive category names
3. Quick access to browse component types

## Tips and Best Practices

### Naming Conventions

Use clear, descriptive names for your saved searches:

- Good: "Resistors - Low Stock"
- Good: "Passive Components - Available"
- Good: "Capacitors - All Categories"
- Avoid: "Search 1", "Test", "Temp"

### Adding Descriptions

Include context in the description field:

- Why you created this search
- What you're monitoring
- When to use this search
- Special criteria or filters applied

Example: "Weekly check for passive components running low on stock. Used for ordering decisions."

### Regular Cleanup

Periodically review and delete:

- Searches you no longer use
- Duplicate searches
- Test searches created while learning the feature

### Duplicating for Variations

Instead of creating similar searches from scratch:

1. Find an existing search that's close to what you need
2. Click the "Duplicate" button
3. Give it a new name (e.g., "Critical Low Stock" from "Low Stock")
4. Execute the duplicated search
5. Modify criteria as needed (e.g., change from "low" to "critical")
6. The modified search is already saved

Note: Currently, to change search parameters in a saved search, you need to execute it, modify the criteria, and save as a new search.

## Managing Your Searches

### Editing

You can edit the **name** and **description** of saved searches through the management page:

1. Click the "Edit" icon next to the search
2. Modify the name or description
3. Click "Save"

To change search parameters:

1. Execute the saved search
2. Modify the search criteria in the search form
3. Click "Save Search" to save as a new search (with a different name)

### Deleting

To delete a saved search:

1. Click the delete icon next to the search
2. Confirm the deletion in the confirmation dialog
3. The search is permanently removed

Warning: Deletion cannot be undone. Consider duplicating important searches before experimenting with variations.

### Execution Updates

Each time you execute a saved search, the system automatically:

- Updates the **Last Used Date** timestamp
- Tracks usage for statistics
- Loads the search parameters into the search form
- Executes the search automatically
- Displays a success notification

## Keyboard Navigation

All saved search components support keyboard navigation:

- **Tab** - Move between interactive elements
- **Enter/Space** - Activate buttons and execute searches
- **Escape** - Close dialogs

## Mobile Support

Saved searches work seamlessly on mobile devices:

- Responsive dropdown interface on component list page
- Touch-optimized buttons
- Full management page accessible on mobile
- All features available on smaller screens

## Troubleshooting

### Save Button Not Appearing

The "Save Search" button only appears after you've performed a search with results. If you don't see it:

1. Ensure you've clicked the "Search" button
2. Verify that search results are displayed
3. Check that you're logged in (authentication required)

### Saved Search Not Loading

If a saved search won't execute:

1. Check your internet connection
2. Try refreshing the page
3. Verify the search still exists in your saved list
4. Check browser console for error messages
5. Ensure you're logged in with a valid session

### Missing Saved Searches

If your saved searches disappeared:

1. Verify you're logged in with the correct account
2. Check if sorting is hiding the search (try sorting by "name" or "created date")
3. Try refreshing the page
4. Check that filters or pagination aren't hiding the search
5. Contact support if searches are truly missing

### Parameters Not Loading

If search parameters don't populate when executing a saved search:

1. Verify you're on the Components page after execution
2. Check the browser console for errors
3. Try refreshing the page and executing again
4. Verify the saved search still exists
5. Check that the search parameters are valid

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
- Metadata (creation date, last used date)
- User association

No actual search results are stored - only the parameters needed to re-run the search.

### Security

- All saved search operations require authentication
- Search data is encrypted in transit (HTTPS)
- User isolation prevents cross-user access
- No sensitive component data is stored in search parameters

## Future Enhancements

Planned improvements to saved searches include:

- **Extended Parameters** - Save additional search criteria (tags, manufacturers, part numbers)
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
- [API Documentation](../api/saved-searches.md) - Technical API reference

## Support

For additional help with saved searches:

1. Check the [Features Guide](features.md) for related functionality
2. Review the [Getting Started Guide](getting-started.md) for general PartsHub usage
3. Submit questions or issues through the GitHub repository
4. Contact your system administrator for account-related issues

---

**Version**: Added in PartsHub v0.5.0
**Last Updated**: 2025-10-15
