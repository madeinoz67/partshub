/**
 * Bulk Operations API Client
 * Handles API calls for bulk component operations
 */

import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance for bulk operations
const bulkApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Longer timeout for bulk operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
bulkApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Type definitions for bulk operation responses
export interface BulkOperationResponse {
  success: boolean
  affected_count: number
  errors?: Array<{
    component_id: string
    component_name: string
    error_message: string
    error_type: string
  }>
}

export interface TagPreview {
  component_id: number
  component_name: string
  current_user_tags: string[]
  current_auto_tags: string[]
  proposed_user_tags: string[]
  proposed_auto_tags: string[]
}

export interface TagPreviewResponse {
  previews: TagPreview[]
}

export interface CommonTag {
  tag: string
  count: number
}

// Bulk Operations API
export const bulkOperationsApi = {
  /**
   * Add tags to multiple components
   */
  async bulkAddTags(
    componentIds: string[],
    tags: string[]
  ): Promise<BulkOperationResponse> {
    const response = await bulkApi.post('/api/v1/components/bulk/tags/add', {
      component_ids: componentIds,
      tags,
    })
    return response.data
  },

  /**
   * Remove tags from multiple components
   */
  async bulkRemoveTags(
    componentIds: string[],
    tags: string[]
  ): Promise<BulkOperationResponse> {
    const response = await bulkApi.post('/api/v1/components/bulk/tags/remove', {
      component_ids: componentIds,
      tags,
    })
    return response.data
  },

  /**
   * Preview tag changes before applying
   */
  async previewTagChanges(
    componentIds: string[],
    addTags: string[],
    removeTags: string[]
  ): Promise<TagPreviewResponse> {
    const response = await bulkApi.post('/api/v1/components/bulk/tags/preview', {
      component_ids: componentIds,
      add_tags: addTags,
      remove_tags: removeTags,
    })
    return response.data
  },

  /**
   * Get common tags across selected components
   */
  async getCommonTags(componentIds: string[]): Promise<CommonTag[]> {
    const response = await bulkApi.post('/api/v1/components/bulk/tags/common', {
      component_ids: componentIds,
    })
    return response.data
  },

  /**
   * Assign multiple components to a project
   */
  async bulkAssignToProject(
    componentIds: string[],
    projectId: string,
    quantities: Record<string, number>
  ): Promise<BulkOperationResponse> {
    const response = await bulkApi.post('/api/v1/components/bulk/projects/assign', {
      component_ids: componentIds,
      project_id: projectId,
      quantities,
    })
    return response.data
  },

  /**
   * Delete multiple components
   */
  async bulkDelete(componentIds: string[]): Promise<BulkOperationResponse> {
    const response = await bulkApi.post('/api/v1/components/bulk/delete', {
      component_ids: componentIds,
    })
    return response.data
  },
}

export default bulkOperationsApi
