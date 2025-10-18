<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Page Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Inventory Analytics Dashboard</h4>
            <p class="text-grey-7 q-mb-none">Real-time insights and metrics</p>
          </div>
          <q-btn
            color="primary"
            icon="refresh"
            label="Refresh All"
            :loading="isRefreshing"
            @click="refreshAll"
          />
        </div>
      </div>

      <!-- Top Row: Inventory Summary (KPI Card) -->
      <div class="col-12">
        <InventoryValueChart ref="inventoryValueChart" />
      </div>

      <!-- Second Row: Stock Distribution & Top Velocity -->
      <div class="col-12 col-md-6">
        <StockDistributionChart ref="stockDistributionChart" />
      </div>

      <div class="col-12 col-md-6">
        <TopVelocityChart ref="topVelocityChart" />
      </div>

      <!-- Additional charts can be added here -->
      <!-- Example: Component-specific charts would go below -->
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import InventoryValueChart from '../components/analytics/InventoryValueChart.vue'
import StockDistributionChart from '../components/analytics/StockDistributionChart.vue'
import TopVelocityChart from '../components/analytics/TopVelocityChart.vue'

// Chart refs for manual refresh
const inventoryValueChart = ref<InstanceType<typeof InventoryValueChart>>()
const stockDistributionChart = ref<InstanceType<typeof StockDistributionChart>>()
const topVelocityChart = ref<InstanceType<typeof TopVelocityChart>>()

const isRefreshing = ref(false)

async function refreshAll() {
  isRefreshing.value = true

  try {
    // Refresh all charts in parallel
    await Promise.all([
      inventoryValueChart.value?.refresh(),
      stockDistributionChart.value?.refresh(),
      topVelocityChart.value?.refresh()
    ])
  } catch (error) {
    console.error('Failed to refresh dashboard:', error)
  } finally {
    isRefreshing.value = false
  }
}
</script>

<style scoped>
h4 {
  font-size: 1.5rem;
  font-weight: 500;
}
</style>
