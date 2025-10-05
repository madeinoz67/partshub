<script setup lang="ts">
/**
 * CreateComponentPage
 * Main page for the component creation wizard
 * Admin-only access
 */

import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useWizardStore } from '../stores/wizardStore'
import WizardContainer from '../components/wizard/WizardContainer.vue'

const router = useRouter()
const authStore = useAuthStore()
const wizardStore = useWizardStore()

/**
 * Check admin access on mount
 */
onMounted(() => {
  // Redirect if not admin
  if (!authStore.isAdmin) {
    router.push('/components')
  }

  // Initialize wizard store
  wizardStore.initialize()
})
</script>

<template>
  <q-page class="create-component-page q-pa-md">
    <!-- Page Header -->
    <div class="page-header q-mb-lg">
      <div class="row items-center q-mb-md">
        <div class="col">
          <h1 class="text-h4 q-ma-none">Create Component</h1>
        </div>
        <div class="col-auto">
          <q-btn
            flat
            icon="close"
            label="Cancel"
            color="negative"
            :to="'/components'"
          />
        </div>
      </div>

      <!-- Breadcrumbs -->
      <q-breadcrumbs>
        <q-breadcrumbs-el label="Home" icon="home" to="/" />
        <q-breadcrumbs-el label="Components" to="/components" />
        <q-breadcrumbs-el label="Create" />
      </q-breadcrumbs>
    </div>

    <!-- Wizard Container -->
    <WizardContainer />
  </q-page>
</template>

<style scoped>
.create-component-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  padding-bottom: 1rem;
}
</style>
