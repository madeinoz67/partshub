import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'

// Create a global Pinia instance for tests
const pinia = createPinia()

// Global mount options
config.global.plugins = [pinia]
config.global.stubs = {
  'q-card': { template: '<div class="q-card"><slot /></div>' },
  'q-card-section': { template: '<div class="q-card-section"><slot /></div>' },
  'q-btn': { template: '<button><slot /></button>' },
  'q-btn-group': { template: '<div><slot /></div>' },
  'q-inner-loading': { template: '<div></div>' },
  'q-banner': { template: '<div><slot /></div>' },
  'q-chip': { template: '<span class="q-chip"><slot /></span>' },
  'q-badge': { template: '<span class="q-badge"><slot /></span>' },
  'q-icon': { template: '<i></i>' },
  'q-table': { template: '<table><slot /></table>' },
  'q-spinner': { template: '<div></div>' }
}