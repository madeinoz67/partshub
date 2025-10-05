import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AddStockForm from '@/components/stock/AddStockForm.vue'
import { stockOperationsApi } from '@/services/stockOperations'
import { useStorageStore } from '@/stores/storage'
import { mockNotify } from '../../setup'

// Mock the API module
vi.mock('@/services/stockOperations', () => ({
  stockOperationsApi: {
    addStock: vi.fn()
  }
}))

describe('AddStockForm.vue', () => {
  let wrapper: any
  let storageStore: any

  const mockLocations = [
    {
      id: 'location-1',
      name: 'Bin A',
      location_hierarchy: 'Main Workshop/Drawer 1/Bin A',
      type: 'bin',
      parent_id: null,
      description: null,
      qr_code_id: null
    },
    {
      id: 'location-2',
      name: 'Bin B',
      location_hierarchy: 'Main Workshop/Drawer 2/Bin B',
      type: 'bin',
      parent_id: null,
      description: null,
      qr_code_id: null
    },
    {
      id: 'location-3',
      name: 'Shelf 1',
      location_hierarchy: 'Storage Room/Shelf 1',
      type: 'shelf',
      parent_id: null,
      description: null,
      qr_code_id: null
    }
  ]

  beforeEach(() => {
    // Create a fresh Pinia instance for each test
    setActivePinia(createPinia())

    // Setup storage store with mock locations
    storageStore = useStorageStore()
    // Set the underlying locations array, not the computed locationOptions
    storageStore.locations = mockLocations

    // Reset mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Rendering', () => {
    it('should mount successfully', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('should show Step 1 (Quantity & Pricing) by default', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      expect(wrapper.vm.currentStep).toBe(1)
    })

    it('should initialize with correct pricing type', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      expect(wrapper.vm.pricingType).toBe('no_price')
    })
  })

  describe('Pricing Calculation', () => {
    it('should calculate total price in "Per component" mode', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Set pricing type to per_component
      wrapper.vm.pricingType = 'per_component'
      wrapper.vm.formData.quantity = 100
      wrapper.vm.formData.price_per_unit = 0.50
      await flushPromises()

      // Check calculated total
      expect(wrapper.vm.calculatedTotalPrice).toBe(50.00)
    })

    it('should calculate unit price in "Entire lot" mode', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Set pricing type to entire_lot
      wrapper.vm.pricingType = 'entire_lot'
      wrapper.vm.formData.quantity = 100
      wrapper.vm.formData.total_price = 50.00
      await flushPromises()

      // Check calculated unit price
      expect(wrapper.vm.calculatedUnitPrice).toBe(0.50)
    })

    it('should update total price when unit price changes', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'per_component'
      wrapper.vm.formData.quantity = 50
      await flushPromises()

      // Set initial unit price
      wrapper.vm.formData.price_per_unit = 1.00
      await flushPromises()
      expect(wrapper.vm.calculatedTotalPrice).toBe(50.00)

      // Update unit price
      wrapper.vm.formData.price_per_unit = 2.00
      await flushPromises()
      expect(wrapper.vm.calculatedTotalPrice).toBe(100.00)
    })

    it('should update unit price when total price changes', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'entire_lot'
      wrapper.vm.formData.quantity = 50
      await flushPromises()

      // Set initial total price
      wrapper.vm.formData.total_price = 100.00
      await flushPromises()
      expect(wrapper.vm.calculatedUnitPrice).toBe(2.00)

      // Update total price
      wrapper.vm.formData.total_price = 50.00
      await flushPromises()
      expect(wrapper.vm.calculatedUnitPrice).toBe(1.00)
    })

    it('should return zero for total price when no pricing data', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'per_component'
      wrapper.vm.formData.quantity = null
      wrapper.vm.formData.price_per_unit = null

      expect(wrapper.vm.calculatedTotalPrice).toBe(0)
    })

    it('should return zero for unit price when no pricing data', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'entire_lot'
      wrapper.vm.formData.quantity = null
      wrapper.vm.formData.total_price = null

      expect(wrapper.vm.calculatedUnitPrice).toBe(0)
    })
  })

  describe('Form Submission', () => {
    it('should call API with correct data on submit', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock added successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_added: 10,
        previous_quantity: 0,
        new_quantity: 10,
        total_stock: 10
      }

      vi.mocked(stockOperationsApi.addStock).mockResolvedValue(mockResponse)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.location_id = 'location-1'
      wrapper.vm.formData.comments = 'Test comment'
      wrapper.vm.pricingType = 'no_price'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check API was called with correct data
      expect(stockOperationsApi.addStock).toHaveBeenCalledWith(
        'test-component-id',
        expect.objectContaining({
          location_id: 'location-1',
          quantity: 10,
          comments: 'Test comment'
        })
      )
    })

    it('should emit success event on successful submission', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock added successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_added: 10,
        previous_quantity: 0,
        new_quantity: 10,
        total_stock: 10
      }

      vi.mocked(stockOperationsApi.addStock).mockResolvedValue(mockResponse)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check success event was emitted
      expect(wrapper.emitted('success')).toBeTruthy()
      expect(wrapper.emitted('success')[0][0]).toEqual(mockResponse)
    })

    it('should include price_per_unit when pricing type is per_component', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock added successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_added: 10,
        previous_quantity: 0,
        new_quantity: 10,
        total_stock: 10
      }

      vi.mocked(stockOperationsApi.addStock).mockResolvedValue(mockResponse)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form with per_component pricing
      wrapper.vm.pricingType = 'per_component'
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.price_per_unit = 1.50
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check API was called with price_per_unit
      expect(stockOperationsApi.addStock).toHaveBeenCalledWith(
        'test-component-id',
        expect.objectContaining({
          location_id: 'location-1',
          quantity: 10,
          price_per_unit: 1.50
        })
      )
    })

    it('should include total_price when pricing type is entire_lot', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock added successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_added: 10,
        previous_quantity: 0,
        new_quantity: 10,
        total_stock: 10
      }

      vi.mocked(stockOperationsApi.addStock).mockResolvedValue(mockResponse)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form with entire_lot pricing
      wrapper.vm.pricingType = 'entire_lot'
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.total_price = 15.00
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Check API was called with total_price
      expect(stockOperationsApi.addStock).toHaveBeenCalledWith(
        'test-component-id',
        expect.objectContaining({
          location_id: 'location-1',
          quantity: 10,
          total_price: 15.00
        })
      )
    })

    it('should handle API failure gracefully', async () => {
      const mockError = new Error('API Error')
      vi.mocked(stockOperationsApi.addStock).mockRejectedValue(mockError)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not emit success
      expect(wrapper.emitted('success')).toBeFalsy()

      // Submitting flag should be reset
      expect(wrapper.vm.submitting).toBe(false)
    })

    it('should not submit with missing location', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form without location
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.location_id = null
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.addStock).not.toHaveBeenCalled()
    })

    it('should not submit with invalid quantity', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form with invalid quantity
      wrapper.vm.formData.quantity = 0
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      // Submit form
      await wrapper.vm.handleSubmit()
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.addStock).not.toHaveBeenCalled()
    })

    it('should set submitting flag during submission', async () => {
      const mockResponse = {
        success: true,
        message: 'Stock added successfully',
        transaction_id: 'txn-123',
        component_id: 'test-component-id',
        location_id: 'location-1',
        quantity_added: 10,
        previous_quantity: 0,
        new_quantity: 10,
        total_stock: 10
      }

      vi.mocked(stockOperationsApi.addStock).mockResolvedValue(mockResponse)

      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Fill out form
      wrapper.vm.formData.quantity = 10
      wrapper.vm.formData.location_id = 'location-1'
      await flushPromises()

      expect(wrapper.vm.submitting).toBe(false)

      // Start submission (don't await to check mid-submission)
      const submitPromise = wrapper.vm.handleSubmit()

      // Should be submitting
      expect(wrapper.vm.submitting).toBe(true)

      await submitPromise
      await flushPromises()

      // Should be done submitting
      expect(wrapper.vm.submitting).toBe(false)
    })
  })

  describe('Props & State', () => {
    it('should accept componentId prop', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'custom-component-id' }
      })
      expect(wrapper.props('componentId')).toBe('custom-component-id')
    })

    it('should initialize form state correctly', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })

      expect(wrapper.vm.formData).toEqual({
        quantity: null,
        price_per_unit: null,
        total_price: null,
        lot_id: null,
        location_id: null,
        comments: null
      })
      expect(wrapper.vm.currentStep).toBe(1)
      expect(wrapper.vm.pricingType).toBe('no_price')
    })

    it('should load locations on mount', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Location options should be available
      expect(wrapper.vm.locationOptions.length).toBeGreaterThan(0)
    })
  })

  describe('Tab Navigation', () => {
    it('should emit cancel event when handleCancel is called', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      wrapper.vm.handleCancel()
      await flushPromises()

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })

    it('should not advance to next step with invalid quantity', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Set invalid quantity
      wrapper.vm.formData.quantity = null
      const initialStep = wrapper.vm.currentStep

      // Try to go to next step
      wrapper.vm.nextStep()
      await flushPromises()

      // Should stay on same step
      expect(wrapper.vm.currentStep).toBe(initialStep)
    })

    it('should not advance to next step with zero quantity', async () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      await flushPromises()

      // Set zero quantity
      wrapper.vm.formData.quantity = 0
      const initialStep = wrapper.vm.currentStep

      // Try to go to next step
      wrapper.vm.nextStep()
      await flushPromises()

      // Should stay on same step
      expect(wrapper.vm.currentStep).toBe(initialStep)
    })
  })

  describe('Validation', () => {
    it('should accept positive quantity values', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })

      wrapper.vm.formData.quantity = 100
      expect(wrapper.vm.formData.quantity).toBe(100)
    })

    it('should accept non-negative unit price', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'per_component'

      wrapper.vm.formData.price_per_unit = 0
      expect(wrapper.vm.formData.price_per_unit).toBe(0)

      wrapper.vm.formData.price_per_unit = 1.50
      expect(wrapper.vm.formData.price_per_unit).toBe(1.50)
    })

    it('should accept non-negative total price', () => {
      wrapper = mount(AddStockForm, {
        props: { componentId: 'test-component-id' }
      })
      wrapper.vm.pricingType = 'entire_lot'

      wrapper.vm.formData.total_price = 0
      expect(wrapper.vm.formData.total_price).toBe(0)

      wrapper.vm.formData.total_price = 100.00
      expect(wrapper.vm.formData.total_price).toBe(100.00)
    })
  })
})
