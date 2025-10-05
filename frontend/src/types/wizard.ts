/**
 * Type definitions for Component Creation Wizard
 */

// Provider types
export interface Provider {
  id: number
  name: string
  base_url: string
  api_key_configured: boolean
  is_active: boolean
  last_sync_at: string | null
  created_at: string
}

// Provider part search result
export interface ProviderPart {
  part_number: string
  name: string
  manufacturer: string | null
  description: string | null
  datasheet_url: string | null
  image_url: string | null
  lifecycle_status: string | null
  match_score?: number
  available_resources?: {
    datasheets: number
    images: number
    footprints: number
    symbols: number
    models_3d: number
  }
}

export interface ProviderSearchResponse {
  results: ProviderPart[]
  total: number
}

// Manufacturer suggestion
export interface ManufacturerSuggestion {
  id: number
  name: string
  score?: number
  component_count?: number
}

// Footprint suggestion
export interface FootprintSuggestion {
  id: number
  name: string
  score?: number
  component_count?: number
}

// Resource selection
export interface ResourceSelection {
  type: 'datasheet' | 'image' | 'footprint' | 'symbol' | '3d_model'
  url?: string
  file_name?: string
  selected: boolean
  required?: boolean // datasheets are required
}

// Resource status (for async tracking)
export interface ResourceStatus {
  id: number
  type: string
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  url: string | null
  file_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

// Provider link for component creation
export interface ProviderLinkCreate {
  provider_id: number
  part_number: string
  part_url: string
  metadata?: Record<string, unknown> | null
}

// Component creation request
export interface CreateComponentRequest {
  part_type: 'linked' | 'local'
  name?: string
  description?: string

  // For linked parts
  provider_link?: ProviderLinkCreate

  // For local parts
  manufacturer_id?: number
  manufacturer_name?: string // For creating new manufacturer
  footprint_id?: number
  footprint_name?: string // For creating new footprint

  // Resource selection
  resources?: Array<{
    type: string
    url?: string
    file_name?: string
  }>

  // Post-creation action
  post_action?: 'view' | 'add_stock' | 'continue'
}

// Component response (from API)
export interface Component {
  id: number
  name: string
  description: string | null
  part_number: string | null
  manufacturer: string | null
  manufacturer_id: number | null
  footprint: string | null
  footprint_id: number | null
  quantity_on_hand: number
  storage_location_id: number | null
  created_at: string
  updated_at: string
  provider_link?: {
    id: number
    provider_id: number
    provider_part_number: string
    last_sync_at: string | null
  }
}

// Wizard state types
export type PartType = 'linked' | 'local' | null
export type PostAction = 'view' | 'add_stock' | 'continue' | null
export type WizardStep = 1 | 2 | 3 | 4 | 5

// Form validation types
export interface ValidationRule {
  (value: string | number | null | undefined): boolean | string
}

export interface NameValidationRules {
  required: ValidationRule
  maxLength: ValidationRule
  validCharacters: ValidationRule
}
