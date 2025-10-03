import { mount, VueWrapper } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import LocationLayoutDialog from '../../src/components/storage/LocationLayoutDialog.vue'

// Mock the locationLayoutService
vi.mock('../../src/services/locationLayoutService', () => ({
  locationLayoutService: {
    generatePreview: vi.fn(),
    bulkCreate: vi.fn()
  }
}))

describe('LocationLayoutDialog', () => {
  let wrapper: VueWrapper<any>
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    wrapper = mount(LocationLayoutDialog, {
      global: {
        plugins: [pinia]
      },
      props: {
        modelValue: true
      }
    })
  })

  describe('Dialog Structure', () => {
    it('should render dialog when modelValue is true', () => {
      expect(wrapper.find('[data-testid="location-layout-dialog"]').exists()).toBe(true)
    })

    it('should render dialog title', () => {
      const title = wrapper.find('[data-testid="dialog-title"]')
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Create Storage Locations')
    })

    it('should render LayoutTypeTabs component', () => {
      expect(wrapper.findComponent({ name: 'LayoutTypeTabs' }).exists()).toBe(true)
    })

    it('should render RangeConfigurator component', () => {
      expect(wrapper.findComponent({ name: 'RangeConfigurator' }).exists()).toBe(true)
    })

    it('should render LocationPreview component', () => {
      expect(wrapper.findComponent({ name: 'LocationPreview' }).exists()).toBe(true)
    })
  })

  describe('Action Buttons', () => {
    it('should render Cancel button', () => {
      const cancelBtn = wrapper.find('[data-testid="cancel-button"]')
      expect(cancelBtn.exists()).toBe(true)
      expect(cancelBtn.attributes('label')).toContain('Cancel')
    })

    it('should render Create button', () => {
      const createBtn = wrapper.find('[data-testid="create-button"]')
      expect(createBtn.exists()).toBe(true)
      expect(createBtn.attributes('label')).toContain('Create')
    })

    it('should emit close event when Cancel is clicked', async () => {
      const cancelBtn = wrapper.find('[data-testid="cancel-button"]')
      await cancelBtn.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
    })

    it('should disable Create button when preview is invalid', async () => {
      // Set invalid configuration (will be handled by preview validation)
      const createBtn = wrapper.find('[data-testid="create-button"]')

      // Button should be disabled if no valid preview (Quasar uses 'disable' not 'disabled')
      await wrapper.vm.$nextTick()
      expect(createBtn.attributes('disable')).toBeDefined()
    })
  })

  describe('Layout Type Selection', () => {
    it('should default to "single" layout type', () => {
      expect(wrapper.vm.selectedLayoutType).toBe('single')
    })

    it('should update layout type when LayoutTypeTabs emits change', async () => {
      const tabs = wrapper.findComponent({ name: 'LayoutTypeTabs' })
      await tabs.vm.$emit('update:modelValue', 'row')

      expect(wrapper.vm.selectedLayoutType).toBe('row')
    })
  })

  describe('Configuration State', () => {
    it('should initialize with empty configuration', () => {
      expect(wrapper.vm.layoutConfig).toBeDefined()
      expect(wrapper.vm.layoutConfig.prefix).toBe('')
      expect(wrapper.vm.layoutConfig.ranges).toEqual([])
      expect(wrapper.vm.layoutConfig.separators).toEqual([])
    })

    it('should update configuration when RangeConfigurator emits change', async () => {
      const configurator = wrapper.findComponent({ name: 'RangeConfigurator' })

      const newConfig = {
        prefix: 'box-',
        ranges: [
          { range_type: 'letters', start: 'a', end: 'f', capitalize: false }
        ],
        separators: []
      }

      await configurator.vm.$emit('update:config', newConfig)

      expect(wrapper.vm.layoutConfig.prefix).toBe('box-')
      expect(wrapper.vm.layoutConfig.ranges).toHaveLength(1)
    })
  })

  describe('Preview Integration', () => {
    it('should pass preview data to LocationPreview component', async () => {
      const preview = wrapper.findComponent({ name: 'LocationPreview' })

      // Initially no preview data
      expect(preview.props('previewData')).toBeNull()

      // Set preview data
      wrapper.vm.previewData = {
        sample_names: ['box-a', 'box-b', 'box-c', 'box-d', 'box-e'],
        last_name: 'box-f',
        total_count: 6,
        warnings: [],
        errors: [],
        is_valid: true
      }

      await wrapper.vm.$nextTick()

      expect(preview.props('previewData')).toBeDefined()
      expect(preview.props('previewData').total_count).toBe(6)
    })

    it('should show loading state in preview when fetching', async () => {
      const preview = wrapper.findComponent({ name: 'LocationPreview' })

      wrapper.vm.previewLoading = true
      await wrapper.vm.$nextTick()

      expect(preview.props('loading')).toBe(true)
    })
  })

  describe('Form Options', () => {
    it('should render location type selector', () => {
      const typeSelect = wrapper.find('[data-testid="location-type-select"]')
      expect(typeSelect.exists()).toBe(true)
    })

    it('should render parent location selector', () => {
      const parentSelect = wrapper.find('[data-testid="parent-location-select"]')
      expect(parentSelect.exists()).toBe(true)
    })

    it('should render single-part-only checkbox', () => {
      const checkbox = wrapper.find('[data-testid="single-part-only-checkbox"]')
      expect(checkbox.exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should display validation errors from preview', async () => {
      wrapper.vm.previewData = {
        sample_names: [],
        last_name: '',
        total_count: 0,
        warnings: [],
        errors: ['Total location count (600) exceeds maximum limit of 500'],
        is_valid: false
      }

      await wrapper.vm.$nextTick()

      const errorMessage = wrapper.find('[data-testid="validation-errors"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('exceeds maximum limit of 500')
    })

    it('should display warnings from preview', async () => {
      wrapper.vm.previewData = {
        sample_names: ['bin-a-1', 'bin-a-2'],
        last_name: 'bin-z-100',
        total_count: 150,
        warnings: ['Creating 150 locations cannot be undone. Locations cannot be deleted.'],
        errors: [],
        is_valid: true
      }

      await wrapper.vm.$nextTick()

      const warning = wrapper.find('[data-testid="validation-warnings"]')
      expect(warning.exists()).toBe(true)
      expect(warning.text()).toContain('cannot be undone')
    })
  })

  describe('Dialog Behavior', () => {
    it('should reset form when dialog is closed', async () => {
      // Set some configuration
      wrapper.vm.layoutConfig.prefix = 'test-'
      wrapper.vm.selectedLayoutType = 'grid'

      // Close dialog
      await wrapper.setProps({ modelValue: false })

      // Should reset on next open
      await wrapper.setProps({ modelValue: true })

      expect(wrapper.vm.layoutConfig.prefix).toBe('')
      expect(wrapper.vm.selectedLayoutType).toBe('single')
    })

    it('should clear preview when configuration changes', async () => {
      wrapper.vm.previewData = {
        sample_names: ['box-a'],
        last_name: 'box-a',
        total_count: 1,
        warnings: [],
        errors: [],
        is_valid: true
      }

      // Change configuration
      const configurator = wrapper.findComponent({ name: 'RangeConfigurator' })
      await configurator.vm.$emit('update:config', { prefix: 'new-', ranges: [], separators: [] })

      // Preview should be cleared (will be refetched with debounce)
      expect(wrapper.vm.previewData).toBeNull()
    })
  })
})
