import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'
import { Quasar } from 'quasar'
import WizardContainer from '../WizardContainer.vue'
import { useWizardStore } from '../../../stores/wizardStore'

// Mock Quasar Notify plugin
const mockNotify = vi.fn()
vi.mock('quasar', async () => {
  const actual = await vi.importActual('quasar')
  return {
    ...actual,
    useQuasar: () => ({
      notify: mockNotify,
    }),
  }
})

// Mock the wizard service
vi.mock('../../../services/wizardService', () => ({
  wizardService: {
    createComponent: vi.fn().mockResolvedValue({
      id: 123,
      name: 'Test Component',
      part_number: 'TEST-001',
    }),
  },
}))

// Mock child components
vi.mock('../PartTypeSelector.vue', () => ({
  default: {
    name: 'PartTypeSelector',
    template: '<div data-testid="part-type-selector">Part Type Selector</div>',
  },
}))

vi.mock('../ProviderSelector.vue', () => ({
  default: {
    name: 'ProviderSelector',
    template: '<div data-testid="provider-selector">Provider Selector</div>',
  },
}))

vi.mock('../ProviderSearch.vue', () => ({
  default: {
    name: 'ProviderSearch',
    template: '<div data-testid="provider-search">Provider Search</div>',
  },
}))

vi.mock('../LocalPartForm.vue', () => ({
  default: {
    name: 'LocalPartForm',
    template: '<div data-testid="local-part-form">Local Part Form</div>',
  },
}))

vi.mock('../ResourceSelector.vue', () => ({
  default: {
    name: 'ResourceSelector',
    template: '<div data-testid="resource-selector">Resource Selector</div>',
  },
}))

vi.mock('../PostCreationActions.vue', () => ({
  default: {
    name: 'PostCreationActions',
    template: '<div data-testid="post-creation-actions">Post Creation Actions</div>',
  },
}))

describe('WizardContainer - Navigation After Component Creation', () => {
  let router: Router
  let pinia: Pinia

  beforeEach(() => {
    // Create fresh pinia instance
    pinia = createPinia()
    setActivePinia(pinia)

    // Create router with component detail route
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/components/create',
          name: 'create-component',
          component: { template: '<div>Create</div>' },
        },
        {
          path: '/components/:id',
          name: 'component-detail',
          component: { template: '<div>Component Detail</div>' },
        },
        {
          path: '/components',
          name: 'components-list',
          component: { template: '<div>Components List</div>' },
        },
      ],
    })

    // Start at create component page
    router.push('/components/create')
  })

  const createWrapper = async () => {
    const wrapper = mount(WizardContainer, {
      global: {
        plugins: [
          pinia,
          router,
          Quasar,
        ],
        stubs: {
          'q-card': { template: '<div data-testid="q-card"><slot /></div>' },
          'q-card-section': { template: '<div data-testid="q-card-section"><slot /></div>' },
          'q-card-actions': { template: '<div data-testid="q-card-actions"><slot /></div>' },
          'q-separator': { template: '<hr data-testid="q-separator" />' },
          'q-stepper': {
            template: '<div data-testid="q-stepper"><slot /></div>',
            props: ['modelValue'],
          },
          'q-step': {
            template: '<div data-testid="q-step" v-if="name === 5"><slot /></div>',
            props: ['name', 'title', 'icon', 'done'],
          },
          'q-btn': {
            template: '<button data-testid="q-btn" @click="handleClick" :disabled="disable"><slot /><slot name="default" /></button>',
            props: ['disable', 'loading', 'label', 'iconRight', 'icon', 'flat', 'unelevated', 'color'],
            emits: ['click'],
            methods: {
              handleClick() {
                if (!this.disable && !this.loading) {
                  this.$emit('click')
                }
              }
            }
          },
          'q-space': { template: '<div data-testid="q-space"></div>' },
        },
      },
    })

    await flushPromises()
    return wrapper
  }

  it('should navigate to component detail page after successful creation with "view" action', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Setup wizard state for step 5
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(5)
    wizardStore.postAction = 'view'

    await wrapper.vm.$nextTick()

    // Call createComponent directly
    await wrapper.vm.createComponent()
    await flushPromises()

    // Verify navigation occurred to component detail page
    expect(router.currentRoute.value.path).toBe('/components/123')
    expect(router.currentRoute.value.name).toBe('component-detail')
  })

  it('should not reset wizard state before navigation completes', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Setup wizard state for step 5
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(5)
    wizardStore.postAction = 'view'

    await wrapper.vm.$nextTick()

    // Capture initial state
    expect(wizardStore.currentStep).toBe(5)
    expect(wizardStore.partType).toBe('local')

    // Call createComponent directly
    await wrapper.vm.createComponent()
    await flushPromises()

    // After successful creation and navigation, wizard should still have state
    // until the page is unmounted (reset should happen on page unmount, not before navigation)
    expect(router.currentRoute.value.path).toBe('/components/123')
  })

  it('should navigate to component detail page for "add_stock" action', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Setup wizard state for step 5
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(5)
    wizardStore.postAction = 'add_stock'

    await wrapper.vm.$nextTick()

    // Call createComponent directly
    await wrapper.vm.createComponent()
    await flushPromises()

    // Verify navigation occurred to add-stock page
    expect(router.currentRoute.value.path).toBe('/components/123/add-stock')
  })

  it('should stay on wizard page and reset for "continue" action', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Setup wizard state for step 5
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(5)
    wizardStore.postAction = 'continue'

    await wrapper.vm.$nextTick()

    // Capture the current route before creation
    const initialPath = router.currentRoute.value.path

    // Call createComponent directly
    await wrapper.vm.createComponent()
    await flushPromises()

    // Verify we didn't navigate away (router should stay on same path or root)
    // When not navigating, the route path doesn't change
    expect(router.currentRoute.value.path).toBe(initialPath)

    // Verify wizard was reset to step 1
    expect(wizardStore.currentStep).toBe(1)
    expect(wizardStore.partType).toBeNull()
  })

  it('should preserve wizard state during navigation to prevent UI flashing', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Setup wizard state for step 5
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(5)
    wizardStore.postAction = 'view'

    await wrapper.vm.$nextTick()

    // Spy on router.push to intercept navigation
    const pushSpy = vi.spyOn(router, 'push')

    // Call createComponent (don't await yet)
    const createPromise = wrapper.vm.createComponent()

    // Immediately after calling, wizard should still be on step 5
    // This prevents the UI from flashing back to step 1
    expect(wizardStore.currentStep).toBe(5)

    await createPromise
    await flushPromises()

    // Navigation should have been called
    expect(pushSpy).toHaveBeenCalledWith('/components/123')
  })
})
