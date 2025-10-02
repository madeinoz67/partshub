<template>
  <div class="row-layout-form q-pa-md">
    <!-- Prefix Input -->
    <div class="q-mb-md">
      <q-input
        v-model="localPrefix"
        label="Prefix"
        hint="Prefix for all generated location names (e.g., 'box1-')"
        dense
        outlined
        :rules="[(val) => !!val || 'Prefix is required']"
        @update:model-value="emitConfig"
      />
    </div>

    <!-- Range Input -->
    <div class="q-mb-md">
      <div class="text-subtitle2 q-mb-sm">Range Configuration</div>
      <RangeInput v-model="localRange" @update:model-value="emitConfig" />
    </div>

    <!-- Example Preview -->
    <div v-if="exampleNames.length > 0" class="q-mt-md">
      <q-banner dense class="bg-blue-1">
        <template #avatar>
          <q-icon name="info" color="blue" />
        </template>
        <div class="text-caption">
          <strong>Example names:</strong> {{ exampleNames.join(', ') }}
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
const localRange = ref<RangeSpecification | null>(
  props.modelValue.ranges?.[0] || null
)

// Computed
const exampleNames = computed(() => {
  if (!localPrefix.value || !localRange.value) {
    return []
  }

  try {
    const { range_type, start, end, capitalize, zero_pad } = localRange.value
    const examples: string[] = []

    if (range_type === 'letters') {
      const startChar = (start as string).toLowerCase()
      const endChar = (end as string).toLowerCase()
      for (let i = 0; i < 3 && startChar.charCodeAt(0) + i <= endChar.charCodeAt(0); i++) {
        const char = String.fromCharCode(startChar.charCodeAt(0) + i)
        const displayChar = capitalize ? char.toUpperCase() : char
        examples.push(`${localPrefix.value}${displayChar}`)
      }
    } else {
      const startNum = start as number
      const endNum = end as number
      for (let i = 0; i < 3 && startNum + i <= endNum; i++) {
        const num = startNum + i
        const displayNum = zero_pad
          ? num.toString().padStart(endNum.toString().length, '0')
          : num.toString()
        examples.push(`${localPrefix.value}${displayNum}`)
      }
    }

    return examples
  } catch (err) {
    return []
  }
})

// Methods
const emitConfig = () => {
  if (!localPrefix.value || !localRange.value) {
    return
  }

  const config: Partial<LayoutConfiguration> = {
    layout_type: 'row',
    prefix: localPrefix.value,
    ranges: [localRange.value],
    separators: []
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
      if (newValue.ranges && newValue.ranges.length > 0) {
        localRange.value = newValue.ranges[0]
      }
    }
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.row-layout-form {
  min-height: 300px;
}
</style>
