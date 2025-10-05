<script setup lang="ts">
/**
 * ResourceSelector Component
 * Step 4: Select which resources to download/attach to the component
 */

import { ref, computed, watch } from 'vue'
import { useWizardStore } from '../../stores/wizardStore'
import type { ResourceSelection } from '../../types/wizard'

const wizardStore = useWizardStore()

// Local state for selected resources
const selectedResources = ref<ResourceSelection[]>([...wizardStore.selectedResources])

// Resource type labels and icons
const resourceConfig = {
  datasheet: { label: 'Datasheet', icon: 'description', color: 'primary' },
  image: { label: 'Images', icon: 'image', color: 'secondary' },
  footprint: { label: 'Footprints', icon: 'grid_on', color: 'accent' },
  symbol: { label: 'Symbols', icon: 'architecture', color: 'info' },
  '3d_model': { label: '3D Models', icon: 'view_in_ar', color: 'warning' },
}

// Computed
const hasResources = computed(() => selectedResources.value.length > 0)

const hasLinkedPart = computed(() => wizardStore.partType === 'linked' && wizardStore.selectedPart)

const selectedCount = computed(
  () => selectedResources.value.filter((r) => r.selected).length
)

/**
 * Toggle resource selection
 */
function toggleResource(resource: ResourceSelection) {
  // Don't allow deselecting required resources
  if (resource.required && resource.selected) {
    return
  }

  resource.selected = !resource.selected
  wizardStore.toggleResource(resource)
}

/**
 * Select all optional resources
 */
function selectAll() {
  selectedResources.value.forEach((resource) => {
    if (!resource.required) {
      resource.selected = true
      wizardStore.toggleResource(resource)
    }
  })
}

/**
 * Deselect all optional resources
 */
function deselectAll() {
  selectedResources.value.forEach((resource) => {
    if (!resource.required) {
      resource.selected = false
      wizardStore.toggleResource(resource)
    }
  })
}

/**
 * Get resource config for display
 */
function getResourceConfig(type: string) {
  return resourceConfig[type as keyof typeof resourceConfig] || {
    label: type,
    icon: 'attach_file',
    color: 'grey',
  }
}

// Watch store changes
watch(
  () => wizardStore.selectedResources,
  (newResources) => {
    selectedResources.value = [...newResources]
  },
  { deep: true }
)
</script>

<template>
  <div class="resource-selector">
    <p class="text-body1 q-mb-md">
      Select resources to download and attach to this component:
    </p>

    <!-- Resources List (for linked parts) -->
    <div v-if="hasLinkedPart && hasResources">
      <q-list bordered separator>
        <q-item
          v-for="resource in selectedResources"
          :key="resource.type"
          tag="label"
          clickable
          @click="toggleResource(resource)"
        >
          <q-item-section avatar>
            <q-checkbox
              :model-value="resource.selected"
              :disable="resource.required"
              :color="getResourceConfig(resource.type).color"
              @update:model-value="toggleResource(resource)"
            />
          </q-item-section>

          <q-item-section avatar>
            <q-icon
              :name="getResourceConfig(resource.type).icon"
              :color="getResourceConfig(resource.type).color"
            />
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ getResourceConfig(resource.type).label }}</q-item-label>
            <q-item-label caption v-if="resource.url">
              {{ resource.url }}
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-badge v-if="resource.required" color="primary" label="Required" />
            <q-badge
              v-else-if="resource.selected"
              color="positive"
              label="Selected"
            />
          </q-item-section>
        </q-item>
      </q-list>

      <!-- Quick Actions -->
      <div class="row q-mt-md q-gutter-sm">
        <q-btn
          flat
          dense
          label="Select All"
          icon="check_box"
          color="primary"
          @click="selectAll"
        />
        <q-btn
          flat
          dense
          label="Deselect All"
          icon="check_box_outline_blank"
          color="grey"
          @click="deselectAll"
        />
      </div>

      <!-- Info Banner -->
      <q-banner class="bg-info text-white q-mt-md" rounded>
        <template v-slot:avatar>
          <q-icon name="info" />
        </template>
        <div>
          Datasheets download immediately during component creation.
          <br />
          Other resources download in the background and may take a few minutes.
        </div>
      </q-banner>

      <!-- Selection Summary -->
      <div class="q-mt-md text-body2 text-grey-7">
        {{ selectedCount }} of {{ selectedResources.length }} resources selected
      </div>
    </div>

    <!-- No Resources (for local/meta parts) -->
    <div v-else-if="!hasLinkedPart" class="text-center q-py-xl">
      <q-icon name="attachment" size="64px" color="grey-5" />
      <p class="text-body1 text-grey-7 q-mt-md">
        No provider resources available for {{ wizardStore.partType }} parts
      </p>
      <p class="text-body2 text-grey-6">
        You can add datasheets and other attachments after creating the component.
      </p>

      <q-banner class="bg-info text-white q-mt-md" rounded>
        <template v-slot:avatar>
          <q-icon name="info" />
        </template>
        Resource management will be available on the component detail page.
      </q-banner>
    </div>

    <!-- No Resources Available (linked part but no resources) -->
    <div v-else-if="!hasResources" class="text-center q-py-xl">
      <q-icon name="attachment" size="64px" color="grey-5" />
      <p class="text-body1 text-grey-7 q-mt-md">
        No resources available for this part
      </p>
      <p class="text-body2 text-grey-6">
        The selected provider part doesn't have any downloadable resources.
      </p>
    </div>
  </div>
</template>

<style scoped>
.resource-selector :deep(.q-item) {
  transition: background-color 0.2s ease;
}

.resource-selector :deep(.q-item:hover) {
  background-color: rgba(0, 0, 0, 0.03);
}
</style>
