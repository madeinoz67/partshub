/**
 * Location Layout Service
 * API client for storage location layout generation
 */

import api from './api'

export interface RangeSpecification {
  range_type: 'letters' | 'numbers'
  start: string | number
  end: string | number
  capitalize?: boolean
  zero_pad?: boolean
}

export interface LayoutConfiguration {
  layout_type: 'single' | 'row' | 'grid' | 'grid_3d'
  prefix: string
  ranges: RangeSpecification[]
  separators: string[]
  parent_id?: string | null
  location_type: string
  single_part_only: boolean
}

export interface PreviewResponse {
  sample_names: string[]
  last_name: string
  total_count: number
  warnings: string[]
  errors: string[]
  is_valid: boolean
}

export interface BulkCreateResponse {
  created_ids: string[]
  created_count: number
  success: boolean
  errors: string[] | null
}

export const locationLayoutService = {
  /**
   * Generate a preview of locations based on layout configuration
   * @param config Layout configuration
   * @returns Preview response with sample names, count, and validation
   */
  async generatePreview(config: LayoutConfiguration): Promise<PreviewResponse> {
    const response = await api.post('/api/v1/storage-locations/generate-preview', config)
    return response.data
  },

  /**
   * Bulk create storage locations from layout configuration
   * @param config Layout configuration
   * @returns Bulk create response with created IDs and count
   */
  async bulkCreate(config: LayoutConfiguration): Promise<BulkCreateResponse> {
    const response = await api.post('/api/v1/storage-locations/bulk-create-layout', config)
    return response.data
  }
}
