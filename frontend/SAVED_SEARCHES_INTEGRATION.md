# Saved Searches Frontend Integration Guide

## Overview

This document describes the complete Vue 3 frontend integration for the saved searches functionality in PartsHub.

## Files Created

### 1. API Service Layer
**File:** `src/services/savedSearchesService.js`

Provides typed API methods for all saved search operations:
- `createSavedSearch(name, searchParameters, description)` - Create new saved search
- `listSavedSearches(options)` - Get paginated list with sorting
- `getSavedSearch(searchId)` - Get specific search details
- `updateSavedSearch(searchId, updates)` - Update name/description
- `deleteSavedSearch(searchId)` - Delete saved search
- `executeSavedSearch(searchId)` - Execute and update last_used_at
- `duplicateSavedSearch(searchId, newName)` - Duplicate a search
- `getSavedSearchesStats()` - Get usage statistics

All methods include comprehensive JSDoc comments with type definitions.

### 2. Save Search Dialog
**File:** `src/components/SaveSearchDialog.vue`

Modal dialog for saving current search parameters:
- Name input (required, 1-100 characters) with validation
- Description input (optional, max 500 characters)
- Search parameters preview (expandable)
- Form validation using Quasar's validation rules
- Loading state during save operation
- Success/error notifications

**Props:**
- `modelValue` (Boolean) - v-model for dialog visibility
- `searchParameters` (Object) - Current search parameters to save

**Emits:**
- `update:modelValue` - Dialog visibility changes
- `saved` - Search saved successfully (passes SavedSearch object)

### 3. Saved Searches List Component
**File:** `src/components/SavedSearches.vue`

Displays and manages user's saved searches with two modes:

#### Compact Mode (for dropdown)
- Simple list of recent searches (default 5)
- Click to execute
- "View all" link if more searches exist

#### Full Mode (for page view)
- Complete list with pagination (20 per page)
- Sorting controls (name, created_at, last_used_at)
- Action buttons per search:
  - Execute (loads and runs search)
  - Edit (name/description only)
  - Duplicate (creates copy)
  - Delete (with confirmation)
- Empty state when no searches
- Loading states

**Props:**
- `compact` (Boolean, default: false) - Enable compact mode
- `maxItems` (Number, default: 5) - Max items in compact mode

**Emits:**
- `execute` - User wants to execute search (passes searchId)
- `view-all` - User clicked "view all" in compact mode
- `updated` - Search list changed (for refresh)

### 4. ComponentSearch.vue Integration
**File:** `src/components/ComponentSearch.vue` (MODIFIED)

Added saved search functionality to existing search component:

**New UI Elements:**
- "Save Search" button (appears after search is performed)
- "Saved Searches" dropdown button (shows compact list)

**New State:**
- `showSaveDialog` - Controls save dialog visibility
- `hasSearched` - Tracks if user has performed a search
- `currentSearchParameters` - Computed property with current search state

**New Methods:**
- `handleExecuteSavedSearch(searchId)` - Loads and executes saved search
- `handleSearchSaved()` - Handles successful save notification

**Search Parameters Saved:**
- `search` - Query string
- `searchType` - unified/part_number/provider_sku
- `limit` - Result limit
- `providers` - Selected provider filters

### 5. Saved Searches Management Page (Optional)
**File:** `src/pages/SavedSearchesPage.vue`

Full-featured page for power users:
- Statistics cards (total, used, unused searches)
- "Most Used Searches" section with quick access
- Complete saved searches list with all management features
- Navigate back to search page

## Integration Steps

### Step 1: Verify Backend Endpoints

Ensure these endpoints are available:
```
POST   /api/v1/saved-searches
GET    /api/v1/saved-searches
GET    /api/v1/saved-searches/{id}
PUT    /api/v1/saved-searches/{id}
DELETE /api/v1/saved-searches/{id}
POST   /api/v1/saved-searches/{id}/execute
POST   /api/v1/saved-searches/{id}/duplicate
GET    /api/v1/saved-searches/stats
```

### Step 2: Update Router (if using management page)

Add route to `src/router/routes.js`:
```javascript
{
  path: '/saved-searches',
  name: 'SavedSearches',
  component: () => import('pages/SavedSearchesPage.vue'),
  meta: { requiresAuth: true } // if using authentication
}
```

### Step 3: Add Navigation Link (optional)

In your main layout or navigation:
```vue
<q-item clickable @click="$router.push('/saved-searches')">
  <q-item-section avatar>
    <q-icon name="bookmark" />
  </q-item-section>
  <q-item-section>
    <q-item-label>Saved Searches</q-item-label>
  </q-item-section>
</q-item>
```

### Step 4: Test the Integration

1. **Test Save Search:**
   - Perform a search in ComponentSearch
   - Click "Save Search" button
   - Fill in name and description
   - Verify search is saved

2. **Test Execute Saved Search:**
   - Click "Saved Searches" dropdown
   - Select a saved search
   - Verify it loads and executes

3. **Test Management:**
   - Edit a search name/description
   - Duplicate a search
   - Delete a search (with confirmation)
   - Check sorting and pagination

4. **Test Statistics Page:**
   - Navigate to /saved-searches
   - Verify statistics display correctly
   - Check "Most Used" section

## Error Handling

All components handle errors gracefully with Quasar notifications:

### API Errors
- **401 Unauthorized** - User not authenticated (redirect to login if needed)
- **403 Forbidden** - Access denied to search
- **404 Not Found** - Search doesn't exist
- **422 Validation Error** - Invalid input (shows error details)
- **500 Server Error** - Backend error (shows generic message)

### User Notifications
- **Success** - Green notification with checkmark
- **Error** - Red notification with error icon
- **Info** - Blue notification for informational messages

## Accessibility Features

All components include:
- Proper ARIA labels
- Keyboard navigation support
- Screen reader friendly
- Focus management in dialogs
- Clear visual feedback

## Performance Considerations

### Pagination
- Default 20 items per page
- Compact mode limited to 5 items
- Efficient loading with skip/limit

### Caching
- No client-side caching (always fresh data)
- Consider adding if needed for performance

### Loading States
- Skeletons/spinners during API calls
- Disabled states to prevent double-clicks
- Loading indicators on buttons

## Customization Options

### Styling
All components use Quasar's design system. Customize via:
- Quasar variables in `src/css/quasar.variables.scss`
- Component-specific styles in scoped `<style>` blocks

### Search Parameters
To add new search parameters:

1. Update `SaveSearchDialog.vue` preview section
2. Update `ComponentSearch.vue` `currentSearchParameters` computed
3. Update `handleExecuteSavedSearch` to apply new parameters
4. Update backend SavedSearchCreate schema if needed

### Sorting Options
To add new sort fields:

1. Update `SavedSearches.vue` sorting buttons
2. Update backend `list_saved_searches` sort_by validation
3. Update API service `listSavedSearches` JSDoc

## Testing Checklist

- [ ] Create saved search with name only
- [ ] Create saved search with name and description
- [ ] Execute saved search from dropdown
- [ ] Execute saved search from management page
- [ ] Edit saved search name
- [ ] Edit saved search description
- [ ] Duplicate saved search
- [ ] Delete saved search (confirm/cancel)
- [ ] Sort by name (asc/desc)
- [ ] Sort by created date
- [ ] Sort by last used date
- [ ] Pagination (next/previous)
- [ ] Empty state display
- [ ] Loading states
- [ ] Error handling (network errors)
- [ ] Form validation (empty name, too long)
- [ ] Mobile responsive design
- [ ] Keyboard navigation
- [ ] Screen reader compatibility

## Future Enhancements

Potential improvements to consider:

1. **Shared Searches** - Share searches between users
2. **Search Folders** - Organize searches into folders
3. **Search Tags** - Tag searches for better organization
4. **Export/Import** - Export searches as JSON
5. **Search Templates** - Pre-defined search templates
6. **Search History** - Track search execution history
7. **Scheduled Searches** - Auto-execute searches on schedule
8. **Search Alerts** - Notify when search results change

## Troubleshooting

### Saved Searches Not Loading
- Check browser console for API errors
- Verify backend is running on correct port
- Check CORS settings if frontend/backend on different domains

### Save Button Not Appearing
- Verify `hasSearched` is set to `true` after search
- Check if search was successful (check searchResults)

### Execute Not Working
- Verify executeSavedSearch API returns search_parameters
- Check that parameters are being applied correctly
- Ensure search() method is called after loading parameters

### Pagination Not Working
- Check total count from API
- Verify skip/limit calculations
- Ensure currentPage updates trigger loadSearches

## Support

For issues or questions:
1. Check browser console for errors
2. Verify API responses in Network tab
3. Check component props and emits
4. Review Quasar documentation for component usage

## License

Same as PartsHub project license.
