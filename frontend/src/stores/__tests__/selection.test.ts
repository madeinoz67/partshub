/**
 * Tests for Selection Store
 * Following TDD - these tests define the expected behavior
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSelectionStore } from '../selection'

describe('SelectionStore', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())
    // Clear localStorage
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should initialize with empty selection', () => {
      const store = useSelectionStore()
      expect(store.selectedIds).toEqual(new Set())
      expect(store.selectedCount).toBe(0)
      expect(store.hasSelection).toBe(false)
    })
  })

  describe('addSelection', () => {
    it('should add single id to selection', () => {
      const store = useSelectionStore()
      store.addSelection([1])
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedCount).toBe(1)
      expect(store.hasSelection).toBe(true)
    })

    it('should add multiple ids to selection', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedIds.has(2)).toBe(true)
      expect(store.selectedIds.has(3)).toBe(true)
      expect(store.selectedCount).toBe(3)
    })

    it('should not duplicate ids when adding existing selection', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2])
      store.addSelection([2, 3])
      expect(store.selectedCount).toBe(3)
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedIds.has(2)).toBe(true)
      expect(store.selectedIds.has(3)).toBe(true)
    })
  })

  describe('removeSelection', () => {
    it('should remove single id from selection', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])
      store.removeSelection([2])
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedIds.has(2)).toBe(false)
      expect(store.selectedIds.has(3)).toBe(true)
      expect(store.selectedCount).toBe(2)
    })

    it('should remove multiple ids from selection', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3, 4])
      store.removeSelection([2, 4])
      expect(store.selectedCount).toBe(2)
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedIds.has(3)).toBe(true)
    })

    it('should not error when removing non-existent ids', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2])
      expect(() => store.removeSelection([3, 4])).not.toThrow()
      expect(store.selectedCount).toBe(2)
    })
  })

  describe('toggleSelection', () => {
    it('should add id if not selected', () => {
      const store = useSelectionStore()
      store.toggleSelection(1)
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedCount).toBe(1)
    })

    it('should remove id if already selected', () => {
      const store = useSelectionStore()
      store.addSelection([1])
      store.toggleSelection(1)
      expect(store.selectedIds.has(1)).toBe(false)
      expect(store.selectedCount).toBe(0)
    })

    it('should toggle multiple times correctly', () => {
      const store = useSelectionStore()
      store.toggleSelection(1)
      expect(store.selectedIds.has(1)).toBe(true)
      store.toggleSelection(1)
      expect(store.selectedIds.has(1)).toBe(false)
      store.toggleSelection(1)
      expect(store.selectedIds.has(1)).toBe(true)
    })
  })

  describe('selectAll', () => {
    it('should select all provided ids', () => {
      const store = useSelectionStore()
      store.selectAll([1, 2, 3, 4, 5])
      expect(store.selectedCount).toBe(5)
      expect(store.selectedIds.has(1)).toBe(true)
      expect(store.selectedIds.has(5)).toBe(true)
    })

    it('should replace existing selection with new ids', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])
      store.selectAll([4, 5, 6])
      expect(store.selectedCount).toBe(3)
      expect(store.selectedIds.has(1)).toBe(false)
      expect(store.selectedIds.has(4)).toBe(true)
    })
  })

  describe('clearSelection', () => {
    it('should clear all selected ids', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])
      store.clearSelection()
      expect(store.selectedCount).toBe(0)
      expect(store.hasSelection).toBe(false)
    })

    it('should be safe to call when already empty', () => {
      const store = useSelectionStore()
      expect(() => store.clearSelection()).not.toThrow()
      expect(store.selectedCount).toBe(0)
    })
  })

  describe('isSelected getter', () => {
    it('should return true for selected id', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2])
      expect(store.isSelected(1)).toBe(true)
      expect(store.isSelected(2)).toBe(true)
    })

    it('should return false for non-selected id', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2])
      expect(store.isSelected(3)).toBe(false)
    })
  })

  describe('Persistence', () => {
    it('should persist selection to localStorage', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])

      // Create a new store instance to test persistence
      const newPinia = createPinia()
      setActivePinia(newPinia)
      const newStore = useSelectionStore()

      // Selection should be restored from localStorage
      expect(newStore.selectedCount).toBe(3)
      expect(newStore.selectedIds.has(1)).toBe(true)
      expect(newStore.selectedIds.has(2)).toBe(true)
      expect(newStore.selectedIds.has(3)).toBe(true)
    })

    it('should persist cleared selection', () => {
      const store = useSelectionStore()
      store.addSelection([1, 2, 3])
      store.clearSelection()

      // Create a new store instance
      const newPinia = createPinia()
      setActivePinia(newPinia)
      const newStore = useSelectionStore()

      expect(newStore.selectedCount).toBe(0)
    })
  })

  describe('getSelectedArray', () => {
    it('should return array of selected ids', () => {
      const store = useSelectionStore()
      store.addSelection([3, 1, 2])
      const selected = store.getSelectedArray()
      expect(selected).toBeInstanceOf(Array)
      expect(selected).toHaveLength(3)
      expect(selected).toContain(1)
      expect(selected).toContain(2)
      expect(selected).toContain(3)
    })

    it('should return empty array when no selection', () => {
      const store = useSelectionStore()
      expect(store.getSelectedArray()).toEqual([])
    })
  })
})
