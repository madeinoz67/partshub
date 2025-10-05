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
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

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
  searchInput.value = value

  // Clear any pending search
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }

  // Don't search for empty or very short queries
  if (!value || value.length < 2) {
    return
  }

  // Debounce search by 300ms
  searchTimeout.value = setTimeout(() => {
    performSearch(value)
  }, 300)
}

/**
 * Perform the actual search
 */
async function performSearch(query: string) {
  await wizardStore.searchProvider(query)
}

/**
 * Handle row click to select a part
 */
function onRowClick(_evt: Event, row: ProviderPart) {
  selectedPartNumber.value = row.part_number
  wizardStore.selectPart(row)

  $q.notify({
    type: 'positive',
    message: `Selected: ${row.part_number}`,
    position: 'top',
  })
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

// Watch for external query changes
watch(() => wizardStore.searchQuery, (newValue) => {
  searchInput.value = newValue
})
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
      clearable
      class="q-mb-md"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>
      <template v-slot:append v-if="wizardStore.isLoading">
        <q-spinner color="primary" size="20px" />
      </template>
    </q-input>

    <!-- Search Results Table -->
    <q-table
      v-if="wizardStore.searchResults.length > 0"
      :rows="wizardStore.searchResults"
      :columns="columns"
      row-key="part_number"
      :loading="wizardStore.isLoading"
      :selected="selectedPartNumber ? [wizardStore.searchResults.find(r => r.part_number === selectedPartNumber)] : []"
      selection="single"
      @row-click="onRowClick"
      flat
      bordered
      class="search-results-table"
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
