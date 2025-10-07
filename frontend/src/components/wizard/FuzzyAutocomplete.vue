<script setup lang="ts">
/**
 * FuzzyAutocomplete Component
 * Reusable autocomplete component with fuzzy search and "create new" option
 */

import { ref, watch } from 'vue'
import type { ManufacturerSuggestion, FootprintSuggestion } from '../../types/wizard'

interface Props {
  modelValue: ManufacturerSuggestion | FootprintSuggestion | null
  searchFunction: (query: string, limit?: number) => Promise<(ManufacturerSuggestion | FootprintSuggestion)[]>
  placeholder?: string
  label?: string
  disable?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: ManufacturerSuggestion | FootprintSuggestion | null): void
  (e: 'createNew', name: string): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Type to search...',
  label: '',
  disable: false,
})

const emit = defineEmits<Emits>()

// Local state
const selected = ref<ManufacturerSuggestion | FootprintSuggestion | null>(props.modelValue)
const options = ref<(ManufacturerSuggestion | FootprintSuggestion)[]>([])
const loading = ref(false)
const inputValue = ref('')
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

// Watch for external updates
watch(() => props.modelValue, (newValue) => {
  selected.value = newValue
})

// Watch for selection changes
watch(selected, (newValue) => {
  emit('update:modelValue', newValue)
})

/**
 * Filter handler with debounced search
 */
async function onFilter(val: string, update: (fn: () => void) => void) {
  inputValue.value = val

  // Clear any pending search
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }

  // Empty query - clear results
  if (!val || val.length < 2) {
    update(() => {
      options.value = []
    })
    return
  }

  // Debounce search by 300ms
  searchTimeout.value = setTimeout(async () => {
    loading.value = true

    try {
      const results = await props.searchFunction(val, 10)
      update(() => {
        options.value = results
      })
    } catch (err) {
      console.error('Search failed:', err)
      update(() => {
        options.value = []
      })
    } finally {
      loading.value = false
    }
  }, 300)
}

/**
 * Handle "Create New" action
 */
function handleCreateNew() {
  if (inputValue.value) {
    emit('createNew', inputValue.value)
  }
}
</script>

<template>
  <q-select
    v-model="selected"
    :options="options"
    :label="label"
    :placeholder="placeholder"
    :loading="loading"
    :disable="disable"
    use-input
    input-debounce="0"
    option-label="name"
    option-value="id"
    options-dense
    clearable
    @filter="onFilter"
  >
    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>{{ scope.opt.name }}</q-item-label>
          <q-item-label caption v-if="scope.opt.component_count !== undefined">
            Used in {{ scope.opt.component_count }} components
          </q-item-label>
        </q-item-section>
        <q-item-section side v-if="scope.opt.score !== undefined">
          <q-badge color="primary">
            {{ Math.round(scope.opt.score) }}%
          </q-badge>
        </q-item-section>
      </q-item>
    </template>

    <template v-slot:no-option>
      <q-item>
        <q-item-section class="text-grey">
          <template v-if="inputValue && inputValue.length >= 2">
            No results found
          </template>
          <template v-else>
            Type at least 2 characters to search
          </template>
        </q-item-section>
      </q-item>
      <q-item
        v-if="inputValue && inputValue.length >= 2"
        clickable
        @click="handleCreateNew"
        class="bg-grey-2"
      >
        <q-item-section avatar>
          <q-icon name="add" color="primary" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-primary">
            Create new "{{ inputValue }}"
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-slot:prepend>
      <q-icon name="search" />
    </template>
  </q-select>
</template>
