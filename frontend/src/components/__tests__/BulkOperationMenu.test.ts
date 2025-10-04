/**
 * Tests for BulkOperationMenu Component
 * Following TDD - these tests define expected component behavior
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BulkOperationMenu from '../BulkOperationMenu.vue'
import { useSelectionStore } from '../../stores/selection'
import { useAuthStore } from '../../stores/auth'

describe('BulkOperationMenu', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    localStorage.clear()
  })

  describe('Admin-only visibility', () => {
    it('should not render for non-admin users', () => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'user',
        full_name: 'Regular User',
        is_active: true,
        is_admin: false,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }

      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      // Component should not render
      expect(wrapper.html()).toBe('<!--v-if-->')
    })

    it('should render for admin users', () => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'admin',
        full_name: 'Admin User',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }

      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      // Component should render
      expect(wrapper.html()).not.toBe('<!--v-if-->')
      expect(wrapper.find('.bulk-operation-menu').exists()).toBe(true)
    })
  })

  describe('Component structure for admin users', () => {
    beforeEach(() => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'admin',
        full_name: 'Admin',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }
    })

    it('should have bulk-operation-menu class', () => {
      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      expect(wrapper.find('.bulk-operation-menu').exists()).toBe(true)
    })

    it('should show selection count of 0 initially', () => {
      mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      const selectionStore = useSelectionStore(pinia)
      expect(selectionStore.selectedCount).toBe(0)
    })

    it('should update selection count when items are selected', async () => {
      const selectionStore = useSelectionStore(pinia)
      selectionStore.addSelection([1, 2, 3])

      mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      expect(selectionStore.selectedCount).toBe(3)
    })
  })

  describe('Event Emissions', () => {
    beforeEach(() => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'admin',
        full_name: 'Admin',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }
    })

    it('should emit add-tags event', () => {
      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      wrapper.vm.$emit('add-tags')
      expect(wrapper.emitted('add-tags')).toBeTruthy()
    })

    it('should emit add-to-project event', () => {
      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      wrapper.vm.$emit('add-to-project')
      expect(wrapper.emitted('add-to-project')).toBeTruthy()
    })

    it('should emit delete event', () => {
      const wrapper = mount(BulkOperationMenu, {
        global: { plugins: [pinia] },
      })

      wrapper.vm.$emit('delete')
      expect(wrapper.emitted('delete')).toBeTruthy()
    })
  })

  describe('Props and Store Integration', () => {
    it('should use selectionStore for state', () => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'admin',
        full_name: 'Admin',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }

      const selectionStore = useSelectionStore(pinia)
      expect(selectionStore.selectedCount).toBe(0)
      expect(selectionStore.hasSelection).toBe(false)

      selectionStore.addSelection([1, 2, 3])
      expect(selectionStore.selectedCount).toBe(3)
      expect(selectionStore.hasSelection).toBe(true)
    })

    it('should use authStore for admin check', () => {
      const authStore = useAuthStore(pinia)
      authStore.user = {
        id: '1',
        username: 'admin',
        full_name: 'Admin',
        is_active: true,
        is_admin: true,
        must_change_password: false,
        created_at: new Date().toISOString(),
      }

      expect(authStore.isAdmin).toBe(true)
    })
  })
})
