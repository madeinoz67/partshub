<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    @update:model-value="$emit('update:model-value', $event)"
  >
    <q-card style="min-width: 400px">
      <q-card-section>
        <div class="text-h6">Update Stock</div>
        <div v-if="component" class="text-caption text-grey q-mt-xs">
          {{ component.name }}
        </div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <q-form ref="formRef" class="q-gutter-md" @submit="onSubmit">
          <!-- Current Stock Display -->
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-caption text-grey">Current Stock</div>
              <div class="text-h6">{{ component?.quantity_on_hand || 0 }}</div>
            </div>
            <div class="col">
              <div class="text-caption text-grey">Minimum Stock</div>
              <div class="text-body2">{{ component?.minimum_stock || 0 }}</div>
            </div>
          </div>

          <q-separator />

          <!-- Transaction Type -->
          <q-select
            v-model="form.transaction_type"
            :options="transactionTypeOptions"
            label="Transaction Type *"
            outlined
            emit-value
            map-options
            :rules="[val => !!val || 'Transaction type is required']"
          />

          <!-- Quantity Change -->
          <q-input
            v-model.number="form.quantity_change"
            label="Quantity Change *"
            type="number"
            outlined
            :rules="[
              val => val !== null && val !== undefined || 'Quantity is required',
              val => Math.abs(val) > 0 || 'Quantity must be greater than 0',
              val => form.transaction_type !== 'remove' || val <= (component?.quantity_on_hand || 0) || 'Cannot remove more than available stock'
            ]"
            :hint="getQuantityHint()"
          >
            <template #prepend>
              <q-icon
                :name="form.transaction_type === 'remove' ? 'remove' : 'add'"
                :color="form.transaction_type === 'remove' ? 'negative' : 'positive'"
              />
            </template>
          </q-input>

          <!-- New Quantity Preview -->
          <div v-if="form.quantity_change && component" class="q-pa-md bg-grey-1 rounded-borders">
            <div class="text-caption text-grey q-mb-xs">New Stock Level</div>
            <div class="row items-center">
              <div class="text-h6" :class="getNewQuantityColor()">
                {{ calculateNewQuantity() }}
              </div>
              <div class="q-ml-sm">
                <q-chip
                  :color="getStockStatusColor(calculateNewQuantity())"
                  text-color="white"
                  size="sm"
                  :label="getStockStatusText(calculateNewQuantity())"
                />
              </div>
            </div>
          </div>

          <!-- Reason -->
          <q-input
            v-model="form.reason"
            label="Reason *"
            outlined
            type="textarea"
            rows="2"
            :rules="[val => !!val || 'Reason is required']"
            hint="Brief description of why stock is being updated"
          />

          <!-- Reference ID (optional) -->
          <q-input
            v-model="form.reference_id"
            label="Reference ID"
            outlined
            hint="Optional reference (order ID, project ID, etc.)"
          />
        </q-form>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          flat
          label="Cancel"
          :disable="loading"
          @click="$emit('update:model-value', false)"
        />
        <q-btn
          color="primary"
          label="Update Stock"
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
import { useComponentsStore } from '../stores/components'
import type { Component } from '../services/api'
import { QForm } from 'quasar'

interface Props {
  modelValue: boolean
  component?: Component | null
}

const props = withDefaults(defineProps<Props>(), {
  component: null
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'updated': []
}>()

const formRef = ref<QForm>()
const componentsStore = useComponentsStore()
const { loading } = storeToRefs(componentsStore)

const form = ref({
  transaction_type: 'add' as 'add' | 'remove' | 'move' | 'adjust',
  quantity_change: 0,
  reason: '',
  reference_id: ''
})

const transactionTypeOptions = [
  { label: 'Add Stock', value: 'add' },
  { label: 'Remove Stock', value: 'remove' },
  { label: 'Move Stock', value: 'move' },
  { label: 'Adjust Stock', value: 'adjust' }
]

const getQuantityHint = () => {
  switch (form.value.transaction_type) {
    case 'add':
      return 'Enter positive number to add to stock'
    case 'remove':
      return 'Enter positive number to remove from stock'
    case 'move':
      return 'Enter quantity being moved'
    case 'adjust':
      return 'Enter adjustment amount (positive or negative)'
    default:
      return ''
  }
}

const calculateNewQuantity = () => {
  if (!props.component) return 0

  const currentStock = props.component.quantity_on_hand
  const change = form.value.quantity_change || 0

  switch (form.value.transaction_type) {
    case 'add':
      return currentStock + Math.abs(change)
    case 'remove':
      return Math.max(0, currentStock - Math.abs(change))
    case 'adjust':
      return Math.max(0, currentStock + change)
    case 'move':
      return Math.max(0, currentStock - Math.abs(change))
    default:
      return currentStock
  }
}

const getNewQuantityColor = () => {
  if (!props.component) return ''

  const newQuantity = calculateNewQuantity()
  const currentStock = props.component.quantity_on_hand

  if (newQuantity > currentStock) return 'text-positive'
  if (newQuantity < currentStock) return 'text-negative'
  return ''
}

const getStockStatusColor = (quantity: number) => {
  if (!props.component) return 'grey'

  if (quantity === 0) return 'negative'
  if (quantity <= props.component.minimum_stock && props.component.minimum_stock > 0) return 'warning'
  return 'positive'
}

const getStockStatusText = (quantity: number) => {
  if (!props.component) return 'Unknown'

  if (quantity === 0) return 'Out of Stock'
  if (quantity <= props.component.minimum_stock && props.component.minimum_stock > 0) return 'Low Stock'
  return 'Available'
}

const resetForm = () => {
  form.value = {
    transaction_type: 'add',
    quantity_change: 0,
    reason: '',
    reference_id: ''
  }
}

const onSubmit = async () => {
  if (!formRef.value || !props.component) return

  const valid = await formRef.value.validate()
  if (!valid) return

  try {
    let quantityChange = form.value.quantity_change

    // Ensure proper sign based on transaction type
    switch (form.value.transaction_type) {
      case 'add':
        quantityChange = Math.abs(quantityChange)
        break
      case 'remove':
      case 'move':
        quantityChange = -Math.abs(quantityChange)
        break
      case 'adjust':
        // Keep as entered (can be positive or negative)
        break
    }

    await componentsStore.updateStock(props.component.id, {
      transaction_type: form.value.transaction_type,
      quantity_change: quantityChange,
      reason: form.value.reason,
      reference_id: form.value.reference_id || undefined
    })

    emit('updated')
  } catch (error) {
    console.error('Failed to update stock:', error)
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    resetForm()
  }
})
</script>