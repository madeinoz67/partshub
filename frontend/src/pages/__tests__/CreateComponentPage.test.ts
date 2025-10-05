import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { Quasar } from 'quasar'
import CreateComponentPage from '../CreateComponentPage.vue'
import { useWizardStore } from '../../stores/wizardStore'
import { useAuthStore } from '../../stores/auth'

// Mock WizardContainer component
vi.mock('../../components/wizard/WizardContainer.vue', () => ({
  default: {
    name: 'WizardContainer',
    template: '<div data-testid="wizard-container">Wizard Container</div>',
  },
}))

describe('CreateComponentPage - Wizard Reset Behavior', () => {
  let router: any
  let pinia: any

  beforeEach(() => {
    // Create fresh pinia instance
    pinia = createPinia()
    setActivePinia(pinia)

    // Set up admin user
    const authStore = useAuthStore()
    authStore.user = {
      id: 1,
      username: 'admin',
      email: 'admin@test.com',
      is_admin: true,
      created_at: new Date().toISOString(),
    }

    // Create router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/components/create',
          name: 'create-component',
          component: CreateComponentPage,
        },
        {
          path: '/components/:id',
          name: 'component-detail',
          component: { template: '<div>Component Detail</div>' },
        },
      ],
    })

    // Start at create component page
    router.push('/components/create')
  })

  const createWrapper = async () => {
    const wrapper = mount(CreateComponentPage, {
      global: {
        plugins: [pinia, router, Quasar],
        stubs: {
          'q-page': { template: '<div data-testid="q-page"><slot /></div>' },
          'q-btn': {
            template: '<button data-testid="q-btn"><slot /></button>',
            props: ['to'],
          },
          'q-breadcrumbs': { template: '<div data-testid="q-breadcrumbs"><slot /></div>' },
          'q-breadcrumbs-el': { template: '<span data-testid="q-breadcrumbs-el"><slot /></span>' },
        },
      },
    })

    await flushPromises()
    return wrapper
  }

  it('should reset wizard state when component unmounts', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Set some wizard state to simulate user interaction
    wizardStore.selectPartType('local')
    wizardStore.updateLocalPartData({ name: 'Test Component' })
    wizardStore.setStep(3)

    // Verify state is set
    expect(wizardStore.partType).toBe('local')
    expect(wizardStore.currentStep).toBe(3)
    expect(wizardStore.localPartData.name).toBe('Test Component')

    // Unmount the component (simulates navigation away)
    wrapper.unmount()
    await flushPromises()

    // Verify wizard state was reset
    expect(wizardStore.partType).toBeNull()
    expect(wizardStore.currentStep).toBe(1)
    expect(wizardStore.localPartData.name).toBe('')
  })

  it('should preserve wizard state while component is mounted', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Set some wizard state
    wizardStore.selectPartType('linked')
    wizardStore.setStep(2)

    // State should remain while component is mounted
    expect(wizardStore.partType).toBe('linked')
    expect(wizardStore.currentStep).toBe(2)

    // Wait for next tick
    await wrapper.vm.$nextTick()

    // State should still be preserved
    expect(wizardStore.partType).toBe('linked')
    expect(wizardStore.currentStep).toBe(2)
  })

  it('should only reset wizard after navigation completes', async () => {
    const wrapper = await createWrapper()
    const wizardStore = useWizardStore()

    // Set wizard state
    wizardStore.selectPartType('local')
    wizardStore.setStep(5)

    // Simulate navigation away (in real app this would be triggered by router.push)
    // While still mounted, state should be preserved
    expect(wizardStore.currentStep).toBe(5)

    // Only when we unmount should state reset
    wrapper.unmount()
    await flushPromises()

    expect(wizardStore.currentStep).toBe(1)
  })
})
