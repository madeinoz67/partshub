<template>
  <div class="move-stock-form q-pa-md">
    <div class="text-h6 q-mb-md">Move Stock</div>

    <q-form @submit.prevent="handleSubmit">
      <div class="q-gutter-md">
        <!-- Source Location (Pre-selected) -->
        <q-select
          v-model="formData.source_location_id"
          :options="sourceLocationOptions"
          label="Source Location *"
          outlined
          dense
          emit-value
          map-options
          :rules="[
            val => !!val || 'Source location is required'
          ]"
          @update:model-value="onSourceLocationChange"
        >
          <template #prepend>
            <q-icon name="place" />
          </template>
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-item-label>{{ scope.opt.label }}</q-item-label>
                <q-item-label caption>
                  Available: {{ scope.opt.quantity }} units
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
          <template #append>
            <span v-if="sourceAvailableQuantity !== null" class="text-caption text-primary">
              Available: {{ sourceAvailableQuantity }}
            </span>
          </template>
        </q-select>

        <!-- Destination Location -->
        <q-select
          v-model="formData.destination_location_id"
          :options="destinationLocationOptions"
          label="Destination Location *"
          outlined
          dense
          emit-value
          map-options
          use-input
          input-debounce="300"
          :rules="[
            val => !!val || 'Destination location is required',
            val => val !== formData.source_location_id || 'Source and destination must be different'
          ]"
          :disable="!formData.source_location_id"
          @filter="filterDestinationLocations"
        >
          <template #prepend>
            <q-icon name="place" />
          </template>
          <template #no-option>
            <q-item>
              <q-item-section class="text-grey">
                No destination locations found
              </q-item-section>
            </q-item>
          </template>
        </q-select>

        <!-- Quantity Input with Auto-capping -->
        <q-input
          v-model.number="formData.quantity"
          type="number"
          label="Quantity *"
          outlined
          dense
          :rules="[
            val => val !== null && val !== '' || 'Quantity is required',
            val => val > 0 || 'Quantity must be positive',
            val => sourceAvailableQuantity === null || val <= sourceAvailableQuantity || `Maximum ${sourceAvailableQuantity} available`
          ]"
          :disable="!formData.source_location_id"
          @update:model-value="onQuantityChange"
        >
          <template #prepend>
            <q-icon name="move_up" />
          </template>
          <template #hint>
            <span v-if="sourceAvailableQuantity !== null">
              Maximum available: {{ sourceAvailableQuantity }}
            </span>
          </template>
        </q-input>

        <!-- Comments -->
        <q-input
          v-model="formData.comments"
          type="textarea"
          label="Comments (optional)"
          outlined
          dense
          rows="3"
          maxlength="500"
          counter
        >
          <template #prepend>
            <q-icon name="notes" />
          </template>
        </q-input>

        <!-- Actions -->
        <div class="row q-gutter-sm justify-end">
          <q-btn
            flat
            color="negative"
            label="Cancel"
            @click="handleCancel"
          />
          <q-btn
            type="submit"
            color="primary"
            label="Move Stock"
            :loading="submitting"
            :disable="!formData.source_location_id || !formData.destination_location_id || !formData.quantity || formData.quantity <= 0 || formData.source_location_id === formData.destination_location_id"
          />
        </div>
      </div>
    </q-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Notify } from 'quasar'
import { useStorageStore } from '../../stores/storage'
import { stockOperationsApi, type MoveStockRequest } from '../../services/stockOperations'

// Props
interface Props {
  componentId: string
  sourceLocationId?: string // Optional: pre-select source location
  allLocations: Array<{
    location: {
      id: string
      name: string
      location_hierarchy: string
    }
    quantity_on_hand: number
  }>
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  success: [response: unknown]
  cancel: []
}>()

// Store
const storageStore = useStorageStore()

// Component state
const submitting = ref(false)
const sourceAvailableQuantity = ref<number | null>(null)
const filteredDestinationOptions = ref<Array<{ label: string; value: string }>>([])

// Form data
const formData = ref<{
  source_location_id: string | null
  destination_location_id: string | null
  quantity: number | null
  comments: string | null
}>({
  source_location_id: props.sourceLocationId || null,
  destination_location_id: null,
  quantity: null,
  comments: null
})

// Computed source location options (locations with stock)
const sourceLocationOptions = computed(() => {
  return props.allLocations
    .filter(loc => loc.quantity_on_hand > 0)
    .map(loc => ({
      label: loc.location.location_hierarchy,
      value: loc.location.id,
      quantity: loc.quantity_on_hand
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

// Computed destination location options (all locations except source)
const destinationLocationOptions = computed(() => {
  // Combine component locations and all storage locations
  const componentLocationIds = new Set(props.allLocations.map(loc => loc.location.id))

  // Get all storage locations from store
  const allDestinations = storageStore.locationOptions
    .filter(loc => loc.value !== formData.value.source_location_id)
    .map(loc => ({
      label: loc.label,
      value: loc.value
    }))

  // Mark "Other locations" section
  const componentDestinations = allDestinations.filter(loc => componentLocationIds.has(loc.value))
  const otherDestinations = allDestinations.filter(loc => !componentLocationIds.has(loc.value))

  // Combine with separators
  const result: Array<{ label: string; value: string; disable?: boolean }> = []

  if (componentDestinations.length > 0) {
    result.push(...componentDestinations)
  }

  if (otherDestinations.length > 0) {
    if (result.length > 0) {
      result.push({ label: '──── Other Locations ────', value: '', disable: true })
    }
    result.push(...otherDestinations)
  }

  return result
})

// Methods
const filterDestinationLocations = (val: string, update: (fn: () => void) => void) => {
  update(() => {
    if (val === '') {
      filteredDestinationOptions.value = destinationLocationOptions.value
    } else {
      const needle = val.toLowerCase()
      filteredDestinationOptions.value = destinationLocationOptions.value.filter(
        loc => !loc.disable && loc.label.toLowerCase().includes(needle)
      )
    }
  })
}

const onSourceLocationChange = (locationId: string | null) => {
  if (locationId) {
    const location = props.allLocations.find(loc => loc.location.id === locationId)
    sourceAvailableQuantity.value = location?.quantity_on_hand ?? null

    // Reset quantity if it exceeds available
    if (formData.value.quantity && sourceAvailableQuantity.value !== null && formData.value.quantity > sourceAvailableQuantity.value) {
      formData.value.quantity = sourceAvailableQuantity.value

      Notify.create({
        type: 'warning',
        message: `Quantity auto-capped at ${sourceAvailableQuantity.value} (maximum available)`,
        position: 'top-right',
        timeout: 3000
      })
    }

    // Clear destination if it's the same as source
    if (formData.value.destination_location_id === locationId) {
      formData.value.destination_location_id = null
      Notify.create({
        type: 'warning',
        message: 'Source and destination locations must be different',
        position: 'top-right',
        timeout: 3000
      })
    }
  } else {
    sourceAvailableQuantity.value = null
  }
}

const onQuantityChange = (value: number | null) => {
  // Auto-cap quantity if it exceeds available
  if (value && sourceAvailableQuantity.value !== null && value > sourceAvailableQuantity.value) {
    formData.value.quantity = sourceAvailableQuantity.value

    Notify.create({
      type: 'warning',
      message: `Quantity auto-capped at ${sourceAvailableQuantity.value} (maximum available)`,
      position: 'top-right',
      timeout: 3000
    })
  }
}

const handleCancel = () => {
  emit('cancel')
}

const handleSubmit = async () => {
  // Validate form
  if (
    !formData.value.source_location_id ||
    !formData.value.destination_location_id ||
    !formData.value.quantity ||
    formData.value.quantity <= 0
  ) {
    return
  }

  // Prevent same source and destination
  if (formData.value.source_location_id === formData.value.destination_location_id) {
    Notify.create({
      type: 'negative',
      message: 'Source and destination locations must be different',
      position: 'top-right',
      timeout: 3000
    })
    return
  }

  submitting.value = true

  try {
    const request: MoveStockRequest = {
      source_location_id: formData.value.source_location_id,
      destination_location_id: formData.value.destination_location_id,
      quantity: formData.value.quantity,
      comments: formData.value.comments || undefined
    }

    const response = await stockOperationsApi.moveStock(props.componentId, request)
    emit('success', response)
  } catch (error: unknown) {
    console.error('Failed to move stock:', error)
  } finally {
    submitting.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch all storage locations if not already loaded
  if (storageStore.locationOptions.length === 0) {
    await storageStore.fetchLocations()
  }

  // Initialize source location if provided
  if (props.sourceLocationId) {
    onSourceLocationChange(props.sourceLocationId)
  }

  filteredDestinationOptions.value = destinationLocationOptions.value
})

// Watch for location changes from parent
watch(() => props.allLocations, () => {
  // Reset selected source location if it no longer has stock
  if (formData.value.source_location_id) {
    const location = props.allLocations.find(loc => loc.location.id === formData.value.source_location_id)
    if (!location || location.quantity_on_hand === 0) {
      formData.value.source_location_id = null
      sourceAvailableQuantity.value = null
    }
  }
}, { deep: true })
</script>

<style scoped>
.move-stock-form {
  max-width: 600px;
}
</style>
