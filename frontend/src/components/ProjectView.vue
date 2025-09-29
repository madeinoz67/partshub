<template>
  <div class="project-view">
    <!-- Close Button - Prominent and visible -->
    <div class="row justify-end q-mb-md" style="position: relative; z-index: 9999;">
      <q-btn
        unelevated
        round
        icon="close"
        aria-label="Close dialog"
        color="red"
        text-color="white"
        size="lg"
        style="position: sticky; top: 0; right: 0; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"
        @click="$emit('close')"
      />
    </div>

    <q-card class="q-pa-md">
      <!-- Project Header -->
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-h5">{{ project?.name || 'Project Details' }}</div>
          <div class="text-subtitle2 text-grey-6">
            Status: <q-chip
              :color="getStatusColor(project?.status)"
              text-color="white"
              size="sm"
            >
              {{ project?.status || 'Unknown' }}
            </q-chip>
          </div>
        </div>
        <div class="col-auto">
          <q-btn
            v-if="project"
            color="primary"
            icon="edit"
            label="Edit Project"
            class="q-mr-sm"
            @click="editProject"
          />
          <q-btn
            v-if="project"
            color="negative"
            icon="delete"
            label="Delete Project"
            @click="confirmDelete"
          />
        </div>
      </div>

      <!-- Project Description -->
      <div v-if="project?.description" class="q-mb-md">
        <q-card flat bordered class="q-pa-md">
          <div class="text-subtitle2 q-mb-sm">Description</div>
          <div class="text-body2">{{ project.description }}</div>
        </q-card>
      </div>

      <!-- Project Statistics -->
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-md-3 col-sm-6 col-12">
          <q-card flat bordered class="text-center q-pa-md">
            <div class="text-h4 text-primary">{{ stats?.unique_components || 0 }}</div>
            <div class="text-subtitle2">Unique Components</div>
          </q-card>
        </div>
        <div class="col-md-3 col-sm-6 col-12">
          <q-card flat bordered class="text-center q-pa-md">
            <div class="text-h4 text-secondary">{{ stats?.total_allocated_quantity || 0 }}</div>
            <div class="text-subtitle2">Total Allocated</div>
          </q-card>
        </div>
        <div class="col-md-3 col-sm-6 col-12">
          <q-card flat bordered class="text-center q-pa-md">
            <div class="text-h4 text-green">{{ formatCurrency(stats?.estimated_cost || 0) }}</div>
            <div class="text-subtitle2">Estimated Cost</div>
          </q-card>
        </div>
        <div class="col-md-3 col-sm-6 col-12">
          <q-card flat bordered class="text-center q-pa-md">
            <div class="text-h4 text-orange">{{ allocatedComponents.length }}</div>
            <div class="text-subtitle2">Components</div>
          </q-card>
        </div>
      </div>

      <!-- Component Allocation Section -->
      <q-card flat bordered class="q-mb-md">
        <q-card-section>
          <div class="row items-center">
            <div class="col">
              <div class="text-h6">Component Allocations</div>
            </div>
            <div class="col-auto">
              <q-btn
                color="primary"
                icon="add"
                label="Allocate Component"
                @click="showAllocateDialog = true"
              />
            </div>
          </div>
        </q-card-section>

        <!-- Allocations Table -->
        <q-table
          :rows="allocatedComponents"
          :columns="allocationColumns"
          row-key="id"
          :loading="loading"
          flat
          :pagination="{ rowsPerPage: 10 }"
        >
          <template #body-cell-component="props">
            <q-td :props="props">
              <div>
                <div class="text-weight-medium">{{ props.row.component_part_number || 'No Part Number' }}</div>
                <div class="text-caption text-grey-6">{{ props.row.component_name || 'No Component Name' }}</div>
              </div>
            </q-td>
          </template>

          <template #body-cell-allocated="props">
            <q-td :props="props">
              <q-chip
                color="blue"
                text-color="white"
                :label="props.row.quantity_allocated"
              />
            </q-td>
          </template>

          <template #body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                icon="remove"
                color="negative"
                size="sm"
                @click="returnComponent(props.row)"
              >
                <q-tooltip>Return to Inventory</q-tooltip>
              </q-btn>
              <q-btn
                flat
                round
                icon="add"
                color="positive"
                size="sm"
                @click="allocateMore(props.row)"
              >
                <q-tooltip>Allocate More</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card>
    </q-card>

    <!-- Component Allocation Dialog -->
    <q-dialog v-model="showAllocateDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Allocate Component to Project</div>
        </q-card-section>

        <q-card-section>
          <div class="q-gutter-md">
            <!-- Component Search -->
            <q-select
              v-model="selectedComponent"
              :options="componentOptions"
              option-label="display_name"
              option-value="id"
              label="Select Component"
              use-input
              input-debounce="300"
              clearable
              @filter="filterComponents"
              @update:model-value="onComponentSelected"
            >
              <template #option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.part_number }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.name }}</q-item-label>
                    <q-item-label caption class="text-positive">
                      Stock: {{ scope.opt.quantity_on_hand }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <!-- Quantity Input -->
            <q-input
              v-model.number="allocationQuantity"
              type="number"
              label="Quantity to Allocate"
              :min="1"
              :max="selectedComponent?.quantity_on_hand || 1"
              outlined
            />

            <!-- Notes -->
            <q-input
              v-model="allocationNotes"
              label="Allocation Notes (Optional)"
              type="textarea"
              rows="3"
              outlined
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeAllocateDialog" />
          <q-btn
            color="primary"
            label="Allocate"
            :disabled="!selectedComponent || !allocationQuantity"
            @click="allocateComponent"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Return Component Dialog -->
    <q-dialog v-model="showReturnDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Return Component to Inventory</div>
        </q-card-section>

        <q-card-section>
          <div class="q-gutter-md">
            <div class="text-body2">
              <strong>Component:</strong> {{ componentToReturn?.component_part_number }}
            </div>
            <div class="text-body2">
              <strong>Currently Allocated:</strong> {{ componentToReturn?.quantity_allocated }}
            </div>

            <q-input
              v-model.number="returnQuantity"
              type="number"
              label="Quantity to Return"
              :min="1"
              :max="componentToReturn?.quantity_allocated || 1"
              outlined
            />

            <q-input
              v-model="returnNotes"
              label="Return Notes (Optional)"
              type="textarea"
              rows="3"
              outlined
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeReturnDialog" />
          <q-btn
            color="negative"
            label="Return"
            :disabled="!returnQuantity"
            @click="confirmReturn"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { APIService } from '../services/api'

const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'project-updated'])

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

// Reactive data
const project = ref(null)
const stats = ref(null)
const allocatedComponents = ref([])
const loading = ref(false)

// Dialog state
const showAllocateDialog = ref(false)
const showReturnDialog = ref(false)
const componentToReturn = ref(null)

// Allocation form
const selectedComponent = ref(null)
const allocationQuantity = ref(1)
const allocationNotes = ref('')
const componentOptions = ref([])

// Return form
const returnQuantity = ref(1)
const returnNotes = ref('')

// Table columns
const allocationColumns = [
  {
    name: 'component',
    label: 'Component',
    field: 'component',
    align: 'left',
    sortable: true
  },
  {
    name: 'allocated',
    label: 'Allocated Quantity',
    field: 'quantity_allocated',
    align: 'center',
    sortable: true
  },
  {
    name: 'allocated_date',
    label: 'Allocated Date',
    field: 'allocated_at',
    align: 'center',
    sortable: true,
    format: (val) => val ? new Date(val).toLocaleDateString() : ''
  },
  {
    name: 'notes',
    label: 'Notes',
    field: 'notes',
    align: 'left'
  },
  {
    name: 'actions',
    label: 'Actions',
    field: 'actions',
    align: 'center'
  }
]

// Computed properties
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount)
}

const getStatusColor = (status) => {
  const colors = {
    'planning': 'blue',
    'active': 'green',
    'on_hold': 'orange',
    'completed': 'purple',
    'cancelled': 'red'
  }
  return colors[status] || 'grey'
}

// Methods
const loadProject = async () => {
  if (!props.projectId) {
    console.log('No projectId provided')
    return
  }

  console.log('Loading project:', props.projectId)
  loading.value = true
  try {
    // Load project details
    console.log('Loading project details...')
    const projectResponse = await APIService.getProject(props.projectId)
    project.value = projectResponse
    console.log('Project details loaded:', projectResponse)

    // Load project statistics
    console.log('Loading project statistics...')
    const statsResponse = await APIService.getProjectStatistics(props.projectId)
    stats.value = statsResponse
    console.log('Project statistics loaded:', statsResponse)

    // Load allocated components
    console.log('Loading allocated components...')
    const allocationsResponse = await APIService.getProjectComponents(props.projectId)
    allocatedComponents.value = allocationsResponse
    console.log('Allocated components loaded:', allocationsResponse)

  } catch (error) {
    console.error('Error loading project:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load project details',
      caption: error.response?.data?.detail || error.message
    })
  }
  loading.value = false
}

const filterComponents = async (val, update) => {
  if (val.length < 2) {
    update(() => {
      componentOptions.value = []
    })
    return
  }

  try {
    const response = await APIService.getComponents({
      search: val,
      limit: 20
    })

    update(() => {
      componentOptions.value = response.components.map(component => ({
        ...component,
        display_name: `${component.part_number} - ${component.name}`
      }))
    })
  } catch (error) {
    console.error('Error searching components:', error)
  }
}

const onComponentSelected = (component) => {
  if (component) {
    allocationQuantity.value = Math.min(1, component.quantity_on_hand)
  }
}

const allocateComponent = async () => {
  if (!selectedComponent.value || !allocationQuantity.value) return

  try {
    await APIService.allocateComponent(props.projectId, {
      component_id: selectedComponent.value.id,
      quantity: allocationQuantity.value
    })

    $q.notify({
      type: 'positive',
      message: 'Component allocated successfully'
    })

    closeAllocateDialog()
    loadProject()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to allocate component',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const returnComponent = (allocation) => {
  componentToReturn.value = allocation
  returnQuantity.value = Math.min(1, allocation.quantity_allocated)
  returnNotes.value = ''
  showReturnDialog.value = true
}

const confirmReturn = async () => {
  if (!componentToReturn.value || !returnQuantity.value) return

  try {
    await APIService.returnComponent(props.projectId, {
      component_id: componentToReturn.value.component_id,
      quantity: returnQuantity.value
    })

    $q.notify({
      type: 'positive',
      message: 'Component returned to inventory'
    })

    closeReturnDialog()
    loadProject()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to return component',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const allocateMore = (allocation) => {
  selectedComponent.value = {
    id: allocation.component_id,
    part_number: allocation.component_part_number,
    name: allocation.component_name,
    display_name: `${allocation.component_part_number || 'Unknown'} - ${allocation.component_name || 'Unknown'}`
  }
  allocationQuantity.value = 1
  allocationNotes.value = `Additional allocation for existing component`
  showAllocateDialog.value = true
}

const closeAllocateDialog = () => {
  showAllocateDialog.value = false
  selectedComponent.value = null
  allocationQuantity.value = 1
  allocationNotes.value = ''
}

const closeReturnDialog = () => {
  showReturnDialog.value = false
  componentToReturn.value = null
  returnQuantity.value = 1
  returnNotes.value = ''
}

const editProject = () => {
  router.push(`/projects/${props.projectId}/edit`)
}

const confirmDelete = () => {
  $q.dialog({
    title: 'Confirm Delete',
    message: 'Are you sure you want to delete this project? This action cannot be undone.',
    cancel: true,
    persistent: true
  }).onOk(() => {
    deleteProject()
  })
}

const deleteProject = async () => {
  try {
    await APIService.deleteProject(props.projectId)

    $q.notify({
      type: 'positive',
      message: 'Project deleted successfully'
    })

    router.push('/projects')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete project',
      caption: error.response?.data?.detail || error.message
    })
  }
}

// Watchers
watch(() => props.projectId, loadProject, { immediate: true })

// Lifecycle
onMounted(() => {
  loadProject()
})
</script>

<style scoped>
.project-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>