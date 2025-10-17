/**
 * Chart.js composable for Vue 3 Composition API
 * Provides lifecycle management and reactive updates for Chart.js charts
 */

import { ref, Ref, onUnmounted, watch, ShallowRef, shallowRef } from 'vue'
import {
  Chart,
  ChartConfiguration,
  ChartType,
  ChartData,
  ChartOptions,
  DefaultDataPoint,
  registerables
} from 'chart.js'

// Register all Chart.js components
Chart.register(...registerables)

/**
 * Chart instance type with proper typing
 */
export type ChartInstance = Chart<ChartType, DefaultDataPoint<ChartType>, unknown>

/**
 * Configuration for creating a chart
 */
export interface ChartConfig<
  TType extends ChartType = ChartType,
  TData = DefaultDataPoint<TType>,
  TLabel = unknown
> {
  type: TType
  data: ChartData<TType, TData, TLabel>
  options?: ChartOptions<TType>
}

/**
 * Return type for useChart composable
 */
export interface UseChartReturn {
  chart: ShallowRef<ChartInstance | null>
  createChart: <TType extends ChartType = ChartType>(
    config: ChartConfig<TType>
  ) => ChartInstance | null
  updateChartData: <TType extends ChartType = ChartType>(
    newData: ChartData<TType>
  ) => void
  updateChartOptions: <TType extends ChartType = ChartType>(
    newOptions: ChartOptions<TType>
  ) => void
  destroyChart: () => void
  isReady: Ref<boolean>
}

/**
 * Utility functions for transforming API data to Chart.js format
 */
export const chartHelpers = {
  /**
   * Format date for chart labels
   * @param dateString ISO 8601 date string
   * @param format 'short' | 'long' | 'time'
   */
  formatDate(dateString: string, format: 'short' | 'long' | 'time' = 'short'): string {
    const date = new Date(dateString)

    switch (format) {
      case 'short':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      case 'long':
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        })
      case 'time':
        return date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
      default:
        return dateString
    }
  },

  /**
   * Color scheme utilities for consistent chart styling
   */
  colors: {
    primary: 'rgb(59, 130, 246)',
    success: 'rgb(34, 197, 94)',
    warning: 'rgb(251, 146, 60)',
    danger: 'rgb(239, 68, 68)',
    info: 'rgb(168, 85, 247)',
    neutral: 'rgb(156, 163, 175)',

    // Alpha variants for backgrounds
    primaryAlpha: 'rgba(59, 130, 246, 0.5)',
    successAlpha: 'rgba(34, 197, 94, 0.5)',
    warningAlpha: 'rgba(251, 146, 60, 0.5)',
    dangerAlpha: 'rgba(239, 68, 68, 0.5)',
    infoAlpha: 'rgba(168, 85, 247, 0.5)',
    neutralAlpha: 'rgba(156, 163, 175, 0.5)',
  },

  /**
   * Generate default chart options with responsive settings
   */
  getDefaultOptions<TType extends ChartType = ChartType>(
    overrides?: ChartOptions<TType>
  ): ChartOptions<TType> {
    return {
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
      interaction: {
        mode: 'nearest' as const,
        axis: 'x' as const,
        intersect: false,
      },
      ...overrides,
    } as ChartOptions<TType>
  },

  /**
   * Transform stock level data to Chart.js format
   */
  transformStockLevels(
    data: Array<{ timestamp: string; quantity: number }>,
    reorderThreshold?: number
  ): ChartData<'line'> {
    const labels = data.map(d => this.formatDate(d.timestamp))

    const datasets: ChartData<'line'>['datasets'] = [
      {
        label: 'Stock Level',
        data: data.map(d => d.quantity),
        borderColor: this.colors.primary,
        backgroundColor: this.colors.primaryAlpha,
        tension: 0.1,
        fill: false,
      },
    ]

    // Add reorder threshold line if provided
    if (reorderThreshold !== undefined) {
      datasets.push({
        label: 'Reorder Threshold',
        data: new Array(data.length).fill(reorderThreshold),
        borderColor: this.colors.warning,
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      })
    }

    return { labels, datasets }
  },

  /**
   * Transform usage trends data to Chart.js format
   */
  transformUsageTrends(
    data: Array<{ timestamp: string; added: number; removed: number }>
  ): ChartData<'bar'> {
    return {
      labels: data.map(d => this.formatDate(d.timestamp)),
      datasets: [
        {
          label: 'Added',
          data: data.map(d => d.added),
          backgroundColor: this.colors.successAlpha,
          borderColor: this.colors.success,
          borderWidth: 1,
        },
        {
          label: 'Removed',
          data: data.map(d => d.removed),
          backgroundColor: this.colors.dangerAlpha,
          borderColor: this.colors.danger,
          borderWidth: 1,
        },
      ],
    }
  },

  /**
   * Transform forecast data to Chart.js format with confidence bands
   */
  transformForecast(
    historical: Array<{ timestamp: string; quantity: number }>,
    forecast: Array<{
      timestamp: string
      predicted_quantity: number
      confidence_level: number
    }>,
    reorderThreshold?: number
  ): ChartData<'line'> {
    const allLabels = [
      ...historical.map(d => this.formatDate(d.timestamp)),
      ...forecast.map(d => this.formatDate(d.timestamp)),
    ]

    const datasets: ChartData<'line'>['datasets'] = [
      {
        label: 'Historical',
        data: [
          ...historical.map(d => d.quantity),
          ...new Array(forecast.length).fill(null),
        ],
        borderColor: this.colors.primary,
        backgroundColor: this.colors.primaryAlpha,
        tension: 0.1,
        fill: false,
      },
      {
        label: 'Forecast',
        data: [
          ...new Array(historical.length).fill(null),
          ...forecast.map(d => d.predicted_quantity),
        ],
        borderColor: this.colors.info,
        backgroundColor: this.colors.infoAlpha,
        borderDash: [5, 5],
        tension: 0.1,
        fill: false,
      },
    ]

    // Add reorder threshold line if provided
    if (reorderThreshold !== undefined) {
      datasets.push({
        label: 'Reorder Threshold',
        data: new Array(allLabels.length).fill(reorderThreshold),
        borderColor: this.colors.warning,
        borderDash: [10, 5],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      })
    }

    return { labels: allLabels, datasets }
  },
}

/**
 * Vue 3 Composable for Chart.js integration
 *
 * @param canvasRef - Ref to the canvas element
 * @returns Chart instance and control methods
 *
 * @example
 * ```vue
 * <script setup lang="ts">
 * import { ref, onMounted } from 'vue'
 * import { useChart } from 'src/composables/useChart'
 *
 * const chartCanvas = ref<HTMLCanvasElement>()
 * const { createChart, updateChartData } = useChart(chartCanvas)
 *
 * onMounted(() => {
 *   createChart({
 *     type: 'line',
 *     data: {
 *       labels: ['Jan', 'Feb', 'Mar'],
 *       datasets: [{ label: 'Sales', data: [10, 20, 30] }]
 *     }
 *   })
 * })
 * </script>
 *
 * <template>
 *   <canvas ref="chartCanvas"></canvas>
 * </template>
 * ```
 */
export function useChart(canvasRef: Ref<HTMLCanvasElement | undefined>): UseChartReturn {
  const chart = shallowRef<ChartInstance | null>(null)
  const isReady = ref(false)

  /**
   * Create a new Chart.js instance
   * @param config Chart configuration
   * @returns Chart instance or null if canvas not available
   */
  const createChart = <TType extends ChartType = ChartType>(
    config: ChartConfig<TType>
  ): ChartInstance | null => {
    if (!canvasRef.value) {
      console.warn('useChart: Canvas element not available')
      return null
    }

    // Destroy existing chart if any
    destroyChart()

    try {
      const ctx = canvasRef.value.getContext('2d')
      if (!ctx) {
        console.error('useChart: Could not get 2D context from canvas')
        return null
      }

      // Create chart configuration
      const chartConfig: ChartConfiguration<TType> = {
        type: config.type,
        data: config.data,
        options: config.options || chartHelpers.getDefaultOptions<TType>(),
      }

      // Create chart instance
      chart.value = new Chart(ctx, chartConfig) as ChartInstance
      isReady.value = true

      return chart.value
    } catch (error) {
      console.error('useChart: Failed to create chart', error)
      isReady.value = false
      return null
    }
  }

  /**
   * Update chart data without recreating the chart
   * @param newData New chart data
   */
  const updateChartData = <TType extends ChartType = ChartType>(
    newData: ChartData<TType>
  ): void => {
    if (!chart.value) {
      console.warn('useChart: No chart instance available to update')
      return
    }

    try {
      // Update labels if provided
      if (newData.labels) {
        chart.value.data.labels = newData.labels
      }

      // Update datasets
      if (newData.datasets) {
        chart.value.data.datasets = newData.datasets as ChartInstance['data']['datasets']
      }

      // Trigger chart update with animation
      chart.value.update()
    } catch (error) {
      console.error('useChart: Failed to update chart data', error)
    }
  }

  /**
   * Update chart options without recreating the chart
   * @param newOptions New chart options
   */
  const updateChartOptions = <TType extends ChartType = ChartType>(
    newOptions: ChartOptions<TType>
  ): void => {
    if (!chart.value) {
      console.warn('useChart: No chart instance available to update')
      return
    }

    try {
      // Merge new options with existing options
      chart.value.options = {
        ...chart.value.options,
        ...newOptions,
      } as ChartInstance['options']

      // Trigger chart update
      chart.value.update()
    } catch (error) {
      console.error('useChart: Failed to update chart options', error)
    }
  }

  /**
   * Destroy the chart instance and clean up resources
   */
  const destroyChart = (): void => {
    if (chart.value) {
      try {
        chart.value.destroy()
        chart.value = null
        isReady.value = false
      } catch (error) {
        console.error('useChart: Failed to destroy chart', error)
      }
    }
  }

  // Watch for canvas ref changes
  watch(canvasRef, (newCanvas, oldCanvas) => {
    if (oldCanvas && !newCanvas) {
      // Canvas was removed, destroy chart
      destroyChart()
    }
  })

  // Clean up on component unmount
  onUnmounted(() => {
    destroyChart()
  })

  return {
    chart,
    createChart,
    updateChartData,
    updateChartOptions,
    destroyChart,
    isReady,
  }
}
