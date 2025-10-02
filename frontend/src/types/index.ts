/**
 * Core TypeScript type definitions for PartsHub Frontend
 */

// Base API Response types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  total_pages: number
  limit: number
}

// Component Specifications and Custom Fields
export interface ComponentSpecifications {
  voltage?: string
  current?: string
  power?: string
  tolerance?: string
  temperature_coefficient?: string
  package_dimensions?: string
  operating_temperature?: string
  frequency_range?: string
  capacitance?: string
  resistance?: string
  inductance?: string
  [key: string]: string | number | boolean | undefined
}

export interface ComponentCustomFields {
  [key: string]: string | number | boolean | null | undefined
}

// Authentication types
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  username: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  must_change_password: boolean
  created_at: string
}

export interface ApiToken {
  id: string
  name: string
  description: string | null
  prefix: string
  is_active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
  token?: string // Only present when creating a new token
}

// Project types
export interface Project {
  id: string
  name: string
  description: string | null
  version: string | null
  status: string
  notes: string | null
  created_at: string
  updated_at: string
  component_count?: number
  total_cost?: number
}

export interface ProjectComponent {
  project_id: string
  component_id: string
  quantity_allocated: number
  quantity_used: number
  quantity_reserved: number
  notes: string | null
  designator: string | null
  unit_cost_at_allocation: number | null
  allocated_at: string
  updated_at: string
  component_name: string | null
  component_part_number: string | null
}

export interface ProjectStatistics {
  total_components: number
  allocated_components: number
  total_cost: number
  completion_percentage: number
}

// Barcode Scanner types
export interface BarcodeResult {
  text: string
  format: string
  confidence?: number
}

export interface ScannerConstraints {
  video: {
    width?: { ideal: number }
    height?: { ideal: number }
    facingMode?: string
    frameRate?: { ideal: number }
  }
}

// Browser API types
declare global {
  interface Window {
    BarcodeDetector?: {
      new (options?: { formats: string[] }): BarcodeDetector
    }
  }
}

export interface BarcodeDetector {
  detect(source: HTMLVideoElement | HTMLCanvasElement | ImageData): Promise<{
    rawValue: string
    format: string
    cornerPoints: Array<{ x: number; y: number }>
  }[]>
}

// Form and UI types
export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

export interface TableColumn {
  name: string
  label: string
  field: string | ((row: unknown) => unknown)
  required?: boolean
  align?: 'left' | 'right' | 'center'
  sortable?: boolean
  style?: string
  classes?: string
  headerStyle?: string
  headerClasses?: string
}

// Storage Location types (extending what's already in api.ts)
export interface StorageLocationCreateData {
  name: string
  description?: string
  type: string
  parent_name?: string
  qr_code_id?: string
}

// Component allocation types
export interface ComponentAllocation {
  component_id: string
  quantity: number
  notes?: string
  designator?: string
}

// Export all types from api.ts as well
export type {
  Component,
  ComponentsListResponse,
  StorageLocation,
  Tag,
  TagsListResponse,
  StockTransaction,
  ComponentFilters
} from '../services/api'