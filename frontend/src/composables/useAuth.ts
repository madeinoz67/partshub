/**
 * Authentication utilities and guards for CRUD operations
 */

import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useQuasar } from 'quasar'

export function useAuth() {
  const router = useRouter()
  const authStore = useAuthStore()
  const $q = useQuasar()

  /**
   * Check if user is authenticated for CRUD operations
   * Redirects to login if not authenticated
   * @returns true if authenticated, false if redirected to login
   */
  const requireAuth = (operation: string = 'perform this action'): boolean => {
    if (!authStore.isAuthenticated) {
      $q.notify({
        type: 'warning',
        message: `Please log in to ${operation}`,
        position: 'top'
      })
      router.push('/login')
      return false
    }
    return true
  }

  /**
   * Check if user is authenticated admin for admin operations
   * Redirects to login if not authenticated or shows error if not admin
   * @returns true if admin, false if not authorized
   */
  const requireAdmin = (operation: string = 'perform this action'): boolean => {
    if (!authStore.isAuthenticated) {
      $q.notify({
        type: 'warning',
        message: `Please log in to ${operation}`,
        position: 'top'
      })
      router.push('/login')
      return false
    }

    if (!authStore.isAdmin) {
      $q.notify({
        type: 'negative',
        message: 'Administrator privileges required for this action',
        position: 'top'
      })
      return false
    }

    return true
  }

  /**
   * Check authentication without redirecting (for conditional UI)
   */
  const canPerformCrud = (): boolean => {
    return authStore.isAuthenticated
  }

  /**
   * Check admin permissions without redirecting (for conditional UI)
   */
  const canPerformAdmin = (): boolean => {
    return authStore.isAuthenticated && authStore.isAdmin
  }

  return {
    requireAuth,
    requireAdmin,
    canPerformCrud,
    canPerformAdmin,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin
  }
}