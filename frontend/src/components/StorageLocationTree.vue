<template>
  <div class="storage-location-tree">
    <!-- Header with actions -->
    <div class="row items-center q-mb-md">
      <div class="text-h6">Storage Locations</div>
      <q-space />
      <q-btn
        color="primary"
        icon="add"
        label="Add Location"
        size="sm"
        @click="$emit('create-location')"
      />
    </div>

    <!-- Barcode Scanner Component -->
    <div v-if="showBarcodeScanner" class="q-mb-sm">
      <BarcodeScanner
        ref="barcodeScannerRef"
        :search-components="false"
        class="barcode-scanner-compact"
        @scan-result="handleBarcodeScanned"
        @close-scanner="closeBarcodeScanner"
      />
    </div>

    <!-- Search -->
    <q-input
      v-model="searchQuery"
      outlined
      dense
      placeholder="Search locations..."
      debounce="300"
      class="q-mb-md"
      @update:model-value="onSearch"
    >
      <template #prepend>
        <q-icon name="search" />
      </template>
      <template #append>
        <q-btn
          v-if="!searchQuery"
          icon="qr_code_scanner"
          flat
          round
          dense
          color="primary"
          class="q-mr-xs"
          @click="openBarcodeScanner"
        >
          <q-tooltip>Scan barcode to search locations</q-tooltip>
        </q-btn>
        <q-icon
          v-if="searchQuery"
          name="clear"
          class="cursor-pointer"
          @click="clearSearch"
        />
      </template>
    </q-input>

    <!-- Loading state -->
    <q-inner-loading :showing="loading">
      <q-spinner color="primary" size="50px" />
    </q-inner-loading>

    <!-- Error message -->
    <q-banner v-if="error" class="text-white bg-negative q-mb-md">
      <template #avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
      <template #action>
        <q-btn flat color="white" label="Dismiss" @click="clearError" />
      </template>
    </q-banner>

    <!-- Tree View -->
    <q-tree
      :nodes="treeNodes"
      node-key="id"
      :expanded="expanded"
      :selected="selectedLocationId"
      :filter="searchQuery"
      :filter-method="filterMethod"
      default-expand-all
      @update:expanded="expanded = $event"
      @update:selected="onLocationSelected"
    >
      <template #default-header="prop">
        <div class="row items-center full-width">
          <div class="col">
            <div class="row items-center q-gutter-xs">
              <q-icon
                :name="getLocationIcon(prop.node.type)"
                :color="getLocationColor(prop.node.type)"
                size="sm"
              />
              <span class="text-weight-medium">{{ prop.node.label }}</span>
              <q-chip
                v-if="prop.node.component_count !== undefined"
                size="sm"
                :label="prop.node.component_count"
                color="grey-4"
                text-color="grey-8"
              />
            </div>
            <div v-if="prop.node.description" class="text-caption text-grey q-ml-md">
              {{ prop.node.description }}
            </div>
          </div>

          <div class="col-auto">
            <q-btn-dropdown
              flat
              dense
              icon="more_vert"
              size="sm"
              @click.stop
            >
              <q-list>
                <q-item
                  v-close-popup
                  clickable
                  @click="$emit('view-location', prop.node.data)"
                >
                  <q-item-section avatar>
                    <q-icon name="visibility" />
                  </q-item-section>
                  <q-item-section>View Details</q-item-section>
                </q-item>

                <q-item
                  v-close-popup
                  clickable
                  @click="$emit('edit-location', prop.node.data)"
                >
                  <q-item-section avatar>
                    <q-icon name="edit" />
                  </q-item-section>
                  <q-item-section>Edit</q-item-section>
                </q-item>

                <q-item
                  v-close-popup
                  clickable
                  @click="$emit('add-child-location', prop.node.data)"
                >
                  <q-item-section avatar>
                    <q-icon name="add" />
                  </q-item-section>
                  <q-item-section>Add Child Location</q-item-section>
                </q-item>

                <q-separator />

                <q-item
                  v-close-popup
                  clickable
                  class="text-negative"
                  @click="$emit('delete-location', prop.node.data)"
                >
                  <q-item-section avatar>
                    <q-icon name="delete" />
                  </q-item-section>
                  <q-item-section>Delete</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
        </div>
      </template>

      <!-- Empty state when no locations -->
      <template v-if="!loading && treeNodes.length === 0" #no-nodes>
        <div class="text-center q-pa-lg">
          <q-icon name="folder_open" size="4em" color="grey-4" />
          <div class="text-h6 text-grey q-mt-md">No Storage Locations</div>
          <div class="text-grey q-mb-md">
            Create your first storage location to organize components
          </div>
          <q-btn
            color="primary"
            label="Create Location"
            @click="$emit('create-location')"
          />
        </div>
      </template>
    </q-tree>

    <!-- Statistics Summary -->
    <div v-if="!loading && locations.length > 0" class="q-mt-lg">
      <q-separator class="q-mb-md" />
      <div class="row q-gutter-md">
        <div class="col">
          <q-card flat>
            <q-card-section class="text-center">
              <div class="text-h6">{{ locations.length }}</div>
              <div class="text-caption text-grey">Total Locations</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card flat>
            <q-card-section class="text-center">
              <div class="text-h6">{{ locationsByType.room?.length || 0 }}</div>
              <div class="text-caption text-grey">Rooms</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card flat>
            <q-card-section class="text-center">
              <div class="text-h6">{{ locationsByType.cabinet?.length || 0 }}</div>
              <div class="text-caption text-grey">Cabinets</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card flat>
            <q-card-section class="text-center">
              <div class="text-h6">{{ (locationsByType.bin?.length || 0) + (locationsByType.shelf?.length || 0) }}</div>
              <div class="text-caption text-grey">Bins & Shelves</div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useQuasar } from 'quasar'
import { useStorageStore } from '../stores/storage'
import BarcodeScanner from './BarcodeScanner.vue'
import type { StorageLocation } from '../services/api'

interface ScanResult {
  data: string
  format: string
  timestamp: Date
}

interface TreeNode {
  id: string
  label: string
  type: string
  description?: string
  component_count?: number
  children?: TreeNode[]
  data: StorageLocation
}

const emit = defineEmits<{
  'create-location': []
  'view-location': [location: StorageLocation]
  'edit-location': [location: StorageLocation]
  'add-child-location': [parentLocation: StorageLocation]
  'delete-location': [location: StorageLocation]
  'location-selected': [location: StorageLocation | null]
}>()

const $q = useQuasar()
const storageStore = useStorageStore()
const {
  locations,
  hierarchicalLocations,
  locationsByType,
  loading,
  error
} = storeToRefs(storageStore)

const searchQuery = ref('')
const expanded = ref<string[]>([])
const selectedLocationId = ref<string | null>(null)
const showBarcodeScanner = ref(false)
const barcodeScannerRef = ref()

const treeNodes = computed<TreeNode[]>(() => {
  const buildTreeNodes = (locations: (StorageLocation & { children?: StorageLocation[] })[]): TreeNode[] => {
    return locations.map(location => ({
      id: location.id,
      label: location.name,
      type: location.type,
      description: location.description || undefined,
      component_count: location.component_count,
      data: location,
      children: location.children ? buildTreeNodes(location.children) : undefined
    }))
  }

  return buildTreeNodes(hierarchicalLocations.value)
})

const getLocationIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    building: 'domain',
    room: 'room',
    cabinet: 'inventory_2',
    shelf: 'shelves',
    drawer: 'inbox',
    bin: 'archive',
    container: 'storage'
  }
  return iconMap[type] || 'folder'
}

const getLocationColor = (type: string) => {
  const colorMap: Record<string, string> = {
    building: 'blue',
    room: 'green',
    cabinet: 'orange',
    shelf: 'purple',
    drawer: 'teal',
    bin: 'amber',
    container: 'grey'
  }
  return colorMap[type] || 'grey'
}

const filterMethod = (node: TreeNode, filter: string) => {
  if (!filter) return true

  const searchTerm = filter.toLowerCase()
  const matchesName = node.label.toLowerCase().includes(searchTerm)
  const matchesDescription = node.description?.toLowerCase().includes(searchTerm) || false
  const matchesType = node.type.toLowerCase().includes(searchTerm)

  return matchesName || matchesDescription || matchesType
}

const onLocationSelected = (locationId: string | null) => {
  selectedLocationId.value = locationId
  const location = locations.value.find(l => l.id === locationId) || null
  emit('location-selected', location)
}

const onSearch = (_query: string) => {
  // The q-tree component handles filtering internally
  // We just need to update the searchQuery ref
}

const clearSearch = () => {
  searchQuery.value = ''
}

const clearError = () => {
  storageStore.clearError()
}

const openBarcodeScanner = () => {
  showBarcodeScanner.value = true
  // Give Vue time to render the component before starting scanner
  nextTick(() => {
    if (barcodeScannerRef.value) {
      barcodeScannerRef.value.startScanning()
    }
  })
}

const closeBarcodeScanner = () => {
  if (barcodeScannerRef.value) {
    barcodeScannerRef.value.stopScanning()
  }
  // Completely hide the scanner component
  showBarcodeScanner.value = false
}

const handleBarcodeScanned = (scanResult: ScanResult) => {
  if (scanResult && scanResult.data) {
    // Set the search query from barcode
    searchQuery.value = scanResult.data
    // Completely close the scanner
    closeBarcodeScanner()
  }
  $q.notify({
    type: 'positive',
    message: `Barcode scanned: ${scanResult.data}`,
    timeout: 2000
  })
}

onMounted(() => {
  storageStore.fetchLocations({
    include_component_count: true
  })
})

// Expose functions and refs to parent component
defineExpose({
  setSearchQuery: (query: string) => {
    searchQuery.value = query
  },
  clearSearch,
  openBarcodeScanner,
  closeBarcodeScanner
})
</script>

<style scoped>
.storage-location-tree {
  min-height: 400px;
}

.q-tree .q-tree__node-header {
  padding: 8px 12px;
}

.q-tree .q-tree__node-header:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.q-tree .q-tree__node--selected > .q-tree__node-header {
  background-color: rgba(25, 118, 210, 0.1);
  color: #1976d2;
}

/* Responsive barcode scanner sizing */
.barcode-scanner-compact {
  max-width: 100%;
}

/* Make scanner more compact on medium and larger screens */
@media (min-width: 768px) {
  .barcode-scanner-compact :deep(.scanner-container) {
    max-width: 400px;
    margin: 0 auto;
  }

  .barcode-scanner-compact :deep(.camera-video) {
    max-height: 300px;
    object-fit: cover;
  }
}
</style>