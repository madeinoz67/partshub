<template>
  <q-card>
    <q-card-section>
      <div class="text-h6 q-mb-md">Stock Levels Over Time</div>

      <q-banner v-if="error" class="bg-negative text-white">
        <template #avatar>
          <q-icon name="error" />
        </template>
        {{ error }}
      </q-banner>

      <div class="chart-container" style="position: relative;">
        <q-inner-loading :showing="loading">
          <q-spinner color="primary" size="50px" />
        </q-inner-loading>
        <canvas ref="chartCanvas"></canvas>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useChart, chartHelpers } from '../../composables/useChart'
import { api } from '../../boot/axios'

interface Props {
  componentId: string
  locationId?: string | null
  startDate: string
  endDate: string
  period?: 'daily' | 'weekly' | 'monthly'
}

interface StockDataPoint {
  timestamp: string
  quantity: number
  transaction_count: number
}

interface StockLevelsResponse {
  component_id: string
  component_name: string
  location_id: string | null
  location_name: string | null
  period: string
  data: StockDataPoint[]
  metadata: {
    start_date: string
    end_date: string
    current_quantity: number
    reorder_threshold?: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  locationId: null,
  period: 'daily'
})

const chartCanvas = ref<HTMLCanvasElement>()
const { createChart } = useChart(chartCanvas)
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      component_id: props.componentId,
      start_date: props.startDate,
      end_date: props.endDate,
      period: props.period
    })

    if (props.locationId) {
      params.append('location_id', props.locationId)
    }

    const response = await api.get<StockLevelsResponse>(
      `/api/v1/analytics/stock-levels?${params.toString()}`
    )

    const data = response.data
    const reorderThreshold = data.metadata.reorder_threshold

    const chartData = chartHelpers.transformStockLevels(
      data.data,
      reorderThreshold
    )

    // Wait for next tick to ensure canvas ref is populated
    await nextTick()

    createChart({
      type: 'line',
      data: chartData,
      options: chartHelpers.getDefaultOptions({
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top' as const,
          },
          tooltip: {
            mode: 'index' as const,
            intersect: false,
            callbacks: {
              footer: (tooltipItems) => {
                const item = tooltipItems[0]
                if (item && data.data[item.dataIndex]) {
                  const point = data.data[item.dataIndex]
                  return `Transactions: ${point.transaction_count}`
                }
                return ''
              }
            }
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Quantity'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date'
            }
          }
        }
      })
    })
  } catch (err: unknown) {
    console.error('Failed to fetch stock levels:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load stock level data'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await nextTick()
  await fetchData()
})

watch(
  () => [props.componentId, props.locationId, props.startDate, props.endDate, props.period],
  async () => {
    await fetchData()
  }
)
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>
