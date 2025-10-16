/**
 * Reorder Alerts API Service
 * Handles API calls for reorder alert management operations
 */

import { api } from './api'

// Type definitions matching backend API responses

export interface ReorderAlert {
  id: number
  component_id: string
  component_name: string
  component_part_number: string | null
  location_id: string
  location_name: string
  status: 'active' | 'dismissed' | 'ordered' | 'resolved'
  severity: 'critical' | 'high' | 'medium' | 'low'
  current_quantity: number
  reorder_threshold: number
  shortage_amount: number
  shortage_percentage: number
  created_at: string
  updated_at: string
  dismissed_at: string | null
  ordered_at: string | null
  resolved_at: string | null
  notes: string | null
}

export interface AlertsListResponse {
  alerts: ReorderAlert[]
  total: number
}

export interface AlertStatistics {
  total_alerts: number
  by_severity: {
    critical: number
    high: number
    medium: number
    low: number
  }
  by_status: {
    active: number
    dismissed: number
    ordered: number
    resolved: number
  }
  total_shortage_value: number
  critical_components: number
}

export interface LowStockItem {
  component_id: string
  component_name: string
  component_part_number: string | null
  location_id: string
  location_name: string
  current_quantity: number
  reorder_threshold: number
  shortage_amount: number
  shortage_percentage: number
  has_active_alert: boolean
}

export interface LowStockReport {
  items: LowStockItem[]
  total_items: number
  total_shortage: number
}

export interface ThresholdUpdate {
  component_id: string
  location_id: string
  threshold: number
  enabled: boolean
}

export interface BulkThresholdUpdate {
  updates: Array<{
    component_id: string
    location_id: string
    threshold: number
    enabled: boolean
  }>
}

export interface AlertsFilters {
  component_id?: string
  location_id?: string
  status?: 'active' | 'dismissed' | 'ordered' | 'resolved'
  severity?: 'critical' | 'high' | 'medium' | 'low'
  min_shortage?: number
  limit?: number
  offset?: number
}

/**
 * Reorder Alerts API Service
 */
export const reorderAlertsApi = {
  /**
   * Get list of reorder alerts with optional filters
   * @param filters - Filter parameters
   * @returns List of alerts
   */
  async getAlerts(filters: AlertsFilters = {}): Promise<AlertsListResponse> {
    const params = new URLSearchParams()

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const response = await api.get<AlertsListResponse>(
      `/api/v1/reorder-alerts/?${params}`
    )
    return response.data
  },

  /**
   * Get historical alerts
   * @param filters - Filter parameters
   * @returns List of historical alerts
   */
  async getHistory(filters: AlertsFilters = {}): Promise<AlertsListResponse> {
    const params = new URLSearchParams()

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const response = await api.get<AlertsListResponse>(
      `/api/v1/reorder-alerts/history?${params}`
    )
    return response.data
  },

  /**
   * Get a single alert by ID
   * @param alertId - Alert ID
   * @returns Single alert
   */
  async getAlert(alertId: number): Promise<ReorderAlert> {
    const response = await api.get<ReorderAlert>(
      `/api/v1/reorder-alerts/${alertId}`
    )
    return response.data
  },

  /**
   * Dismiss an alert
   * @param alertId - Alert ID
   * @param notes - Optional dismissal notes
   * @returns Updated alert
   */
  async dismissAlert(alertId: number, notes?: string): Promise<ReorderAlert> {
    const response = await api.post<ReorderAlert>(
      `/api/v1/reorder-alerts/${alertId}/dismiss`,
      { notes }
    )
    return response.data
  },

  /**
   * Mark an alert as ordered
   * @param alertId - Alert ID
   * @param notes - Optional order notes
   * @returns Updated alert
   */
  async markOrdered(alertId: number, notes?: string): Promise<ReorderAlert> {
    const response = await api.post<ReorderAlert>(
      `/api/v1/reorder-alerts/${alertId}/mark-ordered`,
      { notes }
    )
    return response.data
  },

  /**
   * Update reorder threshold for a component at a location
   * @param componentId - Component ID
   * @param locationId - Location ID
   * @param threshold - New threshold value
   * @param enabled - Whether monitoring is enabled
   * @returns Success response
   */
  async updateThreshold(
    componentId: string,
    locationId: string,
    threshold: number,
    enabled: boolean
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.put<{ success: boolean; message: string }>(
      `/api/v1/reorder-alerts/thresholds/${componentId}/${locationId}`,
      { threshold, enabled }
    )
    return response.data
  },

  /**
   * Bulk update reorder thresholds
   * @param updates - Array of threshold updates
   * @returns Success response with counts
   */
  async bulkUpdateThresholds(
    updates: Array<{
      component_id: string
      location_id: string
      threshold: number
      enabled: boolean
    }>
  ): Promise<{ success: boolean; updated_count: number; failed_count: number }> {
    const response = await api.post<{
      success: boolean
      updated_count: number
      failed_count: number
    }>('/api/v1/reorder-alerts/thresholds/bulk', { updates })
    return response.data
  },

  /**
   * Get low stock report
   * @param filters - Filter parameters
   * @returns Low stock report
   */
  async getLowStockReport(filters: {
    component_id?: string
    location_id?: string
    min_shortage?: number
    limit?: number
    offset?: number
  } = {}): Promise<LowStockReport> {
    const params = new URLSearchParams()

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const response = await api.get<LowStockReport>(
      `/api/v1/reorder-alerts/reports/low-stock?${params}`
    )
    return response.data
  },

  /**
   * Get alert statistics
   * @returns Alert statistics
   */
  async getStatistics(): Promise<AlertStatistics> {
    const response = await api.get<AlertStatistics>(
      '/api/v1/reorder-alerts/reports/statistics'
    )
    return response.data
  },
}

export default reorderAlertsApi
