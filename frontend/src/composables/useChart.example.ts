/**
 * Example usage of useChart composable
 * This file demonstrates how to use the useChart composable in Vue 3 components
 */

import { ref, onMounted } from 'vue'
import { useChart, chartHelpers } from './useChart'

/**
 * Example 1: Basic Line Chart for Stock Levels
 */
export function exampleStockLevelChart() {
  const chartCanvas = ref<HTMLCanvasElement>()
  const { createChart, updateChartData, isReady } = useChart(chartCanvas)

  onMounted(() => {
    // Sample data from analytics API
    const stockLevelData = [
      { timestamp: '2024-01-01T00:00:00Z', quantity: 100 },
      { timestamp: '2024-01-02T00:00:00Z', quantity: 95 },
      { timestamp: '2024-01-03T00:00:00Z', quantity: 88 },
      { timestamp: '2024-01-04T00:00:00Z', quantity: 92 },
      { timestamp: '2024-01-05T00:00:00Z', quantity: 87 },
    ]

    const reorderThreshold = 90

    // Transform API data to Chart.js format
    const chartData = chartHelpers.transformStockLevels(stockLevelData, reorderThreshold)

    // Create chart
    createChart({
      type: 'line',
      data: chartData,
      options: chartHelpers.getDefaultOptions({
        plugins: {
          title: {
            display: true,
            text: 'Stock Levels Over Time',
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Quantity',
            },
          },
        },
      }),
    })
  })

  // Function to update chart with new data (e.g., from polling)
  const refreshData = (newData: Array<{ timestamp: string; quantity: number }>) => {
    const chartData = chartHelpers.transformStockLevels(newData, 90)
    updateChartData(chartData)
  }

  return { chartCanvas, isReady, refreshData }
}

/**
 * Example 2: Bar Chart for Usage Trends
 */
export function exampleUsageTrendsChart() {
  const chartCanvas = ref<HTMLCanvasElement>()
  const { createChart } = useChart(chartCanvas)

  onMounted(() => {
    // Sample data from analytics API
    const usageTrendsData = [
      { timestamp: '2024-01-01T00:00:00Z', added: 50, removed: 30 },
      { timestamp: '2024-01-02T00:00:00Z', added: 20, removed: 45 },
      { timestamp: '2024-01-03T00:00:00Z', added: 30, removed: 25 },
      { timestamp: '2024-01-04T00:00:00Z', added: 40, removed: 35 },
      { timestamp: '2024-01-05T00:00:00Z', added: 25, removed: 40 },
    ]

    // Transform API data to Chart.js format
    const chartData = chartHelpers.transformUsageTrends(usageTrendsData)

    // Create chart
    createChart({
      type: 'bar',
      data: chartData,
      options: chartHelpers.getDefaultOptions({
        plugins: {
          title: {
            display: true,
            text: 'Stock Usage Trends',
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Units',
            },
          },
        },
      }),
    })
  })

  return { chartCanvas }
}

/**
 * Example 3: Forecast Line Chart with Historical Data
 */
export function exampleForecastChart() {
  const chartCanvas = ref<HTMLCanvasElement>()
  const { createChart } = useChart(chartCanvas)

  onMounted(() => {
    // Historical data
    const historical = [
      { timestamp: '2024-01-01T00:00:00Z', quantity: 100 },
      { timestamp: '2024-01-02T00:00:00Z', quantity: 95 },
      { timestamp: '2024-01-03T00:00:00Z', quantity: 88 },
      { timestamp: '2024-01-04T00:00:00Z', quantity: 92 },
      { timestamp: '2024-01-05T00:00:00Z', quantity: 87 },
    ]

    // Forecast data
    const forecast = [
      { timestamp: '2024-01-06T00:00:00Z', predicted_quantity: 82, confidence_level: 0.9 },
      { timestamp: '2024-01-07T00:00:00Z', predicted_quantity: 78, confidence_level: 0.85 },
      { timestamp: '2024-01-08T00:00:00Z', predicted_quantity: 74, confidence_level: 0.8 },
      { timestamp: '2024-01-09T00:00:00Z', predicted_quantity: 70, confidence_level: 0.75 },
    ]

    const reorderThreshold = 75

    // Transform API data to Chart.js format
    const chartData = chartHelpers.transformForecast(historical, forecast, reorderThreshold)

    // Create chart
    createChart({
      type: 'line',
      data: chartData,
      options: chartHelpers.getDefaultOptions({
        plugins: {
          title: {
            display: true,
            text: 'Stock Level Forecast',
          },
          tooltip: {
            callbacks: {
              footer: (tooltipItems) => {
                const index = tooltipItems[0].dataIndex
                if (index >= historical.length) {
                  const forecastIndex = index - historical.length
                  const confidence = forecast[forecastIndex]?.confidence_level
                  return confidence ? `Confidence: ${(confidence * 100).toFixed(0)}%` : ''
                }
                return ''
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Predicted Quantity',
            },
          },
        },
      }),
    })
  })

  return { chartCanvas }
}

/**
 * Example 4: Manual Chart Creation with Custom Configuration
 */
export function exampleCustomChart() {
  const chartCanvas = ref<HTMLCanvasElement>()
  const { createChart, updateChartData } = useChart(chartCanvas)

  onMounted(() => {
    // Create chart with custom configuration
    createChart({
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        datasets: [
          {
            label: 'Dataset 1',
            data: [10, 20, 30, 40, 50],
            borderColor: chartHelpers.colors.primary,
            backgroundColor: chartHelpers.colors.primaryAlpha,
          },
          {
            label: 'Dataset 2',
            data: [15, 25, 35, 45, 55],
            borderColor: chartHelpers.colors.success,
            backgroundColor: chartHelpers.colors.successAlpha,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
          },
        },
      },
    })
  })

  // Update chart data dynamically
  const updateData = () => {
    updateChartData({
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
      datasets: [
        {
          label: 'Updated Dataset',
          data: [Math.random() * 100, Math.random() * 100, Math.random() * 100],
          borderColor: chartHelpers.colors.info,
          backgroundColor: chartHelpers.colors.infoAlpha,
        },
      ],
    })
  }

  return { chartCanvas, updateData }
}

/**
 * Vue SFC Template Example
 *
 * <template>
 *   <q-card>
 *     <q-card-section>
 *       <div class="text-h6">Stock Level Chart</div>
 *     </q-card-section>
 *     <q-card-section>
 *       <div style="height: 400px; position: relative;">
 *         <canvas ref="chartCanvas"></canvas>
 *       </div>
 *     </q-card-section>
 *     <q-card-actions>
 *       <q-btn
 *         flat
 *         label="Refresh Data"
 *         @click="refreshData"
 *         :disable="!isReady"
 *       />
 *     </q-card-actions>
 *   </q-card>
 * </template>
 *
 * <script setup lang="ts">
 * import { ref, onMounted } from 'vue'
 * import { useChart, chartHelpers } from 'src/composables/useChart'
 * import { api } from 'src/services/api'
 *
 * const chartCanvas = ref<HTMLCanvasElement>()
 * const { createChart, updateChartData, isReady } = useChart(chartCanvas)
 *
 * // Fetch data from API
 * const fetchStockLevels = async () => {
 *   const response = await api.get('/analytics/stock-levels', {
 *     params: {
 *       component_id: 'some-uuid',
 *       start_date: '2024-01-01',
 *       end_date: '2024-01-31',
 *       aggregation_period: 'daily'
 *     }
 *   })
 *   return response.data
 * }
 *
 * onMounted(async () => {
 *   const data = await fetchStockLevels()
 *   const chartData = chartHelpers.transformStockLevels(
 *     data.data,
 *     data.metadata.reorder_threshold
 *   )
 *
 *   createChart({
 *     type: 'line',
 *     data: chartData,
 *     options: chartHelpers.getDefaultOptions()
 *   })
 * })
 *
 * const refreshData = async () => {
 *   const data = await fetchStockLevels()
 *   const chartData = chartHelpers.transformStockLevels(
 *     data.data,
 *     data.metadata.reorder_threshold
 *   )
 *   updateChartData(chartData)
 * }
 * </script>
 */
