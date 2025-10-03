<template>
  <q-page class="projects-page">
    <div class="q-pa-lg">
      <!-- Page Header -->
      <div class="row items-center q-mb-lg">
        <div class="col">
          <div class="text-h4">Project Management</div>
          <div class="text-subtitle1 text-grey-6">
            Track component allocation and project lifecycle
          </div>
        </div>
        <div v-if="canPerformCrud()" class="col-auto">
          <q-btn
            color="primary"
            icon="add"
            label="New Project"
            class="q-mr-sm"
            @click="showCreateDialog = true"
          />
          <q-btn
            color="secondary"
            icon="analytics"
            label="Reports"
            @click="showReportsDialog = true"
          />
        </div>
      </div>

      <!-- Search and Filters -->
      <q-card class="q-mb-sm">
        <q-card-section class="q-pa-sm">
          <div class="row q-gutter-md items-center">
            <div class="col-md-4 col-xs-12">
              <q-input
                v-model="searchQuery"
                outlined
                dense
                placeholder="Search projects..."
                debounce="300"
                @update:model-value="searchProjects"
              >
                <template #prepend>
                  <q-icon name="search" />
                </template>
                <template #append>
                  <q-icon
                    v-if="searchQuery"
                    name="clear"
                    class="cursor-pointer"
                    @click="searchQuery = ''; searchProjects()"
                  />
                </template>
              </q-input>
            </div>

            <div v-if="canPerformCrud()" class="col-md-1 col-xs-12">
              <q-btn
                class="add-button-primary"
                icon="add"
                @click="showCreateDialog = true"
              >
                <span class="add-text-full">Add Project</span>
                <span class="add-text-short">Add</span>
              </q-btn>
            </div>

            <!-- View Mode -->
            <div class="col-auto">
              <q-btn-group flat>
                <q-btn
                  flat
                  :color="viewMode === 'list' ? 'primary' : 'grey'"
                  icon="list"
                  @click="viewMode = 'list'"
                />
                <q-btn
                  flat
                  :color="viewMode === 'cards' ? 'primary' : 'grey'"
                  icon="grid_view"
                  @click="viewMode = 'cards'"
                />
              </q-btn-group>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Statistics Cards - Desktop -->
      <div class="row q-gutter-xs q-mb-sm no-wrap gt-sm">
        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'all' }"
            @click="filterByStatus('all')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 q-mb-none">{{ totalProjects }}</div>
              <div class="text-overline text-grey">Total</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'planning' }"
            @click="filterByStatus('planning')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 text-blue q-mb-none">{{ totalPlanning }}</div>
              <div class="text-overline text-grey">Planning</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'active' }"
            @click="filterByStatus('active')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 text-green q-mb-none">{{ totalActive }}</div>
              <div class="text-overline text-grey">Active</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'on_hold' }"
            @click="filterByStatus('on_hold')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 text-orange q-mb-none">{{ totalOnHold }}</div>
              <div class="text-overline text-grey">On Hold</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'completed' }"
            @click="filterByStatus('completed')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 text-purple q-mb-none">{{ totalCompleted }}</div>
              <div class="text-overline text-grey">Completed</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col">
          <q-card
            class="mini-stats clickable-metric"
            :class="{ 'active-filter': activeFilter === 'cancelled' }"
            @click="filterByStatus('cancelled')"
          >
            <q-card-section class="q-pa-xs text-center">
              <div class="text-subtitle2 text-red q-mb-none">{{ totalCancelled }}</div>
              <div class="text-overline text-grey">Cancelled</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Status Filter Dropdown - Mobile -->
      <div class="row q-mb-sm lt-md">
        <div class="col-12">
          <q-select
            v-model="selectedStatus"
            :options="statusDropdownOptions"
            option-label="label"
            option-value="value"
            emit-value
            map-options
            label="Filter by Status"
            outlined
            dense
            clearable
            @update:model-value="onStatusFilterChange"
          >
            <template #prepend>
              <q-icon name="filter_list" />
            </template>
          </q-select>
        </div>
      </div>

      <!-- Results Summary -->
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-body2 text-grey-6">
            Showing {{ projects?.length || 0 }} of {{ totalProjects }} projects
            <span v-if="hasActiveFilters">(filtered)</span>
          </div>
        </div>
      </div>

      <!-- Project List View -->
      <div v-if="viewMode === 'list'">
        <q-table
          v-model:pagination="tablePagination"
          v-model:expanded="expanded"
          :rows="projects"
          :columns="tableColumns"
          :loading="loading"
          :rows-per-page-options="[25, 50, 100]"
          row-key="id"
          flat
          bordered
          :grid="$q.screen.xs"
          class="projects-table responsive-table compact-table"
          dense
          @request="onTableRequest"
        >
          <!-- Use body slot for internal expansion model -->
          <template #body="props">
            <!-- Regular row -->
            <q-tr :props="props">
              <!-- Expand button column -->
              <q-td auto-width>
                <q-btn
                  size="sm"
                  color="accent"
                  round
                  dense
                  flat
                  :icon="props.expand ? 'keyboard_arrow_down' : 'keyboard_arrow_right'"
                  @click="toggleExpand(props)"
                />
              </q-td>

              <!-- Project name column -->
              <q-td key="name" :props="props">
                <div class="text-weight-medium">{{ props.row.name }}</div>
                <div v-if="props.row.version" class="text-caption text-grey">
                  Version: {{ props.row.version }}
                </div>
              </q-td>

              <!-- Status column -->
              <q-td key="status" :props="props">
                <q-chip
                  :color="getStatusColor(props.row.status)"
                  text-color="white"
                  :label="getStatusLabel(props.row.status)"
                  size="sm"
                />
              </q-td>

              <!-- Version column -->
              <q-td key="version" :props="props">
                {{ props.row.version || '—' }}
              </q-td>

              <!-- Progress column -->
              <q-td key="progress" :props="props">
                <div class="row items-center">
                  <div class="col">
                    <q-linear-progress
                      :value="getProjectProgress(props.row)"
                      color="primary"
                      size="8px"
                      class="q-mr-sm"
                    />
                  </div>
                  <div class="col-auto text-caption">
                    {{ Math.round(getProjectProgress(props.row) * 100) }}%
                  </div>
                </div>
              </q-td>

              <!-- Budget column -->
              <q-td key="budget" :props="props">
                <div class="text-right">
                  <div class="text-body2">${{ formatCurrency(props.row.budget_spent || 0) }}</div>
                  <div v-if="props.row.budget_allocated" class="text-caption text-grey-6">
                    of ${{ formatCurrency(props.row.budget_allocated) }}
                  </div>
                </div>
              </q-td>

              <!-- Created column -->
              <q-td key="created_at" :props="props">
                {{ new Date(props.row.created_at).toLocaleDateString() }}
              </q-td>

              <!-- Actions column -->
              <q-td key="actions" :props="props">
                <q-btn-group flat>
                  <q-btn
                    flat
                    dense
                    icon="visibility"
                    color="primary"
                    @click.stop="openProjectDetails(props.row)"
                  >
                    <q-tooltip>View Details</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    icon="edit"
                    color="secondary"
                    @click.stop="editProject(props.row)"
                  >
                    <q-tooltip>Edit Project</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    icon="inventory"
                    color="accent"
                    @click.stop="allocateComponents(props.row)"
                  >
                    <q-tooltip>Allocate Components</q-tooltip>
                  </q-btn>
                </q-btn-group>
              </q-td>
            </q-tr>

            <!-- Expansion row -->
            <q-tr v-if="props.expand" :props="props">
              <q-td colspan="100%" style="padding: 0;">
                <div style="background: #f8f9fa; border-left: 4px solid #1976d2; margin: 0;">
                  <div class="q-pa-md">
                    <div class="row q-col-gutter-md">
                      <!-- Project Description -->
                      <div v-if="props.row.description" class="col-12">
                        <div class="text-subtitle2 q-mb-sm">Description</div>
                        <div class="text-body2 text-grey-8">{{ props.row.description }}</div>
                      </div>

                      <!-- Project Notes -->
                      <div v-if="props.row.notes" class="col-12">
                        <div class="text-subtitle2 q-mb-sm">Notes</div>
                        <div class="text-body2 text-grey-8">{{ props.row.notes }}</div>
                      </div>

                      <!-- Project Dates -->
                      <div class="col-md-6 col-12">
                        <div class="text-subtitle2 q-mb-sm">Timeline</div>
                        <div class="text-body2">
                          <div><strong>Created:</strong> {{ new Date(props.row.created_at).toLocaleDateString() }}</div>
                          <div><strong>Updated:</strong> {{ new Date(props.row.updated_at).toLocaleDateString() }}</div>
                        </div>
                      </div>

                      <!-- Budget Details -->
                      <div v-if="props.row.budget_allocated || props.row.budget_spent" class="col-md-6 col-12">
                        <div class="text-subtitle2 q-mb-sm">Budget Breakdown</div>
                        <div class="text-body2">
                          <div v-if="props.row.budget_allocated">
                            <strong>Allocated:</strong> ${{ formatCurrency(props.row.budget_allocated) }}
                          </div>
                          <div>
                            <strong>Spent:</strong> ${{ formatCurrency(props.row.budget_spent || 0) }}
                          </div>
                          <div v-if="props.row.budget_allocated">
                            <strong>Remaining:</strong> ${{ formatCurrency(props.row.budget_allocated - (props.row.budget_spent || 0)) }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </q-td>
            </q-tr>
          </template>

          <!-- Custom grid template for mobile -->
          <template #item="props">
            <div class="q-pa-xs col-xs-12 col-sm-6 col-md-4">
              <q-card>
                <q-card-section>
                  <div class="row items-center no-wrap">
                    <div class="col">
                      <div class="text-weight-medium">{{ props.row.name }}</div>
                      <div v-if="props.row.version" class="text-caption text-grey">
                        Version: {{ props.row.version }}
                      </div>
                    </div>
                    <div class="col-auto">
                      <q-chip
                        :color="getStatusColor(props.row.status)"
                        text-color="white"
                        :label="getStatusLabel(props.row.status)"
                        size="sm"
                      />
                    </div>
                  </div>

                  <!-- Progress bar -->
                  <div class="q-mt-sm">
                    <div class="row items-center q-mb-xs">
                      <div class="col text-caption text-grey-6">Progress</div>
                      <div class="col-auto text-caption">
                        {{ Math.round(getProjectProgress(props.row) * 100) }}%
                      </div>
                    </div>
                    <q-linear-progress
                      :value="getProjectProgress(props.row)"
                      color="primary"
                      size="4px"
                    />
                  </div>

                  <!-- Budget info -->
                  <div v-if="props.row.budget_allocated || props.row.budget_spent" class="q-mt-sm">
                    <div class="text-caption text-grey-6">Budget</div>
                    <div class="text-body2">
                      ${{ formatCurrency(props.row.budget_spent || 0) }}
                      <span v-if="props.row.budget_allocated" class="text-grey-6">
                        / ${{ formatCurrency(props.row.budget_allocated) }}
                      </span>
                    </div>
                  </div>

                  <!-- Description if available -->
                  <div v-if="props.row.description" class="q-mt-sm">
                    <div class="text-caption text-grey-6">Description</div>
                    <div class="text-body2">
                      {{ props.row.description.length > 100 ? props.row.description.substring(0, 100) + '...' : props.row.description }}
                    </div>
                  </div>

                  <!-- Created date -->
                  <div class="q-mt-sm">
                    <div class="text-caption text-grey-6">
                      Created: {{ new Date(props.row.created_at).toLocaleDateString() }}
                    </div>
                  </div>
                </q-card-section>

                <!-- Actions section -->
                <q-card-actions align="right">
                  <q-btn
                    flat
                    dense
                    icon="visibility"
                    color="primary"
                    @click="openProjectDetails(props.row)"
                  >
                    <q-tooltip>View Details</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    icon="edit"
                    color="secondary"
                    @click="editProject(props.row)"
                  >
                    <q-tooltip>Edit Project</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    icon="inventory"
                    color="accent"
                    @click="allocateComponents(props.row)"
                  >
                    <q-tooltip>Allocate Components</q-tooltip>
                  </q-btn>
                </q-card-actions>
              </q-card>
            </div>
          </template>
        </q-table>
      </div>

      <!-- Project Cards View -->
      <div v-else-if="viewMode === 'cards'" class="row q-col-gutter-md">
        <div
          v-for="project in projects"
          :key="project.id"
          class="col-lg-4 col-md-6 col-12"
        >
          <q-card class="project-card cursor-pointer" @click="openProjectDetails(project)">
            <q-card-section>
              <div class="row items-start q-mb-sm">
                <div class="col">
                  <div class="text-h6">{{ project.name }}</div>
                  <div class="text-caption text-grey-6">{{ project.version || 'v1.0' }}</div>
                </div>
                <div class="col-auto">
                  <q-chip
                    :color="getStatusColor(project.status)"
                    text-color="white"
                    :label="getStatusLabel(project.status)"
                    size="sm"
                  />
                </div>
              </div>

              <div v-if="project.description" class="text-body2 text-grey-8 q-mb-md">
                {{ truncateText(project.description, 100) }}
              </div>

              <!-- Progress Bar -->
              <div class="q-mb-sm">
                <div class="row items-center q-mb-xs">
                  <div class="col text-caption text-grey-6">Progress</div>
                  <div class="col-auto text-caption">
                    {{ Math.round(getProjectProgress(project) * 100) }}%
                  </div>
                </div>
                <q-linear-progress
                  :value="getProjectProgress(project)"
                  color="primary"
                  size="6px"
                />
              </div>

              <!-- Budget Info -->
              <div v-if="project.budget_allocated || project.budget_spent" class="row items-center">
                <div class="col">
                  <div class="text-caption text-grey-6">Budget</div>
                  <div class="text-body2">
                    ${{ formatCurrency(project.budget_spent || 0) }}
                    <span v-if="project.budget_allocated" class="text-grey-6">
                      / ${{ formatCurrency(project.budget_allocated) }}
                    </span>
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon
                    :name="getBudgetIcon(project)"
                    :color="getBudgetColor(project)"
                    size="sm"
                  />
                </div>
              </div>
            </q-card-section>

            <q-card-actions align="right">
              <q-btn
                flat
                dense
                icon="visibility"
                color="primary"
                @click.stop="openProjectDetails(project)"
              />
              <q-btn
                flat
                dense
                icon="edit"
                color="secondary"
                @click.stop="editProject(project)"
              />
              <q-btn
                flat
                dense
                icon="inventory"
                color="accent"
                @click.stop="allocateComponents(project)"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center q-py-lg">
        <q-spinner size="50px" color="primary" />
        <div class="text-subtitle2 q-mt-md">Loading projects...</div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && projects.length === 0" class="text-center q-py-xl">
        <q-icon name="folder_open" size="80px" color="grey-4" />
        <div class="text-h6 text-grey-6 q-mt-md">
          {{ hasActiveFilters ? 'No projects match your filters' : 'No projects found' }}
        </div>
        <div class="text-body2 text-grey-5 q-mt-sm">
          {{ hasActiveFilters ? 'Try adjusting your search criteria' : 'Create your first project to get started' }}
        </div>
        <q-btn
          v-if="!hasActiveFilters"
          color="primary"
          icon="add"
          label="New Project"
          class="q-mt-md"
          @click="showCreateDialog = true"
        />
        <q-btn
          v-else
          flat
          color="primary"
          label="Clear Filters"
          class="q-mt-md"
          @click="clearFilters"
        />
      </div>

    </div>

    <!-- Create Project Dialog -->
    <q-dialog v-model="showCreateDialog" persistent max-width="600px">
      <ProjectForm
        @saved="handleProjectSaved"
        @cancelled="showCreateDialog = false"
      />
    </q-dialog>

    <!-- Edit Project Dialog -->
    <q-dialog v-model="showEditDialog" persistent max-width="600px">
      <ProjectForm
        :project="selectedProject"
        @saved="handleProjectSaved"
        @cancelled="showEditDialog = false"
      />
    </q-dialog>

    <!-- Project Details Dialog -->
    <q-dialog v-model="showDetailsDialog" maximized>
      <ProjectView
        v-if="selectedProject"
        :project-id="selectedProject.id"
        @close="showDetailsDialog = false"
        @project-updated="loadProjects"
      />
    </q-dialog>

    <!-- Component Allocation Dialog -->
    <q-dialog v-model="showAllocationDialog" persistent max-width="800px">
      <ComponentAllocation
        v-if="selectedProject"
        :project="selectedProject"
        @saved="handleAllocationSaved"
        @cancelled="showAllocationDialog = false"
      />
    </q-dialog>

    <!-- Reports Dialog -->
    <q-dialog v-model="showReportsDialog" persistent max-width="900px">
      <ProjectReports
        @close="showReportsDialog = false"
      />
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { APIService } from '../services/api'
import ProjectForm from '../components/ProjectForm.vue'
import ProjectView from '../components/ProjectView.vue'
import ComponentAllocation from '../components/ComponentAllocation.vue'
import ProjectReports from '../components/ProjectReports.vue'
import { useAuth } from '../composables/useAuth'

const $q = useQuasar()
const { canPerformCrud } = useAuth()

// Reactive data
const projects = ref([])
const totalProjects = ref(0)
const loading = ref(false)

// Search and filters
const searchQuery = ref('')
const selectedStatus = ref(null)
const activeFilter = ref('all')
const viewMode = ref('list')

// Table sorting and pagination
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const tablePagination = ref({
  sortBy: 'created_at',
  descending: true,
  page: 1,
  rowsPerPage: 50
})

// Row expansion
const expanded = ref([])

// Dialog state
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailsDialog = ref(false)
const showAllocationDialog = ref(false)
const showReportsDialog = ref(false)
const selectedProject = ref(null)

// Filter options

const statusDropdownOptions = computed(() => [
  { label: `All Projects (${totalProjects.value})`, value: null },
  { label: `Planning (${totalPlanning.value})`, value: 'planning' },
  { label: `Active (${totalActive.value})`, value: 'active' },
  { label: `On Hold (${totalOnHold.value})`, value: 'on_hold' },
  { label: `Completed (${totalCompleted.value})`, value: 'completed' },
  { label: `Cancelled (${totalCancelled.value})`, value: 'cancelled' }
])


// Table columns
const tableColumns = [
  {
    name: 'expand',
    label: '',
    field: 'expand',
    sortable: false,
    required: true,
    align: 'left',
    style: 'width: 40px',
    headerStyle: 'width: 40px'
  },
  {
    name: 'name',
    label: 'Project Name',
    field: 'name',
    align: 'left',
    sortable: true
  },
  {
    name: 'status',
    label: 'Status',
    field: 'status',
    align: 'center',
    sortable: true
  },
  {
    name: 'version',
    label: 'Version',
    field: 'version',
    align: 'center'
  },
  {
    name: 'progress',
    label: 'Progress',
    field: 'progress',
    align: 'center'
  },
  {
    name: 'budget',
    label: 'Budget',
    field: 'budget_spent',
    align: 'right',
    sortable: true
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'center',
    sortable: true,
    format: (val) => new Date(val).toLocaleDateString()
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center'
  }
]

// Computed properties
const hasActiveFilters = computed(() => {
  return searchQuery.value || selectedStatus.value
})

const totalPlanning = computed(() => {
  return projects.value.filter(p => p.status === 'planning').length
})

const totalActive = computed(() => {
  return projects.value.filter(p => p.status === 'active').length
})

const totalOnHold = computed(() => {
  return projects.value.filter(p => p.status === 'on_hold').length
})

const totalCompleted = computed(() => {
  return projects.value.filter(p => p.status === 'completed').length
})

const totalCancelled = computed(() => {
  return projects.value.filter(p => p.status === 'cancelled').length
})

// Methods
const onTableRequest = async (props) => {
  const { page, rowsPerPage, sortBy: newSortBy, descending } = props.pagination

  // Update pagination state
  tablePagination.value.page = page
  tablePagination.value.rowsPerPage = rowsPerPage
  tablePagination.value.sortBy = newSortBy
  tablePagination.value.descending = descending

  // Update internal sort state
  sortBy.value = newSortBy || 'created_at'
  sortOrder.value = descending ? 'desc' : 'asc'

  await loadProjects()
}

const loadProjects = async () => {
  loading.value = true
  try {
    const params = {
      limit: tablePagination.value.rowsPerPage,
      offset: (tablePagination.value.page - 1) * tablePagination.value.rowsPerPage,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }

    // Add filters
    if (searchQuery.value) params.search = searchQuery.value
    if (selectedStatus.value) params.status = selectedStatus.value

    const response = await APIService.getProjects(params)
    projects.value = response.projects || []

    // Update pagination with total count
    tablePagination.value.rowsNumber = response.total || 0
    totalProjects.value = response.total || 0

  } catch (error) {
    projects.value = []
    totalProjects.value = 0
    tablePagination.value.rowsNumber = 0
    $q.notify({
      type: 'negative',
      message: 'Failed to load projects',
      caption: error.response?.data?.detail || error.message
    })
  }
  loading.value = false
}

const searchProjects = () => {
  tablePagination.value.page = 1
  loadProjects()
}


const clearFilters = () => {
  searchQuery.value = ''
  selectedStatus.value = null
  activeFilter.value = 'all'
  tablePagination.value.page = 1
  loadProjects()
}

const filterByStatus = (status) => {
  activeFilter.value = status
  if (status === 'all') {
    selectedStatus.value = null
  } else {
    selectedStatus.value = status
  }
  tablePagination.value.page = 1
  loadProjects()
}

const onStatusFilterChange = (status) => {
  if (status === null) {
    activeFilter.value = 'all'
  } else {
    activeFilter.value = status
  }
  selectedStatus.value = status
  tablePagination.value.page = 1
  loadProjects()
}

const toggleExpand = (props) => {
  props.expand = !props.expand
}

const openProjectDetails = (project) => {
  selectedProject.value = project
  showDetailsDialog.value = true
}

const editProject = (project) => {
  selectedProject.value = project
  showEditDialog.value = true
}

const allocateComponents = (project) => {
  selectedProject.value = project
  showAllocationDialog.value = true
}

const handleProjectSaved = async (projectData) => {
  try {
    if (showCreateDialog.value) {
      // Create new project
      await APIService.createProject(projectData)
      // Reset to first page to see the new project (since we sort by created_at desc)
      tablePagination.value.page = 1
    } else if (showEditDialog.value && selectedProject.value) {
      // Update existing project
      await APIService.updateProject(selectedProject.value.id, projectData)
    }

    showCreateDialog.value = false
    showEditDialog.value = false
    selectedProject.value = null
    await loadProjects()

    $q.notify({
      type: 'positive',
      message: 'Project saved successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to save project',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const handleAllocationSaved = () => {
  showAllocationDialog.value = false
  selectedProject.value = null
  loadProjects()
  $q.notify({
    type: 'positive',
    message: 'Component allocation updated'
  })
}

// Status and progress helpers
const getStatusColor = (status) => {
  const colors = {
    planning: 'blue',
    active: 'green',
    on_hold: 'orange',
    completed: 'positive',
    cancelled: 'negative'
  }
  return colors[status] || 'grey'
}

const getStatusLabel = (status) => {
  const labels = {
    planning: 'Planning',
    active: 'Active',
    on_hold: 'On Hold',
    completed: 'Completed',
    cancelled: 'Cancelled'
  }
  return labels[status] || status
}

const getProjectProgress = (project) => {
  // Calculate progress based on status and component allocation
  if (project.status === 'completed') return 1.0
  if (project.status === 'cancelled') return 0.0
  if (project.status === 'planning') return 0.1
  if (project.status === 'active') return 0.5 // Would need actual progress data
  if (project.status === 'on_hold') return 0.3
  return 0.0
}

const getBudgetIcon = (project) => {
  if (!project.budget_allocated) return 'info'
  const spent = project.budget_spent || 0
  const allocated = project.budget_allocated
  const ratio = spent / allocated

  if (ratio > 1.0) return 'warning'
  if (ratio > 0.8) return 'info'
  return 'check_circle'
}

const getBudgetColor = (project) => {
  if (!project.budget_allocated) return 'grey'
  const spent = project.budget_spent || 0
  const allocated = project.budget_allocated
  const ratio = spent / allocated

  if (ratio > 1.0) return 'negative'
  if (ratio > 0.8) return 'warning'
  return 'positive'
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Lifecycle
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-page {
  max-width: 1400px;
  margin: 0 auto;
}

.project-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.projects-table tbody tr {
  cursor: pointer;
}

.projects-table tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.mini-stats {
  border: 2px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
}

.mini-stats:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.clickable-metric {
  min-height: 60px;
}

.clickable-metric.active-filter {
  border-color: #1976d2;
  background-color: rgba(25, 118, 210, 0.05);
}

/* Compact table styling */
.compact-table {
  font-size: 0.875rem;
}

.compact-table :deep(.q-table__top) {
  padding: 8px 16px;
}

.compact-table :deep(.q-td) {
  padding: 2px 6px;
  font-size: 0.8rem;
  height: 32px;
}

.compact-table :deep(.q-th) {
  padding: 3px 6px;
  font-size: 0.8rem;
  font-weight: 600;
  height: 36px;
}

.compact-table :deep(tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s;
  height: 32px;
}

.compact-table :deep(tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.04);
}

.compact-table :deep(.q-chip) {
  font-size: 0.7rem;
  padding: 1px 4px;
  min-height: 16px;
}

/* Table responsive styling */
.responsive-table {
  min-width: 100%;
  overflow-x: auto;
}

.responsive-table :deep(.q-table__container) {
  overflow-x: auto;
}

.responsive-table :deep(.q-table__middle) {
  min-width: 100%;
}

.responsive-table :deep(.q-td) {
  padding: 4px 8px;
  font-size: 0.875rem;
}

.responsive-table :deep(.q-th) {
  padding: 4px 8px;
  font-size: 0.875rem;
  font-weight: 600;
}

/* Mobile responsive adjustments */
@media (max-width: 599px) {
  .responsive-table :deep(.q-table__container) {
    overflow-x: auto;
  }

  .responsive-table :deep(.q-table__middle) {
    min-width: 100%;
  }

  .responsive-table :deep(.q-td) {
    white-space: nowrap;
    padding: 4px 2px;
    font-size: 0.75rem;
  }

  .responsive-table :deep(.q-th) {
    padding: 4px 2px;
    font-size: 0.75rem;
    white-space: nowrap;
  }

  /* Hide less important columns on very small screens */
  .responsive-table :deep(.q-td:nth-child(4)),
  .responsive-table :deep(.q-th:nth-child(4)),
  .responsive-table :deep(.q-td:nth-child(5)),
  .responsive-table :deep(.q-th:nth-child(5)),
  .responsive-table :deep(.q-td:nth-child(6)),
  .responsive-table :deep(.q-th:nth-child(6)),
  .responsive-table :deep(.q-td:nth-child(7)),
  .responsive-table :deep(.q-th:nth-child(7)) {
    display: none;
  }

  /* Make first column (expand/project name) wider */
  .responsive-table :deep(.q-td:first-child),
  .responsive-table :deep(.q-th:first-child) {
    min-width: 40px;
  }

  /* Make project name column wider */
  .responsive-table :deep(.q-td:nth-child(2)),
  .responsive-table :deep(.q-th:nth-child(2)) {
    min-width: 150px;
  }

  /* Keep status and actions visible */
  .responsive-table :deep(.q-td:nth-child(3)),
  .responsive-table :deep(.q-th:nth-child(3)),
  .responsive-table :deep(.q-td:last-child),
  .responsive-table :deep(.q-th:last-child) {
    display: table-cell;
  }
}

/* Tablet adjustments */
@media (min-width: 600px) and (max-width: 1023px) {
  .responsive-table :deep(.q-td) {
    padding: 3px 6px;
    font-size: 0.8rem;
  }

  .responsive-table :deep(.q-th) {
    padding: 3px 6px;
    font-size: 0.8rem;
  }

  /* Hide some columns on tablets */
  .responsive-table :deep(.q-td:nth-child(4)),
  .responsive-table :deep(.q-th:nth-child(4)),
  .responsive-table :deep(.q-td:nth-child(6)),
  .responsive-table :deep(.q-th:nth-child(6)) {
    display: none;
  }
}

/* Grid mode card styling */
.projects-table :deep(.q-table__grid-content) {
  flex-wrap: wrap;
}

.projects-table :deep(.q-table__grid-item) {
  padding: 4px;
}

.projects-table :deep(.q-table__grid-item .q-card) {
  height: 100%;
  transition: transform 0.2s, box-shadow 0.2s;
}

.projects-table :deep(.q-table__grid-item .q-card:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>