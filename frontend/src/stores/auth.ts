/**
 * Authentication store for PartsHub
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { APIService } from '../services/api'

export interface User {
  id: string
  username: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  must_change_password: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface APIToken {
  id: string
  name: string
  description: string | null
  prefix: string
  is_active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export interface CreateAPITokenRequest {
  name: string
  description?: string
  expires_in_days?: number
}

export interface APITokenCreated extends APIToken {
  token: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const requiresPasswordChange = computed(() => user.value?.must_change_password ?? false)

  // Actions
  async function login(username: string, password: string): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      const response = await APIService.login(username, password)

      token.value = response.access_token
      localStorage.setItem('auth_token', response.access_token)

      // Get user info after successful login
      await fetchCurrentUser()

      return true
    } catch (err: unknown) {
      console.error('Login error:', err)
      const errorMessage = err instanceof Error && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
      error.value = errorMessage || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  async function fetchCurrentUser(): Promise<void> {
    if (!token.value) return

    try {
      user.value = await APIService.getCurrentUser()
    } catch (err: unknown) {
      console.error('Failed to fetch user:', err)
      const response = err instanceof Error && 'response' in err
        ? (err as { response?: { status?: number } }).response
        : undefined
      if (response?.status === 401) {
        await logout()
      }
    }
  }

  async function changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      await APIService.changePassword(currentPassword, newPassword)

      // Update user info to clear password change requirement
      await fetchCurrentUser()

      return true
    } catch (err: unknown) {
      console.error('Password change error:', err)
      const errorMessage = err instanceof Error && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
      error.value = errorMessage || 'Failed to change password'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // API Token management (admin only)
  async function getAPITokens(): Promise<APIToken[]> {
    try {
      return await APIService.getAPITokens()
    } catch (err: unknown) {
      console.error('Failed to fetch API tokens:', err)
      throw err
    }
  }

  async function createAPIToken(data: CreateAPITokenRequest): Promise<APITokenCreated> {
    try {
      return await APIService.createAPIToken(data)
    } catch (err: unknown) {
      console.error('Failed to create API token:', err)
      throw err
    }
  }

  async function revokeAPIToken(tokenId: string): Promise<void> {
    try {
      await APIService.revokeAPIToken(tokenId)
    } catch (err: unknown) {
      console.error('Failed to revoke API token:', err)
      throw err
    }
  }

  // Initialize store
  async function initialize(): Promise<void> {
    if (token.value) {
      await fetchCurrentUser()
    }
  }

  return {
    // State
    token,
    user,
    isLoading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    requiresPasswordChange,
    // Actions
    login,
    logout,
    fetchCurrentUser,
    changePassword,
    getAPITokens,
    createAPIToken,
    revokeAPIToken,
    initialize,
  }
})