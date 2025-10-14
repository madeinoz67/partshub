# Saved Searches - Quick Start Guide

## Usage Overview

### For Users

#### Saving a Search
1. Go to Component Search page
2. Enter search criteria and click "Search"
3. After results appear, click **"Save Search"** button
4. Enter a name (required) and optional description
5. Click "Save Search" - done!

#### Using a Saved Search
1. Click **"Saved Searches"** dropdown button
2. Select a search from the list
3. Search parameters load and execute automatically

#### Managing Saved Searches
1. Navigate to `/saved-searches` page (or add to menu)
2. View statistics and most used searches
3. Use action buttons:
   - **Play** icon - Execute search
   - **Edit** icon - Change name/description
   - **Copy** icon - Duplicate search
   - **Delete** icon - Remove search

### For Developers

#### Quick Integration Test

```bash
# 1. Ensure backend is running
cd backend && uvicorn src.main:app --reload

# 2. Start frontend dev server
cd frontend && npm run dev

# 3. Navigate to search page
open http://localhost:9000/search  # or your dev URL

# 4. Test the flow:
#    - Perform a search
#    - Click "Save Search"
#    - Fill form and save
#    - Click "Saved Searches" dropdown
#    - Select your saved search
#    - Verify it executes
```

## Component Usage

### SaveSearchDialog

```vue
<template>
  <div>
    <q-btn @click="showDialog = true">Save Search</q-btn>

    <save-search-dialog
      v-model="showDialog"
      :search-parameters="currentParams"
      @saved="handleSaved"
    />
  </div>
</template>

<script>
import SaveSearchDialog from './SaveSearchDialog.vue'

export default {
  components: { SaveSearchDialog },
  setup() {
    const showDialog = ref(false)
    const currentParams = ref({
      search: 'resistor',
      searchType: 'unified',
      limit: 20
    })

    const handleSaved = (savedSearch) => {
      console.log('Saved:', savedSearch)
    }

    return { showDialog, currentParams, handleSaved }
  }
}
</script>
```

### SavedSearches (Compact Mode)

```vue
<template>
  <q-btn-dropdown label="Saved Searches" icon="bookmark">
    <saved-searches
      compact
      :max-items="5"
      @execute="handleExecute"
    />
  </q-btn-dropdown>
</template>

<script>
import SavedSearches from './SavedSearches.vue'

export default {
  components: { SavedSearches },
  setup() {
    const handleExecute = (searchId) => {
      console.log('Execute:', searchId)
    }

    return { handleExecute }
  }
}
</script>
```

### SavedSearches (Full Mode)

```vue
<template>
  <q-card>
    <q-card-section>
      <saved-searches
        :compact="false"
        @execute="handleExecute"
        @updated="handleUpdated"
      />
    </q-card-section>
  </q-card>
</template>

<script>
import SavedSearches from './SavedSearches.vue'

export default {
  components: { SavedSearches },
  setup() {
    const handleExecute = (searchId) => {
      console.log('Execute:', searchId)
    }

    const handleUpdated = () => {
      console.log('List updated')
    }

    return { handleExecute, handleUpdated }
  }
}
</script>
```

## API Service Usage

```javascript
import {
  createSavedSearch,
  listSavedSearches,
  executeSavedSearch,
  updateSavedSearch,
  deleteSavedSearch,
  duplicateSavedSearch,
  getSavedSearchesStats
} from '../services/savedSearchesService'

// Create a saved search
const savedSearch = await createSavedSearch(
  'My Search',
  { search: 'resistor', searchType: 'unified' },
  'Optional description'
)

// List saved searches with pagination
const { searches, total } = await listSavedSearches({
  skip: 0,
  limit: 20,
  sort_by: 'created_at',
  sort_order: 'desc'
})

// Execute a saved search
const { search_parameters } = await executeSavedSearch(searchId)
// Apply search_parameters to your search form

// Update a saved search
const updated = await updateSavedSearch(searchId, {
  name: 'New Name',
  description: 'New description'
})

// Duplicate a saved search
const duplicate = await duplicateSavedSearch(searchId, 'Copy of My Search')

// Delete a saved search
await deleteSavedSearch(searchId)

// Get statistics
const stats = await getSavedSearchesStats()
// stats: { total_searches, total_used, total_unused, most_used: [...] }
```

## Router Setup (Optional)

Add to `src/router/routes.js`:

```javascript
const routes = [
  // ... existing routes
  {
    path: '/saved-searches',
    name: 'SavedSearches',
    component: () => import('pages/SavedSearchesPage.vue'),
    meta: {
      requiresAuth: true  // if using authentication
    }
  }
]
```

## Navigation Link (Optional)

Add to your main layout:

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

## Customization Examples

### Custom Search Parameters

To save additional parameters:

```javascript
// In ComponentSearch.vue
const currentSearchParameters = computed(() => ({
  search: query.value,
  searchType: searchType.value,
  limit: limit.value,
  providers: selectedProviders.value,
  // Add your custom parameters:
  category: selectedCategory.value,
  stockStatus: stockFilter.value,
  tags: selectedTags.value
}))

// In handleExecuteSavedSearch
const params = response.search_parameters
query.value = params.search || ''
searchType.value = params.searchType || 'unified'
limit.value = params.limit || 20
selectedProviders.value = params.providers || []
// Apply your custom parameters:
selectedCategory.value = params.category || ''
stockFilter.value = params.stockStatus || ''
selectedTags.value = params.tags || []
```

### Custom Styling

```vue
<style>
/* Override Quasar variables in src/css/quasar.variables.scss */
$primary: #1976d2;
$secondary: #26a69a;
$positive: #21ba45;
$negative: #c10015;

/* Or use scoped styles in components */
.saved-searches-dropdown {
  min-width: 400px;
}

.saved-search-item:hover {
  background-color: #f5f5f5;
}
</style>
```

## Troubleshooting

### Issue: Save button not appearing
**Solution**: Check that `hasSearched` is `true` after search completes

### Issue: Saved searches not loading
**Solution**:
1. Check browser console for API errors
2. Verify backend is running on correct port
3. Check CORS settings

### Issue: Execute not working
**Solution**:
1. Verify `executeSavedSearch` returns `search_parameters`
2. Check that parameters are being applied to form
3. Ensure `search()` is called after loading parameters

### Issue: Delete confirmation not showing
**Solution**: Check that `showDeleteDialog` ref is properly bound to q-dialog

## Testing Checklist

Quick manual test:
- [ ] Perform a search
- [ ] Save the search
- [ ] Open saved searches dropdown
- [ ] Execute the saved search
- [ ] Edit the search name
- [ ] Duplicate the search
- [ ] Delete the duplicate
- [ ] Check statistics page
- [ ] Test on mobile

## Common Patterns

### Loading State Pattern
```javascript
const loading = ref(false)

const doSomething = async () => {
  loading.value = true
  try {
    await apiCall()
    // success
  } catch (error) {
    // handle error
  } finally {
    loading.value = false
  }
}
```

### Notification Pattern
```javascript
import { useQuasar } from 'quasar'

const $q = useQuasar()

// Success
$q.notify({
  type: 'positive',
  message: 'Success!',
  timeout: 2000
})

// Error
$q.notify({
  type: 'negative',
  message: 'Error occurred',
  timeout: 3000
})

// Info
$q.notify({
  type: 'info',
  message: 'Information',
  timeout: 2000
})
```

### Form Validation Pattern
```vue
<q-input
  v-model="name"
  :rules="[
    val => !!val || 'Required',
    val => val.length >= 1 || 'Too short',
    val => val.length <= 100 || 'Too long'
  ]"
/>
```

## Performance Tips

1. **Pagination**: Always use pagination for large lists
2. **Compact Mode**: Limit to 5-10 items in dropdowns
3. **Debounce**: Consider debouncing search input
4. **Cache**: Add client-side caching if needed

## Accessibility Tips

1. **ARIA Labels**: Add to all interactive elements
2. **Keyboard Nav**: Test tab navigation
3. **Screen Reader**: Test with screen reader
4. **Focus Management**: Ensure focus is managed in dialogs

## Support

For detailed information, see:
- `frontend/SAVED_SEARCHES_INTEGRATION.md` - Complete integration guide
- `SAVED_SEARCHES_IMPLEMENTATION_SUMMARY.md` - Implementation details
- Quasar documentation: https://quasar.dev
- Vue 3 documentation: https://vuejs.org
