/**
 * TypeScript interfaces for ComponentList.vue
 * Comprehensive type definitions for component management
 */

// Base interfaces for component data structures
export interface ComponentAttachment {
  id: string
  filename: string
  content_type: string
  file_size: number
  upload_date: string
  description?: string
  url?: string
}

export interface StorageLocation {
  id: string
  name: string
  location_hierarchy: string
  description?: string
  capacity?: number
  current_usage?: number
}

export interface ComponentCategory {
  id: string
  name: string
  description?: string
  parent_category_id?: string
}

export interface ComponentManufacturer {
  id: string
  name: string
  website?: string
  contact_info?: string
}

export interface ComponentDatasheet {
  id: string
  filename: string
  url: string
  version?: string
  language?: string
}

export interface ComponentSpecification {
  [key: string]: string | number | boolean | null
  // Common specifications
  voltage_rating?: number
  current_rating?: number
  power_rating?: number
  tolerance?: string
  temperature_range?: string
  package_type?: string
  mounting_type?: string
}

export interface ComponentPricing {
  id: string
  supplier: string
  part_number: string
  price_per_unit: number
  minimum_quantity: number
  lead_time_days?: number
  currency: string
  last_updated: string
}

export interface ComponentStock {
  quantity_on_hand: number
  minimum_stock: number
  reserved_quantity?: number
  available_quantity: number
  last_counted?: string
  cost_per_unit?: number
}

// Main component interface
export interface Component {
  id: string
  name: string
  part_number: string
  description?: string
  manufacturer: ComponentManufacturer
  category: ComponentCategory
  storage_location: StorageLocation
  stock: ComponentStock
  specifications: ComponentSpecification
  attachments: ComponentAttachment[]
  datasheets: ComponentDatasheet[]
  pricing: ComponentPricing[]
  created_at: string
  updated_at: string
  tags?: string[]
  notes?: string
  status: 'active' | 'discontinued' | 'obsolete'
}

// Quasar table column definitions with proper typing
export interface QuasarTableColumn {
  name: string
  label: string
  field: string | ((row: Component) => unknown)
  required?: boolean
  align?: 'left' | 'right' | 'center'
  sortable?: boolean
  sort?: (a: unknown, b: unknown, rowA: Component, rowB: Component) => number
  sortOrder?: 'ad' | 'da'
  format?: (val: unknown, row: Component) => string
  style?: string | ((row: Component) => string)
  classes?: string | ((row: Component) => string)
  headerStyle?: string
  headerClasses?: string
}

// Search and filter interfaces
export interface ComponentSearchFilters {
  category_id?: string
  manufacturer_id?: string
  storage_location_id?: string
  status?: Component['status']
  in_stock?: boolean
  low_stock?: boolean
  has_datasheets?: boolean
  tags?: string[]
  specifications?: Record<string, string | number | boolean>
}

export interface ComponentSearchOptions {
  query?: string
  filters: ComponentSearchFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  per_page?: number
}

// API response interfaces
export interface ComponentListResponse {
  components: Component[]
  total_count: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface ComponentStatsResponse {
  total_components: number
  total_value: number
  low_stock_count: number
  categories_count: number
  manufacturers_count: number
  locations_count: number
}

// Component operations interfaces
export interface ComponentUpdateData {
  name?: string
  part_number?: string
  description?: string
  manufacturer_id?: string
  category_id?: string
  storage_location_id?: string
  specifications?: ComponentSpecification
  minimum_stock?: number
  notes?: string
  tags?: string[]
  status?: Component['status']
}

export interface ComponentCreateData extends Omit<ComponentUpdateData, 'status'> {
  name: string
  part_number: string
  manufacturer_id: string
  category_id: string
  storage_location_id: string
  initial_quantity?: number
  cost_per_unit?: number
}

// Bulk operation interfaces
export interface BulkOperationResult {
  success_count: number
  error_count: number
  errors: Array<{
    component_id: string
    error_message: string
  }>
}

export interface BulkUpdateData {
  component_ids: string[]
  updates: ComponentUpdateData
}

export interface BulkDeleteData {
  component_ids: string[]
  confirm: boolean
}

// Export/Import interfaces
export interface ComponentExportOptions {
  format: 'csv' | 'xlsx' | 'json'
  include_attachments: boolean
  include_pricing: boolean
  filters?: ComponentSearchFilters
}

export interface ComponentImportResult {
  imported_count: number
  error_count: number
  warnings: string[]
  errors: Array<{
    row: number
    message: string
  }>
}

// UI State interfaces
export interface ComponentListState {
  loading: boolean
  error: string | null
  selected_components: string[]
  active_tab: Record<string, string>
  search_query: string
  filters: ComponentSearchFilters
  sort_field: string
  sort_order: 'asc' | 'desc'
  page: number
  per_page: number
}

// Event interfaces for component operations
export interface ComponentEvent {
  type: 'create' | 'update' | 'delete' | 'stock_change'
  component_id: string
  timestamp: string
  user_id?: string
  changes?: Record<string, unknown>
  previous_values?: Record<string, unknown>
}

// Component validation interfaces
export interface ComponentValidationError {
  field: string
  message: string
  code: string
}

export interface ComponentValidationResult {
  is_valid: boolean
  errors: ComponentValidationError[]
  warnings: ComponentValidationError[]
}

// Advanced search interfaces
export interface AdvancedSearchCriteria {
  name_contains?: string
  part_number_contains?: string
  description_contains?: string
  manufacturer_name?: string
  category_name?: string
  location_name?: string
  specification_matches?: Record<string, string | number | boolean>
  created_after?: string
  created_before?: string
  updated_after?: string
  updated_before?: string
  quantity_min?: number
  quantity_max?: number
  value_min?: number
  value_max?: number
}

// Component relationships
export interface ComponentRelationship {
  id: string
  related_component_id: string
  relationship_type: 'alternative' | 'replacement' | 'compatible' | 'accessory'
  description?: string
  created_at: string
}

// Extended component interface with relationships
export interface ComponentWithRelationships extends Component {
  relationships: ComponentRelationship[]
  alternative_components: Component[]
  replacement_components: Component[]
  compatible_components: Component[]
  accessories: Component[]
}