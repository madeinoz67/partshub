<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    @update:model-value="$emit('update:model-value', $event)"
  >
    <q-card style="min-width: 500px">
      <q-card-section>
        <div class="text-h6">Update Reorder Threshold</div>
        <div v-if="componentName" class="text-caption text-grey q-mt-xs">
          {{ componentName }}
        </div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <!-- Current Stock Info -->
        <div class="q-mb-md q-pa-md bg-grey-1 rounded-borders">
          <div class="row q-col-gutter-md">
            <div class="col-6">
              <div class="text-caption text-grey">Current Stock</div>
              <div class="text-h6 text-weight-bold">
                {{ currentQuantity }}
              </div>
            </div>
            <div class="col-6">
              <div class="text-caption text-grey">Current Threshold</div>
              <div class="text-h6 text-weight-bold">
                {{ currentThreshold }}
              </div>
            </div>
          </div>
        </div>

        <q-form ref="formRef" class="q-gutter-md" @submit="onSubmit">
          <!-- Enabled Toggle -->
          <q-toggle
            v-model="form.enabled"
            label="Enable reorder monitoring"
            color="primary"
          />

          <!-- Threshold Input -->
          <q-input
            v-model.number="form.threshold"
            label="Reorder Threshold *"
            type="number"
            outlined
            :min="0"
            :disable="!form.enabled"
            :rules="[
              val => val !== null && val !== undefined || 'Threshold is required',
              val => val >= 0 || 'Threshold must be zero or greater',
            ]"
            hint="Alert will trigger when stock falls below this level"
          >
            <template #prepend>
              <q-icon name="notifications" />
            </template>
          </q-input>

          <!-- Warning if enabling with current stock below threshold -->
          <div
            v-if="form.enabled && form.threshold > currentQuantity"
            class="q-mb-md"
          >
            <q-banner rounded class="bg-warning text-white">
              <template #avatar>
                <q-icon name="warning" />
              </template>
              Current stock ({{ currentQuantity }}) is below the new threshold
              ({{ form.threshold }}). An alert will be created immediately.
            </q-banner>
          </div>

          <!-- Info about disabling -->
          <div v-if="!form.enabled" class="q-mb-md">
            <q-banner rounded class="bg-info text-white">
              <template #avatar>
                <q-icon name="info" />
              </template>
              Disabling monitoring will prevent new alerts from being created
              for this component at this location. Existing active alerts will
              be automatically resolved.
            </q-banner>
          </div>

          <!-- Threshold Preview -->
          <div v-if="form.enabled" class="q-pa-md bg-grey-1 rounded-borders">
            <div class="text-caption text-grey q-mb-xs">Status Preview</div>
            <div class="row items-center">
              <div class="col">
                <div class="text-body2">
                  <span class="text-weight-medium">Stock Level:</span>
                  <span
                    :class="currentQuantity < form.threshold ? 'text-negative' : 'text-positive'"
                    class="q-ml-sm"
                  >
                    {{ currentQuantity }} / {{ form.threshold }}
                  </span>
                </div>
              </div>
              <div class="col-auto">
                <q-chip
                  :color="currentQuantity < form.threshold ? 'negative' : 'positive'"
                  text-color="white"
                  size="sm"
                  :label="currentQuantity < form.threshold ? 'Below Threshold' : 'Above Threshold'"
                />
              </div>
            </div>
          </div>
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
          label="Update Threshold"
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

interface Props {
  modelValue: boolean
  componentId: string
  locationId: string
  componentName: string
  currentQuantity: number
  currentThreshold: number
}

const props = withDefaults(defineProps<Props>(), {
  componentId: '',
  locationId: '',
  componentName: '',
  currentQuantity: 0,
  currentThreshold: 0,
})

const emit = defineEmits<{
  'update:model-value': [value: boolean]
  'updated': []
}>()

const $q = useQuasar()
const formRef = ref<QForm>()
const loading = ref(false)

const form = ref({
  threshold: 0,
  enabled: true,
})

const resetForm = () => {
  form.value = {
    threshold: props.currentThreshold,
    enabled: true,
  }
}

const onSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await reorderAlertsApi.updateThreshold(
      props.componentId,
      props.locationId,
      form.value.threshold,
      form.value.enabled
    )

    emit('updated')
    resetForm()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update threshold',
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
