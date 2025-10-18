<template>
  <q-card>
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Stock Distribution</div>
        <div v-if="timestamp && !loading" class="text-caption text-grey-7">
          {{ formatTimestamp(timestamp) }}
        </div>
      </div>

      <q-banner v-if="error" class="bg-negative text-white q-mb-md">
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

        <!-- Center label for total components -->
        <div v-if="totalComponents && !loading" class="center-label">
          <div class="text-h5 text-weight-bold">{{ totalComponents }}</div>
          <div class="text-caption text-grey-7">Total Components</div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useChart } from '../../composables/useChart'
import { api } from '../../boot/axios'

interface DistributionItem {
  status: 'critical' | 'low' | 'ok' | 'overstocked'
  count: number
  percentage: number
}

interface StockDistributionResponse {
  total_components: number
  distribution: DistributionItem[]
  timestamp: string
}

const chartCanvas = ref<HTMLCanvasElement>()
const { createChart } = useChart(chartCanvas)
const loading = ref(false)
const error = ref<string | null>(null)
const totalComponents = ref<number>(0)
const timestamp = ref<string>('')

const statusLabels: Record<string, string> = {
  critical: 'Critical',
  low: 'Low Stock',
  ok: 'OK',
  overstocked: 'Overstocked'
}

const statusColors: Record<string, string> = {
  critical: '#f44336',
  low: '#ff9800',
  ok: '#4caf50',
  overstocked: '#2196f3'
}

function formatTimestamp(ts: string): string {
  const date = new Date(ts)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const response = await api.get<StockDistributionResponse>(
      '/api/v1/analytics/stock-distribution'
    )

    const data = response.data
    totalComponents.value = data.total_components
    timestamp.value = data.timestamp

    // Transform data for Chart.js
    const labels = data.distribution.map(item => statusLabels[item.status])
    const counts = data.distribution.map(item => item.count)
    const percentages = data.distribution.map(item => item.percentage)
    const colors = data.distribution.map(item => statusColors[item.status])

    const chartData = {
      labels,
      datasets: [{
        data: counts,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    }

    // Wait for next tick to ensure canvas ref is populated
    await nextTick()

    createChart({
      type: 'doughnut',
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom' as const,
            labels: {
              padding: 15,
              font: {
                size: 12
              },
              generateLabels: (chart) => {
                const datasets = chart.data.datasets
                if (!datasets.length) return []

                return chart.data.labels?.map((label, i) => ({
                  text: `${label}: ${counts[i]} (${percentages[i].toFixed(1)}%)`,
                  fillStyle: colors[i],
                  hidden: false,
                  index: i
                })) || []
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || ''
                const value = context.parsed
                const percentage = percentages[context.dataIndex]
                return `${label}: ${value} components (${percentage.toFixed(1)}%)`
              }
            }
          }
        }
      }
    })
  } catch (err: unknown) {
    console.error('Failed to fetch stock distribution:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load stock distribution data'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await nextTick()
  await fetchData()
})

defineExpose({
  refresh: fetchData
})
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 350px;
  width: 100%;
}

.center-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
</style>
