<script setup lang="ts">
/**
 * AddStockPage
 * Dedicated page for adding stock to a newly created component
 */

import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import AddStockForm from '../components/stock/AddStockForm.vue'
import { APIService, type Component } from '../services/api'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

const componentId = computed(() => String(route.params.id))
const component = ref<Component | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  try {
    isLoading.value = true
    // Fetch component directly by ID from API (not from store cache)
    // This ensures we get the newly created component
    component.value = await APIService.getComponent(componentId.value)
  } catch (err) {
    $q.notify({
      type: 'negative',
      message: 'Component not found',
      position: 'top',
    })
    await router.push('/components')
  } finally {
    isLoading.value = false
  }
})

/**
 * Handle successful stock addition
 */
function handleStockAdded() {
  $q.notify({
    type: 'positive',
    message: 'Stock added successfully!',
    position: 'top',
  })
  // Navigate to component detail page
  router.push(`/components/${componentId.value}`)
}

/**
 * Handle cancellation
 */
function handleCancel() {
  router.push(`/components/${componentId.value}`)
}
</script>

<template>
  <q-page padding>
    <!-- Breadcrumb Navigation -->
    <q-breadcrumbs class="q-mb-md">
      <q-breadcrumbs-el label="Components" to="/components" />
      <q-breadcrumbs-el
        v-if="component"
        :label="component.name"
        :to="`/components/${componentId}`"
      />
      <q-breadcrumbs-el label="Add Stock" />
    </q-breadcrumbs>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center q-pa-lg">
      <q-spinner color="primary" size="3em" />
      <div class="text-grey-7 q-mt-md">Loading component...</div>
    </div>

    <!-- Main Content -->
    <div v-else-if="component" class="add-stock-container">
      <!-- Header -->
      <q-card flat bordered class="q-mb-md">
        <q-card-section>
          <div class="text-h5 q-mb-xs">Add Stock</div>
          <div class="text-body1 text-grey-7">
            Adding stock to: <strong>{{ component.name }}</strong>
          </div>
          <div v-if="component.manufacturer" class="text-caption text-grey-6">
            {{ component.manufacturer }}
            <span v-if="component.package"> • {{ component.package }}</span>
          </div>
        </q-card-section>
      </q-card>

      <!-- Add Stock Form -->
      <q-card flat bordered>
        <q-card-section>
          <AddStockForm
            :component-id="componentId"
            @success="handleStockAdded"
            @cancel="handleCancel"
          />
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<style scoped>
.add-stock-container {
  max-width: 900px;
  margin: 0 auto;
}
</style>
