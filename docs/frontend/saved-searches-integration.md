# Saved Searches Frontend Integration

Complete Vue 3 + Quasar Framework integration guide for the saved searches feature.

## Overview

This guide documents the frontend implementation of saved searches functionality in PartsHub. The implementation follows Vue 3 Composition API patterns and Quasar Framework best practices.

## Architecture

### Component Structure

```
frontend/src/
├── services/
│   └── savedSearchesService.js          # API client layer
├── components/
│   ├── SaveSearchDialog.vue             # Save search modal
│   ├── SavedSearches.vue                # List/manage component
│   └── ComponentSearch.vue              # Integration point
└── pages/
    └── SavedSearchesPage.vue            # Management page
```

### Data Flow

```
User Action
  ↓
Component Event Handler
  ↓
API Service Method
  ↓
Backend Endpoint
  ↓
Response/Error
  ↓
Update Local State
  ↓
Notify User
```

## Components

### SaveSearchDialog.vue

Modal dialog for creating new saved searches.

**Props:**
- `modelValue` (Boolean) - v-model for dialog visibility
- `searchParameters` (Object) - Current search parameters to save

**Emits:**
- `update:modelValue` - Dialog visibility changes
- `saved` - Search saved successfully (payload: SavedSearch object)

**Features:**
- Form validation (name 1-100 chars, description max 500 chars)
- Search parameters preview (expandable)
- Loading states during API calls
- Success/error notifications

**Usage:**
```vue
<template>
  <save-search-dialog
    v-model="showDialog"
    :search-parameters="currentParams"
    @saved="handleSaved"
  />
</template>

<script setup>
import SaveSearchDialog from './SaveSearchDialog.vue'
import { ref } from 'vue'

const showDialog = ref(false)
const currentParams = ref({
  search: 'resistor',
  searchType: 'unified',
  limit: 20,
  providers: []
})

const handleSaved = (savedSearch) => {
  console.log('Saved:', savedSearch)
}
</script>
```

### SavedSearches.vue

Dual-mode component for displaying and managing saved searches.

**Props:**
- `compact` (Boolean, default: false) - Enable compact dropdown mode
- `maxItems` (Number, default: 5) - Max items in compact mode

**Emits:**
- `execute` - User wants to execute search (payload: searchId)
- `view-all` - User clicked "view all" in compact mode
- `updated` - Search list changed (for refresh triggers)

**Modes:**

1. **Compact Mode** (for dropdowns):
   - Shows recent searches (default 5)
   - Click to execute
   - "View all" link if more exist

2. **Full Mode** (for management page):
   - Complete list with pagination (20 per page)
   - Sorting controls (name, created_at, last_used_at)
   - CRUD action buttons (execute, edit, duplicate, delete)
   - Empty state handling

**Usage - Compact:**
```vue
<q-btn-dropdown label="Saved Searches" icon="bookmark">
  <saved-searches
    compact
    :max-items="5"
    @execute="handleExecute"
  />
</q-btn-dropdown>
```

**Usage - Full:**
```vue
<saved-searches
  @execute="handleExecute"
  @updated="refreshData"
/>
```

### ComponentSearch.vue Integration

Modified to support saved searches functionality.

**New State:**
- `showSaveDialog` - Controls save dialog visibility
- `hasSearched` - Tracks if user has performed a search
- `currentSearchParameters` - Computed property with current search state

**New Methods:**
- `handleExecuteSavedSearch(searchId)` - Loads and executes saved search
- `handleSearchSaved()` - Handles successful save notification

**Search Parameters Captured:**
```javascript
{
  search: string,           // Query text
  searchType: string,       // unified/part_number/provider_sku
  limit: number,            // Result limit
  providers: string[]       // Selected providers
}
```

**UI Changes:**
- "Save Search" button (appears after search)
- "Saved Searches" dropdown button
- Integration with SaveSearchDialog and SavedSearches components

### SavedSearchesPage.vue

Full-featured management page for power users.

**Features:**
- Statistics dashboard (total, used, unused searches)
- Most used searches section with quick access
- Complete SavedSearches component integration
- Navigation controls

**Route Configuration:**
```javascript
{
  path: '/saved-searches',
  name: 'SavedSearches',
  component: () => import('pages/SavedSearchesPage.vue'),
  meta: { requiresAuth: true }
}
```

## API Service Layer

### savedSearchesService.js

Centralized API client for all saved search operations.

**Methods:**

```javascript
// Create a new saved search
createSavedSearch(name, searchParameters, description)
  → Promise<SavedSearch>

// List saved searches with pagination and sorting
listSavedSearches({ skip, limit, sort_by, sort_order })
  → Promise<{ searches: SavedSearch[], total: number }>

// Get specific saved search
getSavedSearch(searchId)
  → Promise<SavedSearch>

// Update search name/description
updateSavedSearch(searchId, { name, description })
  → Promise<SavedSearch>

// Delete a saved search
deleteSavedSearch(searchId)
  → Promise<void>

// Execute saved search (updates last_used_at)
executeSavedSearch(searchId)
  → Promise<{ search_parameters: Object }>

// Duplicate a saved search
duplicateSavedSearch(searchId, newName)
  → Promise<SavedSearch>

// Get usage statistics
getSavedSearchesStats()
  → Promise<{ total_searches, total_used, total_unused, most_used }>
```

**Error Handling:**

All methods throw errors with consistent structure:
```javascript
try {
  await createSavedSearch(name, params)
} catch (error) {
  // error.response.data.detail contains error message
  // error.response.status contains HTTP status code
}
```

**Usage Example:**
```javascript
import {
  createSavedSearch,
  listSavedSearches,
  executeSavedSearch
} from '@/services/savedSearchesService'

// Create
const saved = await createSavedSearch(
  'My Search',
  { search: 'resistor', searchType: 'unified' },
  'Find all resistors'
)

// List with pagination
const { searches, total } = await listSavedSearches({
  skip: 0,
  limit: 20,
  sort_by: 'last_used_at',
  sort_order: 'desc'
})

// Execute
const { search_parameters } = await executeSavedSearch(searchId)
// Apply search_parameters to search form
```

## Integration Steps

### 1. Install Dependencies

No additional dependencies required. Uses existing:
- Vue 3
- Quasar Framework
- Axios
- Vue Router

### 2. Add Components

All component files should be in place:
- `frontend/src/services/savedSearchesService.js`
- `frontend/src/components/SaveSearchDialog.vue`
- `frontend/src/components/SavedSearches.vue`
- `frontend/src/pages/SavedSearchesPage.vue`

### 3. Update Router

Add route in `src/router/routes.js`:
```javascript
{
  path: '/saved-searches',
  name: 'SavedSearches',
  component: () => import('pages/SavedSearchesPage.vue'),
  meta: { requiresAuth: true }
}
```

### 4. Add Navigation (Optional)

In main layout or navigation menu:
```vue
<q-item clickable to="/saved-searches">
  <q-item-section avatar>
    <q-icon name="bookmark" />
  </q-item-section>
  <q-item-section>
    <q-item-label>Saved Searches</q-item-label>
  </q-item-section>
</q-item>
```

### 5. Verify Backend Endpoints

Ensure these API endpoints are available:
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

## Customization

### Adding Search Parameters

To track additional search parameters:

1. **Update ComponentSearch.vue:**
```javascript
const currentSearchParameters = computed(() => ({
  search: query.value,
  searchType: searchType.value,
  limit: limit.value,
  providers: selectedProviders.value,
  // Add new parameters:
  category: selectedCategory.value,
  tags: selectedTags.value
}))
```

2. **Update handleExecuteSavedSearch:**
```javascript
const params = response.search_parameters
// Apply existing parameters
query.value = params.search || ''
// Apply new parameters
selectedCategory.value = params.category || ''
selectedTags.value = params.tags || []
```

3. **Update SaveSearchDialog preview** (optional):
Add display for new parameters in the preview section.

### Styling

Override Quasar variables in `src/css/quasar.variables.scss`:
```scss
$primary: #1976d2;
$secondary: #26a69a;
```

Or use scoped styles in components:
```vue
<style scoped>
.saved-search-item:hover {
  background-color: #f5f5f5;
}
</style>
```

### Sorting Options

To add new sort fields, update SavedSearches.vue:
```javascript
const sortOptions = [
  { label: 'Name', value: 'name' },
  { label: 'Created', value: 'created_at' },
  { label: 'Last Used', value: 'last_used_at' },
  // Add new option:
  { label: 'Usage Count', value: 'usage_count' }
]
```

Ensure backend supports the new sort field.

## Error Handling

### API Errors

Components handle errors gracefully with Quasar notifications:

- **401 Unauthorized** - User not authenticated
- **403 Forbidden** - Access denied to search
- **404 Not Found** - Search doesn't exist
- **422 Validation Error** - Invalid input (shows details)
- **500 Server Error** - Backend error (generic message)

### User Notifications

Standard pattern using Quasar's notify:
```javascript
import { useQuasar } from 'quasar'

const $q = useQuasar()

// Success
$q.notify({
  type: 'positive',
  message: 'Search saved successfully',
  timeout: 2000
})

// Error
$q.notify({
  type: 'negative',
  message: 'Failed to save search',
  timeout: 3000
})
```

## Performance Considerations

### Pagination

- Default 20 items per page in full mode
- Compact mode limited to 5 items
- Efficient loading with skip/limit parameters

### Caching

No client-side caching currently implemented. Data is always fresh from API.

Consider adding Pinia store with caching if performance becomes an issue.

### Loading States

All components include proper loading indicators:
- Disabled buttons during operations
- Loading spinners on lists
- Skeleton loaders (optional enhancement)

## Testing

### Manual Testing Checklist

- [ ] Create saved search with name only
- [ ] Create saved search with name and description
- [ ] Execute saved search from dropdown
- [ ] Execute saved search from management page
- [ ] Edit saved search name
- [ ] Edit saved search description
- [ ] Duplicate saved search
- [ ] Delete saved search (with confirmation)
- [ ] Sort by name (ascending/descending)
- [ ] Sort by created date
- [ ] Sort by last used date
- [ ] Pagination (next/previous pages)
- [ ] Empty state display
- [ ] Form validation (empty name, too long)
- [ ] Mobile responsive design
- [ ] Keyboard navigation

### Unit Tests (Vitest)

Recommended test coverage:

```javascript
// Service tests
describe('savedSearchesService', () => {
  test('createSavedSearch creates search', async () => {})
  test('listSavedSearches returns paginated results', async () => {})
  test('executeSavedSearch updates last_used_at', async () => {})
})

// Component tests
describe('SaveSearchDialog', () => {
  test('validates name length', () => {})
  test('emits saved event on success', () => {})
  test('displays search parameters preview', () => {})
})

describe('SavedSearches', () => {
  test('displays compact mode correctly', () => {})
  test('handles edit operation', () => {})
  test('confirms before delete', () => {})
})
```

### Integration Tests

Test complete user flows:
- Save → Execute → Edit → Delete workflow
- Sorting and pagination
- Error handling scenarios
- Form validation edge cases

## Accessibility

All components follow WCAG 2.1 Level AA guidelines:

- Proper ARIA labels on interactive elements
- Keyboard navigation support (Tab, Enter, Escape)
- Screen reader friendly announcements
- Focus management in dialogs
- Sufficient color contrast ratios
- Clear visual feedback for actions

## Browser Support

Same as Quasar Framework:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Save Button Not Appearing

Check that `hasSearched` is set to `true` after search completes:
```javascript
const search = async () => {
  // ... perform search
  hasSearched.value = true  // Must be set
}
```

### Saved Searches Not Loading

1. Check browser console for API errors
2. Verify backend is running on correct port
3. Check CORS settings if frontend/backend on different origins
4. Verify API base URL in `boot/axios.js`

### Execute Not Working

1. Verify `executeSavedSearch` returns `search_parameters`
2. Check that parameters are being applied to form fields
3. Ensure `search()` method is called after loading parameters

### Pagination Issues

1. Verify `total` count from API response
2. Check skip/limit calculations in component
3. Ensure `currentPage` updates trigger `loadSearches()`

## Bundle Size Impact

Estimated impact on production bundle:

- savedSearchesService.js: ~4KB
- SaveSearchDialog.vue: ~6KB
- SavedSearches.vue: ~15KB
- SavedSearchesPage.vue: ~7KB
- **Total: ~32KB** (minified + gzipped: ~10KB)

## Dependencies

No new dependencies required. Uses only existing project dependencies:
- Vue 3 (Composition API)
- Quasar Framework
- Axios (API client)
- Vue Router (page routing)

## Implementation Checklist

- [x] API service layer created
- [x] Save search dialog component
- [x] Saved searches list component
- [x] Management page component
- [x] ComponentSearch.vue integration
- [ ] Router configuration
- [ ] Navigation menu link
- [ ] Manual testing complete
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Documentation complete
- [ ] Production deployment

## Related Documentation

- [User Guide](../user/saved-searches.md) - End-user documentation
- [API Reference](../api.md) - Backend API documentation
- [Component Search](../user/features.md#search-and-filtering-capabilities) - Search features
- [Quasar Framework](https://quasar.dev) - UI framework documentation
- [Vue 3 Composition API](https://vuejs.org) - Vue documentation

## Support

For technical questions or issues:

1. Check browser console for error messages
2. Review Network tab for API response details
3. Verify component props and events
4. Consult Quasar documentation for framework-specific issues
5. Submit issues through GitHub repository

---

**Version**: Implemented in PartsHub v0.5.0
**Last Updated**: 2025-10-14
