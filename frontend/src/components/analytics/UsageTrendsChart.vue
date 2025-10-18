<template>
  <q-card>
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Usage Trends</div>
        <div v-if="velocityMetrics && !loading" class="row q-gutter-sm">
          <q-chip color="primary" text-color="white" size="sm">
            <q-avatar icon="speed" color="primary" text-color="white" />
            {{ velocityMetrics.daily_average.toFixed(1) }}/day
          </q-chip>
          <q-chip color="secondary" text-color="white" size="sm">
            <q-avatar icon="calendar_month" color="secondary" text-color="white" />
            {{ velocityMetrics.monthly_average.toFixed(0) }}/month
          </q-chip>
        </div>
      </div>

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

interface UsageTrendDataPoint {
  timestamp: string
  consumed: number
  added: number
  removed: number
}

interface VelocityMetrics {
  daily_average: number
  weekly_average: number
  monthly_average: number
  total_consumed: number
  days_analyzed: number
}

interface UsageTrendsResponse {
  component_id: string
  component_name: string
  location_id: string | null
  location_name: string | null
  period: string
  data: UsageTrendDataPoint[]
  velocity: VelocityMetrics
  metadata: {
    start_date: string
    end_date: string
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
const velocityMetrics = ref<VelocityMetrics | null>(null)

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

    const response = await api.get<UsageTrendsResponse>(
      `/api/v1/analytics/usage-trends?${params.toString()}`
    )

    const data = response.data
    velocityMetrics.value = data.velocity

    const chartData = chartHelpers.transformUsageTrends(data.data)

    // Wait for next tick to ensure canvas ref is populated
    await nextTick()

    createChart({
      type: 'bar',
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
    console.error('Failed to fetch usage trends:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load usage trend data'
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
