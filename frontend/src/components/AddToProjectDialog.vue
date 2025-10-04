<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card style="min-width: 600px; max-width: 800px">
      <q-card-section>
        <div class="text-h6">Add Parts to Project</div>
      </q-card-section>

      <q-card-section>
        <!-- Component List with Quantities -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm">Selected Components ({{ components.length }})</div>
          <q-table
            :rows="components"
            :columns="componentColumns"
            row-key="id"
            flat
            dense
            :rows-per-page-options="[5, 10, 20]"
          >
            <template #body-cell-quantity="props">
              <q-td :props="props">
                <div class="row items-center no-wrap">
                  <q-btn
                    flat
                    dense
                    round
                    size="sm"
                    icon="remove"
                    @click="decrementQuantity(props.row.id)"
                  />
                  <div class="q-px-sm" style="min-width: 40px; text-align: center">
                    {{ quantities[props.row.id] || 1 }}
                  </div>
                  <q-btn
                    flat
                    dense
                    round
                    size="sm"
                    icon="add"
                    @click="incrementQuantity(props.row.id)"
                  />
                </div>
              </q-td>
            </template>
          </q-table>
        </div>

        <!-- Project Selection -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm">Target Project</div>
          <q-select
            v-model="selectedProject"
            :options="projectOptions"
            outlined
            dense
            label="Select a project"
            option-value="value"
            option-label="label"
            :loading="loadingProjects"
          />
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          flat
          label="Cancel"
          color="primary"
          @click="handleCancel"
        />
        <q-btn
          flat
          label="Add"
          color="primary"
          :loading="loadingAdd"
          :disable="!selectedProject"
          @click="handleAdd"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { APIService, type Component, type Project } from '../services/api'
import { bulkOperationsApi } from '../services/bulkOperationsApi'

// Props
interface Props {
  modelValue: boolean
  componentIds: string[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'added': []
}>()

// State
const $q = useQuasar()
const components = ref<Component[]>([])
const quantities = ref<Record<string, number>>({})
const selectedProject = ref<{ label: string; value: string } | null>(null)
const projects = ref<Project[]>([])
const loadingProjects = ref(false)
const loadingAdd = ref(false)

// Computed
const showDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const componentColumns = [
  {
    name: 'name',
    label: 'Part',
    field: 'name',
    align: 'left' as const,
  },
  {
    name: 'description',
    label: 'Description',
    field: 'part_number',
    align: 'left' as const,
  },
  {
    name: 'quantity',
    label: 'Quantity',
    field: 'quantity',
    align: 'center' as const,
  },
]

const projectOptions = computed(() => {
  return projects.value.map(project => ({
    label: project.name,
    value: project.id,
  }))
})

// Methods
function incrementQuantity(componentId: string) {
  quantities.value[componentId] = (quantities.value[componentId] || 1) + 1
}

function decrementQuantity(componentId: string) {
  if ((quantities.value[componentId] || 1) > 1) {
    quantities.value[componentId] = (quantities.value[componentId] || 1) - 1
  }
}

async function loadProjects() {
  loadingProjects.value = true
  try {
    const response = await APIService.getProjects({ limit: 100 })
    projects.value = response.projects
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load projects',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  } finally {
    loadingProjects.value = false
  }
}

async function loadComponents() {
  try {
    const loadedComponents: Component[] = []
    for (const id of props.componentIds) {
      try {
        const component = await APIService.getComponent(id)
        loadedComponents.push(component)
        // Initialize quantity to 1
        quantities.value[id] = 1
      } catch (error) {
        console.error(`Failed to load component ${id}:`, error)
      }
    }
    components.value = loadedComponents
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load components',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  }
}

async function handleAdd() {
  if (!selectedProject.value) return

  loadingAdd.value = true
  try {
    await bulkOperationsApi.bulkAssignToProject(
      props.componentIds,
      selectedProject.value.value,
      quantities.value
    )

    emit('added')
    handleCancel()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to add components to project',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  } finally {
    loadingAdd.value = false
  }
}

function handleCancel() {
  components.value = []
  quantities.value = {}
  selectedProject.value = null
  showDialog.value = false
}

// Watchers
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      loadProjects()
      loadComponents()
    }
  }
)

onMounted(() => {
  if (props.modelValue) {
    loadProjects()
    loadComponents()
  }
})
</script>
