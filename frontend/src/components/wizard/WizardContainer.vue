<script setup lang="ts">
/**
 * WizardContainer Component
 * Main container for the component creation wizard with step navigation
 */

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useWizardStore } from '../../stores/wizardStore'
import PartTypeSelector from './PartTypeSelector.vue'
import ProviderSelector from './ProviderSelector.vue'
import ProviderSearch from './ProviderSearch.vue'
import LocalPartForm from './LocalPartForm.vue'
import ResourceSelector from './ResourceSelector.vue'
import PostCreationActions from './PostCreationActions.vue'

const router = useRouter()
const $q = useQuasar()
const wizardStore = useWizardStore()

// Local state
const stepper = ref()
const isCreating = ref(false)

// Computed
const stepTitle = computed(() => {
  switch (wizardStore.currentStep) {
    case 1:
      return 'Select Part Type'
    case 2:
      return 'Choose Provider'
    case 3:
      return wizardStore.partType === 'linked' ? 'Search Provider' : 'Enter Part Details'
    case 4:
      return 'Select Resources'
    case 5:
      return 'Create Component'
    default:
      return 'Step ' + wizardStore.currentStep
  }
})

const showProviderStep = computed(() => {
  return wizardStore.partType === 'linked'
})

const showSearchStep = computed(() => {
  return wizardStore.partType === 'linked'
})

const showLocalFormStep = computed(() => {
  return wizardStore.partType === 'local' || wizardStore.partType === 'meta'
})

/**
 * Navigate to next step
 */
function nextStep() {
  if (!wizardStore.canProceed) {
    $q.notify({
      type: 'warning',
      message: 'Please complete the current step before proceeding',
      position: 'top',
    })
    return
  }

  // Skip provider step for non-linked parts
  if (wizardStore.currentStep === 1 && !showProviderStep.value) {
    wizardStore.setStep(3)
  } else if (wizardStore.currentStep < 5) {
    wizardStore.setStep((wizardStore.currentStep + 1) as 1 | 2 | 3 | 4 | 5)
  }
}

/**
 * Navigate to previous step
 */
function previousStep() {
  // Skip provider step for non-linked parts when going back
  if (wizardStore.currentStep === 3 && !showProviderStep.value) {
    wizardStore.setStep(1)
  } else if (wizardStore.currentStep > 1) {
    wizardStore.setStep((wizardStore.currentStep - 1) as 1 | 2 | 3 | 4 | 5)
  }
}

/**
 * Create component and handle post-creation action
 */
async function createComponent() {
  if (!wizardStore.canProceed) {
    $q.notify({
      type: 'warning',
      message: 'Please select a post-creation action',
      position: 'top',
    })
    return
  }

  isCreating.value = true

  try {
    const component = await wizardStore.createComponent()

    $q.notify({
      type: 'positive',
      message: 'Component created successfully!',
      position: 'top',
    })

    // Handle post-creation action
    const action = wizardStore.postAction
    const componentId = component.id

    switch (action) {
      case 'view':
        // Navigate to component detail page
        await router.push(`/components/${componentId}`)
        break
      case 'add_stock':
        // Navigate to dedicated add stock page
        await router.push(`/components/${componentId}/add-stock`)
        break
      case 'continue':
        // Stay on wizard page, reset immediately for next component
        wizardStore.reset()
        $q.notify({
          type: 'info',
          message: 'Ready to create another component',
          position: 'top',
        })
        break
    }
  } catch (err) {
    $q.notify({
      type: 'negative',
      message: err instanceof Error ? err.message : 'Failed to create component',
      position: 'top',
    })
  } finally {
    isCreating.value = false
  }
}

/**
 * Cancel wizard and return to components list
 */
function cancelWizard() {
  $q.dialog({
    title: 'Cancel Component Creation',
    message: 'Are you sure you want to cancel? All progress will be lost.',
    cancel: true,
    persistent: true,
  }).onOk(() => {
    wizardStore.reset()
    router.push('/components')
  })
}
</script>

<template>
  <q-card class="wizard-container">
    <q-card-section>
      <div class="text-h6">{{ stepTitle }}</div>
      <div class="text-caption text-grey-7">
        Step {{ wizardStore.currentStep }} of 5
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="q-pa-md">
      <q-stepper
        v-model="wizardStore.currentStep"
        ref="stepper"
        animated
        flat
        header-nav
      >
        <!-- Step 1: Part Type Selection -->
        <q-step
          :name="1"
          title="Part Type"
          icon="category"
          :done="wizardStore.currentStep > 1"
        >
          <PartTypeSelector />
        </q-step>

        <!-- Step 2: Provider Selection (only for linked parts) -->
        <q-step
          v-if="showProviderStep"
          :name="2"
          title="Provider"
          icon="cloud"
          :done="wizardStore.currentStep > 2"
        >
          <ProviderSelector />
        </q-step>

        <!-- Step 3a: Provider Search (for linked parts) -->
        <q-step
          v-if="showSearchStep"
          :name="3"
          title="Search"
          icon="search"
          :done="wizardStore.currentStep > 3"
        >
          <ProviderSearch />
        </q-step>

        <!-- Step 3b: Local Part Form (for local/meta parts) -->
        <q-step
          v-if="showLocalFormStep"
          :name="3"
          title="Details"
          icon="edit"
          :done="wizardStore.currentStep > 3"
        >
          <LocalPartForm />
        </q-step>

        <!-- Step 4: Resource Selection -->
        <q-step
          :name="4"
          title="Resources"
          icon="attachment"
          :done="wizardStore.currentStep > 4"
        >
          <ResourceSelector />
        </q-step>

        <!-- Step 5: Post-Creation Actions -->
        <q-step
          :name="5"
          title="Create"
          icon="check_circle"
        >
          <PostCreationActions />
        </q-step>
      </q-stepper>
    </q-card-section>

    <q-separator />

    <!-- Navigation Buttons -->
    <q-card-actions align="right" class="q-pa-md">
      <q-btn
        flat
        label="Cancel"
        color="negative"
        @click="cancelWizard"
      />

      <q-space />

      <q-btn
        v-if="wizardStore.currentStep > 1"
        flat
        label="Back"
        icon="arrow_back"
        @click="previousStep"
      />

      <q-btn
        v-if="wizardStore.currentStep < 5"
        unelevated
        label="Next"
        icon-right="arrow_forward"
        color="primary"
        :disable="!wizardStore.canProceed"
        @click="nextStep"
      />

      <q-btn
        v-if="wizardStore.currentStep === 5"
        unelevated
        label="Create Component"
        icon-right="check"
        color="positive"
        :disable="!wizardStore.canProceed"
        :loading="isCreating"
        @click="createComponent"
      />
    </q-card-actions>
  </q-card>
</template>

<style scoped>
.wizard-container {
  max-width: 900px;
  margin: 0 auto;
}
</style>
