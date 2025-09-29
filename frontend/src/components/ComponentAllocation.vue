<template>
  <q-card>
    <q-card-section>
      <div class="row items-center">
        <div class="col">
          <div class="text-h6">Component Allocation</div>
          <div class="text-body2 text-grey-7">Manage component allocations for {{ project?.name }}</div>
        </div>
        <div class="col-auto">
          <q-btn
            flat
            round
            icon="close"
            aria-label="Close dialog"
            @click="$emit('cancelled')"
          />
        </div>
      </div>
    </q-card-section>

    <q-card-section>
      <div class="row q-gutter-md q-mb-md">
        <div class="col">
          <q-input
            v-model="searchQuery"
            label="Search Components"
            filled
            dense
            debounce="300"
          >
            <template #prepend>
              <q-icon name="search" />
            </template>
          </q-input>
        </div>
        <div class="col-auto">
          <q-btn
            color="primary"
            icon="add"
            label="Add Component"
            @click="showAddDialog = true"
          />
        </div>
      </div>

      <q-table
        :rows="allocations"
        :columns="columns"
        row-key="id"
        flat
        bordered
        :loading="loading"
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn
              flat
              round
              dense
              icon="edit"
              @click="editAllocation(props.row)"
            />
            <q-btn
              flat
              round
              dense
              icon="delete"
              color="negative"
              @click="confirmDelete(props.row)"
            />
          </q-td>
        </template>

        <template #body-cell-status="props">
          <q-td :props="props">
            <q-chip
              :color="getStatusColor(props.row.status)"
              text-color="white"
              dense
            >
              {{ props.row.status }}
            </q-chip>
          </q-td>
        </template>
      </q-table>
    </q-card-section>

    <!-- Add/Edit Dialog -->
    <q-dialog v-model="showAddDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editMode ? 'Edit' : 'Add' }} Component Allocation</div>
        </q-card-section>

        <q-form @submit="onSubmit">
          <q-card-section>
            <div class="column q-gutter-md">
              <q-select
                v-model="form.componentId"
                label="Component"
                filled
                :options="componentOptions"
                option-label="display_name"
                option-value="id"
                emit-value
                map-options
                use-input
                input-debounce="300"
                clearable
                :loading="components.length === 0"
                @filter="filterComponents"
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
                <template #no-option>
                  <q-item>
                    <q-item-section class="text-grey">
                      {{ components.length === 0 ? 'Loading components...' : 'No matching components' }}
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>

              <q-input
                v-model.number="form.quantity"
                label="Quantity Required"
                filled
                type="number"
                min="1"
                required
              />

              <q-input
                v-model="form.notes"
                label="Notes"
                filled
                type="textarea"
                rows="2"
              />
            </div>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Cancel" />
            <q-btn
              :label="editMode ? 'Update' : 'Add'"
              type="submit"
              color="primary"
              :loading="submitting"
            />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { APIService } from '../services/api'

interface ComponentAllocation {
  id: string
  componentId: string
  componentName: string
  quantity: number
  notes: string
  status: 'planned' | 'allocated' | 'installed'
}

interface Component {
  id: string
  name: string
  part_number: string
  quantity_on_hand: number
}

interface Props {
  project: any
  loading?: boolean
}

interface Emits {
  (e: 'saved'): void
  (e: 'cancelled'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()

const searchQuery = ref('')
const showAddDialog = ref(false)
const editMode = ref(false)
const submitting = ref(false)

const form = ref({
  componentId: '',
  quantity: 1,
  notes: ''
})

const allocations = ref<ComponentAllocation[]>([])
const components = ref<Component[]>([])
const componentOptions = ref<Component[]>([])
const loading = ref(false)

const columns = [
  {
    name: 'componentName',
    label: 'Component',
    field: 'componentName',
    align: 'left' as const,
    sortable: true
  },
  {
    name: 'quantity',
    label: 'Quantity',
    field: 'quantity',
    align: 'center' as const,
    sortable: true
  },
  {
    name: 'status',
    label: 'Status',
    field: 'status',
    align: 'center' as const,
    sortable: true
  },
  {
    name: 'notes',
    label: 'Notes',
    field: 'notes',
    align: 'left' as const
  },
  {
    name: 'actions',
    label: 'Actions',
    field: 'actions',
    align: 'center' as const
  }
]

// Load components from API
const loadComponents = async () => {
  try {
    console.log('Loading components...')
    const response = await APIService.getComponents({ limit: 100 })
    console.log('Components response:', response)

    components.value = (response.components || []).map(component => ({
      ...component,
      display_name: `${component.part_number} - ${component.name}`
    }))
    componentOptions.value = components.value

    console.log('Loaded components:', components.value.length)
    console.log('Component options:', componentOptions.value.length)
  } catch (error) {
    console.error('Error loading components:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load components',
      caption: error.message
    })
  }
}

// Load project allocations
const loadAllocations = async () => {
  if (!props.project?.id) return

  loading.value = true
  try {
    const response = await APIService.getProjectComponents(props.project.id)
    allocations.value = response.map((allocation: any) => ({
      id: `${allocation.project_id}-${allocation.component_id}`,
      componentId: allocation.component_id,
      componentName: allocation.component_part_number || 'Unknown',
      quantity: allocation.quantity_allocated,
      notes: allocation.notes || '',
      status: 'allocated'
    }))
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load allocations',
      caption: error.message
    })
  }
  loading.value = false
}

function getStatusColor(status: string) {
  switch (status) {
    case 'planned': return 'grey'
    case 'allocated': return 'orange'
    case 'installed': return 'green'
    default: return 'grey'
  }
}

function editAllocation(allocation: ComponentAllocation) {
  editMode.value = true
  form.value = {
    componentId: allocation.componentId,
    quantity: allocation.quantity,
    notes: allocation.notes
  }
  showAddDialog.value = true
}

function confirmDelete(allocation: ComponentAllocation) {
  $q.dialog({
    title: 'Confirm Return',
    message: `Are you sure you want to return ${allocation.componentName} to inventory?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await APIService.returnComponent(props.project.id, {
        component_id: allocation.componentId,
        quantity: allocation.quantity
      })

      $q.notify({
        type: 'positive',
        message: 'Component returned to inventory'
      })

      loadAllocations()
      emit('saved')
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to return component',
        caption: error.response?.data?.detail || error.message
      })
    }
  })
}

function filterComponents(val: string, update: (fn: () => void) => void) {
  update(() => {
    if (val === '') {
      componentOptions.value = components.value
    } else {
      const needle = val.toLowerCase()
      componentOptions.value = components.value.filter(v =>
        v.name?.toLowerCase().indexOf(needle) > -1 ||
        v.part_number?.toLowerCase().indexOf(needle) > -1
      )
    }
  })
}

async function onSubmit() {
  if (!props.project?.id || !form.value.componentId) return

  submitting.value = true
  try {
    await APIService.allocateComponent(props.project.id, {
      component_id: form.value.componentId,
      quantity: form.value.quantity
    })

    $q.notify({
      type: 'positive',
      message: 'Component allocated successfully'
    })

    showAddDialog.value = false
    editMode.value = false
    resetForm()
    loadAllocations()
    emit('saved')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to allocate component',
      caption: error.response?.data?.detail || error.message
    })
  }
  submitting.value = false
}

function resetForm() {
  form.value = {
    componentId: '',
    quantity: 1,
    notes: ''
  }
}

// Initialize data
onMounted(() => {
  loadComponents()
  loadAllocations()
})
</script>