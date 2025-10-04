/**
 * Selection Store for managing bulk operation selections
 * Implements localStorage persistence manually for compatibility
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'partshub_selection'

// Helper to load from localStorage
function loadFromStorage(): Set<string> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return new Set(Array.isArray(parsed) ? parsed : [])
    }
  } catch (error) {
    console.error('Failed to load selection from localStorage:', error)
  }
  return new Set()
}

// Helper to save to localStorage
function saveToStorage(selectedIds: Set<string>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(selectedIds)))
  } catch (error) {
    console.error('Failed to save selection to localStorage:', error)
  }
}

export const useSelectionStore = defineStore('selection', () => {
  // State
  const selectedIds = ref<Set<string>>(loadFromStorage())

  // Getters
  const hasSelection = computed(() => selectedIds.value.size > 0)
  const selectedCount = computed(() => selectedIds.value.size)
  const isSelected = computed(() => (id: string) => selectedIds.value.has(id))

  // Actions
  function addSelection(ids: string[]): void {
    ids.forEach(id => selectedIds.value.add(id))
    saveToStorage(selectedIds.value)
  }

  function removeSelection(ids: string[]): void {
    ids.forEach(id => selectedIds.value.delete(id))
    saveToStorage(selectedIds.value)
  }

  function toggleSelection(id: string): void {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
    saveToStorage(selectedIds.value)
  }

  function selectAll(ids: string[]): void {
    selectedIds.value.clear()
    ids.forEach(id => selectedIds.value.add(id))
    saveToStorage(selectedIds.value)
  }

  function clearSelection(): void {
    selectedIds.value.clear()
    saveToStorage(selectedIds.value)
  }

  function getSelectedArray(): string[] {
    return Array.from(selectedIds.value)
  }

  return {
    // State
    selectedIds,
    // Getters
    hasSelection,
    selectedCount,
    isSelected,
    // Actions
    addSelection,
    removeSelection,
    toggleSelection,
    selectAll,
    clearSelection,
    getSelectedArray,
  }
})
