import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { Quasar, Notify } from 'quasar'
import { vi } from 'vitest'

// Create a global Pinia instance for tests
const pinia = createPinia()

// Mock Quasar Notify
const mockNotify = {
  create: vi.fn()
}

// Global mount options
config.global.plugins = [pinia, [Quasar, {
  plugins: {
    Notify: mockNotify
  }
}]]
config.global.stubs = {
  'q-card': { template: '<div class="q-card"><slot /></div>' },
  'q-card-section': { template: '<div class="q-card-section"><slot /></div>' },
  'q-card-actions': { template: '<div class="q-card-actions"><slot /></div>' },
  'q-btn': { template: '<button><slot /></button>' },
  'q-btn-group': { template: '<div><slot /></div>' },
  'q-tabs': { template: '<div class="q-tabs"><slot /></div>', props: ['modelValue'] },
  'q-tab': { template: '<div class="q-tab"><slot /></div>', props: ['name'] },
  'q-tab-panels': { template: '<div class="q-tab-panels"><slot /></div>', props: ['modelValue'] },
  'q-tab-panel': { template: '<div class="q-tab-panel"><slot /></div>', props: ['name'] },
  'q-dialog': { template: '<div class="q-dialog"><slot /></div>', props: ['modelValue'] },
  'q-input': { template: '<input class="q-input" />', props: ['modelValue', 'label'] },
  'q-select': { template: '<select class="q-select"><slot /></select>', props: ['modelValue', 'options'] },
  'q-checkbox': { template: '<input type="checkbox" class="q-checkbox" />', props: ['modelValue', 'label'] },
  'q-separator': { template: '<hr class="q-separator" />' },
  'q-space': { template: '<div class="q-space"></div>' },
  'q-list': { template: '<ul class="q-list"><slot /></ul>' },
  'q-item': { template: '<li class="q-item"><slot /></li>' },
  'q-item-section': { template: '<div class="q-item-section"><slot /></div>' },
  'q-item-label': { template: '<div class="q-item-label"><slot /></div>' },
  'q-inner-loading': { template: '<div></div>' },
  'q-banner': { template: '<div class="q-banner"><slot /></div>' },
  'q-chip': { template: '<span class="q-chip"><slot /></span>' },
  'q-badge': { template: '<span class="q-badge"><slot /></span>' },
  'q-icon': { template: '<i class="q-icon"><slot /></i>' },
  'q-table': { template: '<div class="q-table"></div>', props: ['rows', 'columns', 'loading', 'pagination', 'rowKey'] },
  'q-td': { template: '<td><slot /></td>', props: ['props'] },
  'q-tooltip': { template: '<div class="q-tooltip"><slot /></div>' },
  'q-spinner': { template: '<div class="q-spinner"></div>' },
  'q-avatar': { template: '<div class="q-avatar"><slot /></div>' },
  'q-stepper': { template: '<div class="q-stepper"><slot /><div class="q-stepper-navigation"><slot name="navigation" /></div></div>' },
  'q-step': { template: '<div class="q-step"><slot /></div>', props: ['name', 'title', 'icon', 'done'] },
  'q-stepper-navigation': { template: '<div class="q-stepper-navigation"><slot /></div>' },
  'q-form': { template: '<form @submit="$emit(\'submit\', $event)"><slot /></form>', emits: ['submit'] }
}

// Export mock Notify for use in tests
export { mockNotify }