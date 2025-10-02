import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import { createRouter, createWebHistory } from 'vue-router'
import { ref } from 'vue'
import ComponentList from '../ComponentList.vue'

// Mock the axios module
vi.mock('../../boot/axios', () => ({
  api: {
    get: vi.fn()
  }
}))

// Mock the components store
vi.mock('../../stores/components', () => ({
  useComponentsStore: () => {
    return {
      components: ref([
        {
          id: 'test-component-1',
          name: '100nF Capacitor',
          part_number: 'CAP-001',
          manufacturer: 'Test Mfg',
          quantity_on_hand: 50,
          minimum_stock: 10,
          category: { name: 'Capacitors' },
          storage_location: { name: 'Bin A1', location_hierarchy: 'Room 1 > Bin A1' },
          attachments: [],
          created_at: '2024-01-01',
          updated_at: '2024-01-01'
        }
      ]),
      loading: ref(false),
      fetchComponents: vi.fn(),
      fetchMetrics: vi.fn()
    }
  }
}))

// Mock the auth composable
vi.mock('../../composables/useAuth', () => ({
  useAuth: () => ({
    canPerformCrud: () => true
  })
}))

// Mock BarcodeScanner component
vi.mock('../BarcodeScanner.vue', () => ({
  default: {
    name: 'BarcodeScanner',
    template: '<div data-testid="barcode-scanner"></div>'
  }
}))

// Create router for testing
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/storage/:id', component: { template: '<div>Storage</div>' } }
  ]
})


const createWrapper = () => {
  return mount(ComponentList, {
    global: {
      plugins: [Quasar, router],
      stubs: {
        'router-link': {
          template: '<a data-testid="router-link" :href="to"><slot /></a>',
          props: ['to']
        },
        'q-table': {
          template: `
            <div data-testid="q-table">
              <div v-if="rows && rows.length > 0">
                <slot name="body-cell-name" :props="{ row: rows[0] }"></slot>
                <div v-if="expandedComponents.includes(rows[0]?.id)" data-testid="expanded-content">
                  <slot name="expand" :props="{ row: rows[0] }"></slot>
                </div>
              </div>
            </div>
          `,
          props: ['rows', 'columns', 'expand', 'expanded'],
          setup(props: { rows?: unknown[]; columns?: unknown[]; expand?: boolean; expanded?: unknown[] }) {
            // Mock expanded state management
            const expandedComponents = props.expanded || []
            return { expandedComponents, rows: props.rows }
          }
        },
        'q-card': { template: '<div data-testid="q-card"><slot /></div>' },
        'q-card-section': { template: '<div data-testid="q-card-section"><slot /></div>' },
        'q-btn': {
          template: '<button data-testid="q-btn" @click="$emit(\'click\')"><slot /></button>',
          emits: ['click']
        },
        'q-input': {
          template: '<input data-testid="q-input" />',
          props: ['modelValue', 'outlined', 'dense', 'placeholder', 'debounce'],
          emits: ['update:modelValue']
        },
        'q-select': {
          template: '<select data-testid="q-select"><option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option></select>',
          props: ['modelValue', 'options', 'outlined', 'dense', 'clearable', 'emit-value', 'map-options'],
          emits: ['update:modelValue']
        },
        'q-chip': { template: '<span data-testid="q-chip"><slot /></span>' },
        'q-icon': { template: '<span data-testid="q-icon"></span>' },
        'q-banner': { template: '<div data-testid="q-banner"><slot /></div>' },
        'q-td': { template: '<td data-testid="q-td"><slot /></td>' },
        'q-tooltip': { template: '<div data-testid="q-tooltip"><slot /></div>' },
        'BarcodeScanner': { template: '<div data-testid="barcode-scanner"></div>' }
      }
    },
    props: {
      embedded: false
    }
  })
}

describe('ComponentList', () => {
  it('should render successfully with basic structure', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Check that the component renders
    expect(wrapper.exists()).toBe(true)

    // Check that the table is rendered
    const table = wrapper.find('[data-testid="q-table"]')
    expect(table.exists()).toBe(true)
  })

  it('should initialize with empty expanded array', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Initially no components should be expanded
    expect(wrapper.vm.expanded).toEqual([])
  })

  it('should have basic reactive data properties', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Check that component has expected data properties
    expect(wrapper.vm.expanded).toBeDefined()
    expect(Array.isArray(wrapper.vm.expanded)).toBe(true)
    expect(wrapper.vm.searchQuery).toBeDefined()
    expect(wrapper.vm.selectedCategory).toBeDefined()
  })

  it('should allow setting expanded state programmatically', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Manually set component as expanded
    wrapper.vm.expanded = ['test-component-1']
    await wrapper.vm.$nextTick()

    // Check expanded state
    expect(wrapper.vm.expanded).toContain('test-component-1')
    expect(wrapper.vm.expanded).toHaveLength(1)
  })

  it('should support multiple components expanded simultaneously', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Expand multiple components
    wrapper.vm.expanded = ['test-component-1', 'test-component-2']
    await wrapper.vm.$nextTick()

    // Both should be in the expanded array
    expect(wrapper.vm.expanded).toContain('test-component-1')
    expect(wrapper.vm.expanded).toContain('test-component-2')
    expect(wrapper.vm.expanded).toHaveLength(2)
  })
})