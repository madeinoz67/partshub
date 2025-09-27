/**
 * Pinia store for components state management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { APIService, Component, ComponentsListResponse, ComponentFilters, StockTransaction } from '../services/api'

export const useComponentsStore = defineStore('components', () => {
  // State
  const components = ref<Component[]>([])
  const currentComponent = ref<Component | null>(null)
  const stockHistory = ref<StockTransaction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Pagination state
  const totalComponents = ref(0)
  const currentPage = ref(1)
  const totalPages = ref(1)
  const itemsPerPage = ref(50)

  // Metrics state (always calculated from full dataset for dashboard)
  const totalLowStock = ref(0)
  const totalOutOfStock = ref(0)
  const totalAvailable = ref(0)

  // Filter state
  const filters = ref<ComponentFilters>({
    search: '',
    category: '',
    storage_location: '',
    component_type: '',
    stock_status: undefined,
    sort_by: 'name',
    sort_order: 'asc',
  })

  // Getters
  const lowStockComponents = computed(() =>
    components.value.filter(c => c.quantity_on_hand <= c.minimum_stock && c.minimum_stock > 0)
  )

  const outOfStockComponents = computed(() =>
    components.value.filter(c => c.quantity_on_hand === 0)
  )

  const componentsByCategory = computed(() => {
    const grouped: Record<string, Component[]> = {}
    components.value.forEach(component => {
      const categoryName = component.category?.name || 'Uncategorized'
      if (!grouped[categoryName]) {
        grouped[categoryName] = []
      }
      grouped[categoryName].push(component)
    })
    return grouped
  })

  // Actions
  const fetchComponents = async (newFilters?: Partial<ComponentFilters>) => {
    loading.value = true
    error.value = null

    try {
      if (newFilters) {
        Object.assign(filters.value, newFilters)
      }

      const params: ComponentFilters = {
        ...filters.value,
        limit: itemsPerPage.value,
        offset: (currentPage.value - 1) * itemsPerPage.value,
      }

      const response: ComponentsListResponse = await APIService.getComponents(params)

      components.value = response.components
      totalComponents.value = response.total
      currentPage.value = response.page
      totalPages.value = response.total_pages

    } catch (err: any) {
      error.value = err.message || 'Failed to fetch components'
      console.error('Error fetching components:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchComponent = async (id: string) => {
    loading.value = true
    error.value = null

    try {
      currentComponent.value = await APIService.getComponent(id)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch component'
      console.error('Error fetching component:', err)
    } finally {
      loading.value = false
    }
  }

  const createComponent = async (data: Partial<Component>) => {
    loading.value = true
    error.value = null

    try {
      const newComponent = await APIService.createComponent(data)
      components.value.push(newComponent)
      totalComponents.value += 1
      return newComponent
    } catch (err: any) {
      error.value = err.message || 'Failed to create component'
      console.error('Error creating component:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateComponent = async (id: string, data: Partial<Component>) => {
    loading.value = true
    error.value = null

    try {
      const updatedComponent = await APIService.updateComponent(id, data)

      // Update in list
      const index = components.value.findIndex(c => c.id === id)
      if (index !== -1) {
        components.value[index] = updatedComponent
      }

      // Update current if it's the same component
      if (currentComponent.value?.id === id) {
        currentComponent.value = updatedComponent
      }

      return updatedComponent
    } catch (err: any) {
      error.value = err.message || 'Failed to update component'
      console.error('Error updating component:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteComponent = async (id: string) => {
    loading.value = true
    error.value = null

    try {
      await APIService.deleteComponent(id)

      // Remove from list
      components.value = components.value.filter(c => c.id !== id)
      totalComponents.value -= 1

      // Clear current if it's the deleted component
      if (currentComponent.value?.id === id) {
        currentComponent.value = null
      }

    } catch (err: any) {
      error.value = err.message || 'Failed to delete component'
      console.error('Error deleting component:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateStock = async (
    id: string,
    transaction: {
      transaction_type: 'add' | 'remove' | 'move' | 'adjust'
      quantity_change: number
      reason: string
      reference_id?: string
    }
  ) => {
    loading.value = true
    error.value = null

    try {
      const stockTransaction = await APIService.updateStock(id, transaction)

      // Update component quantities in store
      const component = components.value.find(c => c.id === id)
      if (component) {
        component.quantity_on_hand = stockTransaction.new_quantity
      }

      if (currentComponent.value?.id === id) {
        currentComponent.value.quantity_on_hand = stockTransaction.new_quantity
      }

      return stockTransaction
    } catch (err: any) {
      error.value = err.message || 'Failed to update stock'
      console.error('Error updating stock:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchStockHistory = async (id: string, limit = 50) => {
    loading.value = true
    error.value = null

    try {
      stockHistory.value = await APIService.getStockHistory(id, limit)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch stock history'
      console.error('Error fetching stock history:', err)
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  const setPage = (page: number) => {
    currentPage.value = page
    fetchComponents()
  }

  const setItemsPerPage = (count: number) => {
    itemsPerPage.value = count
    currentPage.value = 1
    fetchComponents()
  }

  const searchComponents = (query: string) => {
    filters.value.search = query
    currentPage.value = 1
    fetchComponents()
  }

  const filterByCategory = (category: string) => {
    filters.value.category = category
    currentPage.value = 1
    fetchComponents()
  }

  const filterByStockStatus = (status: 'low' | 'out' | 'available' | undefined) => {
    filters.value.stock_status = status
    currentPage.value = 1
    fetchComponents()
  }

  const sortComponents = (field: 'name' | 'quantity' | 'created_at', order: 'asc' | 'desc') => {
    filters.value.sort_by = field
    filters.value.sort_order = order
    fetchComponents()
  }

  const clearFilters = () => {
    filters.value = {
      search: '',
      category: '',
      storage_location: '',
      component_type: '',
      stock_status: undefined,
      sort_by: 'name',
      sort_order: 'asc',
    }
    currentPage.value = 1
    fetchComponents()
  }

  const fetchMetrics = async () => {
    try {
      // Fetch metrics by making separate API calls for each status
      const [lowStockResponse, outOfStockResponse, totalResponse] = await Promise.all([
        APIService.getComponents({ stock_status: 'low', limit: 1 }),
        APIService.getComponents({ stock_status: 'out', limit: 1 }),
        APIService.getComponents({ limit: 1 })
      ])

      totalLowStock.value = lowStockResponse.total
      totalOutOfStock.value = outOfStockResponse.total
      totalComponents.value = totalResponse.total
      totalAvailable.value = totalResponse.total - outOfStockResponse.total

    } catch (err: any) {
      console.error('Error fetching metrics:', err)
    }
  }

  return {
    // State
    components,
    currentComponent,
    stockHistory,
    loading,
    error,
    totalComponents,
    currentPage,
    totalPages,
    itemsPerPage,
    filters,

    // Metrics state
    totalLowStock,
    totalOutOfStock,
    totalAvailable,

    // Getters
    lowStockComponents,
    outOfStockComponents,
    componentsByCategory,

    // Actions
    fetchComponents,
    fetchComponent,
    createComponent,
    updateComponent,
    deleteComponent,
    updateStock,
    fetchStockHistory,
    clearError,
    setPage,
    setItemsPerPage,
    searchComponents,
    filterByCategory,
    filterByStockStatus,
    sortComponents,
    clearFilters,
    fetchMetrics,
  }
})