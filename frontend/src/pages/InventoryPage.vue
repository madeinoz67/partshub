<template>
  <q-page class="inventory-page">
    <div class="q-pa-lg">
      <!-- Page Header -->
      <div class="row items-center q-mb-lg">
        <div class="col">
          <div class="text-h4">Inventory Management</div>
          <div class="text-subtitle1 text-grey-6">
            Manage your electronic components and parts
          </div>
        </div>
        <div class="col-auto">
          <q-btn
            color="primary"
            icon="add"
            label="Add Component"
            @click="showAddDialog = true"
            class="q-mr-sm"
          />
          <q-btn
            color="secondary"
            icon="upload"
            label="Import"
            @click="showImportDialog = true"
          />
        </div>
      </div>

      <!-- Search and Filters -->
      <q-card flat bordered class="q-mb-lg">
        <q-card-section>
          <div class="row q-col-gutter-md items-end">
            <!-- Search Input -->
            <div class="col-md-4 col-sm-6 col-12">
              <q-input
                v-model="searchQuery"
                label="Search components..."
                outlined
                dense
                clearable
                debounce="300"
                @update:model-value="searchComponents"
              >
                <template v-slot:prepend>
                  <q-icon name="search" />
                </template>
                <template v-slot:append>
                  <q-btn
                    icon="qr_code_scanner"
                    flat
                    round
                    dense
                    @click="openBarcodeScanner"
                    color="primary"
                  >
                    <q-tooltip>Scan barcode to search components</q-tooltip>
                  </q-btn>
                </template>
              </q-input>
            </div>

            <!-- Category Filter -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="selectedCategory"
                :options="categoryOptions"
                label="Category"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>

            <!-- Storage Location Filter -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="selectedLocation"
                :options="locationOptions"
                label="Location"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>

            <!-- Component Type Filter -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="selectedType"
                :options="typeOptions"
                label="Type"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>

            <!-- Stock Status Filter -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="stockStatus"
                :options="stockStatusOptions"
                label="Stock Status"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>
          </div>

          <!-- Advanced Filters Toggle -->
          <div class="row q-mt-md">
            <div class="col">
              <q-btn
                flat
                :icon="showAdvancedFilters ? 'expand_less' : 'expand_more'"
                :label="showAdvancedFilters ? 'Hide Advanced Filters' : 'Show Advanced Filters'"
                @click="showAdvancedFilters = !showAdvancedFilters"
              />
            </div>
          </div>

          <!-- Advanced Filters -->
          <div v-show="showAdvancedFilters" class="row q-col-gutter-md q-mt-md">
            <div class="col-md-3 col-sm-6 col-12">
              <q-input
                v-model="minQuantity"
                label="Min Quantity"
                type="number"
                outlined
                dense
                @update:model-value="filterComponents"
              />
            </div>
            <div class="col-md-3 col-sm-6 col-12">
              <q-input
                v-model="maxQuantity"
                label="Max Quantity"
                type="number"
                outlined
                dense
                @update:model-value="filterComponents"
              />
            </div>
            <div class="col-md-3 col-sm-6 col-12">
              <q-input
                v-model="manufacturer"
                label="Manufacturer"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>
            <div class="col-md-3 col-sm-6 col-12">
              <q-input
                v-model="packageFilter"
                label="Package"
                outlined
                dense
                clearable
                @update:model-value="filterComponents"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Results Summary -->
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-body2 text-grey-6">
            Showing {{ components.length }} of {{ totalComponents }} components
            <span v-if="hasActiveFilters">(filtered)</span>
          </div>
        </div>
        <div class="col-auto">
          <q-btn-group flat>
            <q-btn
              flat
              :color="viewMode === 'list' ? 'primary' : 'grey'"
              icon="list"
              @click="viewMode = 'list'"
            />
            <q-btn
              flat
              :color="viewMode === 'cards' ? 'primary' : 'grey'"
              icon="grid_view"
              @click="viewMode = 'cards'"
            />
          </q-btn-group>
        </div>
      </div>

      <!-- Component List -->
      <div v-if="viewMode === 'list'">
        <ComponentList
          :components="components"
          :loading="loading"
          @component-updated="loadComponents"
          @component-deleted="loadComponents"
        />
      </div>

      <!-- Component Cards -->
      <div v-else-if="viewMode === 'cards'" class="row q-col-gutter-md">
        <div
          v-for="component in components"
          :key="component.id"
          class="col-lg-3 col-md-4 col-sm-6 col-12"
        >
          <ComponentCard
            :component="component"
            @component-updated="loadComponents"
            @component-deleted="loadComponents"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center q-py-lg">
        <q-spinner size="50px" color="primary" />
        <div class="text-subtitle2 q-mt-md">Loading components...</div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && components.length === 0" class="text-center q-py-xl">
        <q-icon name="inventory_2" size="80px" color="grey-4" />
        <div class="text-h6 text-grey-6 q-mt-md">
          {{ hasActiveFilters ? 'No components match your filters' : 'No components found' }}
        </div>
        <div class="text-body2 text-grey-5 q-mt-sm">
          {{ hasActiveFilters ? 'Try adjusting your search criteria' : 'Add your first component to get started' }}
        </div>
        <q-btn
          v-if="!hasActiveFilters"
          color="primary"
          icon="add"
          label="Add Component"
          class="q-mt-md"
          @click="showAddDialog = true"
        />
        <q-btn
          v-else
          flat
          color="primary"
          label="Clear Filters"
          class="q-mt-md"
          @click="clearFilters"
        />
      </div>

      <!-- Pagination -->
      <div v-if="totalComponents > pageSize" class="row justify-center q-mt-lg">
        <q-pagination
          v-model="currentPage"
          :max="Math.ceil(totalComponents / pageSize)"
          direction-links
          boundary-links
          @update:model-value="loadComponents"
        />
      </div>
    </div>

    <!-- Add Component Dialog -->
    <q-dialog v-model="showAddDialog" persistent max-width="800px">
      <ComponentForm
        mode="create"
        @saved="handleComponentSaved"
        @cancelled="showAddDialog = false"
      />
    </q-dialog>

    <!-- Import Dialog -->
    <q-dialog v-model="showImportDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Import Components</div>
        </q-card-section>

        <q-card-section>
          <div class="text-body2 q-mb-md">
            Upload a CSV file with component data. The file should include columns for:
            name, part_number, manufacturer, category, quantity_on_hand, etc.
          </div>

          <q-file
            v-model="importFile"
            accept=".csv"
            outlined
            label="Select CSV file"
            @update:model-value="previewImport"
          >
            <template v-slot:prepend>
              <q-icon name="upload_file" />
            </template>
          </q-file>

          <!-- Import Preview -->
          <div v-if="importPreview?.length" class="q-mt-md">
            <div class="text-subtitle2 q-mb-sm">Preview (first 5 rows):</div>
            <q-markup-table flat bordered>
              <thead>
                <tr>
                  <th v-for="(header, index) in importHeaders" :key="index" class="text-left">
                    {{ header }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in importPreview.slice(0, 5)" :key="index">
                  <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                    {{ cell }}
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeImportDialog" />
          <q-btn
            color="primary"
            label="Import"
            :disabled="!importFile"
            :loading="importLoading"
            @click="performImport"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Barcode Scanner Dialog -->
    <q-dialog v-model="showBarcodeDialog" persistent>
      <q-card style="min-width: 400px; max-width: 600px">
        <q-card-section>
          <div class="text-h6">Barcode Scanner</div>
          <div class="text-body2 text-grey-7">Scan a component barcode to search</div>
        </q-card-section>

        <q-card-section>
          <BarcodeScanner
            v-if="showBarcodeDialog"
            @scan-success="handleBarcodeScanned"
            @scan-error="handleBarcodeScanError"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel"
            color="grey"
            @click="closeBarcodeScanner"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from '../services/api'
import ComponentList from '../components/ComponentList.vue'
import ComponentCard from '../components/ComponentCard.vue'
import ComponentForm from '../components/ComponentForm.vue'
import BarcodeScanner from '../components/BarcodeScanner.vue'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

// Reactive data
const components = ref([])
const totalComponents = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)

// Search and filters
const searchQuery = ref('')
const selectedCategory = ref(null)
const selectedLocation = ref(null)
const selectedType = ref(null)
const stockStatus = ref(null)
const showAdvancedFilters = ref(false)
const minQuantity = ref(null)
const maxQuantity = ref(null)
const manufacturer = ref('')
const packageFilter = ref('')
const viewMode = ref('list')

// Dialog state
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const showBarcodeDialog = ref(false)

// Import state
const importFile = ref(null)
const importPreview = ref([])
const importHeaders = ref([])
const importLoading = ref(false)

// Filter options
const categoryOptions = ref([])
const locationOptions = ref([])
const typeOptions = ref([])
const stockStatusOptions = [
  { label: 'All', value: null },
  { label: 'Available', value: 'available' },
  { label: 'Low Stock', value: 'low' },
  { label: 'Out of Stock', value: 'out' }
]

// Computed properties
const hasActiveFilters = computed(() => {
  return searchQuery.value ||
         selectedCategory.value ||
         selectedLocation.value ||
         selectedType.value ||
         stockStatus.value ||
         minQuantity.value ||
         maxQuantity.value ||
         manufacturer.value ||
         packageFilter.value
})

// Methods
const loadComponents = async () => {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }

    // Add filters
    if (searchQuery.value) params.search = searchQuery.value
    if (selectedCategory.value) params.category = selectedCategory.value
    if (selectedLocation.value) params.storage_location = selectedLocation.value
    if (selectedType.value) params.component_type = selectedType.value
    if (stockStatus.value) params.stock_status = stockStatus.value
    if (manufacturer.value) params.manufacturer = manufacturer.value
    if (packageFilter.value) params.package = packageFilter.value
    if (minQuantity.value) params.min_quantity = minQuantity.value
    if (maxQuantity.value) params.max_quantity = maxQuantity.value

    const response = await api.get('/components', { params })
    components.value = response.data
    totalComponents.value = response.headers['x-total-count'] || response.data.length

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load components',
      caption: error.response?.data?.detail || error.message
    })
  }
  loading.value = false
}

const loadFilterOptions = async () => {
  try {
    // Load categories
    const categoriesResponse = await api.get('/categories')
    categoryOptions.value = [
      { label: 'All Categories', value: null },
      ...categoriesResponse.data.map(cat => ({ label: cat.name, value: cat.name }))
    ]

    // Load storage locations
    const locationsResponse = await api.get('/storage-locations')
    locationOptions.value = [
      { label: 'All Locations', value: null },
      ...locationsResponse.data.map(loc => ({ label: loc.name, value: loc.name }))
    ]

    // Load component types (from existing components)
    const typesResponse = await api.get('/components/types')
    typeOptions.value = [
      { label: 'All Types', value: null },
      ...typesResponse.data.map(type => ({ label: type, value: type }))
    ]

  } catch (error) {
    console.error('Failed to load filter options:', error)
  }
}

const searchComponents = () => {
  currentPage.value = 1
  loadComponents()
}

const filterComponents = () => {
  currentPage.value = 1
  loadComponents()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = null
  selectedLocation.value = null
  selectedType.value = null
  stockStatus.value = null
  minQuantity.value = null
  maxQuantity.value = null
  manufacturer.value = ''
  packageFilter.value = ''
  showAdvancedFilters.value = false
  currentPage.value = 1
  loadComponents()
}

// Barcode scanner functions
const openBarcodeScanner = () => {
  showBarcodeDialog.value = true
}

const closeBarcodeScanner = () => {
  showBarcodeDialog.value = false
}

const handleBarcodeScanned = (scannedData) => {
  closeBarcodeScanner()

  // Set the scanned data as search query
  if (scannedData && scannedData.components && scannedData.components.length > 0) {
    // If we found components, use the first one's part number
    const firstComponent = scannedData.components[0]
    searchQuery.value = firstComponent.part_number
  } else if (scannedData && scannedData.barcodes && scannedData.barcodes.length > 0) {
    // If we have barcode data but no components, use the barcode data
    const firstBarcode = scannedData.barcodes[0]
    searchQuery.value = firstBarcode.data
  }

  // Trigger search
  searchComponents()

  // Show notification
  $q.notify({
    type: 'positive',
    message: 'Barcode scanned successfully',
    timeout: 2000
  })
}

const handleBarcodeScanError = (error) => {
  console.error('Barcode scan error:', error)
  $q.notify({
    type: 'negative',
    message: 'Barcode scan failed',
    caption: error.message || 'Please try again',
    timeout: 3000
  })
}

const handleComponentSaved = () => {
  showAddDialog.value = false
  loadComponents()
  $q.notify({
    type: 'positive',
    message: 'Component added successfully'
  })
}

const previewImport = async () => {
  if (!importFile.value) return

  try {
    const text = await importFile.value.text()
    const lines = text.split('\n').filter(line => line.trim())

    if (lines.length === 0) return

    // Parse CSV
    const rows = lines.map(line => line.split(',').map(cell => cell.trim()))
    importHeaders.value = rows[0]
    importPreview.value = rows.slice(1)

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to parse CSV file',
      caption: error.message
    })
  }
}

const performImport = async () => {
  if (!importFile.value) return

  importLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)

    const response = await api.post('/components/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    $q.notify({
      type: 'positive',
      message: `Successfully imported ${response.data.imported_count} components`
    })

    closeImportDialog()
    loadComponents()

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Import failed',
      caption: error.response?.data?.detail || error.message
    })
  }
  importLoading.value = false
}

const closeImportDialog = () => {
  showImportDialog.value = false
  importFile.value = null
  importPreview.value = []
  importHeaders.value = []
}

// Watch for route changes
watch(() => route.query.action, (action) => {
  if (action === 'add') {
    showAddDialog.value = true
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  loadFilterOptions()
  loadComponents()
})
</script>

<style scoped>
.inventory-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>