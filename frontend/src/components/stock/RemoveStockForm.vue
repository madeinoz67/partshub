<template>
  <div class="remove-stock-form q-pa-md">
    <div class="text-h6 q-mb-md">Remove Stock</div>

    <q-form @submit.prevent="handleSubmit">
      <div class="q-gutter-md">
        <!-- Location Selector with Available Quantity -->
        <q-select
          v-model="formData.location_id"
          :options="locationOptionsWithQuantity"
          label="Location *"
          outlined
          dense
          emit-value
          map-options
          use-input
          input-debounce="300"
          :rules="[
            val => !!val || 'Location is required'
          ]"
          @filter="filterLocations"
          @update:model-value="onLocationChange"
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
            <span v-if="availableQuantity !== null" class="text-caption text-primary">
              Available: {{ availableQuantity }}
            </span>
          </template>
          <template #no-option>
            <q-item>
              <q-item-section class="text-grey">
                No locations with stock found
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
            val => availableQuantity === null || val <= availableQuantity || `Maximum ${availableQuantity} available`
          ]"
          :disable="!formData.location_id"
          @update:model-value="onQuantityChange"
        >
          <template #prepend>
            <q-icon name="remove_circle" />
          </template>
          <template #hint>
            <span v-if="availableQuantity !== null">
              Maximum available: {{ availableQuantity }}
            </span>
          </template>
        </q-input>

        <!-- Reason (Optional) -->
        <q-input
          v-model="formData.reason"
          label="Reason (optional)"
          outlined
          dense
          placeholder="e.g., used, damaged, lost"
          maxlength="100"
        >
          <template #prepend>
            <q-icon name="info" />
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
            label="Remove Stock"
            :loading="submitting"
            :disable="!formData.location_id || !formData.quantity || formData.quantity <= 0"
          />
        </div>
      </div>
    </q-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Notify } from 'quasar'
import { stockOperationsApi, type RemoveStockRequest } from '../../services/stockOperations'

// Props
interface Props {
  componentId: string
  locations: Array<{
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

// Component state
const submitting = ref(false)
const availableQuantity = ref<number | null>(null)
const filteredLocationOptions = ref<Array<{ label: string; value: string; quantity: number }>>([])

// Form data
const formData = ref<{
  location_id: string | null
  quantity: number | null
  reason: string | null
  comments: string | null
}>({
  location_id: null,
  quantity: null,
  reason: null,
  comments: null
})

// Computed location options with quantity
const locationOptionsWithQuantity = computed(() => {
  return props.locations
    .filter(loc => loc.quantity_on_hand > 0) // Only show locations with stock
    .map(loc => ({
      label: loc.location.location_hierarchy,
      value: loc.location.id,
      quantity: loc.quantity_on_hand
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

// Methods
const filterLocations = (val: string, update: (fn: () => void) => void) => {
  update(() => {
    if (val === '') {
      filteredLocationOptions.value = locationOptionsWithQuantity.value
    } else {
      const needle = val.toLowerCase()
      filteredLocationOptions.value = locationOptionsWithQuantity.value.filter(
        loc => loc.label.toLowerCase().includes(needle)
      )
    }
  })
}

const onLocationChange = (locationId: string | null) => {
  if (locationId) {
    const location = props.locations.find(loc => loc.location.id === locationId)
    availableQuantity.value = location?.quantity_on_hand ?? null

    // Reset quantity if it exceeds available
    if (formData.value.quantity && availableQuantity.value !== null && formData.value.quantity > availableQuantity.value) {
      formData.value.quantity = availableQuantity.value

      Notify.create({
        type: 'warning',
        message: `Quantity auto-capped at ${availableQuantity.value} (maximum available)`,
        position: 'top-right',
        timeout: 3000
      })
    }
  } else {
    availableQuantity.value = null
  }
}

const onQuantityChange = (value: number | null) => {
  // Auto-cap quantity if it exceeds available
  if (value && availableQuantity.value !== null && value > availableQuantity.value) {
    formData.value.quantity = availableQuantity.value

    Notify.create({
      type: 'warning',
      message: `Quantity auto-capped at ${availableQuantity.value} (maximum available)`,
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
  if (!formData.value.location_id || !formData.value.quantity || formData.value.quantity <= 0) {
    return
  }

  submitting.value = true

  try {
    const request: RemoveStockRequest = {
      location_id: formData.value.location_id,
      quantity: formData.value.quantity,
      reason: formData.value.reason || undefined,
      comments: formData.value.comments || undefined
    }

    const response = await stockOperationsApi.removeStock(props.componentId, request)
    emit('success', response)
  } catch (error: unknown) {
    console.error('Failed to remove stock:', error)
  } finally {
    submitting.value = false
  }
}

// Initialize filtered options
onMounted(() => {
  filteredLocationOptions.value = locationOptionsWithQuantity.value
})

// Watch for location changes from parent
watch(() => props.locations, () => {
  filteredLocationOptions.value = locationOptionsWithQuantity.value

  // Reset selected location if it no longer has stock
  if (formData.value.location_id) {
    const location = props.locations.find(loc => loc.location.id === formData.value.location_id)
    if (!location || location.quantity_on_hand === 0) {
      formData.value.location_id = null
      availableQuantity.value = null
    }
  }
}, { deep: true })
</script>

<style scoped>
.remove-stock-form {
  max-width: 600px;
}
</style>
