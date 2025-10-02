<template>
  <div class="range-configurator">
    <!-- Prefix Input (all layouts) -->
    <q-input
      v-model="config.prefix"
      data-testid="prefix-input"
      label="Prefix"
      outlined
      dense
      placeholder="e.g., box-"
      class="q-mb-md"
      @update:model-value="emitConfig"
    >
      <template #prepend>
        <q-icon name="label" />
      </template>
    </q-input>

    <!-- Range Inputs (row, grid, grid_3d) -->
    <div v-for="(range, index) in config.ranges" :key="index" class="q-mb-md">
      <div
        :data-testid="`range-${index}-label`"
        class="text-caption text-weight-medium q-mb-xs"
      >
        {{ getRangeLabel(index) }}
      </div>

      <div class="row q-gutter-sm">
        <!-- Range Type Selector -->
        <q-select
          v-model="range.range_type"
          :data-testid="`range-${index}-type`"
          :options="rangeTypeOptions"
          label="Type"
          outlined
          dense
          emit-value
          map-options
          class="col-3"
          @update:model-value="onRangeTypeChange(index)"
        />

        <!-- Start Input -->
        <q-input
          v-model="range.start"
          :data-testid="`range-${index}-start`"
          label="Start"
          outlined
          dense
          class="col"
          :type="range.range_type === 'numbers' ? 'number' : 'text'"
          :aria-describedby="rangeErrors[index] ? `range-${index}-error` : undefined"
          @update:model-value="emitConfig"
        />

        <!-- End Input -->
        <q-input
          v-model="range.end"
          :data-testid="`range-${index}-end`"
          label="End"
          outlined
          dense
          class="col"
          :type="range.range_type === 'numbers' ? 'number' : 'text'"
          :aria-describedby="rangeErrors[index] ? `range-${index}-error` : undefined"
          @update:model-value="emitConfig"
        />
      </div>

      <!-- Range Options -->
      <div class="q-mt-sm">
        <!-- Capitalize (letters only) -->
        <q-checkbox
          v-if="range.range_type === 'letters'"
          v-model="range.capitalize"
          :data-testid="`range-${index}-capitalize`"
          label="Capitalize"
          dense
          @update:model-value="emitConfig"
        />

        <!-- Zero Pad (numbers only) -->
        <q-checkbox
          v-if="range.range_type === 'numbers'"
          v-model="range.zero_pad"
          :data-testid="`range-${index}-zero-pad`"
          label="Zero pad"
          dense
          @update:model-value="emitConfig"
        />
      </div>

      <!-- Validation Hints -->
      <div
        v-if="range.range_type === 'letters'"
        :data-testid="`range-${index}-hint`"
        class="text-caption text-grey-6 q-mt-xs"
      >
        Enter a single letter (a-z or A-Z)
      </div>
      <div
        v-if="range.range_type === 'numbers'"
        :data-testid="`range-${index}-hint`"
        class="text-caption text-grey-6 q-mt-xs"
      >
        Enter a number between 0-999
      </div>

      <!-- Error Messages -->
      <div
        v-if="rangeErrors[index]"
        :id="`range-${index}-error`"
        :data-testid="`range-${index}-error`"
        class="text-caption text-negative q-mt-xs"
      >
        {{ rangeErrors[index] }}
      </div>

      <!-- Separator (between ranges) -->
      <q-input
        v-if="index < config.ranges.length - 1"
        v-model="config.separators[index]"
        :data-testid="`separator-${index}`"
        label="Separator"
        outlined
        dense
        placeholder="-"
        class="q-mt-md"
        style="max-width: 150px;"
        @update:model-value="emitConfig"
      >
        <template #prepend>
          <q-icon name="remove" />
        </template>
      </q-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface RangeSpec {
  range_type: 'letters' | 'numbers'
  start: string | number
  end: string | number
  capitalize?: boolean
  zero_pad?: boolean
}

interface LayoutConfig {
  prefix: string
  ranges: RangeSpec[]
  separators: string[]
}

interface Props {
  layoutType: 'single' | 'row' | 'grid' | 'grid_3d'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:config': [config: LayoutConfig]
}>()

const rangeTypeOptions = [
  { label: 'Letters', value: 'letters' },
  { label: 'Numbers', value: 'numbers' }
]

const config = ref<LayoutConfig>({
  prefix: '',
  ranges: [],
  separators: []
})

const rangeErrors = ref<string[]>([])

// Initialize ranges based on layout type
const initializeRanges = () => {
  const rangeCount = props.layoutType === 'single' ? 0 :
                     props.layoutType === 'row' ? 1 :
                     props.layoutType === 'grid' ? 2 : 3

  config.value.ranges = Array.from({ length: rangeCount }, () => ({
    range_type: 'letters' as const,
    start: '',
    end: '',
    capitalize: false
  }))

  config.value.separators = Array.from({ length: rangeCount - 1 }, () => '-')
  rangeErrors.value = Array.from({ length: rangeCount }, () => '')

  emitConfig()
}

// Get label for range based on index and layout type
const getRangeLabel = (index: number): string => {
  if (props.layoutType === 'row') return 'Range'
  if (props.layoutType === 'grid') {
    return index === 0 ? 'Rows' : 'Columns'
  }
  if (props.layoutType === 'grid_3d') {
    return index === 0 ? 'Rows' : index === 1 ? 'Columns' : 'Depth'
  }
  return 'Range'
}

// Handle range type change
const onRangeTypeChange = (index: number) => {
  const range = config.value.ranges[index]

  // Reset start/end and set appropriate defaults
  range.start = ''
  range.end = ''

  if (range.range_type === 'letters') {
    delete range.zero_pad
    range.capitalize = false
  } else {
    delete range.capitalize
    range.zero_pad = false
  }

  validateRange(index)
  emitConfig()
}

// Validate individual range
const validateRange = (index: number) => {
  const range = config.value.ranges[index]

  if (!range.start || !range.end) {
    rangeErrors.value[index] = ''
    return
  }

  if (range.range_type === 'letters') {
    const start = String(range.start).toLowerCase()
    const end = String(range.end).toLowerCase()

    if (start > end) {
      rangeErrors.value[index] = 'start must be less than or equal to end'
    } else {
      rangeErrors.value[index] = ''
    }
  } else {
    const start = Number(range.start)
    const end = Number(range.end)

    if (start > end) {
      rangeErrors.value[index] = 'start must be less than or equal to end'
    } else {
      rangeErrors.value[index] = ''
    }
  }
}

// Emit configuration
const emitConfig = () => {
  // Validate all ranges
  config.value.ranges.forEach((_, index) => validateRange(index))

  // Normalize range values
  const normalizedConfig = {
    prefix: config.value.prefix,
    ranges: config.value.ranges.map(range => {
      if (range.range_type === 'letters') {
        return {
          range_type: range.range_type,
          start: String(range.start),
          end: String(range.end),
          capitalize: range.capitalize || false
        }
      } else {
        return {
          range_type: range.range_type,
          start: range.start === '' ? 0 : Number(range.start),
          end: range.end === '' ? 0 : Number(range.end),
          zero_pad: range.zero_pad || false
        }
      }
    }),
    separators: config.value.separators
  }

  emit('update:config', normalizedConfig)
}

// Watch for layout type changes
watch(() => props.layoutType, () => {
  const oldPrefix = config.value.prefix
  initializeRanges()
  config.value.prefix = oldPrefix // Preserve prefix
}, { immediate: true })
</script>

<style scoped lang="scss">
.range-configurator {
  width: 100%;
}
</style>
