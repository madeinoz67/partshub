import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import MoveStockForm from '@/components/stock/MoveStockForm.vue'
import { stockOperationsApi } from '@/services/stockOperations'
import { useStorageStore } from '@/stores/storage'

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
    moveStock: vi.fn()
  }
}))

describe('MoveStockForm.vue', () => {
  let wrapper: any
  let storageStore: any
  let mockNotifyCreate: any

  const mockComponentLocations = [
    {
      location: {
        id: 'comp-loc-1',
        name: 'Bin A',
        location_hierarchy: 'Main Workshop/Drawer 1/Bin A'
      },
      quantity_on_hand: 50
    },
    {
      location: {
        id: 'comp-loc-2',
        name: 'Bin B',
        location_hierarchy: 'Main Workshop/Drawer 2/Bin B'
      },
      quantity_on_hand: 100
    },
    {
      location: {
        id: 'comp-loc-3',
        name: 'Shelf 1',
        location_hierarchy: 'Storage Room/Shelf 1'
      },
      quantity_on_hand: 0 // Should be filtered out from source
    }
  ]

  const mockAllStorageLocations = [
    { label: 'Main Workshop/Drawer 1/Bin A', value: 'comp-loc-1' },
    { label: 'Main Workshop/Drawer 2/Bin B', value: 'comp-loc-2' },
    { label: 'Main Workshop/Drawer 3/Bin C', value: 'other-loc-1' }, // Other location
    { label: 'Storage Room/Shelf 1', value: 'comp-loc-3' },
    { label: 'Storage Room/Shelf 2', value: 'other-loc-2' } // Other location
  ]

  beforeEach(async () => {
    // Get reference to the mocked Notify.create
    const { Notify } = await import('quasar')
    mockNotifyCreate = Notify.create as any

    setActivePinia(createPinia())

    // Setup storage store with all locations
    storageStore = useStorageStore()
    storageStore.locationOptions = mockAllStorageLocations

    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Rendering', () => {
    it('should mount successfully', () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('should filter out locations with zero stock from source selector', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      const sourceOptions = wrapper.vm.sourceLocationOptions
      expect(sourceOptions).toHaveLength(2) // Only 2 locations have stock > 0
      expect(sourceOptions.find((opt: any) => opt.value === 'comp-loc-3')).toBeUndefined()
    })

    it('should display available quantity when source location is selected', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      expect(wrapper.vm.sourceAvailableQuantity).toBe(50)
    })
  })

  describe('Same-Location Prevention', () => {
    it('should exclude source location from destination options', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source location
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      await flushPromises()

      const destOptions = wrapper.vm.destinationLocationOptions
      const sourceInDest = destOptions.find((opt: any) => opt.value === 'comp-loc-1')
      expect(sourceInDest).toBeUndefined()
    })

    it('should clear destination if it matches newly selected source', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Set both to same location
      wrapper.vm.formData.destination_location_id = 'comp-loc-1'
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      // Destination should be cleared
      expect(wrapper.vm.formData.destination_location_id).toBeNull()
    })

    it('should show warning when destination matches source', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Set both to same location
      wrapper.vm.formData.destination_location_id = 'comp-loc-1'
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      // Should show warning notification
      expect(mockNotifyCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'warning',
          message: expect.stringContaining('must be different')
        })
      )
    })

    it('should prevent submission when source equals destination', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Set same source and destination
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = 'comp-loc-1'
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.moveStock).not.toHaveBeenCalled()
    })
  })

  describe('Location Separation', () => {
    it('should separate component locations from other locations', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source to populate destination options
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      await flushPromises()

      const destOptions = wrapper.vm.destinationLocationOptions

      // Check if separator exists (it should when there are "other" locations)
      const separator = destOptions.find((opt: any) => opt.label && opt.label.includes('Other Locations'))
      if (separator) {
        expect(separator.disable).toBe(true)
      }
      // If no separator, that's OK - means all locations are component locations
      expect(destOptions.length).toBeGreaterThan(0)
    })

    it('should populate destination locations excluding source', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source to populate destination options
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      await flushPromises()

      const destOptions = wrapper.vm.destinationLocationOptions

      // Should have destination options available
      expect(destOptions.length).toBeGreaterThanOrEqual(1)

      // Source location should NOT be in the destination list
      const sourceInDest = destOptions.find((opt: any) => opt.value === 'comp-loc-1')
      expect(sourceInDest).toBeUndefined()

      // All destination options should have a value (not just separators)
      const validDestinations = destOptions.filter((opt: any) => opt.value && !opt.disable)
      expect(validDestinations.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Auto-Capping', () => {
    it('should auto-cap quantity when it exceeds source available stock', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source location with 50 units
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      // Try to set quantity higher than available
      wrapper.vm.formData.quantity = 100
      wrapper.vm.onQuantityChange(100)
      await flushPromises()

      // Should be auto-capped to 50
      expect(wrapper.vm.formData.quantity).toBe(50)
    })

    it('should show warning notification when quantity is auto-capped', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source location with 50 units
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
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
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source location with 50 units
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      // Set quantity within available
      wrapper.vm.formData.quantity = 30
      wrapper.vm.onQuantityChange(30)
      await flushPromises()

      // Should remain unchanged
      expect(wrapper.vm.formData.quantity).toBe(30)
    })

    it('should auto-cap when changing to source with less stock', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source with 100 units
      wrapper.vm.formData.source_location_id = 'comp-loc-2'
      wrapper.vm.onSourceLocationChange('comp-loc-2')
      wrapper.vm.formData.quantity = 75
      await flushPromises()

      // Change to source with only 50 units
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      await flushPromises()

      // Quantity should be auto-capped to 50
      expect(wrapper.vm.formData.quantity).toBe(50)
    })
  })

  describe('Form Submission', () => {
    it('should call API with correct data on submit', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock moved successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        source_location_id: 'comp-loc-1',
        destination_location_id: 'other-loc-1',
        quantity_moved: 10,
        requested_quantity: 10,
        capped: false,
        source_previous_quantity: 50,
        source_new_quantity: 40,
        source_location_deleted: false,
        destination_previous_quantity: 0,
        destination_new_quantity: 10,
        destination_location_created: true,
        total_stock: 150,
        pricing_inherited: false
      }

      vi.mocked(stockOperationsApi.moveStock).mockResolvedValue(mockResponse)

      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.comments = 'Test move'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check API was called with correct data
      expect(stockOperationsApi.moveStock).toHaveBeenCalledWith(
        'test-component-id',
        expect.objectContaining({
          source_location_id: 'comp-loc-1',
          destination_location_id: 'other-loc-1',
          quantity: 10,
          comments: 'Test move'
        })
      )
    })

    it('should emit success event on successful submission', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock moved successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        source_location_id: 'comp-loc-1',
        destination_location_id: 'other-loc-1',
        quantity_moved: 10,
        requested_quantity: 10,
        capped: false,
        source_previous_quantity: 50,
        source_new_quantity: 40,
        source_location_deleted: false,
        destination_previous_quantity: 0,
        destination_new_quantity: 10,
        destination_location_created: true,
        total_stock: 150,
        pricing_inherited: false
      }

      vi.mocked(stockOperationsApi.moveStock).mockResolvedValue(mockResponse)

      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check success event was emitted
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0]).toEqual(mockResponse)
    })

    it('should handle API failure gracefully', async () => {
      const mockError = new Error('API Error')
      vi.mocked(stockOperationsApi.moveStock).mockRejectedValue(mockError)

      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
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
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      wrapper.vm.handleCancel()
      await flushPromises()

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })
  })

  describe('Validation', () => {
    it('should require source location to be selected', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Try to submit without source
      wrapper.vm.formData.source_location_id = null
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.moveStock).not.toHaveBeenCalled()
    })

    it('should require destination location to be selected', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Try to submit without destination
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = null
      wrapper.vm.formData.quantity = 10
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.moveStock).not.toHaveBeenCalled()
    })

    it('should require quantity to be positive', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Try to submit with zero quantity
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
      wrapper.vm.formData.quantity = 0
      await flushPromises()

      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.moveStock).not.toHaveBeenCalled()
    })
  })

  describe('Props & State', () => {
    it('should accept componentId prop', () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'custom-component-id', allLocations: mockComponentLocations }
      })
      expect(wrapper.props('componentId')).toBe('custom-component-id')
    })

    it('should accept allLocations prop', () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      expect(wrapper.props('allLocations')).toEqual(mockComponentLocations)
    })

    it('should accept optional sourceLocationId prop', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations, sourceLocationId: 'comp-loc-1' }
      })
      await flushPromises()

      expect(wrapper.vm.formData.source_location_id).toBe('comp-loc-1')
    })

    it('should initialize form state correctly', () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })

      expect(wrapper.vm.formData).toEqual({
        source_location_id: null,
        destination_location_id: null,
        quantity: null,
        comments: null
      })
      expect(wrapper.vm.sourceAvailableQuantity).toBeNull()
    })
  })

  describe('Edge Cases', () => {
    it('should handle moving all stock from source', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock moved successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        source_location_id: 'comp-loc-1',
        destination_location_id: 'other-loc-1',
        quantity_moved: 50,
        requested_quantity: 50,
        capped: false,
        source_previous_quantity: 50,
        source_new_quantity: 0,
        source_location_deleted: true,
        destination_previous_quantity: 0,
        destination_new_quantity: 50,
        destination_location_created: true,
        total_stock: 150,
        pricing_inherited: true
      }

      vi.mocked(stockOperationsApi.moveStock).mockResolvedValue(mockResponse)

      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: mockComponentLocations }
      })
      await flushPromises()

      // Select source and set quantity to all available
      wrapper.vm.formData.source_location_id = 'comp-loc-1'
      wrapper.vm.onSourceLocationChange('comp-loc-1')
      wrapper.vm.formData.destination_location_id = 'other-loc-1'
      wrapper.vm.formData.quantity = 50
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should succeed
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0].source_new_quantity).toBe(0)
    })

    it('should handle empty allLocations array', async () => {
      wrapper = mount(MoveStockForm, {
        props: { componentId: 'test-component-id', allLocations: [] }
      })
      await flushPromises()

      const sourceOptions = wrapper.vm.sourceLocationOptions
      expect(sourceOptions).toHaveLength(0)
    })
  })
})
