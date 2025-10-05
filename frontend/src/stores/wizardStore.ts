/**
 * Wizard Store for Component Creation
 * Manages the state of the component creation wizard
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  Provider,
  ProviderPart,
  ResourceSelection,
  PartType,
  PostAction,
  WizardStep,
  Component,
  CreateComponentRequest,
} from '../types/wizard'
import { wizardService } from '../services/wizardService'

export const useWizardStore = defineStore('wizard', () => {
  // State
  const currentStep = ref<WizardStep>(1)
  const partType = ref<PartType>(null)
  const selectedProvider = ref<Provider | null>(null)
  const searchQuery = ref<string>('')
  const searchResults = ref<ProviderPart[]>([])
  const searchTotal = ref<number>(0)
  const selectedPart = ref<ProviderPart | null>(null)
  const selectedResources = ref<ResourceSelection[]>([])
  const postAction = ref<PostAction>(null)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Local part form data
  const localPartData = ref<{
    name: string
    description: string
    manufacturer_id: number | null
    manufacturer_name: string
    footprint_id: number | null
    footprint_name: string
  }>({
    name: '',
    description: '',
    manufacturer_id: null,
    manufacturer_name: '',
    footprint_id: null,
    footprint_name: '',
  })

  // Computed
  const canProceed = computed(() => {
    switch (currentStep.value) {
      case 1:
        return partType.value !== null
      case 2:
        return selectedProvider.value !== null || partType.value !== 'linked'
      case 3:
        if (partType.value === 'linked') {
          return selectedPart.value !== null
        } else {
          return localPartData.value.name.length > 0
        }
      case 4:
        return true // Resources are optional
      case 5:
        return postAction.value !== null
      default:
        return false
    }
  })

  // Actions
  function setStep(step: WizardStep) {
    currentStep.value = step
    persistState()
  }

  function selectPartType(type: PartType) {
    partType.value = type
    persistState()
  }

  function selectProvider(provider: Provider) {
    selectedProvider.value = provider
    persistState()
  }

  async function searchProvider(query: string, limit = 20) {
    if (!selectedProvider.value) {
      error.value = 'No provider selected'
      return
    }

    searchQuery.value = query
    isLoading.value = true
    error.value = null

    try {
      const response = await wizardService.searchProvider(
        selectedProvider.value.id,
        query,
        limit
      )
      searchResults.value = response.results
      searchTotal.value = response.total
    } catch (err) {
      console.error('Provider search error:', err)
      error.value = err instanceof Error ? err.message : 'Failed to search provider'
      searchResults.value = []
      searchTotal.value = 0
    } finally {
      isLoading.value = false
    }
  }

  function selectPart(part: ProviderPart) {
    selectedPart.value = part

    // Initialize resources based on available resources
    if (part.available_resources) {
      selectedResources.value = []

      // Datasheet is always selected and required
      if (part.datasheet_url) {
        selectedResources.value.push({
          type: 'datasheet',
          url: part.datasheet_url,
          selected: true,
          required: true,
        })
      }

      // Other resources are optional
      if (part.image_url) {
        selectedResources.value.push({
          type: 'image',
          url: part.image_url,
          selected: false,
        })
      }
    }
  }

  function toggleResource(resource: ResourceSelection) {
    const index = selectedResources.value.findIndex(r => r.type === resource.type)
    if (index >= 0) {
      // Don't allow deselecting required resources
      if (selectedResources.value[index].required) {
        return
      }
      selectedResources.value[index].selected = !selectedResources.value[index].selected
    }
  }

  function updateLocalPartData(data: Partial<typeof localPartData.value>) {
    localPartData.value = { ...localPartData.value, ...data }
  }

  async function createComponent(): Promise<Component> {
    isLoading.value = true
    error.value = null

    try {
      const request: CreateComponentRequest = {
        part_type: partType.value!,
      }

      // Add linked part data
      if (partType.value === 'linked' && selectedPart.value && selectedProvider.value) {
        request.provider_id = selectedProvider.value.id
        request.provider_part_number = selectedPart.value.part_number
      }

      // Add local/meta part data
      if (partType.value === 'local' || partType.value === 'meta') {
        request.name = localPartData.value.name
        request.description = localPartData.value.description || undefined

        if (localPartData.value.manufacturer_id !== null && localPartData.value.manufacturer_id !== 0) {
          request.manufacturer_id = localPartData.value.manufacturer_id
        } else if (localPartData.value.manufacturer_name) {
          request.manufacturer_name = localPartData.value.manufacturer_name
        }

        if (localPartData.value.footprint_id !== null && localPartData.value.footprint_id !== 0) {
          request.footprint_id = localPartData.value.footprint_id
        } else if (localPartData.value.footprint_name) {
          request.footprint_name = localPartData.value.footprint_name
        }
      }

      // Add selected resources
      if (selectedResources.value.length > 0) {
        request.resources = selectedResources.value
          .filter(r => r.selected)
          .map(r => ({
            type: r.type,
            url: r.url,
            file_name: r.file_name,
          }))
      }

      // Add post action
      request.post_action = postAction.value || undefined

      const component = await wizardService.createComponent(request)

      // Don't reset here - let the caller handle it after navigation
      // This prevents the wizard from resetting before the user is navigated away

      return component
    } catch (err) {
      console.error('Component creation error:', err)
      error.value = err instanceof Error ? err.message : 'Failed to create component'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    currentStep.value = 1
    partType.value = null
    searchQuery.value = ''
    searchResults.value = []
    searchTotal.value = 0
    selectedPart.value = null
    selectedResources.value = []
    postAction.value = null
    error.value = null
    localPartData.value = {
      name: '',
      description: '',
      manufacturer_id: null,
      manufacturer_name: '',
      footprint_id: null,
      footprint_name: '',
    }

    // Keep provider selection if it was set (user preference)
    // But clear everything else
    clearPersistedState()
  }

  // Persistence helpers
  function persistState() {
    const state = {
      partType: partType.value,
      providerId: selectedProvider.value?.id,
      providerName: selectedProvider.value?.name,
    }
    localStorage.setItem('wizard_state', JSON.stringify(state))
  }

  function clearPersistedState() {
    localStorage.removeItem('wizard_state')
  }

  // Initialize store
  function initialize() {
    // Always start fresh when opening the wizard
    // Don't restore previous state to avoid confusion
    reset()
  }

  return {
    // State
    currentStep,
    partType,
    selectedProvider,
    searchQuery,
    searchResults,
    searchTotal,
    selectedPart,
    selectedResources,
    postAction,
    localPartData,
    isLoading,
    error,
    // Computed
    canProceed,
    // Actions
    setStep,
    selectPartType,
    selectProvider,
    searchProvider,
    selectPart,
    toggleResource,
    updateLocalPartData,
    createComponent,
    reset,
    initialize,
  }
})
