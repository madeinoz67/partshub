/**
 * Stock Operations API Client
 * Handles API calls for stock management operations (add, remove, move)
 */

import { api } from './api'
import { Notify } from 'quasar'

// Type definitions matching backend Pydantic schemas

export interface AddStockRequest {
  location_id: string
  quantity: number
  price_per_unit?: number | null
  total_price?: number | null
  lot_id?: string | null
  comments?: string | null
  reference_id?: string | null
  reference_type?: string | null
}

export interface RemoveStockRequest {
  location_id: string
  quantity: number
  comments?: string | null
  reason?: string | null
}

export interface MoveStockRequest {
  source_location_id: string
  destination_location_id: string
  quantity: number
  comments?: string | null
}

export interface StockHistoryEntry {
  id: string
  component_id: string
  transaction_type: 'add' | 'remove' | 'move' | 'adjust'
  quantity_change: number
  previous_quantity: number
  new_quantity: number
  from_location_id?: string | null
  from_location_name?: string | null
  to_location_id?: string | null
  to_location_name?: string | null
  lot_id?: string | null
  price_per_unit?: number | null
  total_price?: number | null
  user_name?: string | null
  reason?: string
  notes?: string | null
  comments?: string | null
  created_at: string
}

export interface PaginationMetadata {
  page: number
  page_size: number
  total_entries: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface StockHistoryResponse {
  entries: StockHistoryEntry[]
  pagination: PaginationMetadata
}

export interface AddStockResponse {
  success: boolean
  message: string
  transaction_id: string
  component_id: string
  location_id: string
  quantity_added: number
  previous_quantity: number
  new_quantity: number
  total_stock: number
}

export interface RemoveStockResponse {
  success: boolean
  message: string
  transaction_id: string
  component_id: string
  location_id: string
  quantity_removed: number
  requested_quantity: number
  capped: boolean
  previous_quantity: number
  new_quantity: number
  location_deleted: boolean
  total_stock: number
}

export interface MoveStockResponse {
  success: boolean
  message: string
  transaction_id: string
  component_id: string
  source_location_id: string
  destination_location_id: string
  quantity_moved: number
  requested_quantity: number
  capped: boolean
  source_previous_quantity: number
  source_new_quantity: number
  source_location_deleted: boolean
  destination_previous_quantity: number
  destination_new_quantity: number
  destination_location_created: boolean
  total_stock: number
  pricing_inherited: boolean
}

/**
 * Stock Operations API Service
 */
export const stockOperationsApi = {
  /**
   * Add stock to a component at a specific location
   * @param componentId - UUID of the component
   * @param request - Add stock request data
   * @returns Add stock response with transaction details
   */
  async addStock(componentId: string, request: AddStockRequest): Promise<AddStockResponse> {
    try {
      const response = await api.post<AddStockResponse>(
        `/api/v1/components/${componentId}/stock/add`,
        request
      )

      // Show success notification
      Notify.create({
        type: 'positive',
        message: response.data.message || 'Stock added successfully',
        position: 'top-right',
        timeout: 3000
      })

      return response.data
    } catch (error: unknown) {
      // Handle specific error cases
      if (axiosError.response?.status === 403) {
        Notify.create({
          type: 'negative',
          message: 'Permission denied. Admin access required.',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 404) {
        Notify.create({
          type: 'negative',
          message: 'Component or location not found',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 422) {
        const detail = axiosError.response.data?.detail || 'Invalid request data'
        Notify.create({
          type: 'negative',
          message: `Validation error: ${detail}`,
          position: 'top-right',
          timeout: 4000
        })
      } else {
        Notify.create({
          type: 'negative',
          message: axiosError.response?.data?.detail || 'Failed to add stock',
          position: 'top-right',
          timeout: 4000
        })
      }
      throw error
    }
  },

  /**
   * Remove stock from a component at a specific location
   * @param componentId - UUID of the component
   * @param request - Remove stock request data
   * @returns Remove stock response with transaction details
   */
  async removeStock(componentId: string, request: RemoveStockRequest): Promise<RemoveStockResponse> {
    try {
      const response = await api.post<RemoveStockResponse>(
        `/api/v1/components/${componentId}/stock/remove`,
        request
      )

      // Show notification with auto-capping info if applicable
      const message = response.data.capped
        ? `Stock removed (quantity auto-capped at ${response.data.quantity_removed})`
        : response.data.message || 'Stock removed successfully'

      Notify.create({
        type: response.data.capped ? 'warning' : 'positive',
        message,
        position: 'top-right',
        timeout: 3000
      })

      return response.data
    } catch (error: unknown) {
      // Handle specific error cases
      if (axiosError.response?.status === 403) {
        Notify.create({
          type: 'negative',
          message: 'Permission denied. Admin access required.',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 404) {
        Notify.create({
          type: 'negative',
          message: 'Component or location not found',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 409) {
        Notify.create({
          type: 'negative',
          message: 'No stock available at this location',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 422) {
        const detail = axiosError.response.data?.detail || 'Invalid request data'
        Notify.create({
          type: 'negative',
          message: `Validation error: ${detail}`,
          position: 'top-right',
          timeout: 4000
        })
      } else {
        Notify.create({
          type: 'negative',
          message: axiosError.response?.data?.detail || 'Failed to remove stock',
          position: 'top-right',
          timeout: 4000
        })
      }
      throw error
    }
  },

  /**
   * Move stock between storage locations
   * @param componentId - UUID of the component
   * @param request - Move stock request data
   * @returns Move stock response with transaction details
   */
  async moveStock(componentId: string, request: MoveStockRequest): Promise<MoveStockResponse> {
    try {
      const response = await api.post<MoveStockResponse>(
        `/api/v1/components/${componentId}/stock/move`,
        request
      )

      // Show notification with auto-capping info if applicable
      const message = response.data.capped
        ? `Stock moved (quantity auto-capped at ${response.data.quantity_moved})`
        : response.data.message || 'Stock moved successfully'

      Notify.create({
        type: response.data.capped ? 'warning' : 'positive',
        message,
        position: 'top-right',
        timeout: 3000
      })

      return response.data
    } catch (error: unknown) {
      // Handle specific error cases
      if (axiosError.response?.status === 403) {
        Notify.create({
          type: 'negative',
          message: 'Permission denied. Admin access required.',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 404) {
        Notify.create({
          type: 'negative',
          message: 'Component or location not found',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 409) {
        Notify.create({
          type: 'negative',
          message: 'Insufficient stock at source location',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 422) {
        const detail = axiosError.response.data?.detail || 'Invalid request data'
        Notify.create({
          type: 'negative',
          message: `Validation error: ${detail}`,
          position: 'top-right',
          timeout: 4000
        })
      } else {
        Notify.create({
          type: 'negative',
          message: axiosError.response?.data?.detail || 'Failed to move stock',
          position: 'top-right',
          timeout: 4000
        })
      }
      throw error
    }
  },

  /**
   * Get paginated stock history for a component
   * @param componentId - UUID of the component
   * @param page - Page number (1-indexed)
   * @param pageSize - Number of entries per page
   * @param sortBy - Field to sort by
   * @param sortOrder - Sort order (asc/desc)
   * @returns Stock history response with entries and pagination metadata
   */
  async getStockHistory(
    componentId: string,
    page: number = 1,
    pageSize: number = 10,
    sortBy: string = 'created_at',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<StockHistoryResponse> {
    try {
      const response = await api.get<StockHistoryResponse>(
        `/api/v1/components/${componentId}/stock/history`,
        {
          params: {
            page,
            page_size: pageSize,
            sort_by: sortBy,
            sort_order: sortOrder
          }
        }
      )
      return response.data
    } catch (error: unknown) {
      // Handle errors but don't show notifications (component will handle display)
      const axiosError = error as { response?: { status?: number; data?: { detail?: string } } }
      if (axiosError.response?.status === 404) {
        console.error('Component not found:', componentId)
      } else if (axiosError.response?.status === 403) {
        console.error('Permission denied accessing stock history')
      }
      throw error
    }
  },

  /**
   * Export stock history in specified format
   * @param componentId - UUID of the component
   * @param format - Export format (csv/xlsx/json)
   * @param sortBy - Field to sort by
   * @param sortOrder - Sort order (asc/desc)
   * @returns Promise that triggers browser download
   */
  async exportStockHistory(
    componentId: string,
    format: 'csv' | 'xlsx' | 'json',
    sortBy: string = 'created_at',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<void> {
    try {
      const response = await api.get(
        `/api/v1/components/${componentId}/stock/history/export`,
        {
          params: {
            format,
            sort_by: sortBy,
            sort_order: sortOrder
          },
          responseType: 'blob'
        }
      )

      // Trigger browser download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Get filename from content-disposition header if available
      const contentDisposition = response.headers['content-disposition']
      let filename = `stock_history_${componentId}.${format}`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '')
        }
      }

      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      // Show success notification
      Notify.create({
        type: 'positive',
        message: `Stock history exported successfully as ${format.toUpperCase()}`,
        position: 'top-right',
        timeout: 3000
      })
    } catch (error: unknown) {
      // Handle specific error cases
      const axiosError = error as { response?: { status?: number; data?: { detail?: string }; headers?: Record<string, string> } }
      if (axiosError.response?.status === 403) {
        Notify.create({
          type: 'negative',
          message: 'Permission denied. Admin access required for export.',
          position: 'top-right',
          timeout: 4000
        })
      } else if (axiosError.response?.status === 404) {
        Notify.create({
          type: 'negative',
          message: 'Component not found',
          position: 'top-right',
          timeout: 4000
        })
      } else {
        Notify.create({
          type: 'negative',
          message: axiosError.response?.data?.detail || 'Failed to export stock history',
          position: 'top-right',
          timeout: 4000
        })
      }
      throw error
    }
  }
}

export default stockOperationsApi
