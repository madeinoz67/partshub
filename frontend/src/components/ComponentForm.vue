<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:model-value', $event)"
    persistent
    maximized
    transition-show="slide-up"
    transition-hide="slide-down"
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
        <q-form @submit="onSubmit" ref="formRef" class="q-gutter-md">
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
                v-model="form.part_number"
                label="Part Number"
                outlined
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
            <div class="col-md-6 col-xs-12">
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

            <div class="col-md-6 col-xs-12">
              <q-select
                v-model="form.storage_location_id"
                :options="locationOptions"
                label="Storage Location"
                outlined
                emit-value
                map-options
                clearable
                :loading="locationsLoading"
              />
            </div>
          </div>

          <!-- Stock Information -->
          <div class="text-h6 q-mt-lg q-mb-sm">Stock Information</div>
          <div class="row q-gutter-md">
            <div class="col-md-4 col-xs-12">
              <q-input
                v-model.number="form.quantity_on_hand"
                label="Current Stock *"
                type="number"
                outlined
                min="0"
                :rules="[val => val >= 0 || 'Quantity must be positive']"
              />
            </div>

            <div class="col-md-4 col-xs-12">
              <q-input
                v-model.number="form.minimum_stock"
                label="Minimum Stock"
                type="number"
                outlined
                min="0"
              />
            </div>

            <div class="col-md-4 col-xs-12">
              <q-input
                v-model.number="form.quantity_ordered"
                label="Quantity Ordered"
                type="number"
                outlined
                min="0"
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
              @click="addSpecification"
              class="q-ml-sm"
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
              @click="addCustomField"
              class="q-ml-sm"
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
          <TagSelector
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
          @click="$emit('update:model-value', false)"
          :disable="loading"
        />
        <q-btn
          color="primary"
          label="Save Component"
          @click="onSubmit"
          :loading="loading"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useComponentsStore } from '../stores/components'
import { useStorageStore } from '../stores/storage'
import type { Component } from '../services/api'
import TagSelector from './TagSelector.vue'
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

const formRef = ref<QForm>()
const componentsStore = useComponentsStore()
const storageStore = useStorageStore()

const { loading } = storeToRefs(componentsStore)
const { locations } = storeToRefs(storageStore)

const categoriesLoading = ref(false)
const locationsLoading = ref(false)

const form = ref({
  name: '',
  part_number: '',
  manufacturer: '',
  category_id: '',
  storage_location_id: '',
  component_type: '',
  value: '',
  package: '',
  quantity_on_hand: 0,
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

const locationOptions = computed(() =>
  storageStore.locationOptions
)

const calculatedTotalValue = computed(() => {
  if (form.value.quantity_on_hand && form.value.average_purchase_price) {
    return (form.value.quantity_on_hand * form.value.average_purchase_price).toFixed(2)
  }
  return '0.00'
})

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
    part_number: '',
    manufacturer: '',
    category_id: '',
    storage_location_id: '',
    component_type: '',
    value: '',
    package: '',
    quantity_on_hand: 0,
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
    part_number: component.part_number || '',
    manufacturer: component.manufacturer || '',
    category_id: component.category_id || '',
    storage_location_id: component.storage_location_id || '',
    component_type: component.component_type || '',
    value: component.value || '',
    package: component.package || '',
    quantity_on_hand: component.quantity_on_hand,
    quantity_ordered: component.quantity_ordered,
    minimum_stock: component.minimum_stock,
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
  if (!valid) return

  try {
    const specsObject = specifications.value.reduce((acc, spec) => {
      if (spec.key.trim() && spec.value.trim()) {
        acc[spec.key.trim()] = spec.value.trim()
      }
      return acc
    }, {} as Record<string, any>)

    const fieldsObject = customFields.value.reduce((acc, field) => {
      if (field.key.trim() && field.value.trim()) {
        acc[field.key.trim()] = field.value.trim()
      }
      return acc
    }, {} as Record<string, any>)

    const componentData = {
      ...form.value,
      specifications: Object.keys(specsObject).length > 0 ? specsObject : null,
      custom_fields: Object.keys(fieldsObject).length > 0 ? fieldsObject : null,
      total_purchase_value: form.value.quantity_on_hand * (form.value.average_purchase_price || 0)
    }

    let result: Component
    if (props.isEdit && props.component) {
      result = await componentsStore.updateComponent(props.component.id, componentData)
    } else {
      result = await componentsStore.createComponent(componentData)
    }

    emit('saved', result)
    emit('update:model-value', false)
  } catch (error) {
    console.error('Failed to save component:', error)
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