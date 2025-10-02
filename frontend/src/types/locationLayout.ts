/**
 * TypeScript type definitions for Location Layout Generator
 * Matches backend Pydantic schemas from backend/src/api/storage.py
 */

export type LayoutType = 'single' | 'row' | 'grid' | 'grid_3d'

export type RangeType = 'letters' | 'numbers'

export type LocationType = 'bin' | 'drawer' | 'shelf' | 'box' | 'cabinet' | 'room' | 'building' | 'container'

export interface RangeSpecification {
  range_type: RangeType
  start: string | number
  end: string | number
  capitalize?: boolean
  zero_pad?: boolean
}

export interface LayoutConfiguration {
  layout_type: LayoutType
  prefix: string
  ranges: RangeSpecification[]
  separators: string[]
  parent_id?: string | null
  location_type: LocationType
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

export interface ParentLocationOption {
  label: string
  value: string
  type: LocationType
}
