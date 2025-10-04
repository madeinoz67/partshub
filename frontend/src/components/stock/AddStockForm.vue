<template>
  <div class="add-stock-form">
    <q-stepper
      ref="stepper"
      v-model="currentStep"
      color="primary"
      animated
      flat
      bordered
    >
      <!-- Step 1: Quantity & Pricing -->
      <q-step
        :name="1"
        title="Quantity & Pricing"
        icon="inventory"
        :done="currentStep > 1"
      >
        <div class="q-gutter-md">
          <!-- Quantity Input -->
          <q-input
            v-model.number="formData.quantity"
            type="number"
            label="Quantity *"
            outlined
            dense
            :rules="[
              val => val !== null && val !== '' || 'Quantity is required',
              val => val > 0 || 'Quantity must be positive'
            ]"
          >
            <template #prepend>
              <q-icon name="add_box" />
            </template>
          </q-input>

          <!-- Pricing Type Selector -->
          <q-select
            v-model="pricingType"
            :options="pricingOptions"
            label="Pricing Type"
            outlined
            dense
            emit-value
            map-options
          >
            <template #prepend>
              <q-icon name="attach_money" />
            </template>
          </q-select>

          <!-- Unit Price (Per Component) -->
          <q-input
            v-if="pricingType === 'per_component'"
            v-model.number="formData.price_per_unit"
            type="number"
            label="Unit Price (per component)"
            outlined
            dense
            step="0.01"
            :rules="[
              val => val === null || val === undefined || val >= 0 || 'Price must be non-negative'
            ]"
            @update:model-value="calculateTotalPrice"
          >
            <template #prepend>
              <q-icon name="attach_money" />
            </template>
            <template #append>
              <span class="text-caption text-grey">Total: ${{ calculatedTotalPrice.toFixed(2) }}</span>
            </template>
          </q-input>

          <!-- Total Price (Entire Lot) -->
          <q-input
            v-if="pricingType === 'entire_lot'"
            v-model.number="formData.total_price"
            type="number"
            label="Total Price (entire lot)"
            outlined
            dense
            step="0.01"
            :rules="[
              val => val === null || val === undefined || val >= 0 || 'Price must be non-negative'
            ]"
            @update:model-value="calculateUnitPrice"
          >
            <template #prepend>
              <q-icon name="attach_money" />
            </template>
            <template #append>
              <span class="text-caption text-grey">Unit: ${{ calculatedUnitPrice.toFixed(4) }}</span>
            </template>
          </q-input>

          <!-- Lot ID -->
          <q-input
            v-model="formData.lot_id"
            label="Lot ID (optional)"
            outlined
            dense
            maxlength="100"
          >
            <template #prepend>
              <q-icon name="label" />
            </template>
          </q-input>
        </div>
      </q-step>

      <!-- Step 2: Location & Comments -->
      <q-step
        :name="2"
        title="Location & Comments"
        icon="place"
        :done="currentStep > 2"
      >
        <div class="q-gutter-md">
          <!-- Location Selector -->
          <q-select
            v-model="formData.location_id"
            :options="locationOptions"
            label="Storage Location *"
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
          >
            <template #prepend>
              <q-icon name="place" />
            </template>
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No locations found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

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
        </div>
      </q-step>

      <!-- Navigation Buttons -->
      <template #navigation>
        <q-stepper-navigation>
          <div class="row q-gutter-sm justify-end">
            <q-btn
              v-if="currentStep > 1"
              flat
              color="primary"
              label="Back"
              @click="previousStep"
            />
            <q-btn
              flat
              color="negative"
              label="Cancel"
              @click="handleCancel"
            />
            <q-btn
              v-if="currentStep < 2"
              color="primary"
              label="Next"
              @click="nextStep"
            />
            <q-btn
              v-else
              color="primary"
              label="Add Stock"
              :loading="submitting"
              @click="handleSubmit"
            />
          </div>
        </q-stepper-navigation>
      </template>
    </q-stepper>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStorageStore } from '../../stores/storage'
import { storeToRefs } from 'pinia'
import { stockOperationsApi, type AddStockRequest } from '../../services/stockOperations'
import type { QStepper } from 'quasar'

// Props
interface Props {
  componentId: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  success: [response: unknown]
  cancel: []
}>()

// Store
const storageStore = useStorageStore()
const { locationOptions: allLocationOptions } = storeToRefs(storageStore)

// Component state
const currentStep = ref(1)
const stepper = ref<QStepper | null>(null)
const submitting = ref(false)
const pricingType = ref<'no_price' | 'per_component' | 'entire_lot'>('no_price')
const locationOptions = ref(allLocationOptions.value)

// Form data
const formData = ref<{
  quantity: number | null
  price_per_unit: number | null
  total_price: number | null
  lot_id: string | null
  location_id: string | null
  comments: string | null
}>({
  quantity: null,
  price_per_unit: null,
  total_price: null,
  lot_id: null,
  location_id: null,
  comments: null
})

// Pricing options
const pricingOptions = [
  { label: 'No price', value: 'no_price' },
  { label: 'Per component', value: 'per_component' },
  { label: 'Entire lot', value: 'entire_lot' }
]

// Computed prices
const calculatedTotalPrice = computed(() => {
  if (pricingType.value === 'per_component' && formData.value.price_per_unit && formData.value.quantity) {
    return formData.value.price_per_unit * formData.value.quantity
  }
  return 0
})

const calculatedUnitPrice = computed(() => {
  if (pricingType.value === 'entire_lot' && formData.value.total_price && formData.value.quantity && formData.value.quantity > 0) {
    return formData.value.total_price / formData.value.quantity
  }
  return 0
})

// Methods
const calculateTotalPrice = () => {
  // Reactively computed, no action needed
}

const calculateUnitPrice = () => {
  // Reactively computed, no action needed
}

const filterLocations = (val: string, update: (fn: () => void) => void) => {
  update(() => {
    if (val === '') {
      locationOptions.value = allLocationOptions.value
    } else {
      const needle = val.toLowerCase()
      locationOptions.value = allLocationOptions.value.filter(
        loc => loc.label.toLowerCase().includes(needle)
      )
    }
  })
}

const nextStep = () => {
  // Validate step 1
  if (currentStep.value === 1) {
    if (!formData.value.quantity || formData.value.quantity <= 0) {
      return
    }
  }

  stepper.value?.next()
}

const previousStep = () => {
  stepper.value?.previous()
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
    // Build request based on pricing type
    const request: AddStockRequest = {
      location_id: formData.value.location_id,
      quantity: formData.value.quantity,
      lot_id: formData.value.lot_id || undefined,
      comments: formData.value.comments || undefined
    }

    // Add pricing fields based on selected type
    if (pricingType.value === 'per_component' && formData.value.price_per_unit !== null) {
      request.price_per_unit = formData.value.price_per_unit
    } else if (pricingType.value === 'entire_lot' && formData.value.total_price !== null) {
      request.total_price = formData.value.total_price
    }

    const response = await stockOperationsApi.addStock(props.componentId, request)
    emit('success', response)
  } catch (error: unknown) {
    console.error('Failed to add stock:', error)
  } finally {
    submitting.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch locations if not already loaded
  if (allLocationOptions.value.length === 0) {
    await storageStore.fetchLocations()
  }
  locationOptions.value = allLocationOptions.value
})
</script>

<style scoped>
.add-stock-form {
  width: 100%;
}
</style>
