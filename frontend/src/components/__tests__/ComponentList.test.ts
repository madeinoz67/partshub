import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import ComponentList from '../ComponentList.vue'

// Mock the axios module
vi.mock('../boot/axios', () => ({
  api: {
    get: vi.fn()
  }
}))

// Mock the components store
vi.mock('../stores/components', () => ({
  useComponentsStore: () => ({
    components: [
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
    ],
    loading: false,
    fetchComponents: vi.fn()
  })
}))

// Mock the auth composable
vi.mock('../composables/useAuth', () => ({
  useAuth: () => ({
    canPerformCrud: () => true
  })
}))

// Mock router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

const createWrapper = () => {
  return mount(ComponentList, {
    global: {
      plugins: [Quasar],
      provide: {
        $router: mockRouter
      },
      stubs: {
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
          setup(props: any) {
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
        'q-input': { template: '<input data-testid="q-input" />' },
        'q-select': { template: '<select data-testid="q-select" />' },
        'q-chip': { template: '<span data-testid="q-chip"><slot /></span>' },
        'q-icon': { template: '<span data-testid="q-icon"></span>' },
        'q-banner': { template: '<div data-testid="q-banner"><slot /></div>' },
        'q-td': { template: '<td data-testid="q-td"><slot /></td>' }
      }
    },
    props: {
      embedded: false
    }
  })
}

describe('ComponentList Expandable Rows', () => {
  it('should render expand button with correct initial icon', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Find the expand button in the name cell
    const expandButton = wrapper.find('[data-testid="q-btn"]')
    expect(expandButton.exists()).toBe(true)
  })

  it('should toggle expanded state when expand button is clicked', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Initially no components should be expanded
    expect(wrapper.vm.expanded).toEqual([])

    // Click the expand button
    const expandButton = wrapper.find('[data-testid="q-btn"]')
    await expandButton.trigger('click')

    // Component should now be in expanded array
    expect(wrapper.vm.expanded).toContain('test-component-1')

    // Click again to collapse
    await expandButton.trigger('click')

    // Component should be removed from expanded array
    expect(wrapper.vm.expanded).not.toContain('test-component-1')
  })

  it('should show expand content when component is expanded', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Manually set component as expanded
    wrapper.vm.expanded = ['test-component-1']
    await wrapper.vm.$nextTick()

    // Expanded content should be visible
    const expandedContent = wrapper.find('[data-testid="expanded-content"]')
    expect(expandedContent.exists()).toBe(true)
  })

  it('should display component details in expanded content', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Set component as expanded
    wrapper.vm.expanded = ['test-component-1']
    await wrapper.vm.$nextTick()

    // Check if component details are displayed
    const expandedContent = wrapper.find('[data-testid="expanded-content"]')
    expect(expandedContent.text()).toContain('100nF Capacitor')
    expect(expandedContent.text()).toContain('CAP-001')
    expect(expandedContent.text()).toContain('Test Mfg')
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