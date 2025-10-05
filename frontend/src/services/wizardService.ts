/**
 * Wizard API Service
 * Handles API calls for the component creation wizard
 */

import api from './api'
import type {
  Provider,
  ProviderSearchResponse,
  ManufacturerSuggestion,
  FootprintSuggestion,
  TagSuggestion,
  CreateComponentRequest,
  Component,
} from '../types/wizard'

export const wizardService = {
  /**
   * List all available providers
   */
  async listProviders(): Promise<Provider[]> {
    try {
      const response = await api.get('/api/providers')
      return response.data
    } catch (err) {
      console.error('Failed to list providers:', err)
      throw new Error('Failed to load providers. Please try again.')
    }
  },

  /**
   * Search for parts in a specific provider
   */
  async searchProvider(
    providerId: number,
    query: string,
    limit = 20
  ): Promise<ProviderSearchResponse> {
    try {
      const response = await api.get(`/api/providers/${providerId}/search`, {
        params: {
          query,
          limit,
        },
      })
      return response.data
    } catch (err) {
      console.error('Provider search failed:', err)
      throw new Error('Failed to search provider. Please try again.')
    }
  },

  /**
   * Search for manufacturer suggestions
   */
  async searchManufacturers(
    query: string,
    limit = 10
  ): Promise<ManufacturerSuggestion[]> {
    try {
      const response = await api.get('/api/wizard/manufacturers/search', {
        params: {
          query,
          limit,
        },
      })
      return response.data
    } catch (err) {
      console.error('Manufacturer search failed:', err)
      throw new Error('Failed to search manufacturers. Please try again.')
    }
  },

  /**
   * Search for footprint suggestions
   */
  async searchFootprints(query: string, limit = 10): Promise<FootprintSuggestion[]> {
    try {
      const response = await api.get('/api/wizard/footprints/search', {
        params: {
          query,
          limit,
        },
      })
      return response.data
    } catch (err) {
      console.error('Footprint search failed:', err)
      throw new Error('Failed to search footprints. Please try again.')
    }
  },

  /**
   * Search for tag suggestions
   */
  async searchTags(query: string, limit = 10): Promise<TagSuggestion[]> {
    try {
      const response = await api.get('/api/wizard/tags/search', {
        params: {
          query,
          limit,
        },
      })
      return response.data
    } catch (err) {
      console.error('Tag search failed:', err)
      throw new Error('Failed to search tags. Please try again.')
    }
  },

  /**
   * Create a new component using the wizard
   */
  async createComponent(data: CreateComponentRequest): Promise<Component> {
    try {
      const response = await api.post('/api/wizard/components', data)
      return response.data
    } catch (err) {
      console.error('Component creation failed:', err)

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

      throw new Error('Failed to create component. Please check your inputs and try again.')
    }
  },
}
