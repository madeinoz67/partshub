<script setup lang="ts">
/**
 * ProviderSelector Component
 * Step 2: Choose a provider to search for parts
 */

import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useWizardStore } from '../../stores/wizardStore'
import { wizardService } from '../../services/wizardService'
import type { Provider } from '../../types/wizard'

const $q = useQuasar()
const wizardStore = useWizardStore()

// Local state
const providers = ref<Provider[]>([])
const loading = ref(false)
const selectedProvider = ref<Provider | null>(wizardStore.selectedProvider)

/**
 * Load available providers
 */
async function loadProviders() {
  loading.value = true

  try {
    providers.value = await wizardService.listProviders()

    // Auto-select if only one provider (FR-023)
    if (providers.value.length === 1) {
      selectedProvider.value = providers.value[0]
      wizardStore.selectProvider(providers.value[0])

      $q.notify({
        type: 'info',
        message: `Auto-selected provider: ${providers.value[0].name}`,
        position: 'top',
      })

      // Auto-advance to next step after a short delay
      setTimeout(() => {
        wizardStore.setStep(3)
      }, 500)
    }
  } catch (err) {
    $q.notify({
      type: 'negative',
      message: err instanceof Error ? err.message : 'Failed to load providers',
      position: 'top',
    })
  } finally {
    loading.value = false
  }
}

/**
 * Handle provider selection
 */
function selectProvider(provider: Provider) {
  selectedProvider.value = provider
  wizardStore.selectProvider(provider)
}

// Load providers on mount
onMounted(() => {
  loadProviders()
})
</script>

<template>
  <div class="provider-selector">
    <p class="text-body1 q-mb-md">
      Select a provider to search for parts:
    </p>

    <div v-if="loading" class="text-center q-py-xl">
      <q-spinner color="primary" size="50px" />
      <p class="text-body2 text-grey-7 q-mt-md">Loading providers...</p>
    </div>

    <div v-else-if="providers.length === 0" class="text-center q-py-xl">
      <q-icon name="cloud_off" size="64px" color="grey-5" />
      <p class="text-body1 text-grey-7 q-mt-md">
        No providers configured. Please configure a provider in the admin settings.
      </p>
    </div>

    <div v-else class="row q-col-gutter-md">
      <div
        v-for="provider in providers"
        :key="provider.id"
        class="col-12 col-md-6"
      >
        <q-card
          flat
          bordered
          clickable
          :class="{
            'bg-grey-2': selectedProvider?.id === provider.id,
            'card-hover': true,
          }"
          @click="selectProvider(provider)"
        >
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">{{ provider.name }}</div>
                <div class="text-caption text-grey-7">
                  {{ provider.base_url }}
                </div>
              </div>
              <div class="col-auto">
                <q-badge
                  v-if="provider.is_active"
                  color="positive"
                  label="Active"
                />
                <q-badge
                  v-else
                  color="negative"
                  label="Inactive"
                />
              </div>
            </div>
          </q-card-section>

          <q-card-section v-if="provider.last_sync_at">
            <div class="text-caption text-grey-7">
              Last synced: {{ new Date(provider.last_sync_at).toLocaleString() }}
            </div>
          </q-card-section>

          <q-card-section class="q-pt-none">
            <q-radio
              :model-value="selectedProvider?.id"
              :val="provider.id"
              label="Select this provider"
              color="primary"
              @update:model-value="selectProvider(provider)"
            />
          </q-card-section>

          <q-card-section v-if="!provider.api_key_configured" class="q-pt-none">
            <q-banner class="bg-warning text-white" dense rounded>
              <template v-slot:avatar>
                <q-icon name="warning" />
              </template>
              API key not configured. Search may be limited.
            </q-banner>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-banner
      v-if="providers.length > 0 && selectedProvider"
      class="bg-info text-white q-mt-md"
      rounded
    >
      <template v-slot:avatar>
        <q-icon name="info" />
      </template>
      You can search {{ selectedProvider.name }} for parts in the next step.
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
