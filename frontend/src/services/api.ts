/**
 * API Service for PartsHub - handles all backend communication
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth tokens (when implemented)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Clear token if it exists
      const hadToken = localStorage.getItem('auth_token')
      localStorage.removeItem('auth_token')

      // Only redirect to login if the user had a token (was authenticated)
      // Anonymous users browsing should not be automatically redirected
      if (hadToken && typeof window !== 'undefined') {
        // Use window.location for redirect since we're outside Vue's setup context
        // This is more reliable than trying to use Vue Router in an interceptor
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Type definitions
export interface Component {
  id: string
  name: string
  part_number: string | null // Legacy field maintained for backward compatibility
  local_part_id: string | null // User-friendly local identifier
  barcode_id: string | null // Auto-generated barcode/QR code ID
  manufacturer_part_number: string | null // Official manufacturer part number
  provider_sku: string | null // Provider-specific SKU
  manufacturer: string | null
  category_id: string | null
  storage_location_id: string | null
  component_type: string | null
  value: string | null
  package: string | null
  quantity_on_hand: number
  quantity_ordered: number
  minimum_stock: number
  average_purchase_price: number | null
  total_purchase_value: number | null
  notes: string | null
  specifications: Record<string, string | number | boolean> | null
  custom_fields: Record<string, string | number | boolean | null> | null
  category: { id: string; name: string } | null
  storage_location: {
    id: string
    name: string
    location_hierarchy: string
  } | null
  tags: Array<{ id: string; name: string }>
  attachments: Array<{ id: string; filename: string }>
  created_at: string
  updated_at: string
}

export interface ComponentsListResponse {
  components: Component[]
  total: number
  page: number
  total_pages: number
  limit: number
}

export interface StorageLocation {
  id: string
  name: string
  description: string | null
  type: string
  parent_id: string | null
  location_hierarchy: string
  qr_code_id: string | null
  created_at: string
  updated_at: string
  last_used_at: string | null
  children?: StorageLocation[]
  component_count?: number
  full_hierarchy_path?: Array<{ id: string; name: string }>
  layout_config?: {
    layout_type: string
    prefix?: string
    ranges?: Array<{
      type: string
      start: string
      end: string
      capitalize?: boolean
      zero_pad?: boolean
    }>
    separators?: string[]
  }
}

export interface Tag {
  id: string
  name: string
  description: string | null
  color: string | null
  is_system_tag: boolean
  component_count: number
  created_at: string
  updated_at: string
}

export interface TagsListResponse {
  tags: Tag[]
  total: number
}

export interface StockTransaction {
  id: string
  component_id: string
  transaction_type: 'add' | 'remove' | 'move' | 'adjust'
  quantity_change: number
  previous_quantity: number
  new_quantity: number
  reason: string
  reference_id: string | null
  created_at: string
}

export interface ComponentFilters {
  search?: string
  category?: string
  storage_location?: string
  component_type?: string
  stock_status?: 'low' | 'out' | 'available'
  sort_by?: 'name' | 'quantity' | 'created_at'
  sort_order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

// API Service Class
export class APIService {
  // Components API
  static async getComponents(filters: ComponentFilters = {}): Promise<ComponentsListResponse> {
    const params = new URLSearchParams()

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/v1/components?${params}`)
    return response.data
  }

  static async getComponent(id: string): Promise<Component> {
    const response = await api.get(`/api/v1/components/${id}`)
    return response.data
  }

  static async createComponent(data: Partial<Component>): Promise<Component> {
    const response = await api.post('/api/v1/components', data)
    return response.data
  }

  static async updateComponent(id: string, data: Partial<Component>): Promise<Component> {
    const response = await api.put(`/api/v1/components/${id}`, data)
    return response.data
  }

  static async deleteComponent(id: string): Promise<void> {
    await api.delete(`/api/v1/components/${id}`)
  }

  static async updateStock(
    id: string,
    transaction: {
      transaction_type: 'add' | 'remove' | 'move' | 'adjust'
      quantity_change: number
      reason: string
      reference_id?: string
    }
  ): Promise<StockTransaction> {
    const response = await api.post(`/api/v1/components/${id}/stock`, transaction)
    return response.data
  }

  static async getStockHistory(id: string, limit = 50): Promise<StockTransaction[]> {
    const response = await api.get(`/api/v1/components/${id}/history?limit=${limit}`)
    return response.data
  }

  // Storage Locations API
  static async getStorageLocations(params: {
    search?: string
    type?: string
    include_component_count?: boolean
    limit?: number
    offset?: number
  } = {}): Promise<StorageLocation[]> {
    const query = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/v1/storage-locations?${query}`)
    return response.data
  }

  static async getStorageLocation(
    id: string,
    options: {
      include_children?: boolean
      include_component_count?: boolean
      include_full_hierarchy?: boolean
    } = {}
  ): Promise<StorageLocation> {
    const params = new URLSearchParams()

    Object.entries(options).forEach(([key, value]) => {
      if (value) {
        params.append(key, 'true')
      }
    })

    const response = await api.get(`/api/v1/storage-locations/${id}?${params}`)
    return response.data
  }

  static async createStorageLocation(data: Partial<StorageLocation>): Promise<StorageLocation> {
    const response = await api.post('/api/v1/storage-locations', data)
    return response.data
  }

  static async updateStorageLocation(id: string, data: Partial<StorageLocation>): Promise<StorageLocation> {
    const response = await api.put(`/api/v1/storage-locations/${id}`, data)
    return response.data
  }

  static async bulkCreateStorageLocations(locations: Array<{
    name: string
    description?: string
    type: string
    parent_name?: string
    qr_code_id?: string
  }>): Promise<StorageLocation[]> {
    const response = await api.post('/api/v1/storage-locations/bulk-create', { locations })
    return response.data
  }

  static async getLocationComponents(
    id: string,
    params: {
      include_children?: boolean
      search?: string
      category?: string
      component_type?: string
      stock_status?: 'low' | 'out' | 'available'
      sort_by?: 'name' | 'quantity'
      sort_order?: 'asc' | 'desc'
      limit?: number
      offset?: number
    } = {}
  ): Promise<Component[]> {
    const query = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/v1/storage-locations/${id}/components?${query}`)
    return response.data
  }

  // Tags API
  static async getTags(params: {
    search?: string
    limit?: number
    offset?: number
  } = {}): Promise<TagsListResponse> {
    const query = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/v1/tags?${query}`)
    return response.data
  }

  static async getTag(id: string): Promise<Tag> {
    const response = await api.get(`/api/v1/tags/${id}`)
    return response.data
  }

  static async createTag(data: {
    name: string
    description?: string
    color?: string
  }): Promise<Tag> {
    const response = await api.post('/api/v1/tags', data)
    return response.data
  }

  static async updateTag(id: string, data: {
    name?: string
    description?: string
    color?: string
  }): Promise<Tag> {
    const response = await api.put(`/api/v1/tags/${id}`, data)
    return response.data
  }

  static async deleteTag(id: string): Promise<void> {
    await api.delete(`/api/v1/tags/${id}`)
  }

  // Authentication API
  static async login(username: string, password: string): Promise<{
    access_token: string
    token_type: string
    expires_in: number
  }> {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/api/v1/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  }

  static async getCurrentUser(): Promise<{
    id: string
    username: string
    full_name: string | null
    is_active: boolean
    is_admin: boolean
    must_change_password: boolean
    created_at: string
  }> {
    const response = await api.get('/api/v1/auth/me')
    return response.data
  }

  static async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/api/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  // API Token Management
  static async getAPITokens(): Promise<Array<{
    id: string
    name: string
    description: string | null
    prefix: string
    is_active: boolean
    expires_at: string | null
    last_used_at: string | null
    created_at: string
  }>> {
    const response = await api.get('/api/v1/auth/api-tokens')
    return response.data
  }

  static async createAPIToken(data: {
    name: string
    description?: string
    expires_in_days?: number
  }): Promise<{
    id: string
    name: string
    description: string | null
    prefix: string
    is_active: boolean
    expires_at: string | null
    last_used_at: string | null
    created_at: string
    token: string
  }> {
    const response = await api.post('/api/v1/auth/api-tokens', data)
    return response.data
  }

  static async revokeAPIToken(tokenId: string): Promise<void> {
    await api.delete(`/api/v1/auth/api-tokens/${tokenId}`)
  }

  // Projects API
  static async getProjects(params: {
    search?: string
    status?: string
    limit?: number
    offset?: number
    sort_by?: string
    sort_order?: string
  } = {}): Promise<{
    projects: Array<{
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
    }>
    total: number
  }> {
    const query = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/v1/projects/?${query}`)
    return response.data
  }

  static async getProject(id: string): Promise<{
    id: string
    name: string
    description: string | null
    version: string | null
    status: string
    notes: string | null
    created_at: string
    updated_at: string
  }> {
    const response = await api.get(`/api/v1/projects/${id}`)
    return response.data
  }

  static async createProject(data: {
    name: string
    description?: string
    version?: string
    status?: string
    notes?: string
  }): Promise<{
    id: string
    name: string
    description: string | null
    version: string | null
    status: string
    notes: string | null
    created_at: string
    updated_at: string
  }> {
    const response = await api.post('/api/v1/projects/', data)
    return response.data
  }

  static async updateProject(id: string, data: {
    name?: string
    description?: string
    version?: string
    status?: string
    notes?: string
  }): Promise<{
    id: string
    name: string
    description: string | null
    version: string | null
    status: string
    notes: string | null
    created_at: string
    updated_at: string
  }> {
    const response = await api.patch(`/api/v1/projects/${id}`, data)
    return response.data
  }

  static async deleteProject(id: string): Promise<void> {
    await api.delete(`/api/v1/projects/${id}`)
  }

  static async getProjectStatistics(id: string): Promise<{
    total_components: number
    allocated_components: number
    total_cost: number
    completion_percentage: number
  }> {
    const response = await api.get(`/api/v1/projects/${id}/statistics`)
    return response.data
  }

  static async getProjectComponents(id: string): Promise<Array<{
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
  }>> {
    const response = await api.get(`/api/v1/projects/${id}/components`)
    return response.data
  }

  static async allocateComponent(projectId: string, data: {
    component_id: string
    quantity: number
  }): Promise<void> {
    await api.post(`/api/v1/projects/${projectId}/allocate`, data)
  }

  static async returnComponent(projectId: string, data: {
    component_id: string
    quantity: number
  }): Promise<void> {
    await api.post(`/api/v1/projects/${projectId}/return`, data)
  }
}

export default api
export { api }