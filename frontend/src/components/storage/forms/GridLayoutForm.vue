<template>
  <div class="grid-layout-form q-pa-md">
    <!-- Prefix Input -->
    <div class="q-mb-md">
      <q-input
        v-model="localPrefix"
        label="Prefix"
        hint="Prefix for all generated location names (e.g., 'drawer-')"
        dense
        outlined
        :rules="[(val) => !!val || 'Prefix is required']"
        @update:model-value="emitConfig"
      />
    </div>

    <!-- Separator Input -->
    <div class="q-mb-md">
      <q-input
        v-model="localSeparator"
        label="Separator"
        hint="Character to separate row and column (e.g., '-')"
        dense
        outlined
        maxlength="1"
        :rules="[(val) => !!val || 'Separator is required']"
        @update:model-value="emitConfig"
      />
    </div>

    <!-- Row Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Row Range</div>
      <RangeInput v-model="localRowRange" @update:model-value="emitConfig" />
    </div>

    <!-- Column Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Column Range</div>
      <RangeInput v-model="localColumnRange" @update:model-value="emitConfig" />
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
const localSeparator = ref<string>(props.modelValue.separators?.[0] || '-')
const localRowRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[0] || null
)
const localColumnRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[1] || null
)

// Helper function to generate range values
const generateRangeValues = (range: RangeSpecification, limit: number = 3): string[] => {
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
  if (!localRowRange.value || !localColumnRange.value) {
    return 0
  }

  try {
    const rowCount = calculateRangeCount(localRowRange.value)
    const colCount = calculateRangeCount(localColumnRange.value)
    return rowCount * colCount
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
  if (!localPrefix.value || !localRowRange.value || !localColumnRange.value) {
    return []
  }

  try {
    const rows = generateRangeValues(localRowRange.value, 2)
    const cols = generateRangeValues(localColumnRange.value, 2)
    const examples: string[] = []

    for (const row of rows) {
      for (const col of cols) {
        if (examples.length < 4) {
          examples.push(`${localPrefix.value}${row}${localSeparator.value}${col}`)
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
  if (!localPrefix.value || !localRowRange.value || !localColumnRange.value || !localSeparator.value) {
    return
  }

  const config: Partial<LayoutConfiguration> = {
    layout_type: 'grid',
    prefix: localPrefix.value,
    ranges: [localRowRange.value, localColumnRange.value],
    separators: [localSeparator.value]
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
      if (newValue.separators && newValue.separators.length > 0) {
        localSeparator.value = newValue.separators[0]
      }
      if (newValue.ranges && newValue.ranges.length >= 2) {
        localRowRange.value = newValue.ranges[0]
        localColumnRange.value = newValue.ranges[1]
      }
    }
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.grid-layout-form {
  min-height: 400px;
}
</style>
