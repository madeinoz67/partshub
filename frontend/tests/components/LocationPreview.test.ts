import { mount, VueWrapper } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import LocationPreview from '../../src/components/storage/LocationPreview.vue'

describe('LocationPreview', () => {
  let wrapper: VueWrapper<any>

  describe('Loading State', () => {
    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: true,
          previewData: null
        }
      })
    })

    it('should display loading spinner when loading is true', () => {
      const spinner = wrapper.find('[data-testid="preview-loading"]')
      expect(spinner.exists()).toBe(true)
    })

    it('should not display preview content when loading', () => {
      const previewContent = wrapper.find('[data-testid="preview-content"]')
      expect(previewContent.exists()).toBe(false)
    })
  })

  describe('Empty State', () => {
    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: null
        }
      })
    })

    it('should display empty state when no preview data', () => {
      const emptyState = wrapper.find('[data-testid="preview-empty"]')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.text()).toContain('Configure')
    })

    it('should show icon in empty state', () => {
      const emptyState = wrapper.find('[data-testid="preview-empty"]')
      const icon = emptyState.find('i')
      expect(icon.exists()).toBe(true)
    })
  })

  describe('Valid Preview', () => {
    const validPreviewData = {
      sample_names: ['box-a', 'box-b', 'box-c', 'box-d', 'box-e'],
      last_name: 'box-f',
      total_count: 6,
      warnings: [],
      errors: [],
      is_valid: true
    }

    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: validPreviewData
        }
      })
    })

    it('should display preview content when data is available', () => {
      const previewContent = wrapper.find('[data-testid="preview-content"]')
      expect(previewContent.exists()).toBe(true)
    })

    it('should display total count', () => {
      const totalCount = wrapper.find('[data-testid="total-count"]')
      expect(totalCount.exists()).toBe(true)
      expect(totalCount.text()).toContain('6')
      expect(totalCount.text()).toContain('location')
    })

    it('should display sample names (first 5)', () => {
      const sampleNames = wrapper.findAll('[data-testid^="sample-name-"]')
      expect(sampleNames).toHaveLength(5)

      expect(sampleNames[0].text()).toBe('box-a')
      expect(sampleNames[1].text()).toBe('box-b')
      expect(sampleNames[2].text()).toBe('box-c')
      expect(sampleNames[3].text()).toBe('box-d')
      expect(sampleNames[4].text()).toBe('box-e')
    })

    it('should display ellipsis if total count > 5', () => {
      const ellipsis = wrapper.find('[data-testid="preview-ellipsis"]')
      expect(ellipsis.exists()).toBe(true)
      expect(ellipsis.text()).toBe('...')
    })

    it('should display last name', () => {
      const lastName = wrapper.find('[data-testid="last-name"]')
      expect(lastName.exists()).toBe(true)
      expect(lastName.text()).toBe('box-f')
    })

    it('should not display warnings or errors when none exist', () => {
      const warnings = wrapper.find('[data-testid="preview-warnings"]')
      const errors = wrapper.find('[data-testid="preview-errors"]')

      expect(warnings.exists()).toBe(false)
      expect(errors.exists()).toBe(false)
    })

    it('should use success color for valid preview', () => {
      const previewContent = wrapper.find('[data-testid="preview-content"]')
      expect(previewContent.classes()).toContain('preview-valid')
    })
  })

  describe('Preview with Warnings', () => {
    const warningPreviewData = {
      sample_names: ['shelf-a-1', 'shelf-a-2', 'shelf-a-3', 'shelf-a-4', 'shelf-a-5'],
      last_name: 'shelf-f-30',
      total_count: 150,
      warnings: ['Creating 150 locations cannot be undone. Locations cannot be deleted.'],
      errors: [],
      is_valid: true
    }

    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: warningPreviewData
        }
      })
    })

    it('should display warning banner', () => {
      const warnings = wrapper.find('[data-testid="preview-warnings"]')
      expect(warnings.exists()).toBe(true)
    })

    it('should display all warning messages', () => {
      const warningMessages = wrapper.findAll('[data-testid^="warning-message-"]')
      expect(warningMessages).toHaveLength(1)
      expect(warningMessages[0].text()).toContain('cannot be undone')
    })

    it('should show warning icon', () => {
      const warnings = wrapper.find('[data-testid="preview-warnings"]')
      const icon = warnings.find('i')
      expect(icon.exists()).toBe(true)
    })

    it('should use warning color for warnings', () => {
      const warnings = wrapper.find('[data-testid="preview-warnings"]')
      expect(warnings.classes()).toContain('warning')
    })
  })

  describe('Preview with Errors', () => {
    const errorPreviewData = {
      sample_names: [],
      last_name: '',
      total_count: 600,
      warnings: [],
      errors: ['Total location count (600) exceeds maximum limit of 500'],
      is_valid: false
    }

    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: errorPreviewData
        }
      })
    })

    it('should display error banner', () => {
      const errors = wrapper.find('[data-testid="preview-errors"]')
      expect(errors.exists()).toBe(true)
    })

    it('should display all error messages', () => {
      const errorMessages = wrapper.findAll('[data-testid^="error-message-"]')
      expect(errorMessages).toHaveLength(1)
      expect(errorMessages[0].text()).toContain('exceeds maximum limit')
    })

    it('should show error icon', () => {
      const errors = wrapper.find('[data-testid="preview-errors"]')
      const icon = errors.find('i')
      expect(icon.exists()).toBe(true)
    })

    it('should use error/negative color for errors', () => {
      const errors = wrapper.find('[data-testid="preview-errors"]')
      expect(errors.classes()).toContain('error')
    })

    it('should not display sample names when errors exist', () => {
      const sampleNames = wrapper.findAll('[data-testid^="sample-name-"]')
      expect(sampleNames).toHaveLength(0)
    })

    it('should use error color for invalid preview', () => {
      const previewContent = wrapper.find('[data-testid="preview-content"]')
      expect(previewContent.classes()).toContain('preview-invalid')
    })
  })

  describe('Preview with Multiple Warnings and Errors', () => {
    const multipleMessagesData = {
      sample_names: [],
      last_name: '',
      total_count: 0,
      warnings: ['Warning 1', 'Warning 2'],
      errors: ['Error 1', 'Error 2', 'Error 3'],
      is_valid: false
    }

    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: multipleMessagesData
        }
      })
    })

    it('should display all warnings', () => {
      const warningMessages = wrapper.findAll('[data-testid^="warning-message-"]')
      expect(warningMessages).toHaveLength(2)
    })

    it('should display all errors', () => {
      const errorMessages = wrapper.findAll('[data-testid^="error-message-"]')
      expect(errorMessages).toHaveLength(3)
    })

    it('should display errors above warnings', () => {
      const errors = wrapper.find('[data-testid="preview-errors"]')
      const warnings = wrapper.find('[data-testid="preview-warnings"]')

      const errorsIndex = wrapper.html().indexOf('data-testid="preview-errors"')
      const warningsIndex = wrapper.html().indexOf('data-testid="preview-warnings"')

      expect(errorsIndex).toBeLessThan(warningsIndex)
    })
  })

  describe('Edge Cases', () => {
    it('should handle total_count of 1 (single location)', () => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: {
            sample_names: ['box-a'],
            last_name: 'box-a',
            total_count: 1,
            warnings: [],
            errors: [],
            is_valid: true
          }
        }
      })

      const totalCount = wrapper.find('[data-testid="total-count"]')
      expect(totalCount.text()).toContain('1 location')

      const ellipsis = wrapper.find('[data-testid="preview-ellipsis"]')
      expect(ellipsis.exists()).toBe(false)
    })

    it('should handle exactly 5 locations (no ellipsis)', () => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: {
            sample_names: ['a', 'b', 'c', 'd', 'e'],
            last_name: 'e',
            total_count: 5,
            warnings: [],
            errors: [],
            is_valid: true
          }
        }
      })

      const ellipsis = wrapper.find('[data-testid="preview-ellipsis"]')
      expect(ellipsis.exists()).toBe(false)
    })

    it('should pluralize "locations" correctly', () => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: {
            sample_names: ['a', 'b'],
            last_name: 'c',
            total_count: 3,
            warnings: [],
            errors: [],
            is_valid: true
          }
        }
      })

      const totalCount = wrapper.find('[data-testid="total-count"]')
      expect(totalCount.text()).toContain('3 locations')
    })
  })

  describe('Visual Hierarchy', () => {
    beforeEach(() => {
      wrapper = mount(LocationPreview, {
        props: {
          loading: false,
          previewData: {
            sample_names: ['box-a', 'box-b', 'box-c', 'box-d', 'box-e'],
            last_name: 'box-z',
            total_count: 26,
            warnings: [],
            errors: [],
            is_valid: true
          }
        }
      })
    })

    it('should highlight total count prominently', () => {
      const totalCount = wrapper.find('[data-testid="total-count"]')
      expect(totalCount.classes()).toContain('text-h6')
    })

    it('should display sample names in a list format', () => {
      const sampleList = wrapper.find('[data-testid="sample-names-list"]')
      expect(sampleList.exists()).toBe(true)
    })

    it('should emphasize last name separately', () => {
      const lastName = wrapper.find('[data-testid="last-name"]')
      expect(lastName.exists()).toBe(true)
    })
  })
})
