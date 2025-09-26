import { route } from 'quasar/wrappers'
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router'

const routes = [
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

  return Router
})