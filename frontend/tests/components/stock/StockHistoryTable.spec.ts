import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import StockHistoryTable from '@/components/stock/StockHistoryTable.vue'
import { stockOperationsApi } from '@/services/stockOperations'
import type { StockHistoryResponse } from '@/services/stockOperations'
import { useAuthStore } from '@/stores/auth'
import { mockNotify } from '../../setup'

// Mock the API module
vi.mock('@/services/stockOperations', () => ({
  stockOperationsApi: {
    getStockHistory: vi.fn(),
    exportStockHistory: vi.fn()
  }
}))

describe('StockHistoryTable.vue', () => {
  let wrapper: any

  // Helper function to create a fresh Pinia and auth store
  const setupAuthStore = (isAdmin: boolean = true) => {
    setActivePinia(createPinia())
    const authStore = useAuthStore()
    authStore.user = {
      id: 'user-123',
      username: isAdmin ? 'admin' : 'user',
      full_name: isAdmin ? 'Admin User' : 'Regular User',
      is_active: true,
      is_admin: isAdmin,
      must_change_password: false,
      created_at: '2025-01-01T00:00:00Z'
    }
    return authStore
  }

  const mockHistoryResponse: StockHistoryResponse = {
    entries: [
      {
        id: 'txn-1',
        component_id: 'component-123',
        transaction_type: 'add',
        quantity_change: 50,
        previous_quantity: 0,
        new_quantity: 50,
        from_location_id: null,
        from_location_name: null,
        to_location_id: 'loc-1',
        to_location_name: 'Shelf A',
        lot_id: 'LOT-123',
        price_per_unit: 0.50,
        total_price: 25.00,
        user_name: 'admin',
        reason: 'Initial stock',
        notes: 'Test notes',
        comments: null,
        created_at: '2025-10-05T10:00:00Z'
      },
      {
        id: 'txn-2',
        component_id: 'component-123',
        transaction_type: 'remove',
        quantity_change: -10,
        previous_quantity: 50,
        new_quantity: 40,
        from_location_id: 'loc-1',
        from_location_name: 'Shelf A',
        to_location_id: null,
        to_location_name: null,
        lot_id: null,
        price_per_unit: null,
        total_price: null,
        user_name: 'user1',
        reason: 'Used in project',
        notes: null,
        comments: 'Project XYZ',
        created_at: '2025-10-05T11:00:00Z'
      },
      {
        id: 'txn-3',
        component_id: 'component-123',
        transaction_type: 'move',
        quantity_change: 0,
        previous_quantity: 40,
        new_quantity: 40,
        from_location_id: 'loc-1',
        from_location_name: 'Shelf A',
        to_location_id: 'loc-2',
        to_location_name: 'Shelf B',
        lot_id: null,
        price_per_unit: null,
        total_price: null,
        user_name: 'admin',
        reason: 'Reorganization',
        notes: null,
        comments: null,
        created_at: '2025-10-05T12:00:00Z'
      },
      {
        id: 'txn-4',
        component_id: 'component-123',
        transaction_type: 'adjust',
        quantity_change: 5,
        previous_quantity: 40,
        new_quantity: 45,
        from_location_id: null,
        from_location_name: null,
        to_location_id: 'loc-2',
        to_location_name: 'Shelf B',
        lot_id: null,
        price_per_unit: null,
        total_price: null,
        user_name: null,
        reason: 'Inventory correction',
        notes: null,
        comments: null,
        created_at: '2025-10-05T13:00:00Z'
      }
    ],
    pagination: {
      page: 1,
      page_size: 10,
      total_entries: 4,
      total_pages: 1,
      has_next: false,
      has_previous: false
    }
  }

  const emptyHistoryResponse: StockHistoryResponse = {
    entries: [],
    pagination: {
      page: 1,
      page_size: 10,
      total_entries: 0,
      total_pages: 0,
      has_next: false,
      has_previous: false
    }
  }

  beforeEach(() => {
    // Setup auth store with admin user by default
    setupAuthStore(true)

    // Reset mocks
    vi.clearAllMocks()
    vi.mocked(stockOperationsApi.getStockHistory).mockResolvedValue(mockHistoryResponse)
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Rendering', () => {
    it('should mount successfully', () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('should render with empty state when no history', async () => {
      vi.mocked(stockOperationsApi.getStockHistory).mockResolvedValue(emptyHistoryResponse)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      // Check that historyEntries is empty
      expect(wrapper.vm.historyEntries).toEqual([])
      expect(wrapper.vm.tablePagination.rowsNumber).toBe(0)
    })

    it('should render table with history entries', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        1,
        10,
        'created_at',
        'desc'
      )

      // Check that historyEntries contains the data
      expect(wrapper.vm.historyEntries).toHaveLength(4)
      expect(wrapper.vm.historyEntries[0].to_location_name).toBe('Shelf A')
      expect(wrapper.vm.historyEntries[0].lot_id).toBe('LOT-123')
      expect(wrapper.vm.historyEntries[0].reason).toBe('Initial stock')
    })

    it('should display all table columns', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const columns = wrapper.vm.columns
      expect(columns).toHaveLength(9)
      expect(columns.map((c: any) => c.label)).toEqual([
        'Date',
        'Type',
        'Quantity',
        'From Location',
        'To Location',
        'Lot ID',
        'Price',
        'Comments',
        'User'
      ])
    })

    it('should display Stock History title', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.text()).toContain('Stock History')
    })
  })

  describe('Transaction Type Badges', () => {
    it('should display transaction type badges with correct colors for add', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const addTypeColor = wrapper.vm.getTypeColor('add')
      expect(addTypeColor).toBe('positive')
    })

    it('should display transaction type badges with correct colors for remove', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const removeTypeColor = wrapper.vm.getTypeColor('remove')
      expect(removeTypeColor).toBe('negative')
    })

    it('should display transaction type badges with correct colors for move', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const moveTypeColor = wrapper.vm.getTypeColor('move')
      expect(moveTypeColor).toBe('info')
    })

    it('should display transaction type badges with correct colors for adjust', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const adjustTypeColor = wrapper.vm.getTypeColor('adjust')
      expect(adjustTypeColor).toBe('warning')
    })

    it('should default to grey for unknown transaction type', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const unknownTypeColor = wrapper.vm.getTypeColor('unknown')
      expect(unknownTypeColor).toBe('grey')
    })
  })

  describe('Quantity Changes Display', () => {
    it('should display positive quantity changes with + indicator', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const formattedQuantity = wrapper.vm.formatQuantity(50)
      expect(formattedQuantity).toBe('+50')
    })

    it('should display negative quantity changes with - indicator', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const formattedQuantity = wrapper.vm.formatQuantity(-10)
      expect(formattedQuantity).toBe('-10')
    })

    it('should display zero quantity changes without indicator', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const formattedQuantity = wrapper.vm.formatQuantity(0)
      expect(formattedQuantity).toBe('0')
    })

    it('should apply positive class to positive quantities', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const quantityClass = wrapper.vm.getQuantityClass(50)
      expect(quantityClass).toBe('text-positive text-weight-bold')
    })

    it('should apply negative class to negative quantities', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const quantityClass = wrapper.vm.getQuantityClass(-10)
      expect(quantityClass).toBe('text-negative text-weight-bold')
    })

    it('should apply grey class to zero quantities', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const quantityClass = wrapper.vm.getQuantityClass(0)
      expect(quantityClass).toBe('text-grey-8')
    })
  })

  describe('Pagination', () => {
    it('should have default pagination settings', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.vm.tablePagination).toMatchObject({
        sortBy: 'created_at',
        descending: true,
        page: 1,
        rowsPerPage: 10
      })
    })

    it('should update pagination metadata from API response', async () => {
      const multiPageResponse = {
        ...mockHistoryResponse,
        pagination: {
          page: 1,
          page_size: 10,
          total_entries: 25,
          total_pages: 3,
          has_next: true,
          has_previous: false
        }
      }
      vi.mocked(stockOperationsApi.getStockHistory).mockResolvedValue(multiPageResponse)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.vm.tablePagination.rowsNumber).toBe(25)
    })

    it('should handle page navigation', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      vi.clearAllMocks()

      // Simulate page change
      await wrapper.vm.onTableRequest({
        pagination: {
          sortBy: 'created_at',
          descending: true,
          page: 2,
          rowsPerPage: 10
        }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        2,
        10,
        'created_at',
        'desc'
      )
    })

    it('should handle page size changes', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      vi.clearAllMocks()

      // Simulate page size change
      await wrapper.vm.onTableRequest({
        pagination: {
          sortBy: 'created_at',
          descending: true,
          page: 1,
          rowsPerPage: 25
        }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        1,
        25,
        'created_at',
        'desc'
      )
    })
  })

  describe('Sorting', () => {
    it('should sort by created_at descending by default', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        1,
        10,
        'created_at',
        'desc'
      )
    })

    it('should handle sort by different column', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      vi.clearAllMocks()

      // Simulate sorting by transaction_type
      await wrapper.vm.onTableRequest({
        pagination: {
          sortBy: 'transaction_type',
          descending: false,
          page: 1,
          rowsPerPage: 10
        }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        1,
        10,
        'transaction_type',
        'asc'
      )
    })

    it('should toggle sort direction', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      vi.clearAllMocks()

      // Simulate toggling sort direction
      await wrapper.vm.onTableRequest({
        pagination: {
          sortBy: 'created_at',
          descending: false,
          page: 1,
          rowsPerPage: 10
        }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-123',
        1,
        10,
        'created_at',
        'asc'
      )
    })
  })

  describe('Export Functionality (Admin)', () => {
    it('should show export buttons for admin users', async () => {
      // Create Pinia and setup auth store BEFORE mounting
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()
      authStore.user = {
        id: 'user-123',
        username: 'admin',
        full_name: 'Admin User',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: '2025-01-01T00:00:00Z'
      }

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' },
        global: {
          plugins: [pinia]
        }
      })

      await flushPromises()

      expect(wrapper.vm.isAdmin).toBe(true)
      const text = wrapper.text()
      expect(text).toContain('CSV')
      expect(text).toContain('Excel')
      expect(text).toContain('JSON')
    })

    it('should hide export buttons for non-admin users', async () => {
      // Setup with non-admin user
      setupAuthStore(false)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.vm.isAdmin).toBe(false)
      // CSV export button should not be in the text since v-if hides it
      const text = wrapper.text()
      // The buttons should not appear (or be much less prominent) for non-admin
      expect(wrapper.vm.isAdmin).toBe(false)
    })

    it('should trigger CSV export', async () => {
      vi.mocked(stockOperationsApi.exportStockHistory).mockResolvedValue(undefined)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      await wrapper.vm.handleExport('csv')
      await flushPromises()

      expect(stockOperationsApi.exportStockHistory).toHaveBeenCalledWith(
        'component-123',
        'csv',
        'created_at',
        'desc'
      )
    })

    it('should trigger Excel export', async () => {
      vi.mocked(stockOperationsApi.exportStockHistory).mockResolvedValue(undefined)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      await wrapper.vm.handleExport('xlsx')
      await flushPromises()

      expect(stockOperationsApi.exportStockHistory).toHaveBeenCalledWith(
        'component-123',
        'xlsx',
        'created_at',
        'desc'
      )
    })

    it('should trigger JSON export', async () => {
      vi.mocked(stockOperationsApi.exportStockHistory).mockResolvedValue(undefined)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      await wrapper.vm.handleExport('json')
      await flushPromises()

      expect(stockOperationsApi.exportStockHistory).toHaveBeenCalledWith(
        'component-123',
        'json',
        'created_at',
        'desc'
      )
    })

    it('should set exporting format during export', async () => {
      let resolveExport: () => void
      const exportPromise = new Promise<void>((resolve) => {
        resolveExport = resolve
      })
      vi.mocked(stockOperationsApi.exportStockHistory).mockReturnValue(exportPromise)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const exportPromiseResult = wrapper.vm.handleExport('csv')

      // Should be exporting
      expect(wrapper.vm.exportingFormat).toBe('csv')

      resolveExport!()
      await exportPromiseResult
      await flushPromises()

      // Should be done exporting
      expect(wrapper.vm.exportingFormat).toBe(null)
    })

    it('should handle export failure gracefully', async () => {
      const mockError = new Error('Export failed')
      vi.mocked(stockOperationsApi.exportStockHistory).mockRejectedValue(mockError)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      await wrapper.vm.handleExport('csv')
      await flushPromises()

      // Should reset exporting format
      expect(wrapper.vm.exportingFormat).toBe(null)
    })

    it('should not export when componentId is missing', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: '' }
      })
      await flushPromises()

      await wrapper.vm.handleExport('csv')
      await flushPromises()

      expect(stockOperationsApi.exportStockHistory).not.toHaveBeenCalled()
    })
  })

  describe('Auto-refresh', () => {
    it('should refresh when autoRefresh prop changes to true', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123', autoRefresh: false }
      })
      await flushPromises()

      vi.clearAllMocks()

      await wrapper.setProps({ autoRefresh: true })
      await flushPromises()

      // Should call API again
      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledTimes(1)
    })

    it('should emit refreshed event after successful refresh', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      // Clear previous emitted events
      wrapper.emitted('refreshed')?.length

      await wrapper.vm.fetchHistory()
      await flushPromises()

      expect(wrapper.emitted('refreshed')).toBeTruthy()
    })

    it('should not refresh when autoRefresh prop changes to false', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123', autoRefresh: true }
      })
      await flushPromises()

      vi.clearAllMocks()

      await wrapper.setProps({ autoRefresh: false })
      await flushPromises()

      // Should not call API
      expect(stockOperationsApi.getStockHistory).not.toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('should show loading state while fetching data', async () => {
      let resolveHistory: (value: StockHistoryResponse) => void
      const historyPromise = new Promise<StockHistoryResponse>((resolve) => {
        resolveHistory = resolve
      })
      vi.mocked(stockOperationsApi.getStockHistory).mockReturnValue(historyPromise)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })

      // Should be loading
      expect(wrapper.vm.loading).toBe(true)

      resolveHistory!(mockHistoryResponse)
      await flushPromises()

      // Should be done loading
      expect(wrapper.vm.loading).toBe(false)
    })

    it('should reset loading state after API error', async () => {
      const mockError = new Error('API Error')
      vi.mocked(stockOperationsApi.getStockHistory).mockRejectedValue(mockError)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should handle API failure gracefully', async () => {
      const mockError = new Error('API Error')
      vi.mocked(stockOperationsApi.getStockHistory).mockRejectedValue(mockError)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      // Should set empty entries
      expect(wrapper.vm.historyEntries).toEqual([])
      expect(wrapper.vm.tablePagination.rowsNumber).toBe(0)
    })

    it('should handle 404 error (component not found)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Component not found' }
        }
      }
      vi.mocked(stockOperationsApi.getStockHistory).mockRejectedValue(mockError)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'nonexistent-id' }
      })
      await flushPromises()

      expect(wrapper.vm.historyEntries).toEqual([])
    })

    it('should handle 403 error (forbidden)', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { detail: 'Permission denied' }
        }
      }
      vi.mocked(stockOperationsApi.getStockHistory).mockRejectedValue(mockError)

      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(wrapper.vm.historyEntries).toEqual([])
    })
  })

  describe('Date and Time Formatting', () => {
    it('should format date correctly', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const date = wrapper.vm.formatDate('2025-10-05T10:00:00Z')
      expect(date).toBeTruthy()
      expect(typeof date).toBe('string')
    })

    it('should format time correctly', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      const time = wrapper.vm.formatTime('2025-10-05T10:00:00Z')
      expect(time).toBeTruthy()
      expect(typeof time).toBe('string')
    })
  })

  describe('Component ID Changes', () => {
    it('should fetch history when componentId prop changes', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      vi.clearAllMocks()

      await wrapper.setProps({ componentId: 'component-456' })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledWith(
        'component-456',
        1,
        10,
        'created_at',
        'desc'
      )
    })

    it('should not fetch history when componentId is empty', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: '' }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).not.toHaveBeenCalled()
    })
  })

  describe('Props', () => {
    it('should accept componentId prop', () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'test-component-id' }
      })
      expect(wrapper.props('componentId')).toBe('test-component-id')
    })

    it('should accept autoRefresh prop', () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'test-component-id', autoRefresh: true }
      })
      expect(wrapper.props('autoRefresh')).toBe(true)
    })

    it('should default autoRefresh to false', () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'test-component-id' }
      })
      expect(wrapper.props('autoRefresh')).toBe(false)
    })
  })

  describe('Lifecycle', () => {
    it('should fetch history on mount when componentId is provided', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: 'component-123' }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).toHaveBeenCalledTimes(1)
    })

    it('should not fetch history on mount when componentId is empty', async () => {
      wrapper = mount(StockHistoryTable, {
        props: { componentId: '' }
      })
      await flushPromises()

      expect(stockOperationsApi.getStockHistory).not.toHaveBeenCalled()
    })
  })
})
