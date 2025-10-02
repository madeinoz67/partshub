/**
 * Pinia store for Location Layout Generator
 *
 * Manages the state and actions for generating storage locations
 * in bulk using configurable layouts (row, grid, 3D grid).
 *
 * Features:
 * - Real-time layout preview generation
 * - Debounced preview updates
 * - Configuration tracking
 * - Bulk location creation
 * - Error and warning management
 *
 * Usage:
 * const locationStore = useLocationGenerationStore()
 * locationStore.updateConfig({ prefix: 'shelf-', layout_type: 'grid' })
 * const preview = await locationStore.fetchPreview()
 * const createdLocations = await locationStore.createLocations()
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { locationGenerationService } from '../services/locationGenerationService'
import type {
  LayoutConfiguration,
  PreviewResponse,
  BulkCreateResponse
} from '../types/locationLayout'

// Debounce helper function
function debounce<T extends (...args: never[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export const useLocationGenerationStore = defineStore('locationGeneration', () => {
  // State
  const currentConfig = ref<LayoutConfiguration>({
    layout_type: 'row',
    prefix: '',
    ranges: [],
    separators: [],
    parent_id: null,
    location_type: 'bin',
    single_part_only: false
  })

  const previewData = ref<PreviewResponse | null>(null)
  const isLoadingPreview = ref(false)
  const isCreating = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isValid = computed(() => {
    return previewData.value?.is_valid ?? false
  })

  const totalCount = computed(() => {
    return previewData.value?.total_count ?? 0
  })

  const hasWarnings = computed(() => {
    return (previewData.value?.warnings?.length ?? 0) > 0
  })

  const hasErrors = computed(() => {
    return (previewData.value?.errors?.length ?? 0) > 0
  })

  // Actions
  const updateConfig = (config: Partial<LayoutConfiguration>) => {
    currentConfig.value = {
      ...currentConfig.value,
      ...config
    }
    // Trigger debounced preview fetch
    debouncedFetchPreview()
  }

  const fetchPreview = async () => {
    isLoadingPreview.value = true
    error.value = null

    try {
      previewData.value = await locationGenerationService.generatePreview(
        currentConfig.value
      )
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Failed to generate preview'
      error.value = errorMessage
      console.error('Error generating preview:', err)

      // Set preview data to invalid state
      previewData.value = {
        sample_names: [],
        last_name: '',
        total_count: 0,
        warnings: [],
        errors: [errorMessage],
        is_valid: false
      }
    } finally {
      isLoadingPreview.value = false
    }
  }

  // Debounced version of fetchPreview (300ms delay)
  const debouncedFetchPreview = debounce(fetchPreview, 300)

  const createLocations = async (): Promise<BulkCreateResponse> => {
    isCreating.value = true
    error.value = null

    try {
      const response = await locationGenerationService.bulkCreateLocations(
        currentConfig.value
      )

      if (!response.success) {
        throw new Error(response.errors?.join(', ') || 'Creation failed')
      }

      return response
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create locations'
      error.value = errorMessage
      console.error('Error creating locations:', err)
      throw err
    } finally {
      isCreating.value = false
    }
  }

  const resetState = () => {
    currentConfig.value = {
      layout_type: 'row',
      prefix: '',
      ranges: [],
      separators: [],
      parent_id: null,
      location_type: 'bin',
      single_part_only: false
    }
    previewData.value = null
    isLoadingPreview.value = false
    isCreating.value = false
    error.value = null
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    currentConfig,
    previewData,
    isLoadingPreview,
    isCreating,
    error,

    // Getters
    isValid,
    totalCount,
    hasWarnings,
    hasErrors,

    // Actions
    updateConfig,
    fetchPreview,
    createLocations,
    resetState,
    clearError
  }
})
