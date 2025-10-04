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
  from_location_id?: string | null
  to_location_id?: string | null
  lot_id?: string | null
  price_per_unit?: number | null
  total_price?: number | null
  user_name?: string | null
  comments?: string | null
  created_at: string
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
  }
}

export default stockOperationsApi
