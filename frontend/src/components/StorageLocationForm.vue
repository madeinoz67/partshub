<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    maximized
    transition-show="slide-up"
    transition-hide="slide-down"
    @update:model-value="$emit('update:model-value', $event)"
  >
    <q-card class="column full-height">
      <q-card-section class="q-pb-none">
        <div class="row items-center">
          <div class="text-h6">{{ isEdit ? 'Edit Storage Location' : 'Add Storage Location' }}</div>
          <q-space />
          <q-btn
            icon="close"
            flat
            round
            dense
            @click="$emit('update:model-value', false)"
          />
        </div>
      </q-card-section>

      <q-separator />

      <q-card-section class="col scroll">
        <q-form ref="formRef" class="q-gutter-md" @submit="onSubmit">
          <!-- Basic Information -->
          <div class="text-h6 q-mt-md q-mb-sm">Basic Information</div>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.name"
                label="Location Name *"
                outlined
                :rules="[val => !!val || 'Name is required']"
                autofocus
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-select
                v-model="form.type"
                :options="locationTypeOptions"
                label="Location Type *"
                outlined
                emit-value
                map-options
                :rules="[val => !!val || 'Type is required']"
              />
            </div>

            <div class="col-12">
              <q-input
                v-model="form.description"
                label="Description"
                outlined
                type="textarea"
                rows="2"
                hint="Optional description of this location"
              />
            </div>
          </div>

          <!-- Hierarchy -->
          <div class="text-h6 q-mt-lg q-mb-sm">Location Hierarchy</div>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-select
                v-model="form.parent_id"
                :options="parentLocationOptions"
                label="Parent Location"
                outlined
                emit-value
                map-options
                clearable
                :loading="locationsLoading"
                hint="Optional parent location for hierarchy"
              />
            </div>

            <div v-if="parentLocation" class="col-md-6 col-xs-12">
              <q-input
                :model-value="parentLocation.location_hierarchy + ' > ' + (form.name || 'New Location')"
                label="Full Hierarchy Preview"
                outlined
                readonly
                hint="How this location will appear in the hierarchy"
              />
            </div>
          </div>

          <!-- QR Code -->
          <div class="text-h6 q-mt-lg q-mb-sm">Identification</div>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.qr_code_id"
                label="QR Code ID"
                outlined
                hint="Optional QR code identifier for this location"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <div class="q-pa-md bg-grey-1 rounded-borders">
                <div class="text-caption text-grey q-mb-sm">Quick Actions</div>
                <q-btn
                  outline
                  color="primary"
                  icon="qr_code"
                  label="Generate QR Code"
                  size="sm"
                  :disable="!form.name"
                  class="q-mr-sm"
                  @click="generateQRCode"
                />
                <q-btn
                  outline
                  color="secondary"
                  icon="qr_code_scanner"
                  label="Scan QR Code"
                  size="sm"
                  @click="scanQRCode"
                />
              </div>
            </div>
          </div>

          <!-- Location Guidelines -->
          <div class="text-h6 q-mt-lg q-mb-sm">Organization Tips</div>
          <q-card flat bordered>
            <q-card-section>
              <div class="text-caption text-grey q-mb-sm">Location Type Guidelines:</div>
              <div class="q-gutter-sm">
                <div class="row items-center">
                  <q-icon name="domain" color="blue" class="q-mr-sm" />
                  <span class="text-caption"><strong>Building:</strong> Main facility or workspace</span>
                </div>
                <div class="row items-center">
                  <q-icon name="room" color="green" class="q-mr-sm" />
                  <span class="text-caption"><strong>Room:</strong> Individual rooms within a building</span>
                </div>
                <div class="row items-center">
                  <q-icon name="inventory_2" color="orange" class="q-mr-sm" />
                  <span class="text-caption"><strong>Cabinet:</strong> Storage cabinets or enclosures</span>
                </div>
                <div class="row items-center">
                  <q-icon name="shelves" color="purple" class="q-mr-sm" />
                  <span class="text-caption"><strong>Shelf:</strong> Individual shelves within cabinets</span>
                </div>
                <div class="row items-center">
                  <q-icon name="inbox" color="teal" class="q-mr-sm" />
                  <span class="text-caption"><strong>Drawer:</strong> Drawers within cabinets</span>
                </div>
                <div class="row items-center">
                  <q-icon name="archive" color="amber" class="q-mr-sm" />
                  <span class="text-caption"><strong>Bin:</strong> Small containers or compartments</span>
                </div>
                <div class="row items-center">
                  <q-icon name="storage" color="grey" class="q-mr-sm" />
                  <span class="text-caption"><strong>Container:</strong> Boxes or other containers</span>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right" class="q-pa-md">
        <q-btn
          flat
          label="Cancel"
          :disable="loading"
          @click="$emit('update:model-value', false)"
        />
        <q-btn
          color="primary"
          label="Save Location"
          :loading="loading"
          @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useStorageStore } from '../stores/storage'
import type { StorageLocation } from '../services/api'
import { QForm } from 'quasar'

interface Props {
  modelValue: boolean
  location?: StorageLocation | null
  parentLocation?: StorageLocation | null
  isEdit?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  location: null,
  parentLocation: null,
  isEdit: false
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'saved': [location: StorageLocation]
}>()

const formRef = ref<QForm>()
const storageStore = useStorageStore()

const { locations, loading } = storeToRefs(storageStore)
const locationsLoading = ref(false)

const form = ref({
  name: '',
  description: '',
  type: '',
  parent_id: '',
  qr_code_id: ''
})

const locationTypeOptions = [
  { label: 'Building', value: 'building' },
  { label: 'Room', value: 'room' },
  { label: 'Cabinet', value: 'cabinet' },
  { label: 'Shelf', value: 'shelf' },
  { label: 'Drawer', value: 'drawer' },
  { label: 'Bin', value: 'bin' },
  { label: 'Container', value: 'container' }
]

const parentLocationOptions = computed(() => {
  let availableLocations = locations.value

  // If editing, exclude the current location and its children to prevent circular references
  if (props.isEdit && props.location) {
    availableLocations = locations.value.filter(loc => {
      // Exclude self
      if (loc.id === props.location?.id) return false

      // Exclude if this location is in the hierarchy of the location being edited
      return !loc.location_hierarchy.includes(props.location?.name || '')
    })
  }

  return availableLocations.map(loc => ({
    label: loc.location_hierarchy,
    value: loc.id
  })).sort((a, b) => a.label.localeCompare(b.label))
})

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    type: '',
    parent_id: props.parentLocation?.id || '',
    qr_code_id: ''
  }
}

const populateForm = (location: StorageLocation) => {
  form.value = {
    name: location.name,
    description: location.description || '',
    type: location.type,
    parent_id: location.parent_id || '',
    qr_code_id: location.qr_code_id || ''
  }
}

const generateQRCode = () => {
  if (!form.value.name) return

  // Generate a simple QR code ID based on the location name
  const qrId = `LOC-${form.value.name.replace(/\s+/g, '-').toUpperCase()}-${Date.now().toString(36).toUpperCase()}`
  form.value.qr_code_id = qrId
}

const scanQRCode = () => {
  // TODO: Implement QR code scanning functionality
  console.log('QR Code scanning not implemented yet')
}

const onSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate()
  if (!valid) return

  try {
    const locationData = {
      ...form.value,
      parent_id: form.value.parent_id || null,
      description: form.value.description || null,
      qr_code_id: form.value.qr_code_id || null
    }

    let result: StorageLocation
    if (props.isEdit && props.location) {
      result = await storageStore.updateLocation(props.location.id, locationData)
    } else {
      result = await storageStore.createLocation(locationData)
    }

    emit('saved', result)
    emit('update:model-value', false)
  } catch (error) {
    console.error('Failed to save storage location:', error)
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (props.isEdit && props.location) {
      populateForm(props.location)
    } else {
      resetForm()
    }

    // Ensure we have locations loaded for parent selection
    if (locations.value.length === 0) {
      storageStore.fetchLocations()
    }
  }
})

watch(() => props.location, (newLocation) => {
  if (newLocation && props.isEdit) {
    populateForm(newLocation)
  }
})

watch(() => props.parentLocation, (newParentLocation) => {
  if (newParentLocation && !props.isEdit) {
    form.value.parent_id = newParentLocation.id
  }
})
</script>

<style scoped>
.full-height {
  height: 100vh;
}
</style>