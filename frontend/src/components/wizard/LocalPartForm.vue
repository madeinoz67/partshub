<script setup lang="ts">
/**
 * LocalPartForm Component
 * Step 3 (for local/meta parts): Enter part details manually
 */

import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useWizardStore } from '../../stores/wizardStore'
import { wizardService } from '../../services/wizardService'
import FuzzyAutocomplete from './FuzzyAutocomplete.vue'
import type { ManufacturerSuggestion, FootprintSuggestion } from '../../types/wizard'

const $q = useQuasar()
const wizardStore = useWizardStore()

// Local form state
const formData = ref({
  name: wizardStore.localPartData.name,
  description: wizardStore.localPartData.description,
  manufacturer: null as ManufacturerSuggestion | null,
  footprint: null as FootprintSuggestion | null,
})

// Validation rules (FR-022)
const nameRules = [
  (val: string) => !!val || 'Name is required',
  (val: string) => val.length <= 255 || 'Name must be 255 characters or less',
  (val: string) =>
    /^[a-zA-Z0-9\s\-._]+$/.test(val) ||
    'Name can only contain letters, numbers, spaces, hyphens, periods, and underscores',
]

const descriptionRules = [
  (val: string) => !val || val.length <= 500 || 'Description must be 500 characters or less',
]

// Character count
const nameCharCount = computed(() => formData.value.name.length)
const descriptionCharCount = computed(() => formData.value.description.length)

/**
 * Search for manufacturer suggestions
 */
async function searchManufacturers(query: string) {
  return await wizardService.searchManufacturers(query, 10)
}

/**
 * Search for footprint suggestions
 */
async function searchFootprints(query: string) {
  return await wizardService.searchFootprints(query, 10)
}

/**
 * Handle "Create New Manufacturer"
 */
function createNewManufacturer(name: string) {
  formData.value.manufacturer = {
    id: 0, // 0 indicates new manufacturer
    name,
  }

  $q.notify({
    type: 'info',
    message: `Will create new manufacturer: ${name}`,
    position: 'top',
  })

  updateStore()
}

/**
 * Handle "Create New Footprint"
 */
function createNewFootprint(name: string) {
  formData.value.footprint = {
    id: 0, // 0 indicates new footprint
    name,
  }

  $q.notify({
    type: 'info',
    message: `Will create new footprint: ${name}`,
    position: 'top',
  })

  updateStore()
}

/**
 * Update wizard store with form data
 */
function updateStore() {
  wizardStore.updateLocalPartData({
    name: formData.value.name,
    description: formData.value.description,
    manufacturer_id: formData.value.manufacturer?.id || null,
    manufacturer_name: formData.value.manufacturer?.name || '',
    footprint_id: formData.value.footprint?.id || null,
    footprint_name: formData.value.footprint?.name || '',
  })
}

// Watch form changes and update store
watch(
  formData,
  () => {
    updateStore()
  },
  { deep: true }
)

// Watch store changes (e.g., reset)
watch(
  () => wizardStore.localPartData,
  (newValue) => {
    formData.value.name = newValue.name
    formData.value.description = newValue.description

    // Restore manufacturer if available
    if (newValue.manufacturer_id || newValue.manufacturer_name) {
      formData.value.manufacturer = {
        id: newValue.manufacturer_id || 0,
        name: newValue.manufacturer_name,
      }
    } else {
      formData.value.manufacturer = null
    }

    // Restore footprint if available
    if (newValue.footprint_id || newValue.footprint_name) {
      formData.value.footprint = {
        id: newValue.footprint_id || 0,
        name: newValue.footprint_name,
      }
    } else {
      formData.value.footprint = null
    }
  }
)
</script>

<template>
  <div class="local-part-form">
    <p class="text-body1 q-mb-md">
      Enter details for your {{ wizardStore.partType === 'meta' ? 'meta-part' : 'local part' }}:
    </p>

    <q-form class="q-gutter-md">
      <!-- Name Field (Required) -->
      <q-input
        v-model="formData.name"
        outlined
        label="Part Name *"
        placeholder="e.g., 10K Resistor 0805"
        :rules="nameRules"
        lazy-rules
        counter
        maxlength="255"
        hint="Required. Max 255 characters. Letters, numbers, spaces, hyphens, periods, underscores only."
      >
        <template v-slot:prepend>
          <q-icon name="label" />
        </template>
        <template v-slot:append>
          <q-badge :color="nameCharCount > 255 ? 'negative' : 'grey'">
            {{ nameCharCount }}/255
          </q-badge>
        </template>
      </q-input>

      <!-- Description Field (Optional) -->
      <q-input
        v-model="formData.description"
        outlined
        label="Description"
        placeholder="Optional detailed description"
        type="textarea"
        rows="3"
        :rules="descriptionRules"
        lazy-rules
        counter
        maxlength="500"
        hint="Optional. Max 500 characters."
      >
        <template v-slot:prepend>
          <q-icon name="description" />
        </template>
        <template v-slot:append>
          <q-badge :color="descriptionCharCount > 500 ? 'negative' : 'grey'">
            {{ descriptionCharCount }}/500
          </q-badge>
        </template>
      </q-input>

      <!-- Manufacturer Field (Optional, Fuzzy Search) -->
      <FuzzyAutocomplete
        v-model="formData.manufacturer"
        :search-function="searchManufacturers"
        label="Manufacturer"
        placeholder="Start typing to search..."
        @create-new="createNewManufacturer"
      />

      <!-- Footprint Field (Optional, Fuzzy Search) -->
      <FuzzyAutocomplete
        v-model="formData.footprint"
        :search-function="searchFootprints"
        label="Footprint"
        placeholder="Start typing to search..."
        @create-new="createNewFootprint"
      />
    </q-form>

    <!-- Helpful Info Banners -->
    <q-banner
      v-if="wizardStore.partType === 'local'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      Local parts are perfect for generic components or custom items without a manufacturer part number.
    </q-banner>

    <q-banner
      v-if="wizardStore.partType === 'meta'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      Meta-parts represent generic component types. You can link specific parts to this meta-part later.
    </q-banner>

    <!-- Validation Summary -->
    <div v-if="formData.name" class="q-mt-md">
      <q-banner class="bg-positive text-white" rounded>
        <template v-slot:avatar>
          <q-icon name="check_circle" />
        </template>
        <div>
          <strong>Part Name:</strong> {{ formData.name }}
          <br v-if="formData.manufacturer" />
          <span v-if="formData.manufacturer">
            <strong>Manufacturer:</strong> {{ formData.manufacturer.name }}
            <q-badge v-if="formData.manufacturer.id === 0" color="orange" class="q-ml-sm">
              New
            </q-badge>
          </span>
          <br v-if="formData.footprint" />
          <span v-if="formData.footprint">
            <strong>Footprint:</strong> {{ formData.footprint.name }}
            <q-badge v-if="formData.footprint.id === 0" color="orange" class="q-ml-sm">
              New
            </q-badge>
          </span>
        </div>
      </q-banner>
    </div>
  </div>
</template>

<style scoped>
.local-part-form {
  max-width: 600px;
}
</style>
