<script setup lang="ts">
/**
 * PartTypeSelector Component
 * Step 1: Select the type of part to create
 */

import { ref, watch } from 'vue'
import { useWizardStore } from '../../stores/wizardStore'
import type { PartType } from '../../types/wizard'

const wizardStore = useWizardStore()

// Local state for the selected option
const selectedType = ref<PartType>(wizardStore.partType)

// Part type options with descriptions
const partTypeOptions = [
  {
    value: 'linked' as PartType,
    label: 'Linked Part',
    description: 'Component with manufacturer part number from a provider (e.g., LCSC, Digi-Key, Mouser)',
    icon: 'link',
    color: 'primary',
  },
  {
    value: 'local' as PartType,
    label: 'Local Part',
    description: 'Generic or no-name component without provider link',
    icon: 'inventory_2',
    color: 'secondary',
  },
]

// Watch for changes and update store
watch(selectedType, (newValue) => {
  if (newValue) {
    wizardStore.selectPartType(newValue)
  }
})

// Watch for store changes (e.g., reset)
watch(() => wizardStore.partType, (newValue) => {
  selectedType.value = newValue
})
</script>

<template>
  <div class="part-type-selector">
    <p class="text-body1 q-mb-md">
      Choose the type of component you want to create:
    </p>

    <div class="row q-col-gutter-md">
      <div
        v-for="option in partTypeOptions"
        :key="String(option.value)"
        class="col-12 col-md-4"
      >
        <q-card
          flat
          bordered
          clickable
          :class="{
            'bg-grey-2': selectedType === option.value,
            'card-hover': true,
          }"
          @click="selectedType = option.value"
        >
          <q-card-section class="text-center">
            <q-icon
              :name="option.icon"
              :color="selectedType === option.value ? option.color : 'grey-6'"
              size="64px"
            />
          </q-card-section>

          <q-card-section>
            <div class="text-h6 text-center q-mb-sm">
              {{ option.label }}
            </div>
            <div class="text-body2 text-grey-7 text-center">
              {{ option.description }}
            </div>
          </q-card-section>

          <q-card-section class="text-center">
            <q-radio
              v-model="selectedType"
              :val="option.value"
              :label="'Select ' + option.label"
              :color="option.color"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-banner
      v-if="selectedType === 'linked'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      Linked parts automatically fetch specifications, datasheets, and other resources from the provider.
    </q-banner>

    <q-banner
      v-if="selectedType === 'local'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      Local parts are perfect for generic components like resistors, capacitors, or custom PCBs.
    </q-banner>
  </div>
</template>

<style scoped>
.card-hover {
  transition: all 0.3s ease;
}

.card-hover:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
</style>
