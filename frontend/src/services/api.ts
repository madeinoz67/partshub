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
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('auth_token')
      // Router redirect would go here
    }
    return Promise.reject(error)
  }
)

// Type definitions
export interface Component {
  id: string
  name: string
  part_number: string | null
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
  specifications: Record<string, any> | null
  custom_fields: Record<string, any> | null
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
  children?: StorageLocation[]
  component_count?: number
  full_hierarchy_path?: Array<{ id: string; name: string }>
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
}

export default api