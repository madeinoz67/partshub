<template>
  <div class="provider-sku-search">
    <q-card class="q-pa-md">
      <q-card-section>
        <div class="text-h6 q-mb-md">Provider SKU Search</div>
        <p class="text-body2 text-grey-7 q-mb-md">
          Search for components using provider-specific SKUs (e.g., LCSC: C123456, Digi-Key: DK123456)
        </p>

        <q-form @submit="searchBySku" class="q-gutter-md">
          <q-input
            v-model="skuQuery"
            label="Provider SKU"
            placeholder="Enter provider SKU (e.g., C123456)"
            outlined
            dense
            :loading="loading"
            @keyup.enter="searchBySku"
          >
            <template v-slot:prepend>
              <q-icon name="inventory_2" />
            </template>
            <template v-slot:append>
              <q-btn
                icon="search"
                color="primary"
                flat
                round
                dense
                :disable="!skuQuery.trim() || loading"
                @click="searchBySku"
              />
            </template>
          </q-input>

          <div class="row q-gutter-sm">
            <q-btn
              type="submit"
              label="Search by SKU"
              color="primary"
              :loading="loading"
              :disable="!skuQuery.trim()"
            />
            <q-btn
              label="Clear"
              color="grey"
              flat
              @click="clearSearch"
              :disable="loading"
            />
          </div>
        </q-form>
      </q-card-section>

      <!-- Provider Selection -->
      <q-card-section v-if="providers.length > 0">
        <q-separator class="q-mb-md" />
        <div class="text-subtitle2 q-mb-sm">Search Providers</div>
        <div class="row q-gutter-sm">
          <q-chip
            v-for="provider in providers"
            :key="provider"
            :model-value="selectedProviders.includes(provider)"
            @update:model-value="toggleProvider(provider)"
            clickable
            :color="selectedProviders.includes(provider) ? 'primary' : 'grey-4'"
            :text-color="selectedProviders.includes(provider) ? 'white' : 'black'"
          >
            {{ provider.toUpperCase() }}
          </q-chip>
        </div>
      </q-card-section>

      <!-- Search Results -->
      <q-card-section v-if="searchResults">
        <q-separator class="q-mb-md" />
        <div class="text-subtitle1 q-mb-md">
          Search Results for "{{ searchResults.provider_sku }}"
          <q-badge v-if="searchResults.total_found > 0" color="positive" class="q-ml-sm">
            {{ searchResults.total_found }} found
          </q-badge>
          <q-badge v-else color="negative" class="q-ml-sm">
            No results
          </q-badge>
        </div>

        <!-- Results by Provider -->
        <div v-if="searchResults.total_found > 0" class="q-gutter-md">
          <q-card
            v-for="(result, providerName) in searchResults.results"
            :key="providerName"
            class="provider-result-card"
            flat
            bordered
          >
            <q-card-section>
              <div class="row items-center q-mb-md">
                <q-icon name="business" class="q-mr-sm" />
                <div class="text-subtitle1 text-weight-medium">
                  {{ providerName.toUpperCase() }}
                </div>
                <q-space />
                <q-chip color="primary" text-color="white" dense>
                  {{ result.provider_part_id }}
                </q-chip>
              </div>

              <div class="component-details">
                <div class="row q-gutter-md">
                  <div class="col-md-6 col-xs-12">
                    <div class="text-weight-medium">{{ result.part_number }}</div>
                    <div class="text-body2 text-grey-7">{{ result.manufacturer }}</div>
                    <div class="text-body2 q-mt-sm">{{ result.description }}</div>
                  </div>
                  <div class="col-md-6 col-xs-12">
                    <div v-if="result.category" class="text-body2">
                      <strong>Category:</strong> {{ result.category }}
                    </div>
                    <div v-if="result.availability" class="text-body2">
                      <strong>Availability:</strong> {{ result.availability }}
                    </div>
                  </div>
                </div>

                <!-- Specifications -->
                <div v-if="result.specifications && Object.keys(result.specifications).length > 0"
                     class="q-mt-md">
                  <q-expansion-item
                    label="Specifications"
                    icon="info"
                    dense
                  >
                    <div class="q-pa-sm">
                      <div v-for="(value, key) in result.specifications" :key="key" class="row">
                        <div class="col-4 text-weight-medium">{{ key }}:</div>
                        <div class="col-8">{{ value }}</div>
                      </div>
                    </div>
                  </q-expansion-item>
                </div>

                <!-- Pricing -->
                <div v-if="result.price_breaks && result.price_breaks.length > 0"
                     class="q-mt-md">
                  <q-expansion-item
                    label="Pricing"
                    icon="attach_money"
                    dense
                  >
                    <q-table
                      :rows="result.price_breaks"
                      :columns="priceColumns"
                      flat
                      dense
                      hide-header
                      class="q-mt-sm"
                    />
                  </q-expansion-item>
                </div>

                <!-- Actions -->
                <div class="row q-gutter-sm q-mt-md">
                  <q-btn
                    label="Import Component"
                    color="primary"
                    size="sm"
                    @click="importComponent(result, providerName)"
                    :loading="importing === `${providerName}-${result.provider_part_id}`"
                  />
                  <q-btn
                    v-if="result.datasheet_url"
                    label="Datasheet"
                    color="blue"
                    size="sm"
                    flat
                    icon="description"
                    @click="openUrl(result.datasheet_url)"
                  />
                  <q-btn
                    v-if="result.provider_url"
                    label="View on {{ providerName.toUpperCase() }}"
                    color="grey"
                    size="sm"
                    flat
                    icon="launch"
                    @click="openUrl(result.provider_url)"
                  />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- No Results -->
        <div v-else class="text-center q-pa-lg">
          <q-icon name="search_off" size="4em" color="grey-5" />
          <div class="text-h6 q-mt-md text-grey-6">No components found</div>
          <div class="text-body2 text-grey-5">
            Try a different SKU or check if the format is correct
          </div>
        </div>
      </q-card-section>

      <!-- Search Tips -->
      <q-card-section v-if="!searchResults">
        <q-separator class="q-mb-md" />
        <div class="text-subtitle2 q-mb-sm">SKU Format Examples</div>
        <div class="q-gutter-sm">
          <q-chip outline color="grey-7" size="sm">LCSC: C123456</q-chip>
          <q-chip outline color="grey-7" size="sm">Digi-Key: DK123456</q-chip>
          <q-chip outline color="grey-7" size="sm">Mouser: M123456</q-chip>
          <q-chip outline color="grey-7" size="sm">RS: RS123456</q-chip>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'ProviderSkuSearch',
  setup() {
    const $q = useQuasar()
    const skuQuery = ref('')
    const loading = ref(false)
    const importing = ref('')
    const searchResults = ref(null)
    const providers = ref(['lcsc']) // Available providers
    const selectedProviders = ref(['lcsc']) // Default selected providers

    const priceColumns = [
      { name: 'quantity', label: 'Qty', field: 'quantity', align: 'left' },
      { name: 'price', label: 'Price', field: 'price', align: 'right',
        format: (val, row) => `${val} ${row.currency || 'USD'}` }
    ]

    // Load available providers
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

    const searchBySku = async () => {
      if (!skuQuery.value.trim()) return

      loading.value = true
      searchResults.value = null

      try {
        const response = await api.post('/api/v1/providers/search-sku', {
          provider_sku: skuQuery.value.trim(),
          providers: selectedProviders.value.length > 0 ? selectedProviders.value : null
        })

        searchResults.value = response.data

        if (response.data.total_found > 0) {
          $q.notify({
            type: 'positive',
            message: `Found ${response.data.total_found} component(s) for SKU: ${response.data.provider_sku}`,
            timeout: 3000
          })
        } else {
          $q.notify({
            type: 'warning',
            message: `No components found for SKU: ${response.data.provider_sku}`,
            timeout: 3000
          })
        }
      } catch (error) {
        console.error('Error searching by SKU:', error)
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
      skuQuery.value = ''
      searchResults.value = null
    }

    const toggleProvider = (providerName) => {
      const index = selectedProviders.value.indexOf(providerName)
      if (index > -1) {
        selectedProviders.value.splice(index, 1)
      } else {
        selectedProviders.value.push(providerName)
      }
    }

    const importComponent = async (component, providerName) => {
      const importKey = `${providerName}-${component.provider_part_id}`
      importing.value = importKey

      try {
        // Prepare component data for import
        const componentData = {
          part_number: component.part_number,
          manufacturer: component.manufacturer,
          description: component.description,
          category: component.category,
          specifications: component.specifications || {},
          search_result: component // Include the full search result
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
      } finally {
        importing.value = ''
      }
    }

    const openUrl = (url) => {
      window.open(url, '_blank')
    }

    onMounted(() => {
      loadProviders()
    })

    return {
      skuQuery,
      loading,
      importing,
      searchResults,
      providers,
      selectedProviders,
      priceColumns,
      searchBySku,
      clearSearch,
      toggleProvider,
      importComponent,
      openUrl
    }
  }
}
</script>

<style scoped>
.provider-sku-search {
  max-width: 1000px;
  margin: 0 auto;
}

.provider-result-card {
  margin-bottom: 16px;
}

.component-details {
  border-left: 3px solid #1976d2;
  padding-left: 16px;
}
</style>