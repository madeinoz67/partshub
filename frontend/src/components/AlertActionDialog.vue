<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    @update:model-value="$emit('update:model-value', $event)"
  >
    <q-card style="min-width: 500px">
      <q-card-section>
        <div class="text-h6">
          {{ action === 'dismiss' ? 'Dismiss Alert' : 'Mark as Ordered' }}
        </div>
        <div v-if="alert" class="text-caption text-grey q-mt-xs">
          {{ alert.component_name }} at {{ alert.location_name }}
        </div>
      </q-card-section>

      <q-card-section v-if="alert" class="q-pt-none">
        <!-- Alert Details -->
        <div class="q-mb-md q-pa-md bg-grey-1 rounded-borders">
          <div class="row q-col-gutter-md">
            <div class="col-6">
              <div class="text-caption text-grey">Current Stock</div>
              <div class="text-body1 text-weight-medium">
                {{ alert.current_quantity }}
              </div>
            </div>
            <div class="col-6">
              <div class="text-caption text-grey">Reorder Threshold</div>
              <div class="text-body1 text-weight-medium">
                {{ alert.reorder_threshold }}
              </div>
            </div>
            <div class="col-6">
              <div class="text-caption text-grey">Shortage</div>
              <div class="text-body1 text-weight-medium text-negative">
                {{ alert.shortage_amount }} units
              </div>
            </div>
            <div class="col-6">
              <div class="text-caption text-grey">Severity</div>
              <div>
                <q-badge
                  :color="getSeverityColor(alert.severity)"
                  :label="alert.severity.toUpperCase()"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Action-specific information -->
        <div v-if="action === 'dismiss'" class="q-mb-md">
          <q-banner rounded class="bg-info text-white">
            <template #avatar>
              <q-icon name="info" />
            </template>
            Dismissing this alert will mark it as acknowledged but not resolved.
            The alert may reappear if conditions remain unchanged.
          </q-banner>
        </div>

        <div v-if="action === 'ordered'" class="q-mb-md">
          <q-banner rounded class="bg-positive text-white">
            <template #avatar>
              <q-icon name="shopping_cart" />
            </template>
            Mark this alert as ordered when you have placed a replenishment order.
            This helps track pending deliveries.
          </q-banner>
        </div>

        <!-- Notes input -->
        <q-form ref="formRef" @submit="onSubmit">
          <q-input
            v-model="notes"
            label="Notes"
            type="textarea"
            outlined
            rows="3"
            :hint="action === 'ordered' ? 'Add order details, supplier, expected delivery, etc.' : 'Add reason for dismissal (optional)'"
            counter
            maxlength="500"
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
          :color="action === 'dismiss' ? 'grey' : 'positive'"
          :label="action === 'dismiss' ? 'Dismiss Alert' : 'Mark as Ordered'"
          :loading="loading"
          @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuasar, QForm } from 'quasar'
import { reorderAlertsApi } from '../services/reorderAlertsService'
import type { ReorderAlert } from '../services/reorderAlertsService'

interface Props {
  modelValue: boolean
  alert: ReorderAlert | null
  action: 'dismiss' | 'ordered'
}

const props = withDefaults(defineProps<Props>(), {
  alert: null,
  action: 'dismiss',
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'action-completed': []
}>()

const $q = useQuasar()
const formRef = ref<QForm>()
const loading = ref(false)
const notes = ref('')

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'negative'
    case 'high':
      return 'warning'
    case 'medium':
      return 'orange-5'
    case 'low':
      return 'info'
    default:
      return 'grey'
  }
}

const resetForm = () => {
  notes.value = ''
}

const onSubmit = async () => {
  if (!props.alert) return

  loading.value = true
  try {
    if (props.action === 'dismiss') {
      await reorderAlertsApi.dismissAlert(
        props.alert.id,
        notes.value || undefined
      )
    } else {
      await reorderAlertsApi.markOrdered(
        props.alert.id,
        notes.value || undefined
      )
    }

    emit('action-completed')
    resetForm()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: `Failed to ${props.action === 'dismiss' ? 'dismiss' : 'mark as ordered'} alert`,
      caption: error instanceof Error ? error.message : 'Unknown error',
      position: 'top-right',
    })
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    resetForm()
  }
})
</script>
