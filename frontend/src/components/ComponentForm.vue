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
          <div class="text-h6">{{ isEdit ? 'Edit Component' : 'Add New Component' }}</div>
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
        <q-form ref="formRef" class="q-gutter-md" greedy @submit="onSubmit">
          <!-- Basic Information -->
          <div class="text-h6 q-mt-md q-mb-sm">Basic Information</div>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.name"
                label="Component Name *"
                outlined
                :rules="[val => !!val || 'Name is required']"
                autofocus
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.local_part_id"
                label="Local Part ID"
                outlined
                hint="User-friendly local identifier (recommended)"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.manufacturer_part_number"
                label="Manufacturer Part Number"
                outlined
                hint="Official manufacturer part number"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.part_number"
                label="Part Number (Legacy)"
                outlined
                hint="Legacy part number field"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.barcode_id"
                label="Barcode/QR ID"
                outlined
                hint="Auto-generated or scanned barcode ID"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.provider_sku"
                label="Provider SKU"
                outlined
                hint="Provider-specific SKU or catalog number"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.manufacturer"
                label="Manufacturer"
                outlined
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.component_type"
                label="Component Type"
                outlined
                hint="e.g., Resistor, Capacitor, IC, etc."
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.value"
                label="Value"
                outlined
                hint="e.g., 10kΩ, 100µF, etc."
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model="form.package"
                label="Package"
                outlined
                hint="e.g., 0805, TO-220, QFP-64, etc."
              />
            </div>
          </div>

          <!-- Organization -->
          <div class="text-h6 q-mt-lg q-mb-sm">Organization</div>
          <div class="row q-gutter-md">
            <div class="col-12">
              <q-select
                v-model="form.category_id"
                :options="categoryOptions"
                label="Category"
                outlined
                emit-value
                map-options
                clearable
                :loading="categoriesLoading"
              />
            </div>
          </div>
          <q-banner class="bg-info text-white q-mt-md" rounded>
            <template v-slot:avatar>
              <q-icon name="info" />
            </template>
            Storage locations are managed through stock movements (Add/Remove Stock).
          </q-banner>

          <!-- Stock Information -->
          <div class="text-h6 q-mt-lg q-mb-sm">Stock Information</div>
          <q-banner class="bg-info text-white q-mb-md" rounded>
            <template v-slot:avatar>
              <q-icon name="info" />
            </template>
            Stock quantities are managed per storage location. Use the stock management buttons to add/remove stock.
          </q-banner>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-input
                v-model.number="form.minimum_stock"
                label="Minimum Stock (Global)"
                type="number"
                outlined
                min="0"
                hint="Overall minimum stock threshold for alerts"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model.number="form.quantity_ordered"
                label="Quantity Ordered (Global)"
                type="number"
                outlined
                min="0"
                hint="Overall quantity on order"
              />
            </div>
          </div>

          <!-- Pricing -->
          <div class="text-h6 q-mt-lg q-mb-sm">Pricing</div>
          <div class="row q-gutter-md">
            <div class="col-md-6 col-xs-12">
              <q-input
                v-model.number="form.average_purchase_price"
                label="Average Purchase Price"
                type="number"
                step="0.01"
                min="0"
                outlined
                prefix="$"
              />
            </div>

            <div class="col-md-6 col-xs-12">
              <q-input
                v-model.number="form.total_purchase_value"
                label="Total Purchase Value"
                type="number"
                step="0.01"
                min="0"
                outlined
                prefix="$"
                readonly
                :model-value="calculatedTotalValue"
                hint="Calculated: Quantity × Average Price"
              />
            </div>
          </div>

          <!-- Specifications -->
          <div class="text-h6 q-mt-lg q-mb-sm">
            Specifications
            <q-btn
              icon="add"
              size="sm"
              flat
              round
              class="q-ml-sm"
              @click="addSpecification"
            />
          </div>
          <div v-if="specifications.length === 0" class="text-grey q-mb-md">
            No specifications defined. Click + to add specifications.
          </div>
          <div v-for="(spec, index) in specifications" :key="index" class="row q-gutter-md q-mb-sm">
            <div class="col-5">
              <q-input
                v-model="spec.key"
                label="Parameter"
                outlined
                dense
                placeholder="e.g., Voltage, Current, etc."
              />
            </div>
            <div class="col-5">
              <q-input
                v-model="spec.value"
                label="Value"
                outlined
                dense
                placeholder="e.g., 5V, 100mA, etc."
              />
            </div>
            <div class="col-2">
              <q-btn
                icon="delete"
                flat
                dense
                color="negative"
                @click="removeSpecification(index)"
              />
            </div>
          </div>

          <!-- Custom Fields -->
          <div class="text-h6 q-mt-lg q-mb-sm">
            Custom Fields
            <q-btn
              icon="add"
              size="sm"
              flat
              round
              class="q-ml-sm"
              @click="addCustomField"
            />
          </div>
          <div v-if="customFields.length === 0" class="text-grey q-mb-md">
            No custom fields defined. Click + to add custom fields.
          </div>
          <div v-for="(field, index) in customFields" :key="index" class="row q-gutter-md q-mb-sm">
            <div class="col-5">
              <q-input
                v-model="field.key"
                label="Field Name"
                outlined
                dense
                placeholder="e.g., Supplier, Datasheet URL, etc."
              />
            </div>
            <div class="col-5">
              <q-input
                v-model="field.value"
                label="Value"
                outlined
                dense
                placeholder="Field value"
              />
            </div>
            <div class="col-2">
              <q-btn
                icon="delete"
                flat
                dense
                color="negative"
                @click="removeCustomField(index)"
              />
            </div>
          </div>

          <!-- Notes -->
          <div class="text-h6 q-mt-lg q-mb-sm">Notes</div>
          <q-input
            v-model="form.notes"
            label="Additional notes or comments"
            outlined
            type="textarea"
            rows="3"
          />

          <!-- Tags -->
          <div class="text-h6 q-mt-lg q-mb-sm">Tags</div>
          <FuzzyTagSelector
            v-model="form.tags"
            class="q-mb-md"
          />
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
          label="Save Component"
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
import { useQuasar } from 'quasar'
import { useComponentsStore } from '../stores/components'
import { useStorageStore } from '../stores/storage'
import type { Component } from '../services/api'
import FuzzyTagSelector from './FuzzyTagSelector.vue'
import { QForm } from 'quasar'

interface Props {
  modelValue: boolean
  component?: Component | null
  isEdit?: boolean
}

interface KeyValuePair {
  key: string
  value: string
}

const props = withDefaults(defineProps<Props>(), {
  component: null,
  isEdit: false
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'saved': [component: Component]
}>()

const $q = useQuasar()
const formRef = ref<QForm>()
const componentsStore = useComponentsStore()
const storageStore = useStorageStore()

const { loading } = storeToRefs(componentsStore)
const { locations } = storeToRefs(storageStore)
const categoriesLoading = ref(false)

const form = ref({
  name: '',
  local_part_id: '',
  barcode_id: '',
  manufacturer_part_number: '',
  provider_sku: '',
  part_number: '',
  manufacturer: '',
  category_id: '',
  component_type: '',
  value: '',
  package: '',
  quantity_ordered: 0,
  minimum_stock: 0,
  average_purchase_price: 0,
  total_purchase_value: 0,
  notes: '',
  tags: [] as string[]
})

const specifications = ref<KeyValuePair[]>([])
const customFields = ref<KeyValuePair[]>([])

const categoryOptions = computed(() => {
  const categoryMap = new Map<string, string>()
  componentsStore.components.forEach(c => {
    if (c.category?.id && c.category?.name) {
      categoryMap.set(c.category.id, c.category.name)
    }
  })
  return Array.from(categoryMap.entries()).map(([id, name]) => ({
    label: name,
    value: id
  }))
})

// Note: Total value is now calculated server-side based on storage locations

const addSpecification = () => {
  specifications.value.push({ key: '', value: '' })
}

const removeSpecification = (index: number) => {
  specifications.value.splice(index, 1)
}

const addCustomField = () => {
  customFields.value.push({ key: '', value: '' })
}

const removeCustomField = (index: number) => {
  customFields.value.splice(index, 1)
}

const resetForm = () => {
  form.value = {
    name: '',
    local_part_id: '',
    barcode_id: '',
    manufacturer_part_number: '',
    provider_sku: '',
    part_number: '',
    manufacturer: '',
    category_id: '',
    component_type: '',
    value: '',
    package: '',
    quantity_ordered: 0,
    minimum_stock: 0,
    average_purchase_price: 0,
    total_purchase_value: 0,
    notes: '',
    tags: []
  }
  specifications.value = []
  customFields.value = []
}

const populateForm = (component: Component) => {
  form.value = {
    name: component.name,
    local_part_id: component.local_part_id || '',
    barcode_id: component.barcode_id || '',
    manufacturer_part_number: component.manufacturer_part_number || '',
    provider_sku: component.provider_sku || '',
    part_number: component.part_number || '',
    manufacturer: component.manufacturer || '',
    category_id: component.category_id || '',
    component_type: component.component_type || '',
    value: component.value || '',
    package: component.package || '',
    quantity_ordered: component.quantity_ordered || 0,
    minimum_stock: component.minimum_stock || 0,
    average_purchase_price: component.average_purchase_price || 0,
    total_purchase_value: component.total_purchase_value || 0,
    notes: component.notes || '',
    tags: component.tags ? component.tags.map(tag => tag.id) : []
  }

  specifications.value = component.specifications
    ? Object.entries(component.specifications).map(([key, value]) => ({
        key,
        value: value?.toString() || ''
      }))
    : []

  customFields.value = component.custom_fields
    ? Object.entries(component.custom_fields).map(([key, value]) => ({
        key,
        value: value?.toString() || ''
      }))
    : []
}

const onSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate()
  if (!valid) {
    $q.notify({
      type: 'negative',
      message: 'Please fill in all required fields correctly',
      position: 'top'
    })
    return
  }

  try {
    const specsObject = specifications.value.reduce((acc, spec) => {
      if (spec.key.trim() && spec.value.trim()) {
        acc[spec.key.trim()] = spec.value.trim()
      }
      return acc
    }, {} as Record<string, string>)

    const fieldsObject = customFields.value.reduce((acc, field) => {
      if (field.key.trim() && field.value.trim()) {
        acc[field.key.trim()] = field.value.trim()
      }
      return acc
    }, {} as Record<string, string>)

    // Build component data, omitting empty/null optional fields
    const componentData: Record<string, unknown> = {
      name: form.value.name,
      // Note: quantity_on_hand and storage_location_id are managed via stock movements
      // Components are created without stock, users add stock via Add Stock button
    }

    // Include these stock fields for both create and update
    componentData.quantity_ordered = form.value.quantity_ordered
    componentData.minimum_stock = form.value.minimum_stock

    // Only include optional fields if they have values
    if (form.value.part_number) componentData.part_number = form.value.part_number
    if (form.value.local_part_id) componentData.local_part_id = form.value.local_part_id
    if (form.value.barcode_id) componentData.barcode_id = form.value.barcode_id
    if (form.value.manufacturer_part_number) componentData.manufacturer_part_number = form.value.manufacturer_part_number
    if (form.value.provider_sku) componentData.provider_sku = form.value.provider_sku
    if (form.value.manufacturer) componentData.manufacturer = form.value.manufacturer
    if (form.value.category_id) componentData.category_id = form.value.category_id
    if (form.value.component_type) componentData.component_type = form.value.component_type
    if (form.value.value) componentData.value = form.value.value
    if (form.value.package) componentData.package = form.value.package
    if (form.value.average_purchase_price) componentData.average_purchase_price = form.value.average_purchase_price
    if (form.value.notes) componentData.notes = form.value.notes
    if (form.value.tags.length > 0) componentData.tags = form.value.tags

    // Total value is calculated server-side based on storage locations
    // Don't send it from the client

    // Add specifications and custom fields if present
    if (Object.keys(specsObject).length > 0) componentData.specifications = specsObject
    if (Object.keys(fieldsObject).length > 0) componentData.custom_fields = fieldsObject

    let result: Component
    if (props.isEdit && props.component) {
      result = await componentsStore.updateComponent(props.component.id, componentData)
    } else {
      result = await componentsStore.createComponent(componentData)
    }

    $q.notify({
      type: 'positive',
      message: `Component ${props.isEdit ? 'updated' : 'created'} successfully`,
      position: 'top'
    })

    emit('saved', result)
    emit('update:model-value', false)
  } catch (error: unknown) {
    console.error('Failed to save component:', error)

    // Extract detailed error message from API response
    let errorMessage = 'Failed to save component. Please try again.'
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: unknown } } }
      if (axiosError.response?.data?.detail) {
        errorMessage = typeof axiosError.response.data.detail === 'string'
          ? axiosError.response.data.detail
          : JSON.stringify(axiosError.response.data.detail)
      }
    } else if (error instanceof Error) {
      errorMessage = error.message
    }

    $q.notify({
      type: 'negative',
      message: errorMessage,
      position: 'top',
      timeout: 5000
    })
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (props.isEdit && props.component) {
      populateForm(props.component)
    } else {
      resetForm()
    }

    if (locations.value.length === 0) {
      storageStore.fetchLocations()
    }
  }
})

watch(() => props.component, (newComponent) => {
  if (newComponent && props.isEdit) {
    populateForm(newComponent)
  }
})
</script>

<style scoped>
.full-height {
  height: 100vh;
}
</style>