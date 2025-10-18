<template>
  <q-card>
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Inventory Summary</div>
        <q-btn
          flat
          round
          dense
          icon="refresh"
          :loading="loading"
          @click="fetchData"
        >
          <q-tooltip>Refresh</q-tooltip>
        </q-btn>
      </div>

      <q-banner v-if="error" class="bg-negative text-white q-mb-md">
        <template #avatar>
          <q-icon name="error" />
        </template>
        {{ error }}
      </q-banner>

      <div v-if="summaryData" class="row q-col-gutter-md">
        <!-- Total Stock Value -->
        <div class="col-12 col-md-6">
          <q-card flat bordered class="metric-card bg-primary text-white">
            <q-card-section>
              <div class="row items-center">
                <q-icon name="attach_money" size="md" class="q-mr-sm" />
                <div class="metric-content">
                  <div class="text-h5 text-weight-bold">
                    {{ formatCurrency(summaryData.total_stock_value) }}
                  </div>
                  <div class="text-caption">Total Stock Value</div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Total Components -->
        <div class="col-12 col-md-6">
          <q-card flat bordered class="metric-card bg-secondary text-white">
            <q-card-section>
              <div class="row items-center">
                <q-icon name="inventory_2" size="md" class="q-mr-sm" />
                <div class="metric-content">
                  <div class="text-h5 text-weight-bold">
                    {{ summaryData.total_components.toLocaleString() }}
                  </div>
                  <div class="text-caption">Total Components</div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Average Stock Level -->
        <div class="col-12 col-md-6">
          <q-card flat bordered class="metric-card">
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon name="show_chart" size="md" class="q-mr-sm" color="accent" />
                <div class="metric-content">
                  <div class="text-h5 text-weight-bold">
                    {{ summaryData.average_stock_level_percentage.toFixed(1) }}%
                  </div>
                  <div class="text-caption text-grey-7">Average Stock Level</div>
                </div>
              </div>
              <q-linear-progress
                :value="summaryData.average_stock_level_percentage / 100"
                color="accent"
                size="8px"
                rounded
              />
            </q-card-section>
          </q-card>
        </div>

        <!-- Total Locations -->
        <div class="col-12 col-md-6">
          <q-card flat bordered class="metric-card">
            <q-card-section>
              <div class="row items-center">
                <q-icon name="place" size="md" class="q-mr-sm" color="info" />
                <div class="metric-content">
                  <div class="text-h5 text-weight-bold">
                    {{ summaryData.total_locations }}
                  </div>
                  <div class="text-caption text-grey-7">Total Locations</div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Stock Status Indicators -->
        <div class="col-12">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm text-grey-7">Stock Status Overview</div>
              <div class="row q-col-gutter-sm">
                <div class="col-4">
                  <div class="status-indicator">
                    <q-icon name="error" color="negative" size="sm" />
                    <span class="text-weight-bold q-ml-xs">{{ summaryData.out_of_stock_count }}</span>
                    <span class="text-caption text-grey-7 q-ml-xs">Out of Stock</span>
                  </div>
                </div>
                <div class="col-4">
                  <div class="status-indicator">
                    <q-icon name="warning" color="warning" size="sm" />
                    <span class="text-weight-bold q-ml-xs">{{ summaryData.low_stock_count }}</span>
                    <span class="text-caption text-grey-7 q-ml-xs">Low Stock</span>
                  </div>
                </div>
                <div class="col-4">
                  <div class="status-indicator">
                    <q-icon name="trending_up" color="info" size="sm" />
                    <span class="text-weight-bold q-ml-xs">{{ summaryData.overstocked_count }}</span>
                    <span class="text-caption text-grey-7 q-ml-xs">Overstocked</span>
                  </div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <q-inner-loading :showing="loading">
        <q-spinner color="primary" size="50px" />
      </q-inner-loading>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../../boot/axios'

interface InventorySummaryResponse {
  total_components: number
  total_stock_value: number
  low_stock_count: number
  out_of_stock_count: number
  overstocked_count: number
  average_stock_level_percentage: number
  total_locations: number
  metadata: Record<string, unknown>
}

const loading = ref(false)
const error = ref<string | null>(null)
const summaryData = ref<InventorySummaryResponse | null>(null)

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const response = await api.get<InventorySummaryResponse>(
      '/api/v1/analytics/inventory-summary'
    )

    summaryData.value = response.data
  } catch (err: unknown) {
    console.error('Failed to fetch inventory summary:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load inventory summary data'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchData()
})

defineExpose({
  refresh: fetchData
})
</script>

<style scoped>
.metric-card {
  min-height: 100px;
  transition: transform 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-content {
  flex: 1;
}

.status-indicator {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}
</style>
