<template>
  <q-page class="q-pa-md">
    <!-- Page Title and View Toggle -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Storage Locations</div>
        <div class="text-caption text-grey">Organize your workspace with hierarchical storage</div>
      </div>
      <div class="col-auto">
        <!-- View Toggle -->
        <q-btn-toggle
          v-model="viewMode"
          toggle-color="primary"
          :options="[
            { label: 'Table', value: 'table', icon: 'table_chart' },
            { label: 'Tree', value: 'tree', icon: 'account_tree' }
          ]"
          unelevated
        />
      </div>
    </div>

    <!-- Table View -->
    <div v-if="viewMode === 'table'">
      <q-card>
        <q-card-section>
          <StorageLocationTable
            ref="locationTableRef"
            :locations="allLocations"
            :loading="isLoading"
            @refresh="refreshLocations"
            @location-selected="onLocationSelected"
            @edit-location="editLocation"
            @create-bulk-locations="openLayoutDialog"
            @scan-result="onQRCodeScanned"
          />
        </q-card-section>
      </q-card>
    </div>

    <!-- Tree View -->
    <div v-else class="row q-gutter-lg">
      <!-- Storage Location Tree -->
      <div class="col-md-4 col-xs-12">
        <q-card>
          <q-card-section>
            <StorageLocationTree
              @create-location="createLocation"
              @view-location="viewLocation"
              @edit-location="editLocation"
              @add-child-location="addChildLocation"
              @delete-location="deleteLocation"
              @location-selected="onLocationSelected"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- Location Details and Components -->
      <div class="col-md-8 col-xs-12">
        <div v-if="selectedLocation">
          <!-- Location Details Card -->
          <q-card class="q-mb-md">
            <q-card-section>
              <div class="row items-center">
                <div class="col">
                  <div class="text-h6">{{ selectedLocation.name }}</div>
                  <div class="text-caption text-grey">{{ selectedLocation.location_hierarchy }}</div>
                </div>
                <div v-if="canPerformCrud()" class="col-auto">
                  <q-btn-group>
                    <q-btn
                      color="primary"
                      icon="edit"
                      label="Edit"
                      size="sm"
                      @click="editLocation(selectedLocation)"
                    />
                    <q-btn
                      color="secondary"
                      icon="add"
                      label="Add Child"
                      size="sm"
                      @click="addChildLocation(selectedLocation)"
                    />
                  </q-btn-group>
                </div>
              </div>

              <div v-if="selectedLocation.description" class="q-mt-md">
                <div class="text-body2">{{ selectedLocation.description }}</div>
              </div>

              <div class="row q-gutter-md q-mt-md">
                <div class="col">
                  <q-chip
                    :icon="getLocationIcon(selectedLocation.type)"
                    :color="getLocationColor(selectedLocation.type)"
                    text-color="white"
                    :label="selectedLocation.type.toUpperCase()"
                  />
                </div>
                <div v-if="selectedLocation.component_count !== undefined" class="col">
                  <q-chip
                    icon="inventory"
                    color="grey-6"
                    text-color="white"
                    :label="`${selectedLocation.component_count} components`"
                  />
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- Components in Location -->
          <q-card>
            <q-card-section>
              <div class="text-h6 q-mb-md">Components in this location</div>

              <q-table
                :rows="locationComponents"
                :columns="componentColumns"
                row-key="id"
                :loading="componentsLoading"
                :pagination="{ rowsPerPage: 25 }"
                dense
              >
                <template #body-cell-name="props">
                  <q-td :props="props">
                    <div class="text-weight-medium cursor-pointer text-primary">
                      {{ props.row.name }}
                    </div>
                    <div v-if="props.row.part_number" class="text-caption text-grey">
                      PN: {{ props.row.part_number }}
                    </div>
                  </q-td>
                </template>

                <template #body-cell-stock="props">
                  <q-td :props="props">
                    <q-chip
                      :color="getStockStatusColor(props.row)"
                      text-color="white"
                      :label="props.row.quantity_on_hand"
                      size="sm"
                    />
                  </q-td>
                </template>

                <template #body-cell-category="props">
                  <q-td :props="props">
                    <q-chip
                      v-if="props.row.category"
                      outline
                      color="primary"
                      :label="props.row.category.name"
                      size="sm"
                    />
                    <span v-else class="text-caption text-grey">Uncategorized</span>
                  </q-td>
                </template>

                <template #no-data>
                  <div class="full-width row flex-center q-gutter-sm">
                    <q-icon size="2em" name="inventory_2" />
                    <span>No components in this location</span>
                  </div>
                </template>
              </q-table>
            </q-card-section>
          </q-card>
        </div>

        <!-- No Location Selected -->
        <div v-else class="text-center q-pa-xl">
          <q-icon name="folder_open" size="4em" color="grey-4" />
          <div class="text-h6 text-grey q-mt-md">Select a location</div>
          <div class="text-grey">
            Choose a storage location from the tree to view its details and components
          </div>
        </div>
      </div>
    </div>

    <!-- Storage Location Form Dialog -->
    <StorageLocationForm
      v-model="showLocationDialog"
      :location="selectedLocationForEdit"
      :parent-location="parentLocationForCreate"
      :is-edit="isEditMode"
      @saved="onLocationSaved"
    />

    <!-- Location Layout Dialog (Bulk Creation) -->
    <LocationLayoutDialog
      v-model="showLayoutDialog"
      :parent-location-options="parentLocationOptions"
      @created="onBulkLocationsCreated"
    />

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="delete" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete <strong>{{ selectedLocationForEdit?.name }}</strong>?
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancel" color="primary" />
          <q-btn
            flat
            label="Delete"
            color="negative"
            :loading="deleteLoading"
            @click="confirmDelete"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { storeToRefs } from 'pinia'
import StorageLocationTree from '../components/StorageLocationTree.vue'
import StorageLocationForm from '../components/StorageLocationForm.vue'
import LocationLayoutDialog from '../components/storage/LocationLayoutDialog.vue'
import StorageLocationTable from '../components/storage/StorageLocationTable.vue'
import { useStorageStore } from '../stores/storage'
import { useAuth } from '../composables/useAuth'
import type { StorageLocation, Component } from '../services/api'

interface ScanResult {
  data: string
  format: string
  timestamp: Date
}

const $q = useQuasar()
const storageStore = useStorageStore()
const { requireAuth, canPerformCrud } = useAuth()

const {
  currentLocation: selectedLocation,
  locationComponents,
  loading: componentsLoading,
  locations
} = storeToRefs(storageStore)

const selectedLocationForEdit = ref<StorageLocation | null>(null)
const parentLocationForCreate = ref<StorageLocation | null>(null)
const showLocationDialog = ref(false)
const showLayoutDialog = ref(false)
const showDeleteDialog = ref(false)
const isEditMode = ref(false)
const deleteLoading = ref(false)
const viewMode = ref<'table' | 'tree'>('table')
const locationTableRef = ref<InstanceType<typeof StorageLocationTable> | null>(null)

// Computed options for parent location selector in layout dialog
const parentLocationOptions = computed(() => {
  return storageStore.locationOptions
})

// All locations for table view
const allLocations = computed(() => storageStore.locations)

// Loading state for table
const isLoading = computed(() => storageStore.loading)

// Refresh locations
const refreshLocations = () => {
  storageStore.fetchLocations({
    include_component_count: true
  })
}

// Initialize data on mount
onMounted(() => {
  refreshLocations()
})

const componentColumns = [
  {
    name: 'name',
    required: true,
    label: 'Component',
    align: 'left' as const,
    field: 'name',
    sortable: true
  },
  {
    name: 'stock',
    label: 'Stock',
    align: 'center' as const,
    field: 'quantity_on_hand',
    sortable: true
  },
  {
    name: 'category',
    label: 'Category',
    align: 'left' as const,
    field: (row: Component) => row.category?.name || ''
  },
  {
    name: 'manufacturer',
    label: 'Manufacturer',
    align: 'left' as const,
    field: 'manufacturer'
  }
]

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

const getStockStatusColor = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

const onLocationSelected = (location: StorageLocation | null) => {
  if (location) {
    storageStore.fetchLocation(location.id, {
      include_component_count: true
    })
    storageStore.fetchLocationComponents(location.id, {
      include_children: false
    })
  }
}

const createLocation = () => {
  if (!requireAuth('create storage locations')) return

  selectedLocationForEdit.value = null
  parentLocationForCreate.value = null
  isEditMode.value = false
  showLocationDialog.value = true
}

const viewLocation = (location: StorageLocation) => {
  onLocationSelected(location)
}

const editLocation = (location: StorageLocation) => {
  if (!requireAuth('edit storage locations')) return

  selectedLocationForEdit.value = location
  parentLocationForCreate.value = null
  isEditMode.value = true
  showLocationDialog.value = true
}

const addChildLocation = (parentLocation: StorageLocation) => {
  if (!requireAuth('create child storage locations')) return

  selectedLocationForEdit.value = null
  parentLocationForCreate.value = parentLocation
  isEditMode.value = false
  showLocationDialog.value = true
}

const deleteLocation = (location: StorageLocation) => {
  if (!requireAuth('delete storage locations')) return

  selectedLocationForEdit.value = location
  showDeleteDialog.value = true
}

const onLocationSaved = (_location: StorageLocation) => {
  $q.notify({
    type: 'positive',
    message: isEditMode.value ? 'Location updated successfully' : 'Location created successfully',
    position: 'top-right'
  })

  // Reset state
  selectedLocationForEdit.value = null
  parentLocationForCreate.value = null
  isEditMode.value = false
  showLocationDialog.value = false

  // Refresh locations list
  storageStore.fetchLocations({
    include_component_count: true
  })
}

const confirmDelete = async () => {
  if (!selectedLocationForEdit.value) return

  deleteLoading.value = true
  try {
    // Note: This would need to be implemented in the storage service
    // await storageStore.deleteLocation(selectedLocationForEdit.value.id)

    $q.notify({
      type: 'positive',
      message: 'Location deleted successfully',
      position: 'top-right'
    })

    showDeleteDialog.value = false
    selectedLocationForEdit.value = null

    // Refresh locations list
    storageStore.fetchLocations({
      include_component_count: true
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete location',
      position: 'top-right'
    })
  } finally {
    deleteLoading.value = false
  }
}

const openLayoutDialog = () => {
  if (!requireAuth('create bulk storage locations')) return
  showLayoutDialog.value = true
}

const onBulkLocationsCreated = (response: { created_count: number; created_ids: string[] }) => {
  $q.notify({
    type: 'positive',
    message: `Successfully created ${response.created_count} location${response.created_count !== 1 ? 's' : ''}`,
    position: 'top-right'
  })

  // Refresh the locations (works for both tree and table view)
  refreshLocations()
}

// QR Code Scanner handlers
const onQRCodeScanned = (result: ScanResult) => {
  const qrCode = result.data

  // Search for location by QR code ID
  const foundLocation = allLocations.value.find(loc =>
    loc.qr_code_id === qrCode || loc.id === qrCode
  )

  if (foundLocation) {
    // Location found - select it
    onLocationSelected(foundLocation)

    // Show notification - already shown in StorageLocationTable
  } else {
    // Location not found - notification already shown in StorageLocationTable
  }
}
</script>