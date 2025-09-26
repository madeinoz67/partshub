import { route } from 'quasar/wrappers'
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/LoginPage.vue')
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../pages/ComponentsPage.vue')
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../pages/DashboardPage.vue')
      },
      {
        path: 'components',
        name: 'components',
        component: () => import('../pages/ComponentsPage.vue')
      },
      {
        path: 'components/:id',
        name: 'component-detail',
        component: () => import('../pages/ComponentDetailPage.vue')
      },
      {
        path: 'storage',
        name: 'storage',
        component: () => import('../pages/StorageLocationsPage.vue')
      },
      {
        path: 'api-tokens',
        name: 'api-tokens',
        component: () => import('../pages/ApiTokensPage.vue'),
        meta: { requiresAdmin: true }
      }
    ]
  },
  // Catch all 404s
  {
    path: '/:catchAll(.*)*',
    component: () => import('../pages/ErrorNotFound.vue')
  }
]

export default route(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : (process.env.VUE_ROUTER_MODE === 'history' ? createWebHistory : createWebHashHistory)

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE)
  })

  // Navigation guard for authentication
  Router.beforeEach(async (to) => {
    // Import auth store dynamically to avoid circular dependency
    const { useAuthStore } = await import('../stores/auth')
    const authStore = useAuthStore()

    // Initialize auth store if not already done
    if (!authStore.user && authStore.token) {
      await authStore.initialize()
    }

    // Allow access to login page without authentication
    if (to.name === 'login') {
      return true
    }

    // Check admin-only routes - redirect to login if not authenticated as admin
    if (to.meta?.requiresAdmin) {
      if (!authStore.isAuthenticated) {
        return { name: 'login' }
      }
      if (!authStore.isAdmin) {
        return { name: 'home' } // Redirect non-admin users to home
      }
    }

    // For all other routes, allow anonymous access (tiered access model)
    // Authentication will be checked at the component/API level for CRUD operations
    return true
  })

  return Router
})