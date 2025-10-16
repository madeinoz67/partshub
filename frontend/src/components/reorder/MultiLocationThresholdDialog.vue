<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    @update:model-value="$emit('update:model-value', $event)"
  >
    <q-card style="min-width: 600px; max-width: 800px">
      <q-card-section>
        <div class="text-h6">Configure Reorder Alerts</div>
        <div v-if="component" class="text-caption text-grey q-mt-xs">
          {{ component.name }}
          <span v-if="component.local_part_id || component.manufacturer_part_number" class="q-ml-sm">
            ({{ component.local_part_id || component.manufacturer_part_number }})
          </span>
        </div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <!-- Info Banner -->
        <q-banner rounded class="bg-info text-white q-mb-md">
          <template #avatar>
            <q-icon name="info" />
          </template>
          Configure reorder thresholds for each storage location. When stock falls below the threshold, an alert will be created.
        </q-banner>

        <!-- No Locations Warning -->
        <div v-if="!locations || locations.length === 0" class="text-center q-pa-lg">
          <q-icon name="location_off" size="3rem" color="grey-4" />
          <div class="q-mt-md text-grey">
            No storage locations assigned to this component
          </div>
        </div>

        <!-- Locations List -->
        <div v-else class="q-gutter-md">
          <q-card
            v-for="location in locations"
            :key="location.location.id"
            flat
            bordered
            class="location-threshold-card"
          >
            <q-card-section>
              <!-- Location Header -->
              <div class="row items-center q-mb-md">
                <div class="col">
                  <div class="text-weight-medium">{{ location.location.name }}</div>
                  <div class="text-caption text-grey">
                    {{ location.location.location_hierarchy }}
                  </div>
                </div>
                <div class="col-auto">
                  <q-chip
                    :color="getStockStatusColor(location.quantity_on_hand, location.minimum_stock)"
                    text-color="white"
                    size="sm"
                  >
                    Stock: {{ location.quantity_on_hand }}
                  </q-chip>
                </div>
              </div>

              <!-- Threshold Configuration -->
              <div class="row q-col-gutter-md items-end">
                <div class="col-auto" style="width: 120px">
                  <q-toggle
                    v-model="thresholdForms[location.location.id].enabled"
                    label="Monitor"
                    color="primary"
                    dense
                  />
                </div>

                <div class="col">
                  <q-input
                    v-model.number="thresholdForms[location.location.id].threshold"
                    label="Reorder Threshold"
                    type="number"
                    outlined
                    dense
                    :min="0"
                    :disable="!thresholdForms[location.location.id].enabled"
                    :rules="[
                      val => val !== null && val !== undefined || 'Required',
                      val => val >= 0 || 'Must be zero or greater',
                    ]"
                  >
                    <template #prepend>
                      <q-icon name="notifications" />
                    </template>
                  </q-input>
                </div>

                <div class="col-auto">
                  <q-chip
                    v-if="thresholdForms[location.location.id].enabled"
                    :color="location.quantity_on_hand < thresholdForms[location.location.id].threshold ? 'negative' : 'positive'"
                    text-color="white"
                    size="sm"
                    :label="location.quantity_on_hand < thresholdForms[location.location.id].threshold ? 'Below' : 'OK'"
                  />
                </div>
              </div>

              <!-- Warning if stock below new threshold -->
              <div
                v-if="thresholdForms[location.location.id].enabled &&
                      location.quantity_on_hand < thresholdForms[location.location.id].threshold"
                class="q-mt-sm"
              >
                <q-banner dense rounded class="bg-warning text-white">
                  <template #avatar>
                    <q-icon name="warning" size="sm" />
                  </template>
                  <span class="text-caption">
                    Stock ({{ location.quantity_on_hand }}) is below threshold ({{ thresholdForms[location.location.id].threshold }}). Alert will be created.
                  </span>
                </q-banner>
              </div>
            </q-card-section>
          </q-card>
        </div>
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
          label="Save All Thresholds"
          :loading="loading"
          :disable="!locations || locations.length === 0"
          @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import { reorderAlertsApi } from '../../services/reorderAlertsService'
import type { Component } from '../../services/api'

interface StorageLocationWithStock {
  location: {
    id: string
    name: string
    location_hierarchy: string
  }
  quantity_on_hand: number
  minimum_stock: number
  quantity_ordered?: number
  unit_cost_at_location?: number
  location_notes?: string
}

interface Props {
  modelValue: boolean
  component: Component | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  component: null,
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'saved': []
}>()

const $q = useQuasar()
const loading = ref(false)

// Form state for each location
const thresholdForms = ref<Record<string, { threshold: number; enabled: boolean }>>({})

// Computed locations from component
const locations = ref<StorageLocationWithStock[]>([])

const getStockStatusColor = (quantity: number, minStock: number) => {
  if (quantity === 0) return 'negative'
  if (quantity <= minStock && minStock > 0) return 'warning'
  return 'positive'
}

const initializeForms = () => {
  if (!props.component || !props.component.storage_locations) {
    locations.value = []
    thresholdForms.value = {}
    return
  }

  locations.value = props.component.storage_locations as StorageLocationWithStock[]

  // Initialize form for each location
  const forms: Record<string, { threshold: number; enabled: boolean }> = {}
  locations.value.forEach(location => {
    forms[location.location.id] = {
      threshold: location.minimum_stock || 0,
      enabled: true, // Default to enabled
    }
  })
  thresholdForms.value = forms
}

const onSubmit = async () => {
  if (!props.component || !locations.value.length) return

  loading.value = true
  try {
    // Build updates array
    const updates = locations.value.map(location => ({
      component_id: props.component!.id,
      location_id: location.location.id,
      threshold: thresholdForms.value[location.location.id].threshold,
      enabled: thresholdForms.value[location.location.id].enabled,
    }))

    // Call bulk update API
    const result = await reorderAlertsApi.bulkUpdateThresholds(updates)

    $q.notify({
      type: 'positive',
      message: `Updated ${result.updated_count} threshold(s)`,
      caption: result.failed_count > 0 ? `${result.failed_count} failed` : undefined,
      position: 'top-right',
    })

    emit('saved')
    emit('update:model-value', false)
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update thresholds',
      caption: error instanceof Error ? error.message : 'Unknown error',
      position: 'top-right',
    })
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    initializeForms()
  }
})
</script>

<style scoped>
.location-threshold-card {
  transition: box-shadow 0.2s ease;
}

.location-threshold-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
