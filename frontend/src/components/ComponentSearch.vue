<template>
  <div class="component-search">
    <q-card class="q-pa-md">
      <q-card-section>
        <div class="text-h6 q-mb-md">Component Search</div>

        <q-form class="q-gutter-md" @submit="search">
          <!-- Search Mode Toggle -->
          <div class="row items-center q-mb-md">
            <div class="col-auto q-mr-md">
              <q-btn-toggle
                v-model="searchMode"
                :options="searchModeOptions"
                toggle-color="primary"
                unelevated
                @update:model-value="onSearchModeChange"
              />
            </div>
            <div v-if="searchMode === 'nl'" class="col-auto">
              <q-icon name="info" color="info" size="sm" class="q-mr-xs" />
              <span class="text-caption text-grey-7">
                Try natural language like "resistors with low stock" or "capacitors in A1"
              </span>
            </div>
          </div>

          <!-- Search Type Selection (Standard Mode Only) -->
          <q-option-group
            v-if="searchMode === 'standard'"
            v-model="searchType"
            :options="searchTypeOptions"
            color="primary"
            inline
            class="q-mb-md"
          />

          <!-- Natural Language Search Input -->
          <div v-if="searchMode === 'nl'">
            <q-input
              v-model="nlQuery"
              label="Natural Language Query"
              placeholder="Try: 'find resistors with low stock', 'capacitors in A1', '10k SMD resistors'"
              outlined
              dense
              :loading="loading"
              @keyup.enter="search"
            >
              <template #prepend>
                <q-icon name="psychology" />
              </template>
              <template #append>
                <q-btn
                  icon="search"
                  color="primary"
                  flat
                  round
                  dense
                  :disable="!nlQuery.trim() || loading"
                  @click="search"
                />
              </template>
            </q-input>

            <!-- Example Queries -->
            <div class="q-mt-sm">
              <span class="text-caption text-grey-7 q-mr-sm">Examples:</span>
              <q-chip
                v-for="example in exampleQueries"
                :key="example"
                clickable
                size="sm"
                color="grey-3"
                text-color="grey-8"
                class="q-mr-xs"
                @click="useExampleQuery(example)"
              >
                {{ example }}
              </q-chip>
            </div>

            <!-- NL Metadata Display -->
            <div v-if="nlMetadata && hasSearched" class="q-mt-md">
              <q-card flat bordered>
                <q-card-section class="q-pa-sm">
                  <div class="row items-center q-mb-sm">
                    <div class="col">
                      <span class="text-caption text-weight-medium">Query Understanding</span>
                      <!-- Visual confidence progress bar -->
                      <q-linear-progress
                        :value="nlMetadata.confidence"
                        :color="getConfidenceColor(nlMetadata.confidence * 100)"
                        size="6px"
                        rounded
                        class="q-mt-xs"
                      />
                    </div>
                    <div class="col-auto">
                      <!-- Confidence Score (convert 0-1 to percentage) -->
                      <q-badge
                        :color="getConfidenceColor(nlMetadata.confidence * 100)"
                        :label="`${Math.round(nlMetadata.confidence * 100)}% confidence`"
                      >
                        <q-tooltip>
                          {{ getConfidenceTooltip(nlMetadata.confidence * 100) }}
                        </q-tooltip>
                      </q-badge>
                    </div>
                  </div>

                  <!-- Parsed Parameters as Chips -->
                  <div v-if="nlMetadata.parsed_entities && Object.keys(nlMetadata.parsed_entities).length > 0" class="q-mt-sm">
                    <div class="text-caption text-grey-7 q-mb-xs">Parsed filters:</div>
                    <div class="row q-gutter-xs">
                      <q-chip
                        v-for="(value, key) in nlMetadata.parsed_entities"
                        :key="key"
                        removable
                        :color="getEntityChipColor(key)"
                        text-color="white"
                        size="sm"
                        @remove="removeParsedFilter(key)"
                      >
                        <strong>{{ formatEntityKey(key) }}:</strong> {{ value }}
                      </q-chip>
                    </div>
                  </div>

                  <!-- FTS5 Fallback Warning -->
                  <div v-if="nlMetadata.fallback_to_fts5" class="q-mt-sm">
                    <q-banner dense class="bg-orange-1 text-orange-9">
                      <template #avatar>
                        <q-icon name="warning" color="orange" />
                      </template>
                      <span class="text-caption">
                        Query couldn't be fully understood. Using text search fallback.
                      </span>
                    </q-banner>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <!-- Standard Search Input -->
          <q-input
            v-else
            v-model="query"
            :label="searchInputLabel"
            :placeholder="searchInputPlaceholder"
            outlined
            dense
            :loading="loading"
            @keyup.enter="search"
          >
            <template #prepend>
              <q-icon :name="searchIcon" />
            </template>
            <template #append>
              <q-btn
                icon="search"
                color="primary"
                flat
                round
                dense
                :disable="!query.trim() || loading"
                @click="search"
              />
            </template>
          </q-input>

          <!-- Advanced Options -->
          <q-expansion-item
            label="Advanced Search Options"
            icon="tune"
            dense
          >
            <div class="q-pa-md q-gutter-md">
              <!-- Result Limit -->
              <q-input
                v-model.number="limit"
                label="Result Limit"
                type="number"
                min="1"
                max="100"
                outlined
                dense
                style="max-width: 200px"
              />

              <!-- Provider Selection -->
              <div v-if="providers.length > 0">
                <div class="text-subtitle2 q-mb-sm">Search Providers</div>
                <div class="row q-gutter-sm">
                  <q-chip
                    v-for="provider in providers"
                    :key="provider"
                    :model-value="selectedProviders.includes(provider)"
                    clickable
                    :color="selectedProviders.includes(provider) ? 'primary' : 'grey-4'"
                    :text-color="selectedProviders.includes(provider) ? 'white' : 'black'"
                    @update:model-value="toggleProvider(provider)"
                  >
                    {{ provider.toUpperCase() }}
                  </q-chip>
                </div>
              </div>
            </div>
          </q-expansion-item>

          <div class="row q-gutter-sm items-center">
            <q-btn
              type="submit"
              :label="searchButtonLabel"
              color="primary"
              :loading="loading"
              :disable="!query.trim()"
            />
            <q-btn
              label="Clear"
              color="grey"
              flat
              :disable="loading"
              @click="clearSearch"
            />

            <!-- Save Search Button -->
            <q-btn
              v-if="hasSearched"
              label="Save Search"
              icon="bookmark_border"
              color="secondary"
              outline
              :disable="loading"
              @click="showSaveDialog = true"
            />

            <!-- Saved Searches Dropdown -->
            <q-btn-dropdown
              label="Saved Searches"
              icon="bookmark"
              color="primary"
              outline
              :disable="loading"
            >
              <saved-searches
                compact
                :max-items="5"
                @execute="handleExecuteSavedSearch"
              />
            </q-btn-dropdown>

            <!-- NL Search History Dropdown -->
            <q-btn-dropdown
              v-if="searchMode === 'nl' && nlSearchHistory.length > 0"
              label="History"
              icon="history"
              color="secondary"
              outline
              :disable="loading"
            >
              <q-list>
                <q-item
                  v-for="(historyQuery, index) in nlSearchHistory"
                  :key="index"
                  v-close-popup
                  clickable
                  @click="nlQuery = historyQuery; search()"
                >
                  <q-item-section>
                    <q-item-label>{{ historyQuery }}</q-item-label>
                  </q-item-section>
                </q-item>
                <q-separator />
                <q-item
                  v-close-popup
                  clickable
                  @click="clearSearchHistory"
                >
                  <q-item-section avatar>
                    <q-icon name="delete_sweep" color="negative" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Clear History</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
        </q-form>
      </q-card-section>

      <!-- Search Results -->
      <q-card-section v-if="searchResults || (searchMode === 'nl' && standardResults.length > 0)">
        <q-separator class="q-mb-md" />

        <!-- Natural Language Search Results -->
        <div v-if="searchMode === 'nl' && standardResults.length > 0">
          <div class="text-subtitle1 q-mb-md">
            Natural Language Search Results
            <q-badge color="positive" class="q-ml-sm">
              {{ standardResults.length }} found
            </q-badge>
          </div>
          <component-search-results
            :results="standardResults"
            @import="importComponent"
            @view-details="viewComponentDetails"
          />
        </div>

        <!-- Unified Search Results -->
        <div v-else-if="searchType === 'unified'">
          <div class="text-subtitle1 q-mb-md">
            Unified Search Results for "{{ searchResults.query }}"
            <q-badge :color="searchResults.total_results > 0 ? 'positive' : 'negative'" class="q-ml-sm">
              {{ searchResults.total_results }} total
            </q-badge>
          </div>

          <!-- Part Number Results -->
          <div v-if="searchResults.part_number_results.length > 0" class="q-mb-lg">
            <div class="text-subtitle2 q-mb-sm text-weight-medium">
              Part Number Search Results ({{ searchResults.part_number_results.length }})
            </div>
            <component-search-results
              :results="searchResults.part_number_results"
              @import="importComponent"
              @view-details="viewComponentDetails"
            />
          </div>

          <!-- Provider SKU Results -->
          <div v-if="Object.keys(searchResults.provider_sku_results).length > 0" class="q-mb-lg">
            <div class="text-subtitle2 q-mb-sm text-weight-medium">
              Provider SKU Search Results ({{ Object.keys(searchResults.provider_sku_results).length }})
            </div>
            <div class="q-gutter-md">
              <q-card
                v-for="(result, providerName) in searchResults.provider_sku_results"
                :key="providerName"
                flat
                bordered
              >
                <q-card-section>
                  <div class="row items-center q-mb-sm">
                    <q-icon name="business" class="q-mr-sm" />
                    <div class="text-subtitle2 text-weight-medium">
                      {{ providerName.toUpperCase() }}
                    </div>
                    <q-space />
                    <q-chip color="primary" text-color="white" dense>
                      {{ result.provider_part_id }}
                    </q-chip>
                  </div>
                  <component-search-result-card
                    :result="result"
                    :provider-name="providerName"
                    @import="importComponent"
                  />
                </q-card-section>
              </q-card>
            </div>
          </div>
        </div>

        <!-- Standard Search Results -->
        <div v-else-if="searchType === 'part_number'">
          <div class="text-subtitle1 q-mb-md">
            Part Number Search Results
            <q-badge :color="standardResults.length > 0 ? 'positive' : 'negative'" class="q-ml-sm">
              {{ standardResults.length }} found
            </q-badge>
          </div>
          <component-search-results
            v-if="standardResults.length > 0"
            :results="standardResults"
            @import="importComponent"
            @view-details="viewComponentDetails"
          />
        </div>

        <!-- SKU Search Results -->
        <div v-else-if="searchType === 'provider_sku'">
          <div class="text-subtitle1 q-mb-md">
            Provider SKU Search Results
            <q-badge :color="skuResults.total_found > 0 ? 'positive' : 'negative'" class="q-ml-sm">
              {{ skuResults.total_found }} found
            </q-badge>
          </div>
          <div v-if="skuResults.total_found > 0" class="q-gutter-md">
            <q-card
              v-for="(result, providerName) in skuResults.results"
              :key="providerName"
              flat
              bordered
            >
              <q-card-section>
                <div class="row items-center q-mb-sm">
                  <q-icon name="business" class="q-mr-sm" />
                  <div class="text-subtitle2 text-weight-medium">
                    {{ providerName.toUpperCase() }}
                  </div>
                  <q-space />
                  <q-chip color="primary" text-color="white" dense>
                    {{ result.provider_part_id }}
                  </q-chip>
                </div>
                <component-search-result-card
                  :result="result"
                  :provider-name="providerName"
                  @import="importComponent"
                />
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- No Results -->
        <div v-if="hasNoResults" class="text-center q-pa-lg">
          <q-icon name="search_off" size="4em" color="grey-5" />
          <div class="text-h6 q-mt-md text-grey-6">No components found</div>
          <div class="text-body2 text-grey-5">
            Try a different search term or adjust your search type
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Save Search Dialog -->
    <save-search-dialog
      v-model="showSaveDialog"
      :search-parameters="currentSearchParameters"
      @saved="handleSearchSaved"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../boot/axios'
import { useQuasar } from 'quasar'
import ComponentSearchResults from './ComponentSearchResults.vue'
import ComponentSearchResultCard from './ComponentSearchResultCard.vue'
import SaveSearchDialog from './SaveSearchDialog.vue'
import SavedSearches from './SavedSearches.vue'
import { executeSavedSearch } from '../services/savedSearchesService'

export default {
  name: 'ComponentSearch',
  components: {
    ComponentSearchResults,
    ComponentSearchResultCard,
    SaveSearchDialog,
    SavedSearches
  },
  setup() {
    const $q = useQuasar()
    const query = ref('')
    const nlQuery = ref('')
    const searchMode = ref('standard')
    const searchType = ref('unified')
    const loading = ref(false)
    const limit = ref(20)
    const searchResults = ref(null)
    const standardResults = ref([])
    const skuResults = ref({ total_found: 0, results: {} })
    const providers = ref(['lcsc'])
    const selectedProviders = ref(['lcsc'])
    const nlMetadata = ref(null)
    const nlSearchHistory = ref([])

    // Saved searches state
    const showSaveDialog = ref(false)
    const hasSearched = ref(false)

    const searchModeOptions = [
      { label: 'Standard Search', value: 'standard' },
      { label: 'Natural Language', value: 'nl' }
    ]

    const searchTypeOptions = [
      { label: 'Unified Search', value: 'unified' },
      { label: 'Part Number', value: 'part_number' },
      { label: 'Provider SKU', value: 'provider_sku' }
    ]

    const exampleQueries = [
      'resistors with low stock',
      'capacitors in location A1',
      '10k SMD resistors',
      'out of stock transistors',
      'capacitors under 1uF'
    ]

    // Load NL search history from localStorage
    const loadSearchHistory = () => {
      try {
        const stored = localStorage.getItem('nl_search_history')
        if (stored) {
          nlSearchHistory.value = JSON.parse(stored)
        }
      } catch (error) {
        console.error('Failed to load search history:', error)
      }
    }

    // Save NL search to history
    const saveToHistory = (query) => {
      if (!query || !query.trim()) return

      // Remove duplicate if exists
      nlSearchHistory.value = nlSearchHistory.value.filter(q => q !== query)

      // Add to beginning
      nlSearchHistory.value.unshift(query)

      // Keep only last 10
      nlSearchHistory.value = nlSearchHistory.value.slice(0, 10)

      // Save to localStorage
      try {
        localStorage.setItem('nl_search_history', JSON.stringify(nlSearchHistory.value))
      } catch (error) {
        console.error('Failed to save search history:', error)
      }
    }

    // Clear search history
    const clearSearchHistory = () => {
      nlSearchHistory.value = []
      localStorage.removeItem('nl_search_history')
    }

    // Use example query
    const useExampleQuery = (example) => {
      nlQuery.value = example
      search()
    }

    // Format entity key for display
    const formatEntityKey = (key) => {
      return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
    }

    // Get confidence color
    const getConfidenceColor = (confidence) => {
      if (confidence >= 80) return 'positive'
      if (confidence >= 50) return 'warning'
      return 'negative'
    }

    // Get confidence tooltip
    const getConfidenceTooltip = (confidence) => {
      if (confidence >= 80) return 'High confidence - Query well understood'
      if (confidence >= 50) return 'Medium confidence - Query partially understood'
      return 'Low confidence - Using fallback text search'
    }

    // Get chip color based on entity type
    const getEntityChipColor = (entityKey) => {
      const colorMap = {
        component_type: 'purple',
        stock_status: 'orange',
        storage_location: 'blue',
        category: 'teal',
        search: 'indigo',
        value: 'deep-purple',
        package: 'cyan'
      }
      return colorMap[entityKey] || 'primary'
    }

    // Remove parsed filter and re-search automatically
    const removeParsedFilter = async (key) => {
      if (nlMetadata.value && nlMetadata.value.parsed_entities) {
        // Remove the entity from metadata
        delete nlMetadata.value.parsed_entities[key]

        // Rebuild the query without the removed filter
        // This is a simple approach - we just re-run the search with updated metadata
        await search()

        $q.notify({
          type: 'info',
          message: `Filter "${formatEntityKey(key)}" removed`,
          timeout: 2000
        })
      }
    }

    // Handle search mode change
    const onSearchModeChange = () => {
      // Clear results when switching modes
      searchResults.value = null
      standardResults.value = []
      skuResults.value = { total_found: 0, results: {} }
      nlMetadata.value = null
      hasSearched.value = false
    }

    const currentSearchParameters = computed(() => ({
      search: query.value,
      searchType: searchType.value,
      limit: limit.value,
      providers: selectedProviders.value.length > 0 ? selectedProviders.value : null
    }))

    const searchInputLabel = computed(() => {
      switch (searchType.value) {
        case 'part_number':
          return 'Part Number or Description'
        case 'provider_sku':
          return 'Provider SKU'
        case 'unified':
        default:
          return 'Search Term (Part Number or SKU)'
      }
    })

    const searchInputPlaceholder = computed(() => {
      switch (searchType.value) {
        case 'part_number':
          return 'Enter part number, manufacturer, or description'
        case 'provider_sku':
          return 'Enter provider SKU (e.g., C123456)'
        case 'unified':
        default:
          return 'Enter part number, description, or provider SKU'
      }
    })

    const searchIcon = computed(() => {
      switch (searchType.value) {
        case 'part_number':
          return 'memory'
        case 'provider_sku':
          return 'inventory_2'
        case 'unified':
        default:
          return 'search'
      }
    })

    const searchButtonLabel = computed(() => {
      switch (searchType.value) {
        case 'part_number':
          return 'Search Parts'
        case 'provider_sku':
          return 'Search by SKU'
        case 'unified':
        default:
          return 'Unified Search'
      }
    })

    const hasNoResults = computed(() => {
      if (searchMode.value === 'nl') {
        return hasSearched.value && standardResults.value.length === 0
      }

      if (!searchResults.value) return false

      if (searchType.value === 'unified') {
        return searchResults.value.total_results === 0
      } else if (searchType.value === 'part_number') {
        return standardResults.value.length === 0
      } else if (searchType.value === 'provider_sku') {
        return skuResults.value.total_found === 0
      }
      return false
    })

    const loadProviders = async () => {
      try {
        const response = await api.get('/api/v1/providers/status')
        if (response.data.providers) {
          providers.value = Object.keys(response.data.providers)
        }
      } catch (error) {
        console.error('Error loading providers:', error)
      }
    }

    const search = async () => {
      // Natural Language Search
      if (searchMode.value === 'nl') {
        if (!nlQuery.value.trim()) return

        loading.value = true
        searchResults.value = null
        standardResults.value = []
        skuResults.value = { total_found: 0, results: {} }

        // Keep existing metadata if we're re-searching after filter removal
        const previousMetadata = nlMetadata.value
        if (!previousMetadata || !previousMetadata.parsed_entities || Object.keys(previousMetadata.parsed_entities).length === 0) {
          nlMetadata.value = null
        }

        hasSearched.value = true

        try {
          // Build parameters from current metadata if it exists (for filter removal case)
          const params = {
            nl_query: nlQuery.value.trim(),
            limit: limit.value
          }

          // If we have modified metadata (after filter removal), apply manual filters
          if (previousMetadata && previousMetadata.parsed_entities) {
            const entities = previousMetadata.parsed_entities
            if (entities.component_type) params.component_type = entities.component_type
            if (entities.stock_status) params.stock_status = entities.stock_status
            if (entities.storage_location) params.storage_location = entities.storage_location
            if (entities.category) params.category = entities.category
            if (entities.search) params.search = entities.search
          }

          const response = await api.get('/api/v1/components', { params })

          // Store results
          standardResults.value = response.data.components || []

          // Update metadata - merge with previous if we had filter removal
          nlMetadata.value = response.data.nl_metadata || previousMetadata || null

          // Save to history only for fresh queries
          if (!previousMetadata || Object.keys(previousMetadata.parsed_entities || {}).length === 0) {
            saveToHistory(nlQuery.value.trim())
          }

          // Show notification
          if (standardResults.value.length > 0) {
            $q.notify({
              type: 'positive',
              message: `Found ${standardResults.value.length} component(s)`,
              timeout: 3000
            })
          } else {
            $q.notify({
              type: 'warning',
              message: 'No components found',
              timeout: 3000
            })
          }
        } catch (error) {
          console.error('Error in NL search:', error)
          $q.notify({
            type: 'negative',
            message: `Search failed: ${error.response?.data?.detail || error.message}`,
            timeout: 5000
          })
        } finally {
          loading.value = false
        }
        return
      }

      // Standard Search
      if (!query.value.trim()) return

      loading.value = true
      searchResults.value = null
      standardResults.value = []
      skuResults.value = { total_found: 0, results: {} }
      nlMetadata.value = null
      hasSearched.value = true

      try {
        let response

        if (searchType.value === 'unified') {
          response = await api.post('/api/v1/providers/unified-search', {
            query: query.value.trim(),
            search_type: 'auto',
            limit: limit.value,
            providers: selectedProviders.value.length > 0 ? selectedProviders.value : null
          })
          searchResults.value = response.data
        } else if (searchType.value === 'part_number') {
          response = await api.post('/api/v1/providers/search', {
            query: query.value.trim(),
            limit: limit.value,
            providers: selectedProviders.value.length > 0 ? selectedProviders.value : null
          })
          standardResults.value = response.data.results || []
        } else if (searchType.value === 'provider_sku') {
          response = await api.post('/api/v1/providers/search-sku', {
            provider_sku: query.value.trim(),
            providers: selectedProviders.value.length > 0 ? selectedProviders.value : null
          })
          skuResults.value = response.data
        }

        const totalResults = searchType.value === 'unified'
          ? searchResults.value?.total_results || 0
          : searchType.value === 'part_number'
          ? standardResults.value.length
          : skuResults.value.total_found

        if (totalResults > 0) {
          $q.notify({
            type: 'positive',
            message: `Found ${totalResults} component(s)`,
            timeout: 3000
          })
        } else {
          $q.notify({
            type: 'warning',
            message: 'No components found',
            timeout: 3000
          })
        }
      } catch (error) {
        console.error('Error searching:', error)
        $q.notify({
          type: 'negative',
          message: `Search failed: ${error.response?.data?.detail || error.message}`,
          timeout: 5000
        })
      } finally {
        loading.value = false
      }
    }

    const clearSearch = () => {
      query.value = ''
      nlQuery.value = ''
      searchResults.value = null
      standardResults.value = []
      skuResults.value = { total_found: 0, results: {} }
      nlMetadata.value = null
      hasSearched.value = false
    }

    const handleExecuteSavedSearch = async (searchId) => {
      try {
        loading.value = true
        const response = await executeSavedSearch(searchId)
        const params = response.search_parameters

        // Apply parameters to search state
        query.value = params.search || ''
        searchType.value = params.searchType || 'unified'
        limit.value = params.limit || 20
        selectedProviders.value = params.providers || ['lcsc']

        // Execute the search
        await search()

        $q.notify({
          type: 'positive',
          message: 'Saved search loaded',
          timeout: 2000,
          icon: 'bookmark'
        })
      } catch (error) {
        console.error('Error executing saved search:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to execute saved search',
          timeout: 3000
        })
      } finally {
        loading.value = false
      }
    }

    const handleSearchSaved = () => {
      $q.notify({
        type: 'info',
        message: 'Search saved successfully',
        timeout: 2000
      })
    }

    const toggleProvider = (providerName) => {
      const index = selectedProviders.value.indexOf(providerName)
      if (index > -1) {
        selectedProviders.value.splice(index, 1)
      } else {
        selectedProviders.value.push(providerName)
      }
    }

    const importComponent = async (component) => {
      try {
        const componentData = {
          part_number: component.part_number,
          manufacturer: component.manufacturer,
          description: component.description,
          category: component.category,
          specifications: component.specifications || {},
          search_result: component
        }

        const response = await api.post('/api/v1/import/components', {
          components: [componentData]
        })

        if (response.data.imported_components > 0) {
          $q.notify({
            type: 'positive',
            message: `Successfully imported ${component.part_number}`,
            timeout: 3000
          })
        } else {
          $q.notify({
            type: 'warning',
            message: `Component ${component.part_number} may already exist`,
            timeout: 3000
          })
        }
      } catch (error) {
        console.error('Error importing component:', error)
        $q.notify({
          type: 'negative',
          message: `Import failed: ${error.response?.data?.detail || error.message}`,
          timeout: 5000
        })
      }
    }

    const viewComponentDetails = (component) => {
      // Emit event for parent to handle
      console.log('View component details:', component)
      // Could open a dialog or navigate to details page
    }

    onMounted(() => {
      loadProviders()
      loadSearchHistory()
    })

    return {
      query,
      nlQuery,
      searchMode,
      searchModeOptions,
      searchType,
      searchTypeOptions,
      loading,
      limit,
      searchResults,
      standardResults,
      skuResults,
      providers,
      selectedProviders,
      nlMetadata,
      nlSearchHistory,
      exampleQueries,
      searchInputLabel,
      searchInputPlaceholder,
      searchIcon,
      searchButtonLabel,
      hasNoResults,
      search,
      clearSearch,
      toggleProvider,
      importComponent,
      viewComponentDetails,
      // Saved searches
      showSaveDialog,
      hasSearched,
      currentSearchParameters,
      handleExecuteSavedSearch,
      handleSearchSaved,
      // NL search functions
      useExampleQuery,
      formatEntityKey,
      getConfidenceColor,
      getConfidenceTooltip,
      getEntityChipColor,
      removeParsedFilter,
      onSearchModeChange,
      clearSearchHistory
    }
  }
}
</script>

<style scoped>
.component-search {
  max-width: 1000px;
  margin: 0 auto;
}

/* Natural Language Search Styling */
.q-btn-toggle {
  border-radius: 4px;
}

/* Example queries styling */
.component-search :deep(.q-chip--clickable) {
  cursor: pointer;
  transition: all 0.2s ease;
}

.component-search :deep(.q-chip--clickable:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Metadata card styling */
.q-card.flat.bordered {
  background-color: #f8f9fa;
}

/* Responsive adjustments for NL search */
@media (max-width: 599px) {
  .component-search .row.items-center {
    flex-direction: column;
    align-items: flex-start !important;
  }

  .component-search .col-auto {
    width: 100%;
    margin-bottom: 8px;
  }

  .q-btn-toggle {
    width: 100%;
  }

  /* Stack example chips on mobile */
  .component-search :deep(.q-chip) {
    margin-bottom: 4px;
  }

  /* Make parsed filter chips wrap nicely */
  .component-search .row.q-gutter-xs {
    flex-wrap: wrap;
  }
}

/* Enhanced chip animations */
.component-search :deep(.q-chip) {
  transition: all 0.3s ease;
}

.component-search :deep(.q-chip:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Confidence badge styling */
.q-badge {
  font-weight: 600;
  padding: 4px 10px;
}
</style>