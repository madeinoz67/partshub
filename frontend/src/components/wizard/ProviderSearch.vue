<script setup lang="ts">
/**
 * ProviderSearch Component
 * Step 3 (for linked parts): Search for parts in the selected provider
 */

import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useWizardStore } from '../../stores/wizardStore'
import type { ProviderPart } from '../../types/wizard'

const $q = useQuasar()
const wizardStore = useWizardStore()

// Local state
const searchInput = ref(wizardStore.searchQuery)
const selectedPartNumber = ref<string | null>(
  wizardStore.selectedPart?.part_number || null
)
const selectedRows = ref<ProviderPart[]>([])
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)
const lastSearchQuery = ref<string>('')  // Track last search to prevent duplicates
const isSelecting = ref<boolean>(false)  // Prevent searches during selection

// Table columns
const columns = [
  {
    name: 'part_number',
    label: 'Part Number',
    field: 'part_number',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'name',
    label: 'Description',
    field: 'name',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'manufacturer',
    label: 'Manufacturer',
    field: 'manufacturer',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'datasheet',
    label: 'Datasheet',
    field: 'datasheet_url',
    align: 'center' as const,
  },
]

/**
 * Debounced search handler
 */
function onSearchInput(value: string) {
  console.log('[ProviderSearch] ========================================')
  console.log('[ProviderSearch] onSearchInput called with:', JSON.stringify(value), 'length:', value.length)
  console.log('[ProviderSearch] Current searchInput:', JSON.stringify(searchInput.value))
  console.log('[ProviderSearch] Last search query:', JSON.stringify(lastSearchQuery.value))
  console.log('[ProviderSearch] isSelecting:', isSelecting.value)
  console.log('[ProviderSearch] ========================================')

  // CRITICAL: Don't process input changes during selection
  if (isSelecting.value) {
    console.log('[ProviderSearch] !!! IGNORING input change during selection')
    return
  }

  // Also ignore if we have a selected part and results (prevents clearing after selection)
  if (wizardStore.selectedPart && wizardStore.searchResults.length > 0) {
    console.log('[ProviderSearch] !!! Part already selected, ignoring spurious input event')
    return
  }

  searchInput.value = value

  // Clear any pending search
  if (searchTimeout.value) {
    console.log('[ProviderSearch] Clearing pending timeout')
    clearTimeout(searchTimeout.value)
  }

  // Don't search for empty or very short queries
  if (!value || value.length < 2) {
    console.log('[ProviderSearch] Query too short, skipping search')
    return
  }

  // Debounce search by 300ms
  console.log('[ProviderSearch] Scheduling search in 300ms for:', JSON.stringify(value))
  searchTimeout.value = setTimeout(() => {
    performSearch(value)
  }, 300)
}

/**
 * Perform the actual search
 */
async function performSearch(query: string) {
  console.log('[ProviderSearch] *** performSearch called with:', JSON.stringify(query))
  console.log('[ProviderSearch] *** lastSearchQuery:', JSON.stringify(lastSearchQuery.value))
  console.log('[ProviderSearch] *** current results count:', wizardStore.searchResults.length)

  // Skip if this is the same query we just searched for
  if (query === lastSearchQuery.value) {
    console.log('[ProviderSearch] !!! SKIPPING - duplicate search detected')
    return
  }

  // Skip if query is too short (defensive check)
  if (!query || query.length < 2) {
    console.log('[ProviderSearch] !!! SKIPPING - query too short in performSearch')
    return
  }

  console.log('[ProviderSearch] >>> Executing search for:', JSON.stringify(query))
  lastSearchQuery.value = query
  await wizardStore.searchProvider(query)
}

/**
 * Handle selection change
 */
function onSelectionChange(selected: ProviderPart[]) {
  console.log('[ProviderSearch] Selection changed:', selected)

  // Set flag to prevent search input from triggering during selection
  isSelecting.value = true

  if (selected && selected.length > 0) {
    const row = selected[0]
    console.log('[ProviderSearch] Part selected:', row.part_number)
    selectedPartNumber.value = row.part_number
    wizardStore.selectPart(row)

    $q.notify({
      type: 'positive',
      message: `Selected: ${row.part_number}`,
      position: 'top',
    })
  } else {
    console.log('[ProviderSearch] Selection cleared')
    selectedPartNumber.value = null
  }

  // Clear the flag after a longer delay to allow background detail fetch
  setTimeout(() => {
    isSelecting.value = false
    console.log('[ProviderSearch] Selection complete, re-enabling search input')
  }, 500)
}

/**
 * Switch to local part creation
 */
function switchToLocal() {
  $q.dialog({
    title: 'Switch to Local Part',
    message: 'Do you want to create a local part instead?',
    cancel: true,
    persistent: false,
  }).onOk(() => {
    wizardStore.selectPartType('local')
    wizardStore.setStep(1)
  })
}

// Watch for external query changes (only update if different to prevent loops)
watch(() => wizardStore.searchQuery, (newValue, oldValue) => {
  console.log('[ProviderSearch] wizardStore.searchQuery changed from:', oldValue, 'to:', newValue, 'current searchInput:', searchInput.value)

  // NEVER allow the watcher to modify searchInput - it creates loops
  // The input should only be updated by user typing
  console.log('[ProviderSearch] Ignoring searchQuery watcher to prevent reactive loops')
  return

  /* DISABLED TO PREVENT LOOPS
  // Don't update if we already have the right value
  if (searchInput.value === newValue) {
    console.log('[ProviderSearch] searchInput already matches, skipping update')
    return
  }

  // Prevent clearing the input if we have results showing
  if (!newValue && wizardStore.searchResults.length > 0) {
    console.warn('[ProviderSearch] Preventing search input clear while results are displayed')
    return
  }

  console.log('[ProviderSearch] Updating searchInput to:', newValue)
  searchInput.value = newValue
  */
})

// Watch for search results changes
watch(() => wizardStore.searchResults, (newResults) => {
  console.log('[ProviderSearch] Search results changed. Count:', newResults.length)
}, { deep: true })
</script>

<template>
  <div class="provider-search">
    <p class="text-body1 q-mb-md">
      Search for parts in {{ wizardStore.selectedProvider?.name }}:
    </p>

    <!-- Search Input -->
    <q-input
      v-model="searchInput"
      outlined
      placeholder="Enter part number or description..."
      @update:model-value="(val: string | number | null) => onSearchInput(String(val || ''))"
      class="q-mb-md"
      autocomplete="off"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>
      <template v-slot:append>
        <q-spinner v-if="wizardStore.isLoading" color="primary" size="20px" />
        <q-icon
          v-else-if="searchInput"
          name="clear"
          class="cursor-pointer"
          @click="searchInput = ''; lastSearchQuery = ''"
        />
      </template>
    </q-input>

    <!-- Search Results Table -->
    <q-table
      v-if="wizardStore.searchResults.length > 0"
      :rows="wizardStore.searchResults"
      :columns="columns"
      row-key="part_number"
      :loading="wizardStore.isLoading"
      v-model:selected="selectedRows"
      selection="single"
      flat
      bordered
      class="search-results-table"
      @update:selected="onSelectionChange"
    >
      <template v-slot:body-cell-datasheet="props">
        <q-td :props="props">
          <a
            v-if="props.row.datasheet_url"
            :href="props.row.datasheet_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-decoration-none"
          >
            <q-btn
              flat
              dense
              round
              icon="description"
              color="primary"
            >
              <q-tooltip>View Datasheet</q-tooltip>
            </q-btn>
          </a>
          <span v-else class="text-grey-5">-</span>
        </q-td>
      </template>

      <template v-slot:body-cell-manufacturer="props">
        <q-td :props="props">
          {{ props.row.manufacturer || '-' }}
        </q-td>
      </template>
    </q-table>

    <!-- No Results Message -->
    <div
      v-if="!wizardStore.isLoading && searchInput.length >= 2 && wizardStore.searchResults.length === 0"
      class="text-center q-py-xl"
    >
      <q-icon name="search_off" size="64px" color="grey-5" />
      <p class="text-body1 text-grey-7 q-mt-md">
        No results found for "{{ searchInput }}"
      </p>
      <p class="text-body2 text-grey-6">
        Try a different search term or create a local part instead.
      </p>
      <q-btn
        unelevated
        color="secondary"
        label="Switch to Local Part"
        icon="inventory_2"
        @click="switchToLocal"
        class="q-mt-md"
      />
    </div>

    <!-- Empty State -->
    <div
      v-if="!searchInput || searchInput.length < 2"
      class="text-center q-py-xl"
    >
      <q-icon name="search" size="64px" color="grey-5" />
      <p class="text-body1 text-grey-7 q-mt-md">
        Enter at least 2 characters to search
      </p>
    </div>

    <!-- Results Summary -->
    <div
      v-if="wizardStore.searchResults.length > 0"
      class="q-mt-md text-body2 text-grey-7"
    >
      Showing {{ wizardStore.searchResults.length }} of {{ wizardStore.searchTotal }} results
    </div>

    <!-- Selection Info -->
    <q-banner
      v-if="wizardStore.selectedPart"
      class="bg-positive text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="check_circle" />
      </template>
      <div>
        <strong>Selected:</strong> {{ wizardStore.selectedPart.part_number }}
        <br />
        {{ wizardStore.selectedPart.name }}
      </div>
    </q-banner>
  </div>
</template>

<style scoped>
.search-results-table :deep(.q-table__card) {
  box-shadow: none;
}

.search-results-table :deep(tbody tr) {
  cursor: pointer;
}

.search-results-table :deep(tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.03);
}

.search-results-table :deep(tbody tr.selected) {
  background-color: rgba(25, 118, 210, 0.12);
}
</style>
