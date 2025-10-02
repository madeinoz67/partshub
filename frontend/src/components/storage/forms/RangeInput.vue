<template>
  <div class="range-input">
    <!-- Range Type Selector -->
    <div class="row q-col-gutter-sm q-mb-sm">
      <div class="col-12">
        <div class="text-subtitle2 q-mb-xs">Range Type</div>
        <q-option-group
          v-model="localRangeType"
          :options="rangeTypeOptions"
          inline
          dense
          @update:model-value="onRangeTypeChange"
        />
      </div>
    </div>

    <!-- Start/End Inputs -->
    <div class="row q-col-gutter-sm q-mb-sm">
      <div class="col-6">
        <q-input
          v-model="localStart"
          :label="`Start ${localRangeType === 'letters' ? 'Letter' : 'Number'}`"
          dense
          outlined
          :rules="startRules"
          :hint="localRangeType === 'letters' ? 'Single letter (a-z)' : 'Number (0-999)'"
          @update:model-value="onValueChange"
        />
      </div>
      <div class="col-6">
        <q-input
          v-model="localEnd"
          :label="`End ${localRangeType === 'letters' ? 'Letter' : 'Number'}`"
          dense
          outlined
          :rules="endRules"
          :hint="localRangeType === 'letters' ? 'Single letter (a-z)' : 'Number (0-999)'"
          @update:model-value="onValueChange"
        />
      </div>
    </div>

    <!-- Options (capitalize for letters, zero-pad for numbers) -->
    <div class="row q-col-gutter-sm">
      <div v-if="localRangeType === 'letters'" class="col-12">
        <q-checkbox
          v-model="localCapitalize"
          label="Capitalize letters (A-Z)"
          dense
          @update:model-value="onValueChange"
        />
      </div>
      <div v-if="localRangeType === 'numbers'" class="col-12">
        <q-checkbox
          v-model="localZeroPad"
          label="Zero-pad numbers (01, 02, ...)"
          dense
          @update:model-value="onValueChange"
        />
      </div>
    </div>

    <!-- Validation Messages -->
    <div v-if="validationError" class="q-mt-sm">
      <q-banner dense class="bg-negative text-white">
        <template #avatar>
          <q-icon name="error" />
        </template>
        {{ validationError }}
      </q-banner>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { RangeSpecification } from '../../../types/locationLayout'

// Props
interface Props {
  modelValue?: RangeSpecification | null
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  label: 'Range'
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: RangeSpecification]
}>()

// Local state
const localRangeType = ref<'letters' | 'numbers'>(
  props.modelValue?.range_type || 'letters'
)
const localStart = ref<string>(
  props.modelValue?.start?.toString() || ''
)
const localEnd = ref<string>(
  props.modelValue?.end?.toString() || ''
)
const localCapitalize = ref<boolean>(props.modelValue?.capitalize || false)
const localZeroPad = ref<boolean>(props.modelValue?.zero_pad || false)
const validationError = ref<string | null>(null)

// Options
const rangeTypeOptions = [
  { label: 'Letters (a-z)', value: 'letters' },
  { label: 'Numbers (0-999)', value: 'numbers' }
]

// Validation rules
const startRules = computed(() => [
  (val: string) => {
    if (!val) return 'Start value is required'
    if (localRangeType.value === 'letters') {
      if (!/^[a-zA-Z]$/.test(val)) {
        return 'Must be a single letter (a-z)'
      }
    } else {
      const num = parseInt(val, 10)
      if (isNaN(num) || num < 0 || num > 999) {
        return 'Must be a number between 0 and 999'
      }
    }
    return true
  }
])

const endRules = computed(() => [
  (val: string) => {
    if (!val) return 'End value is required'
    if (localRangeType.value === 'letters') {
      if (!/^[a-zA-Z]$/.test(val)) {
        return 'Must be a single letter (a-z)'
      }
      // Check start <= end
      if (localStart.value && val < localStart.value.toLowerCase()) {
        return 'End must be >= start'
      }
    } else {
      const num = parseInt(val, 10)
      if (isNaN(num) || num < 0 || num > 999) {
        return 'Must be a number between 0 and 999'
      }
      // Check start <= end
      const startNum = parseInt(localStart.value, 10)
      if (!isNaN(startNum) && num < startNum) {
        return 'End must be >= start'
      }
    }
    return true
  }
])

// Handlers
const onRangeTypeChange = () => {
  // Reset values when switching range type
  localStart.value = ''
  localEnd.value = ''
  localCapitalize.value = false
  localZeroPad.value = false
  validationError.value = null
  onValueChange()
}

const onValueChange = () => {
  // Validate and emit
  validationError.value = null

  if (!localStart.value || !localEnd.value) {
    return
  }

  try {
    let start: string | number
    let end: string | number

    if (localRangeType.value === 'letters') {
      start = localStart.value.toLowerCase()
      end = localEnd.value.toLowerCase()

      if (!/^[a-z]$/.test(start) || !/^[a-z]$/.test(end)) {
        validationError.value = 'Start and end must be single letters (a-z)'
        return
      }

      if (start > end) {
        validationError.value = 'Start letter must be <= end letter'
        return
      }
    } else {
      start = parseInt(localStart.value, 10)
      end = parseInt(localEnd.value, 10)

      if (isNaN(start) || isNaN(end)) {
        validationError.value = 'Start and end must be valid numbers'
        return
      }

      if (start < 0 || start > 999 || end < 0 || end > 999) {
        validationError.value = 'Numbers must be between 0 and 999'
        return
      }

      if (start > end) {
        validationError.value = 'Start number must be <= end number'
        return
      }
    }

    // Emit valid range specification
    const rangeSpec: RangeSpecification = {
      range_type: localRangeType.value,
      start,
      end
    }

    if (localRangeType.value === 'letters' && localCapitalize.value) {
      rangeSpec.capitalize = true
    }

    if (localRangeType.value === 'numbers' && localZeroPad.value) {
      rangeSpec.zero_pad = true
    }

    emit('update:modelValue', rangeSpec)
  } catch (err) {
    console.error('Error validating range:', err)
    validationError.value = 'Invalid range specification'
  }
}

// Watch for external changes to modelValue
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      localRangeType.value = newValue.range_type
      localStart.value = newValue.start.toString()
      localEnd.value = newValue.end.toString()
      localCapitalize.value = newValue.capitalize || false
      localZeroPad.value = newValue.zero_pad || false
    }
  },
  { deep: true }
)
</script>

<style scoped>
.range-input {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fafafa;
}
</style>
