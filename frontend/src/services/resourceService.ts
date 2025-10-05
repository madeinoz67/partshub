/**
 * Resource API Service
 * Handles API calls for resource management and status tracking
 */

import api from './api'
import type { ResourceStatus } from '../types/wizard'

export interface Resource {
  id: number
  provider_link_id: number
  type: string
  url: string | null
  file_name: string | null
  file_path: string | null
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  updated_at: string
}

export const resourceService = {
  /**
   * Get the status of a specific resource
   * Used for polling async resource downloads
   */
  async getResourceStatus(resourceId: number): Promise<ResourceStatus> {
    try {
      const response = await api.get(`/api/resources/${resourceId}/status`)
      return response.data
    } catch (err) {
      console.error('Failed to get resource status:', err)
      throw new Error('Failed to check resource status. Please try again.')
    }
  },

  /**
   * Add a new resource to a provider link
   */
  async addResource(
    linkId: number,
    resource: {
      type: string
      url?: string
      file_name?: string
    }
  ): Promise<Resource> {
    try {
      const response = await api.post(`/api/provider-links/${linkId}/resources`, resource)
      return response.data
    } catch (err) {
      console.error('Failed to add resource:', err)

      // Extract error message from API response
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as {
          response?: {
            data?: {
              detail?: string
              message?: string
            }
          }
        }
        const detail =
          axiosError.response?.data?.detail || axiosError.response?.data?.message
        if (detail) {
          throw new Error(detail)
        }
      }

      throw new Error('Failed to add resource. Please try again.')
    }
  },

  /**
   * Poll resource status until completion or failure
   * Returns when resource reaches a terminal state
   */
  async pollResourceStatus(
    resourceId: number,
    options: {
      maxAttempts?: number
      intervalMs?: number
      onUpdate?: (status: ResourceStatus) => void
    } = {}
  ): Promise<ResourceStatus> {
    const maxAttempts = options.maxAttempts || 60 // 60 attempts
    const intervalMs = options.intervalMs || 2000 // 2 seconds

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.getResourceStatus(resourceId)

      // Notify caller of update
      if (options.onUpdate) {
        options.onUpdate(status)
      }

      // Check if in terminal state
      if (status.status === 'completed' || status.status === 'failed') {
        return status
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, intervalMs))
    }

    throw new Error('Resource download timed out')
  },

  /**
   * Poll multiple resources concurrently
   */
  async pollMultipleResources(
    resourceIds: number[],
    options: {
      maxAttempts?: number
      intervalMs?: number
      onUpdate?: (resourceId: number, status: ResourceStatus) => void
    } = {}
  ): Promise<Map<number, ResourceStatus>> {
    const results = new Map<number, ResourceStatus>()

    await Promise.all(
      resourceIds.map(async resourceId => {
        try {
          const status = await this.pollResourceStatus(resourceId, {
            maxAttempts: options.maxAttempts,
            intervalMs: options.intervalMs,
            onUpdate: options.onUpdate
              ? status => options.onUpdate!(resourceId, status)
              : undefined,
          })
          results.set(resourceId, status)
        } catch (err) {
          console.error(`Failed to poll resource ${resourceId}:`, err)
          // Store error status
          results.set(resourceId, {
            id: resourceId,
            type: 'unknown',
            status: 'failed',
            url: null,
            file_name: null,
            error_message: err instanceof Error ? err.message : 'Unknown error',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }
      })
    )

    return results
  },
}
