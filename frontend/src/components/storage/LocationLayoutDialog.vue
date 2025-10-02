<template>
  <q-dialog
    :model-value="modelValue"
    data-testid="location-layout-dialog"
    @update:model-value="onDialogClose"
  >
    <q-card style="min-width: 700px; max-width: 900px;">
      <!-- Dialog Header -->
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6" data-testid="dialog-title">
          Create Storage Locations
        </div>
        <q-space />
        <q-btn
          icon="close"
          flat
          round
          dense
          @click="closeDialog"
        />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <!-- Layout Type Selection -->
        <div class="q-mb-md">
          <LayoutTypeTabs
            v-model="selectedLayoutType"
            @update:model-value="onLayoutTypeChange"
          />
        </div>

        <q-separator class="q-my-md" />

        <!-- Configuration -->
        <div class="row q-col-gutter-md">
          <div class="col-md-6 col-xs-12">
            <div class="text-subtitle2 q-mb-md">Configuration</div>

            <!-- Range Configurator -->
            <RangeConfigurator
              :layout-type="selectedLayoutType"
              @update:config="onConfigChange"
            />

            <!-- Location Type -->
            <q-select
              v-model="locationType"
              data-testid="location-type-select"
              :options="locationTypeOptions"
              label="Location Type"
              outlined
              dense
              emit-value
              map-options
              class="q-mb-md"
            />

            <!-- Parent Location -->
            <q-select
              v-model="parentLocationId"
              data-testid="parent-location-select"
              :options="parentLocationOptions"
              label="Parent Location (optional)"
              outlined
              dense
              clearable
              emit-value
              map-options
              class="q-mb-md"
            />

            <!-- Single Part Only -->
            <q-checkbox
              v-model="singlePartOnly"
              data-testid="single-part-only-checkbox"
              label="Single part only"
              dense
            />
          </div>

          <div class="col-md-6 col-xs-12">
            <div class="text-subtitle2 q-mb-md">Preview</div>

            <!-- Location Preview -->
            <LocationPreview
              :loading="previewLoading"
              :preview-data="previewData"
            />
          </div>
        </div>
      </q-card-section>

      <!-- Validation Errors (if any) -->
      <q-card-section v-if="previewData && previewData.errors.length > 0" class="q-pt-none">
        <div data-testid="validation-errors" class="text-negative">
          <ul class="q-pl-md q-my-none">
            <li v-for="(error, index) in previewData.errors" :key="index">
              {{ error }}
            </li>
          </ul>
        </div>
      </q-card-section>

      <!-- Validation Warnings (if any) -->
      <q-card-section v-if="previewData && previewData.warnings.length > 0" class="q-pt-none">
        <div data-testid="validation-warnings" class="text-warning">
          <ul class="q-pl-md q-my-none">
            <li v-for="(warning, index) in previewData.warnings" :key="index">
              {{ warning }}
            </li>
          </ul>
        </div>
      </q-card-section>

      <q-separator />

      <!-- Actions -->
      <q-card-actions align="right">
        <q-btn
          data-testid="cancel-button"
          flat
          label="Cancel"
          color="primary"
          @click="closeDialog"
        />
        <q-btn
          data-testid="create-button"
          unelevated
          label="Create"
          color="primary"
          :loading="createLoading"
          :disable="!previewData || !previewData.is_valid"
          @click="createLocations"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import LayoutTypeTabs from './LayoutTypeTabs.vue'
import RangeConfigurator from './RangeConfigurator.vue'
import LocationPreview from './LocationPreview.vue'
import { locationLayoutService, type PreviewResponse } from '../../services/locationLayoutService'

interface Props {
  modelValue: boolean
  parentLocationOptions?: Array<{ label: string; value: string }>
}

const props = withDefaults(defineProps<Props>(), {
  parentLocationOptions: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'created': [response: any]
}>()

const $q = useQuasar()

const selectedLayoutType = ref<'single' | 'row' | 'grid' | 'grid_3d'>('single')
const layoutConfig = ref({
  prefix: '',
  ranges: [] as any[],
  separators: [] as string[]
})
const locationType = ref('bin')
const parentLocationId = ref<string | null>(null)
const singlePartOnly = ref(false)

const previewData = ref<PreviewResponse | null>(null)
const previewLoading = ref(false)
const createLoading = ref(false)

const locationTypeOptions = [
  { label: 'Bin', value: 'bin' },
  { label: 'Drawer', value: 'drawer' },
  { label: 'Shelf', value: 'shelf' },
  { label: 'Box', value: 'box' },
  { label: 'Cabinet', value: 'cabinet' },
  { label: 'Room', value: 'room' }
]

let debounceTimer: NodeJS.Timeout | null = null

const onLayoutTypeChange = () => {
  // Clear preview when layout type changes
  previewData.value = null
}

const onConfigChange = (config: any) => {
  layoutConfig.value = config

  // Clear existing preview (will be refetched with debounce)
  previewData.value = null

  // Debounce preview API call (300ms)
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(() => {
    fetchPreview()
  }, 300)
}

const fetchPreview = async () => {
  // Don't fetch if no configuration
  if (!layoutConfig.value.prefix && layoutConfig.value.ranges.length === 0) {
    return
  }

  previewLoading.value = true

  try {
    const config = {
      layout_type: selectedLayoutType.value,
      prefix: layoutConfig.value.prefix,
      ranges: layoutConfig.value.ranges,
      separators: layoutConfig.value.separators,
      parent_id: parentLocationId.value,
      location_type: locationType.value,
      single_part_only: singlePartOnly.value
    }

    previewData.value = await locationLayoutService.generatePreview(config)
  } catch (error: any) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to generate preview',
      position: 'top-right'
    })
  } finally {
    previewLoading.value = false
  }
}

const createLocations = async () => {
  if (!previewData.value || !previewData.value.is_valid) {
    return
  }

  createLoading.value = true

  try {
    const config = {
      layout_type: selectedLayoutType.value,
      prefix: layoutConfig.value.prefix,
      ranges: layoutConfig.value.ranges,
      separators: layoutConfig.value.separators,
      parent_id: parentLocationId.value,
      location_type: locationType.value,
      single_part_only: singlePartOnly.value
    }

    const response = await locationLayoutService.bulkCreate(config)

    $q.notify({
      type: 'positive',
      message: `Successfully created ${response.created_count} location${response.created_count === 1 ? '' : 's'}`,
      position: 'top-right'
    })

    emit('created', response)
    closeDialog()
  } catch (error: any) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create locations',
      position: 'top-right'
    })
  } finally {
    createLoading.value = false
  }
}

const closeDialog = () => {
  emit('update:modelValue', false)
}

const onDialogClose = (value: boolean) => {
  if (!value) {
    // Reset form when dialog closes
    resetForm()
  }
  emit('update:modelValue', value)
}

const resetForm = () => {
  selectedLayoutType.value = 'single'
  layoutConfig.value = {
    prefix: '',
    ranges: [],
    separators: []
  }
  locationType.value = 'bin'
  parentLocationId.value = null
  singlePartOnly.value = false
  previewData.value = null
}

// Watch for dialog open to reset form
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    resetForm()
  }
})
</script>

<style scoped lang="scss">
// Add any custom styles here
</style>
