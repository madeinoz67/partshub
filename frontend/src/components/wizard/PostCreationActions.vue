<script setup lang="ts">
/**
 * PostCreationActions Component
 * Step 5: Select what to do after component creation
 */

import { ref, watch } from 'vue'
import { useWizardStore } from '../../stores/wizardStore'
import type { PostAction } from '../../types/wizard'

const wizardStore = useWizardStore()

// Local state - default to 'view' if no action selected
const selectedAction = ref<PostAction>(wizardStore.postAction || 'view')

// Set default action in store if none selected
if (!wizardStore.postAction) {
  wizardStore.postAction = 'view'
}

// Post-action options (FR-012)
const actionOptions = [
  {
    value: 'view' as PostAction,
    label: 'Go to Created Part',
    description: 'View the newly created component details',
    icon: 'visibility',
    color: 'primary',
  },
  {
    value: 'add_stock' as PostAction,
    label: 'Add Stock',
    description: 'Add initial stock quantity to the component',
    icon: 'inventory',
    color: 'secondary',
  },
  {
    value: 'continue' as PostAction,
    label: 'Stay and Continue',
    description: 'Reset the wizard and create another component',
    icon: 'refresh',
    color: 'accent',
  },
]

/**
 * Handle action selection
 */
function selectAction(action: PostAction) {
  selectedAction.value = action
  wizardStore.postAction = action
}

// Watch for store changes
watch(
  () => wizardStore.postAction,
  (newAction) => {
    selectedAction.value = newAction
  }
)
</script>

<template>
  <div class="post-creation-actions">
    <p class="text-body1 q-mb-md">
      What would you like to do after creating this component?
    </p>

    <!-- Summary of what will be created -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-h6 q-mb-md">Component Summary</div>

        <!-- Linked Part Summary -->
        <div v-if="wizardStore.partType === 'linked' && wizardStore.selectedPart">
          <div class="row q-mb-sm">
            <div class="col-4 text-grey-7">Type:</div>
            <div class="col-8">
              <q-badge color="primary">Linked Part</q-badge>
            </div>
          </div>
          <div class="row q-mb-sm">
            <div class="col-4 text-grey-7">Name:</div>
            <div class="col-8">{{ wizardStore.selectedPart.name || wizardStore.selectedPart.part_number }}</div>
          </div>
          <div class="row q-mb-sm">
            <div class="col-4 text-grey-7">Part Number:</div>
            <div class="col-8">{{ wizardStore.selectedPart.part_number }}</div>
          </div>
          <div class="row q-mb-sm" v-if="wizardStore.selectedPart.description">
            <div class="col-4 text-grey-7">Description:</div>
            <div class="col-8">{{ wizardStore.selectedPart.description }}</div>
          </div>
          <div class="row q-mb-sm" v-if="wizardStore.selectedPart.manufacturer">
            <div class="col-4 text-grey-7">Manufacturer:</div>
            <div class="col-8">{{ wizardStore.selectedPart.manufacturer }}</div>
          </div>
          <div class="row" v-if="wizardStore.selectedProvider">
            <div class="col-4 text-grey-7">Provider:</div>
            <div class="col-8">{{ wizardStore.selectedProvider.name }}</div>
          </div>
        </div>

        <!-- Local/Meta Part Summary -->
        <div v-else-if="wizardStore.partType === 'local' || wizardStore.partType === 'meta'">
          <div class="row q-mb-sm">
            <div class="col-4 text-grey-7">Type:</div>
            <div class="col-8">
              <q-badge :color="wizardStore.partType === 'local' ? 'secondary' : 'accent'">
                {{ wizardStore.partType === 'local' ? 'Local Part' : 'Meta-Part' }}
              </q-badge>
            </div>
          </div>
          <div class="row q-mb-sm">
            <div class="col-4 text-grey-7">Name:</div>
            <div class="col-8">{{ wizardStore.localPartData.name }}</div>
          </div>
          <div class="row q-mb-sm" v-if="wizardStore.localPartData.description">
            <div class="col-4 text-grey-7">Description:</div>
            <div class="col-8">{{ wizardStore.localPartData.description }}</div>
          </div>
          <div class="row q-mb-sm" v-if="wizardStore.localPartData.manufacturer_name">
            <div class="col-4 text-grey-7">Manufacturer:</div>
            <div class="col-8">
              {{ wizardStore.localPartData.manufacturer_name }}
              <q-badge v-if="!wizardStore.localPartData.manufacturer_id" color="orange" class="q-ml-sm">
                New
              </q-badge>
            </div>
          </div>
          <div class="row" v-if="wizardStore.localPartData.footprint_name">
            <div class="col-4 text-grey-7">Footprint:</div>
            <div class="col-8">
              {{ wizardStore.localPartData.footprint_name }}
              <q-badge v-if="!wizardStore.localPartData.footprint_id" color="orange" class="q-ml-sm">
                New
              </q-badge>
            </div>
          </div>
        </div>

        <!-- Resources Summary -->
        <div
          v-if="wizardStore.selectedResources.length > 0"
          class="row q-mt-md"
        >
          <div class="col-4 text-grey-7">Resources:</div>
          <div class="col-8">
            <q-badge
              v-for="resource in wizardStore.selectedResources.filter(r => r.selected)"
              :key="resource.type"
              color="info"
              class="q-mr-xs q-mb-xs"
            >
              {{ resource.type }}
            </q-badge>
            <span v-if="wizardStore.selectedResources.filter(r => r.selected).length === 0" class="text-grey-6">
              None selected
            </span>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Action Selection -->
    <div class="row q-col-gutter-md">
      <div
        v-for="option in actionOptions"
        :key="String(option.value)"
        class="col-12 col-md-4"
      >
        <q-card
          flat
          bordered
          clickable
          :class="{
            'bg-grey-2': selectedAction === option.value,
            'card-hover': true,
          }"
          @click="selectAction(option.value)"
        >
          <q-card-section class="text-center">
            <q-icon
              :name="option.icon"
              :color="selectedAction === option.value ? option.color : 'grey-6'"
              size="48px"
            />
          </q-card-section>

          <q-card-section>
            <div class="text-subtitle1 text-center q-mb-sm">
              {{ option.label }}
            </div>
            <div class="text-body2 text-grey-7 text-center">
              {{ option.description }}
            </div>
          </q-card-section>

          <q-card-section class="text-center">
            <q-radio
              v-model="selectedAction"
              :val="option.value"
              :label="'Select'"
              :color="option.color"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Action-specific info banners -->
    <q-banner
      v-if="selectedAction === 'view'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      You will be redirected to the component detail page after creation.
    </q-banner>

    <q-banner
      v-if="selectedAction === 'add_stock'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      You will be redirected to the component page where you can add initial stock.
    </q-banner>

    <q-banner
      v-if="selectedAction === 'continue'"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      The wizard will reset and you can create another component immediately. (FR-014)
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
