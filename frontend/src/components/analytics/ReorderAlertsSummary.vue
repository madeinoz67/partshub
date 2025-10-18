<template>
  <div>
    <q-spinner v-if="loading" color="primary" size="50px" class="absolute-center q-pa-xl" />

    <q-banner v-else-if="error" class="bg-negative text-white">
      <template #avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
    </q-banner>

    <div v-else class="dashboard-summary">
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <div class="text-h4 text-primary">{{ healthMetrics.total_components }}</div>
              <div class="text-caption text-grey">Total Components</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <div class="text-h4 text-warning">{{ healthMetrics.low_stock_count }}</div>
              <div class="text-caption text-grey">Low Stock Alerts</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <div class="text-h4 text-negative">{{ healthMetrics.out_of_stock_count }}</div>
              <div class="text-caption text-grey">Out of Stock</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <div class="text-h4 text-positive">${{ healthMetrics.total_inventory_value.toFixed(0) }}</div>
              <div class="text-caption text-grey">Inventory Value</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6 q-mb-md">Top 10 Low Stock Components</div>
              <q-list v-if="topLowStock.length > 0" bordered separator>
                <q-item
                  v-for="item in topLowStock"
                  :key="item.component_id"
                  clickable
                  @click="navigateToComponent(item.component_id)"
                >
                  <q-item-section>
                    <q-item-label>{{ item.component_name }}</q-item-label>
                    <q-item-label caption>
                      {{ item.total_quantity }} units in {{ item.locations_count }} location(s)
                    </q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <div class="column items-end">
                      <q-badge
                        v-if="item.has_active_alerts"
                        color="negative"
                        label="Alert"
                      />
                      <div v-if="item.days_until_stockout" class="text-caption text-warning q-mt-xs">
                        {{ item.days_until_stockout }} days left
                      </div>
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
              <div v-else class="text-center text-grey q-pa-md">
                No low stock components
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6 q-mb-md">Top 10 High Consumers</div>
              <q-list v-if="topConsumers.length > 0" bordered separator>
                <q-item
                  v-for="item in topConsumers"
                  :key="item.component_id"
                  clickable
                  @click="navigateToComponent(item.component_id)"
                >
                  <q-item-section>
                    <q-item-label>{{ item.component_name }}</q-item-label>
                    <q-item-label caption>
                      {{ item.total_quantity }} units in {{ item.locations_count }} location(s)
                    </q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <div class="column items-end">
                      <q-chip color="primary" text-color="white" size="sm">
                        {{ item.daily_velocity.toFixed(1) }}/day
                      </q-chip>
                      <div v-if="item.days_until_stockout" class="text-caption text-grey q-mt-xs">
                        {{ item.days_until_stockout }} days supply
                      </div>
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
              <div v-else class="text-center text-grey q-pa-md">
                No high consumption components
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <q-card flat bordered class="q-mt-md">
        <q-card-section>
          <div class="row items-center justify-between">
            <div class="text-body1">
              <q-icon name="info" color="info" class="q-mr-xs" />
              Recent Activity: {{ recentActivityCount }} transactions in last 7 days
            </div>
            <div class="text-caption text-grey">
              Average Velocity: {{ healthMetrics.average_stock_velocity.toFixed(2) }} units/day
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../boot/axios'

interface Props {
  categoryId?: string | null
  locationId?: string | null
}

interface ComponentStockSummary {
  component_id: string
  component_name: string
  total_quantity: number
  locations_count: number
  has_active_alerts: boolean
  daily_velocity: number
  days_until_stockout: number | null
}

interface InventoryHealthMetrics {
  total_components: number
  low_stock_count: number
  out_of_stock_count: number
  total_inventory_value: number
  active_alerts_count: number
  average_stock_velocity: number
}

interface DashboardSummaryResponse {
  health_metrics: InventoryHealthMetrics
  top_low_stock: ComponentStockSummary[]
  top_consumers: ComponentStockSummary[]
  recent_activity_count: number
  metadata: {
    last_updated: string
    category_filter: string | null
    location_filter: string | null
  }
}

const props = withDefaults(defineProps<Props>(), {
  categoryId: null,
  locationId: null
})

const router = useRouter()
const loading = ref(false)
const error = ref<string | null>(null)
const healthMetrics = ref<InventoryHealthMetrics>({
  total_components: 0,
  low_stock_count: 0,
  out_of_stock_count: 0,
  total_inventory_value: 0,
  active_alerts_count: 0,
  average_stock_velocity: 0
})
const topLowStock = ref<ComponentStockSummary[]>([])
const topConsumers = ref<ComponentStockSummary[]>([])
const recentActivityCount = ref(0)

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams()

    if (props.categoryId) {
      params.append('category_id', props.categoryId)
    }

    if (props.locationId) {
      params.append('location_id', props.locationId)
    }

    const queryString = params.toString()
    const url = queryString
      ? `/api/v1/analytics/dashboard?${queryString}`
      : '/api/v1/analytics/dashboard'

    const response = await api.get<DashboardSummaryResponse>(url)

    const data = response.data
    healthMetrics.value = data.health_metrics
    topLowStock.value = data.top_low_stock
    topConsumers.value = data.top_consumers
    recentActivityCount.value = data.recent_activity_count
  } catch (err: unknown) {
    console.error('Failed to fetch dashboard summary:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

function navigateToComponent(componentId: string) {
  router.push(`/components/${componentId}`)
}

onMounted(() => fetchData())

watch(
  () => [props.categoryId, props.locationId],
  () => fetchData()
)
</script>

<style scoped>
.dashboard-summary {
  width: 100%;
}
</style>
