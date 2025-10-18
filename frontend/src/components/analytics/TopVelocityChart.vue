<template>
  <q-card>
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Top Velocity Components</div>
        <div class="row items-center q-gutter-sm">
          <q-select
            v-model="selectedPeriod"
            :options="periodOptions"
            option-value="days"
            option-label="label"
            dense
            outlined
            style="min-width: 120px"
            @update:model-value="fetchData"
          />
        </div>
      </div>

      <div v-if="periodAnalyzed && !loading" class="text-caption text-grey-7 q-mb-md">
        {{ periodAnalyzed }}
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
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useChart } from '../../composables/useChart'
import { api } from '../../boot/axios'

interface VelocityComponent {
  component_id: string
  component_name: string
  part_number: string | null
  daily_velocity: number
  weekly_velocity: number
  monthly_velocity: number
  current_quantity: number
  days_until_stockout: number | null
  location_name: string | null
}

interface TopVelocityResponse {
  components: VelocityComponent[]
  period_analyzed: string
  total_components_analyzed: number
  metadata: Record<string, unknown>
}

interface PeriodOption {
  label: string
  days: number
}

const chartCanvas = ref<HTMLCanvasElement>()
const { createChart } = useChart(chartCanvas)
const loading = ref(false)
const error = ref<string | null>(null)
const periodAnalyzed = ref<string>('')

const periodOptions: PeriodOption[] = [
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 }
]

const selectedPeriod = ref<PeriodOption>(periodOptions[1]) // Default to 30 days

function getBarColor(daysUntilStockout: number | null): string {
  if (daysUntilStockout === null) return '#2196f3' // Blue - no urgency
  if (daysUntilStockout <= 7) return '#f44336' // Red - critical
  if (daysUntilStockout <= 14) return '#ff9800' // Orange - warning
  return '#2196f3' // Blue - OK
}

async function fetchData() {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      limit: '10',
      lookback_days: selectedPeriod.value.days.toString(),
      min_transactions: '2'
    })

    const response = await api.get<TopVelocityResponse>(
      `/api/v1/analytics/top-velocity?${params.toString()}`
    )

    const data = response.data
    periodAnalyzed.value = data.period_analyzed

    // Transform data for Chart.js
    const labels = data.components.map(c => c.component_name)
    const velocities = data.components.map(c => c.daily_velocity)
    const colors = data.components.map(c => getBarColor(c.days_until_stockout))

    const chartData = {
      labels,
      datasets: [{
        label: 'Daily Velocity (units/day)',
        data: velocities,
        backgroundColor: colors,
        borderWidth: 1,
        borderColor: colors.map(color => {
          // Darken the color for border
          return color.replace(')', ', 0.8)')
        })
      }]
    }

    // Wait for next tick to ensure canvas ref is populated
    await nextTick()

    createChart({
      type: 'bar',
      data: chartData,
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              title: (context) => {
                const index = context[0].dataIndex
                const component = data.components[index]
                return component.component_name
              },
              afterTitle: (context) => {
                const index = context[0].dataIndex
                const component = data.components[index]
                return component.part_number ? `Part #: ${component.part_number}` : ''
              },
              label: (context) => {
                const index = context.dataIndex
                const component = data.components[index]
                return [
                  `Daily velocity: ${component.daily_velocity.toFixed(2)} units/day`,
                  `Current stock: ${component.current_quantity} units`,
                  component.days_until_stockout !== null
                    ? `Days until stockout: ${component.days_until_stockout}`
                    : 'Stockout: Not projected',
                  component.location_name ? `Location: ${component.location_name}` : ''
                ].filter(Boolean)
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Daily Velocity (units/day)'
            },
            grid: {
              display: true
            }
          },
          y: {
            grid: {
              display: false
            }
          }
        }
      }
    })
  } catch (err: unknown) {
    console.error('Failed to fetch top velocity data:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load top velocity data'
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
  height: 400px;
  width: 100%;
}
</style>
