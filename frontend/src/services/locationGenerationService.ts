/**
 * Location Generation Service
 * API client for storage location layout generation
 */

import axios from 'axios'
import type {
  LayoutConfiguration,
  PreviewResponse,
  BulkCreateResponse
} from '../types/locationLayout'

// Use the same base URL as the main API service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token interceptor
api.interceptors.request.use(
  (config) => {
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

/**
 * Generate a preview of locations based on layout configuration
 * Does not require authentication (anonymous users can preview)
 * @param config Layout configuration
 * @returns Preview response with sample names, count, and validation
 */
export async function generatePreview(
  config: LayoutConfiguration
): Promise<PreviewResponse> {
  const response = await api.post<PreviewResponse>(
    '/api/v1/storage-locations/generate-preview',
    config
  )
  return response.data
}

/**
 * Bulk create storage locations from layout configuration
 * Requires JWT authentication
 * @param config Layout configuration
 * @returns Bulk create response with created IDs and count
 */
export async function bulkCreateLocations(
  config: LayoutConfiguration
): Promise<BulkCreateResponse> {
  const response = await api.post<BulkCreateResponse>(
    '/api/v1/storage-locations/bulk-create-layout',
    config
  )
  return response.data
}

export const locationGenerationService = {
  generatePreview,
  bulkCreateLocations
}
