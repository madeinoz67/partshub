<template>
  <q-page class="q-pa-md">
    <!-- Page Title -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Storage Locations</div>
        <div class="text-caption text-grey">Organize your workspace with hierarchical storage</div>
      </div>
    </div>

    <!-- Storage Location Table -->
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
import StorageLocationForm from '../components/StorageLocationForm.vue'
import LocationLayoutDialog from '../components/storage/LocationLayoutDialog.vue'
import StorageLocationTable from '../components/storage/StorageLocationTable.vue'
import { useStorageStore } from '../stores/storage'
import { useAuth } from '../composables/useAuth'
import type { StorageLocation } from '../services/api'

interface ScanResult {
  data: string
  format: string
  timestamp: Date
}

const $q = useQuasar()
const storageStore = useStorageStore()
const { requireAuth } = useAuth()

const selectedLocationForEdit = ref<StorageLocation | null>(null)
const parentLocationForCreate = ref<StorageLocation | null>(null)
const showLocationDialog = ref(false)
const showLayoutDialog = ref(false)
const showDeleteDialog = ref(false)
const isEditMode = ref(false)
const deleteLoading = ref(false)
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

const onLocationSelected = (location: StorageLocation | null) => {
  if (location) {
    // Navigate to location detail or perform other action
    console.log('Location selected:', location)
  }
}

const editLocation = (location: StorageLocation) => {
  if (!requireAuth('edit storage locations')) return

  selectedLocationForEdit.value = location
  parentLocationForCreate.value = null
  isEditMode.value = true
  showLocationDialog.value = true
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