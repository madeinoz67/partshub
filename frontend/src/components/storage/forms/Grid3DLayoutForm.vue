<template>
  <div class="grid3d-layout-form q-pa-md">
    <!-- Prefix Input -->
    <div class="q-mb-md">
      <q-input
        v-model="localPrefix"
        label="Prefix"
        hint="Prefix for all generated location names (e.g., 'warehouse-')"
        dense
        outlined
        :rules="[(val) => !!val || 'Prefix is required']"
        @update:model-value="emitConfig"
      />
    </div>

    <!-- Separators -->
    <div class="row q-col-gutter-sm q-mb-md">
      <div class="col-6">
        <q-input
          v-model="localSeparator1"
          label="Separator 1 (Aisle-Shelf)"
          hint="e.g., '-'"
          dense
          outlined
          maxlength="1"
          :rules="[(val) => !!val || 'Separator 1 is required']"
          @update:model-value="emitConfig"
        />
      </div>
      <div class="col-6">
        <q-input
          v-model="localSeparator2"
          label="Separator 2 (Shelf-Bin)"
          hint="e.g., '.'"
          dense
          outlined
          maxlength="1"
          :rules="[(val) => !!val || 'Separator 2 is required']"
          @update:model-value="emitConfig"
        />
      </div>
    </div>

    <!-- Aisle Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Aisle Range (1st Dimension)</div>
      <RangeInput v-model="localAisleRange" @update:model-value="emitConfig" />
    </div>

    <!-- Shelf Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Shelf Range (2nd Dimension)</div>
      <RangeInput v-model="localShelfRange" @update:model-value="emitConfig" />
    </div>

    <!-- Bin Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Bin Range (3rd Dimension)</div>
      <RangeInput v-model="localBinRange" @update:model-value="emitConfig" />
    </div>

    <!-- Example Preview -->
    <div v-if="exampleNames.length > 0" class="q-mt-md">
      <q-banner dense class="bg-blue-1">
        <template #avatar>
          <q-icon name="info" color="blue" />
        </template>
        <div class="text-caption">
          <strong>Example names:</strong> {{ exampleNames.join(', ') }}
          <div v-if="totalCount > 3" class="q-mt-xs">
            <strong>Total locations:</strong> {{ totalCount }}
          </div>
        </div>
      </q-banner>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import RangeInput from './RangeInput.vue'
import type { LayoutConfiguration, RangeSpecification } from '../../../types/locationLayout'

// Props
interface Props {
  modelValue?: Partial<LayoutConfiguration>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({})
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: Partial<LayoutConfiguration>]
}>()

// Local state
const localPrefix = ref<string>(props.modelValue.prefix || '')
const localSeparator1 = ref<string>(props.modelValue.separators?.[0] || '-')
const localSeparator2 = ref<string>(props.modelValue.separators?.[1] || '.')
const localAisleRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[0] || null
)
const localShelfRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[1] || null
)
const localBinRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[2] || null
)

// Helper function to generate range values
const generateRangeValues = (range: RangeSpecification, limit: number = 2): string[] => {
  const values: string[] = []
  const { range_type, start, end, capitalize, zero_pad } = range

  if (range_type === 'letters') {
    const startChar = (start as string).toLowerCase()
    const endChar = (end as string).toLowerCase()
    for (let i = 0; i < limit && startChar.charCodeAt(0) + i <= endChar.charCodeAt(0); i++) {
      const char = String.fromCharCode(startChar.charCodeAt(0) + i)
      values.push(capitalize ? char.toUpperCase() : char)
    }
  } else {
    const startNum = start as number
    const endNum = end as number
    for (let i = 0; i < limit && startNum + i <= endNum; i++) {
      const num = startNum + i
      const displayNum = zero_pad
        ? num.toString().padStart(endNum.toString().length, '0')
        : num.toString()
      values.push(displayNum)
    }
  }

  return values
}

// Calculate total count
const totalCount = computed(() => {
  if (!localAisleRange.value || !localShelfRange.value || !localBinRange.value) {
    return 0
  }

  try {
    const aisleCount = calculateRangeCount(localAisleRange.value)
    const shelfCount = calculateRangeCount(localShelfRange.value)
    const binCount = calculateRangeCount(localBinRange.value)
    return aisleCount * shelfCount * binCount
  } catch (err) {
    return 0
  }
})

const calculateRangeCount = (range: RangeSpecification): number => {
  if (range.range_type === 'letters') {
    const startChar = (range.start as string).toLowerCase()
    const endChar = (range.end as string).toLowerCase()
    return endChar.charCodeAt(0) - startChar.charCodeAt(0) + 1
  } else {
    return (range.end as number) - (range.start as number) + 1
  }
}

// Computed example names
const exampleNames = computed(() => {
  if (
    !localPrefix.value ||
    !localAisleRange.value ||
    !localShelfRange.value ||
    !localBinRange.value ||
    !localSeparator1.value ||
    !localSeparator2.value
  ) {
    return []
  }

  try {
    const aisles = generateRangeValues(localAisleRange.value, 2)
    const shelves = generateRangeValues(localShelfRange.value, 2)
    const bins = generateRangeValues(localBinRange.value, 2)
    const examples: string[] = []

    for (const aisle of aisles) {
      for (const shelf of shelves) {
        for (const bin of bins) {
          if (examples.length < 4) {
            examples.push(
              `${localPrefix.value}${aisle}${localSeparator1.value}${shelf}${localSeparator2.value}${bin}`
            )
          }
        }
      }
    }

    return examples
  } catch (err) {
    return []
  }
})

// Methods
const emitConfig = () => {
  if (
    !localPrefix.value ||
    !localAisleRange.value ||
    !localShelfRange.value ||
    !localBinRange.value ||
    !localSeparator1.value ||
    !localSeparator2.value
  ) {
    return
  }

  const config: Partial<LayoutConfiguration> = {
    layout_type: 'grid_3d',
    prefix: localPrefix.value,
    ranges: [localAisleRange.value, localShelfRange.value, localBinRange.value],
    separators: [localSeparator1.value, localSeparator2.value]
  }

  emit('update:modelValue', config)
}

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      if (newValue.prefix !== undefined) {
        localPrefix.value = newValue.prefix
      }
      if (newValue.separators && newValue.separators.length >= 2) {
        localSeparator1.value = newValue.separators[0]
        localSeparator2.value = newValue.separators[1]
      }
      if (newValue.ranges && newValue.ranges.length >= 3) {
        localAisleRange.value = newValue.ranges[0]
        localShelfRange.value = newValue.ranges[1]
        localBinRange.value = newValue.ranges[2]
      }
    }
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.grid3d-layout-form {
  min-height: 500px;
}
</style>
