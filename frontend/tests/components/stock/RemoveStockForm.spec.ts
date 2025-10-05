import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import RemoveStockForm from '@/components/stock/RemoveStockForm.vue'
import { stockOperationsApi } from '@/services/stockOperations'

// Mock Quasar Notify - create inline mock
vi.mock('quasar', async () => {
  const actual = await vi.importActual('quasar')
  return {
    ...actual,
    Notify: {
      create: vi.fn()
    }
  }
})

// Mock the API module
vi.mock('@/services/stockOperations', () => ({
  stockOperationsApi: {
    removeStock: vi.fn()
  }
}))

describe('RemoveStockForm.vue', () => {
  let wrapper: any
  let mockNotifyCreate: any

  const mockLocations = [
    {
      location: {
        id: 'location-1',
        name: 'Bin A',
        location_hierarchy: 'Main Workshop/Drawer 1/Bin A'
      },
      quantity_on_hand: 50
    },
    {
      location: {
        id: 'location-2',
        name: 'Bin B',
        location_hierarchy: 'Main Workshop/Drawer 2/Bin B'
      },
      quantity_on_hand: 100
    },
    {
      location: {
        id: 'location-3',
        name: 'Shelf 1',
        location_hierarchy: 'Storage Room/Shelf 1'
      },
      quantity_on_hand: 0 // Should be filtered out
    }
  ]

  beforeEach(async () => {
    // Get reference to the mocked Notify.create
    const { Notify } = await import('quasar')
    mockNotifyCreate = Notify.create as any

    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Rendering', () => {
    it('should mount successfully', () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('should filter out locations with zero stock', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      const options = wrapper.vm.locationOptionsWithQuantity
      expect(options).toHaveLength(2) // Only 2 locations have stock > 0
      expect(options.find((opt: any) => opt.value === 'location-3')).toBeUndefined()
    })

    it('should display available quantity when location is selected', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      await flushPromises()

      expect(wrapper.vm.availableQuantity).toBe(50)
    })
  })

  describe('Auto-Capping Behavior', () => {
    it('should auto-cap quantity when it exceeds available stock', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Select location with 50 units
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      await flushPromises()

      // Try to set quantity higher than available
      wrapper.vm.formData.quantity = 100
      wrapper.vm.onQuantityChange(100)
      await flushPromises()

      // Should be auto-capped to 50
      expect(wrapper.vm.formData.quantity).toBe(50)
    })

    it('should show warning notification when quantity is auto-capped', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Select location with 50 units
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      await flushPromises()

      // Try to set quantity higher than available
      wrapper.vm.formData.quantity = 100
      wrapper.vm.onQuantityChange(100)
      await flushPromises()

      // Should show warning notification
      expect(mockNotifyCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'warning',
          message: expect.stringContaining('auto-capped at 50')
        })
      )
    })

    it('should not auto-cap when quantity is within available stock', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Select location with 50 units
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      await flushPromises()

      // Set quantity within available
      wrapper.vm.formData.quantity = 30
      wrapper.vm.onQuantityChange(30)
      await flushPromises()

      // Should remain unchanged
      expect(wrapper.vm.formData.quantity).toBe(30)
    })

    it('should auto-cap quantity when changing to location with less stock', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Select location with 100 units
      wrapper.vm.formData.location_id = 'location-2'
      wrapper.vm.onLocationChange('location-2')
      wrapper.vm.formData.quantity = 75
      await flushPromises()

      // Change to location with only 50 units
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      await flushPromises()

      // Quantity should be auto-capped to 50
      expect(wrapper.vm.formData.quantity).toBe(50)
    })
  })

  describe('Form Submission', () => {
    it('should call API with correct data on submit', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock removed successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_removed: 10,
        requested_quantity: 10,
        capped: false,
        previous_quantity: 50,
        new_quantity: 40,
        location_deleted: false,
        total_stock: 140
      }

      vi.mocked(stockOperationsApi.removeStock).mockResolvedValue(mockResponse)

      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.reason = 'used'
      wrapper.vm.formData.comments = 'Test removal'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check API was called with correct data
      expect(stockOperationsApi.removeStock).toHaveBeenCalledWith(
        'test-component-id',
        expect.objectContaining({
          location_id: 'location-1',
          quantity: 10,
          reason: 'used',
          comments: 'Test removal'
        })
      )
    })

    it('should emit success event on successful submission', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock removed successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_removed: 10,
        requested_quantity: 10,
        capped: false,
        previous_quantity: 50,
        new_quantity: 40,
        location_deleted: false,
        total_stock: 140
      }

      vi.mocked(stockOperationsApi.removeStock).mockResolvedValue(mockResponse)

      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check success event was emitted
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0]).toEqual(mockResponse)
    })

    it('should handle capped response correctly', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock removed (capped)',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_removed: 50,
        requested_quantity: 100,
        capped: true,
        previous_quantity: 50,
        new_quantity: 0,
        location_deleted: true,
        total_stock: 100
      }

      vi.mocked(stockOperationsApi.removeStock).mockResolvedValue(mockResponse)

      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.quantity = 100
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should emit success with capped response
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0].capped).toBe(true)
    })

    it('should handle API failure gracefully', async () => {
      const mockError = new Error('API Error')
      vi.mocked(stockOperationsApi.removeStock).mockRejectedValue(mockError)

      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not emit success
      expect(wrapper.emitted('success')).toBeFalsy()

      // Submitting flag should be reset
      expect(wrapper.vm.submitting).toBe(false)
    })

    it('should emit cancel event when handleCancel is called', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      wrapper.vm.handleCancel()
      await flushPromises()

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })
  })

  describe('Validation', () => {
    it('should require location to be selected', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Try to submit without location
      wrapper.vm.formData.location_id = null
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.removeStock).not.toHaveBeenCalled()
    })

    it('should require quantity to be positive', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Try to submit with zero quantity
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.quantity = 0
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.removeStock).not.toHaveBeenCalled()
    })
  })

  describe('Props & State', () => {
    it('should accept componentId prop', () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'custom-component-id', locations: mockLocations }
      })
      expect(wrapper.props('componentId')).toBe('custom-component-id')
    })

    it('should accept locations prop', () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      expect(wrapper.props('locations')).toEqual(mockLocations)
    })

    it('should initialize form state correctly', () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })

      expect(wrapper.vm.formData).toEqual({
        location_id: null,
        quantity: null,
        reason: null,
        comments: null
      })
      expect(wrapper.vm.availableQuantity).toBeNull()
    })
  })

  describe('Edge Cases', () => {
    it('should handle removing all stock (quantity = available)', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock removed successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_removed: 50,
        requested_quantity: 50,
        capped: false,
        previous_quantity: 50,
        new_quantity: 0,
        location_deleted: true,
        total_stock: 100
      }

      vi.mocked(stockOperationsApi.removeStock).mockResolvedValue(mockResponse)

      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: mockLocations }
      })
      await flushPromises()

      // Select location and set quantity to all available
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.onLocationChange('location-1')
      wrapper.vm.formData.quantity = 50
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should succeed
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0].new_quantity).toBe(0)
    })

    it('should handle empty locations array', async () => {
      wrapper = mount(RemoveStockForm, {
        props: { componentId: 'test-component-id', locations: [] }
      })
      await flushPromises()

      const options = wrapper.vm.locationOptionsWithQuantity
      expect(options).toHaveLength(0)
    })
  })
})
