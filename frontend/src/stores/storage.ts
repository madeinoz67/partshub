/**
 * Pinia store for storage locations state management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { APIService, StorageLocation, Component } from '../services/api'

export const useStorageStore = defineStore('storage', () => {
  // State
  const locations = ref<StorageLocation[]>([])
  const currentLocation = ref<StorageLocation | null>(null)
  const locationComponents = ref<Component[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hierarchicalLocations = computed(() => {
    // Build a tree structure from flat list
    const locationMap = new Map<string, StorageLocation & { children: StorageLocation[] }>()
    const rootLocations: (StorageLocation & { children: StorageLocation[] })[] = []

    // Initialize all locations
    locations.value.forEach(loc => {
      locationMap.set(loc.id, { ...loc, children: [] })
    })

    // Build hierarchy
    locations.value.forEach(loc => {
      const locationWithChildren = locationMap.get(loc.id)!
      if (loc.parent_id && locationMap.has(loc.parent_id)) {
        locationMap.get(loc.parent_id)!.children.push(locationWithChildren)
      } else {
        rootLocations.push(locationWithChildren)
      }
    })

    return rootLocations.sort((a, b) => a.name.localeCompare(b.name))
  })

  const locationsByType = computed(() => {
    const grouped: Record<string, StorageLocation[]> = {}
    locations.value.forEach(location => {
      if (!grouped[location.type]) {
        grouped[location.type] = []
      }
      grouped[location.type].push(location)
    })
    return grouped
  })

  const locationOptions = computed(() =>
    locations.value.map(loc => ({
      label: loc.location_hierarchy,
      value: loc.id,
      type: loc.type
    })).sort((a, b) => a.label.localeCompare(b.label))
  )

  // Actions
  const fetchLocations = async (params: {
    search?: string
    type?: string
    include_component_count?: boolean
  } = {}) => {
    loading.value = true
    error.value = null

    try {
      locations.value = await APIService.getStorageLocations({
        ...params,
        limit: 1000 // Get all locations for hierarchy
      })
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch storage locations'
      console.error('Error fetching storage locations:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchLocation = async (
    id: string,
    options: {
      include_children?: boolean
      include_component_count?: boolean
      include_full_hierarchy?: boolean
    } = {}
  ) => {
    loading.value = true
    error.value = null

    try {
      currentLocation.value = await APIService.getStorageLocation(id, options)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch storage location'
      console.error('Error fetching storage location:', err)
    } finally {
      loading.value = false
    }
  }

  const createLocation = async (data: Partial<StorageLocation>) => {
    loading.value = true
    error.value = null

    try {
      const newLocation = await APIService.createStorageLocation(data)
      locations.value.push(newLocation)
      return newLocation
    } catch (err: any) {
      error.value = err.message || 'Failed to create storage location'
      console.error('Error creating storage location:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateLocation = async (id: string, data: Partial<StorageLocation>) => {
    loading.value = true
    error.value = null

    try {
      const updatedLocation = await APIService.updateStorageLocation(id, data)

      // Update in list
      const index = locations.value.findIndex(l => l.id === id)
      if (index !== -1) {
        locations.value[index] = updatedLocation
      }

      // Update current if it's the same location
      if (currentLocation.value?.id === id) {
        currentLocation.value = updatedLocation
      }

      return updatedLocation
    } catch (err: any) {
      error.value = err.message || 'Failed to update storage location'
      console.error('Error updating storage location:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const bulkCreateLocations = async (locations: Array<{
    name: string
    description?: string
    type: string
    parent_name?: string
    qr_code_id?: string
  }>) => {
    loading.value = true
    error.value = null

    try {
      const newLocations = await APIService.bulkCreateStorageLocations(locations)
      // Add to existing locations
      locations.value.push(...newLocations)
      return newLocations
    } catch (err: any) {
      error.value = err.message || 'Failed to create storage locations'
      console.error('Error creating storage locations:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchLocationComponents = async (
    id: string,
    params: {
      include_children?: boolean
      search?: string
      category?: string
      component_type?: string
      stock_status?: 'low' | 'out' | 'available'
      sort_by?: 'name' | 'quantity'
      sort_order?: 'asc' | 'desc'
      limit?: number
      offset?: number
    } = {}
  ) => {
    loading.value = true
    error.value = null

    try {
      locationComponents.value = await APIService.getLocationComponents(id, params)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch location components'
      console.error('Error fetching location components:', err)
    } finally {
      loading.value = false
    }
  }

  const findLocationById = (id: string): StorageLocation | null => {
    return locations.value.find(loc => loc.id === id) || null
  }

  const findLocationsByParent = (parentId: string | null): StorageLocation[] => {
    return locations.value.filter(loc => loc.parent_id === parentId)
  }

  const getLocationPath = (location: StorageLocation): StorageLocation[] => {
    const path: StorageLocation[] = [location]
    let current = location

    while (current.parent_id) {
      const parent = findLocationById(current.parent_id)
      if (parent) {
        path.unshift(parent)
        current = parent
      } else {
        break
      }
    }

    return path
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    locations,
    currentLocation,
    locationComponents,
    loading,
    error,

    // Getters
    hierarchicalLocations,
    locationsByType,
    locationOptions,

    // Actions
    fetchLocations,
    fetchLocation,
    createLocation,
    updateLocation,
    bulkCreateLocations,
    fetchLocationComponents,
    findLocationById,
    findLocationsByParent,
    getLocationPath,
    clearError,
  }
})