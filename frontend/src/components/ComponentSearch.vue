<template>
  <div class="component-search">
    <q-card class="q-pa-md">
      <q-card-section>
        <div class="text-h6 q-mb-md">Component Search</div>

        <q-form class="q-gutter-md" @submit="search">
          <!-- Search Type Selection -->
          <q-option-group
            v-model="searchType"
            :options="searchTypeOptions"
            color="primary"
            inline
            class="q-mb-md"
          />

          <!-- Search Input -->
          <q-input
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

          <div class="row q-gutter-sm">
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
          </div>
        </q-form>
      </q-card-section>

      <!-- Search Results -->
      <q-card-section v-if="searchResults">
        <q-separator class="q-mb-md" />

        <!-- Unified Search Results -->
        <div v-if="searchType === 'unified'">
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
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../boot/axios'
import { useQuasar } from 'quasar'
import ComponentSearchResults from './ComponentSearchResults.vue'
import ComponentSearchResultCard from './ComponentSearchResultCard.vue'

export default {
  name: 'ComponentSearch',
  components: {
    ComponentSearchResults,
    ComponentSearchResultCard
  },
  setup() {
    const $q = useQuasar()
    const query = ref('')
    const searchType = ref('unified')
    const loading = ref(false)
    const limit = ref(20)
    const searchResults = ref(null)
    const standardResults = ref([])
    const skuResults = ref({ total_found: 0, results: {} })
    const providers = ref(['lcsc'])
    const selectedProviders = ref(['lcsc'])

    const searchTypeOptions = [
      { label: 'Unified Search', value: 'unified' },
      { label: 'Part Number', value: 'part_number' },
      { label: 'Provider SKU', value: 'provider_sku' }
    ]

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
      if (!query.value.trim()) return

      loading.value = true
      searchResults.value = null
      standardResults.value = []
      skuResults.value = { total_found: 0, results: {} }

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
      searchResults.value = null
      standardResults.value = []
      skuResults.value = { total_found: 0, results: {} }
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
    })

    return {
      query,
      searchType,
      searchTypeOptions,
      loading,
      limit,
      searchResults,
      standardResults,
      skuResults,
      providers,
      selectedProviders,
      searchInputLabel,
      searchInputPlaceholder,
      searchIcon,
      searchButtonLabel,
      hasNoResults,
      search,
      clearSearch,
      toggleProvider,
      importComponent,
      viewComponentDetails
    }
  }
}
</script>

<style scoped>
.component-search {
  max-width: 1000px;
  margin: 0 auto;
}
</style>