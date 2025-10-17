<template>
  <q-card>
    <q-card-section>
      <div class="text-h6 q-mb-md">Stock Forecast</div>

      <q-spinner v-if="loading" color="primary" size="50px" class="absolute-center" />

      <q-banner v-else-if="error" class="bg-negative text-white">
        <template #avatar>
          <q-icon name="error" />
        </template>
        {{ error }}
      </q-banner>

      <div v-else>
        <div class="chart-container">
          <canvas ref="chartCanvas"></canvas>
        </div>

        <q-card
          v-if="reorderSuggestion?.should_reorder"
          flat
          bordered
          class="q-mt-md bg-warning text-white"
        >
          <q-card-section class="q-pa-md">
            <div class="row items-center q-gutter-md">
              <q-icon name="warning" size="md" />
              <div class="col">
                <div class="text-subtitle1 text-weight-bold">Reorder Recommended</div>
                <div class="text-body2">
                  <div>Suggested Order: {{ reorderSuggestion.suggested_quantity }} units</div>
                  <div>Order By: {{ formatDate(reorderSuggestion.suggested_date) }}</div>
                  <div>
                    Estimated Stockout: {{ formatDate(reorderSuggestion.estimated_stockout_date) }}
                    ({{ reorderSuggestion.days_until_stockout }} days)
                  </div>
                  <div class="text-caption q-mt-xs">
                    Confidence: {{ (reorderSuggestion.confidence_level * 100).toFixed(0) }}%
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
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
  horizon?: '7d' | '14d' | '30d' | '90d'
  lookbackDays?: number
}

interface ForecastDataPoint {
  timestamp: string
  predicted_quantity: number
  confidence_level: number
  will_trigger_reorder: boolean
}

interface ReorderSuggestion {
  should_reorder: boolean
  suggested_date: string | null
  suggested_quantity: number | null
  estimated_stockout_date: string | null
  days_until_stockout: number | null
  confidence_level: number
}

interface StockDataPoint {
  timestamp: string
  quantity: number
}

interface ForecastResponse {
  component_id: string
  component_name: string
  location_id: string | null
  location_name: string | null
  current_quantity: number
  reorder_threshold: number | null
  forecast_horizon: string
  lookback_days: number
  data: ForecastDataPoint[]
  reorder_suggestion: ReorderSuggestion
  metadata: {
    algorithm: string
    daily_velocity: number
    notes: string
    historical_data?: StockDataPoint[]
  }
}

const props = withDefaults(defineProps<Props>(), {
  locationId: null,
  horizon: '14d',
  lookbackDays: 30
})

const chartCanvas = ref<HTMLCanvasElement>()
const { createChart } = useChart(chartCanvas)
const loading = ref(false)
const error = ref<string | null>(null)
const reorderSuggestion = ref<ReorderSuggestion | null>(null)

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      component_id: props.componentId,
      horizon: props.horizon,
      lookback_days: props.lookbackDays.toString()
    })

    if (props.locationId) {
      params.append('location_id', props.locationId)
    }

    const response = await api.get<ForecastResponse>(
      `/api/v1/analytics/forecast?${params.toString()}`
    )

    const data = response.data
    reorderSuggestion.value = data.reorder_suggestion

    const historical = data.metadata.historical_data || []
    const chartData = chartHelpers.transformForecast(
      historical,
      data.data,
      data.reorder_threshold || undefined
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
                const datasetIndex = item.datasetIndex

                if (datasetIndex === 1) {
                  const forecastIndex = item.dataIndex - historical.length
                  if (forecastIndex >= 0 && data.data[forecastIndex]) {
                    const point = data.data[forecastIndex]
                    return `Confidence: ${(point.confidence_level * 100).toFixed(0)}%`
                  }
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
    console.error('Failed to fetch forecast:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load forecast data'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Wait for canvas to be available
  await nextTick()
  if (chartCanvas.value) {
    await fetchData()
  }
})

watch(
  () => [props.componentId, props.locationId, props.horizon, props.lookbackDays],
  async () => {
    await nextTick()
    if (chartCanvas.value) {
      await fetchData()
    }
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
