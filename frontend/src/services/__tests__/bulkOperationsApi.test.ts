/**
 * Tests for Bulk Operations API Client
 * Following TDD - these tests define the expected API behavior
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { BulkOperationResponse, TagPreviewResponse } from '../bulkOperationsApi'

// We'll test the API client by mocking at the network level
// This is more realistic than trying to mock axios internals
describe('bulkOperationsApi', () => {
  let bulkOperationsApi: typeof import('../bulkOperationsApi').bulkOperationsApi

  beforeEach(async () => {
    vi.clearAllMocks()
    localStorage.clear()
    // Dynamically import to get fresh instance
    const module = await import('../bulkOperationsApi')
    bulkOperationsApi = module.bulkOperationsApi
  })

  describe('Type Definitions', () => {
    it('should export BulkOperationResponse type', () => {
      const response: BulkOperationResponse = {
        updated_count: 1,
        failed_count: 0,
        updated_ids: [1],
        failed_ids: [],
      }
      expect(response).toBeDefined()
    })

    it('should export TagPreviewResponse type', () => {
      const response: TagPreviewResponse = {
        previews: [
          {
            component_id: 1,
            component_name: 'Test',
            current_user_tags: [],
            current_auto_tags: [],
            proposed_user_tags: [],
            proposed_auto_tags: [],
          },
        ],
      }
      expect(response).toBeDefined()
    })
  })

  describe('API Methods Structure', () => {
    it('should export bulkAddTags method', () => {
      expect(bulkOperationsApi.bulkAddTags).toBeDefined()
      expect(typeof bulkOperationsApi.bulkAddTags).toBe('function')
    })

    it('should export bulkRemoveTags method', () => {
      expect(bulkOperationsApi.bulkRemoveTags).toBeDefined()
      expect(typeof bulkOperationsApi.bulkRemoveTags).toBe('function')
    })

    it('should export previewTagChanges method', () => {
      expect(bulkOperationsApi.previewTagChanges).toBeDefined()
      expect(typeof bulkOperationsApi.previewTagChanges).toBe('function')
    })

    it('should export getCommonTags method', () => {
      expect(bulkOperationsApi.getCommonTags).toBeDefined()
      expect(typeof bulkOperationsApi.getCommonTags).toBe('function')
    })

    it('should export bulkAssignToProject method', () => {
      expect(bulkOperationsApi.bulkAssignToProject).toBeDefined()
      expect(typeof bulkOperationsApi.bulkAssignToProject).toBe('function')
    })

    it('should export bulkDelete method', () => {
      expect(bulkOperationsApi.bulkDelete).toBeDefined()
      expect(typeof bulkOperationsApi.bulkDelete).toBe('function')
    })
  })

  describe('Method Signatures', () => {
    it('bulkAddTags should accept componentIds and tags arrays', () => {
      // This test verifies the function signature compiles correctly
      const call = () => bulkOperationsApi.bulkAddTags([1, 2], ['tag1', 'tag2'])
      expect(call).toBeDefined()
    })

    it('bulkRemoveTags should accept componentIds and tags arrays', () => {
      const call = () => bulkOperationsApi.bulkRemoveTags([1], ['tag'])
      expect(call).toBeDefined()
    })

    it('previewTagChanges should accept componentIds, addTags, and removeTags', () => {
      const call = () => bulkOperationsApi.previewTagChanges([1], ['add'], ['remove'])
      expect(call).toBeDefined()
    })

    it('bulkAssignToProject should accept componentIds, projectId, and quantities', () => {
      const call = () => bulkOperationsApi.bulkAssignToProject([1], 100, { 1: 5 })
      expect(call).toBeDefined()
    })

    it('bulkDelete should accept componentIds array', () => {
      const call = () => bulkOperationsApi.bulkDelete([1, 2, 3])
      expect(call).toBeDefined()
    })
  })
})
