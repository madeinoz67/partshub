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
        <div class="col-auto">
          <q-btn
            color="primary"
            icon="add"
            label="New Project"
            @click="showCreateDialog = true"
            class="q-mr-sm"
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
      <q-card flat bordered class="q-mb-lg">
        <q-card-section>
          <div class="row q-col-gutter-md items-end">
            <!-- Search Input -->
            <div class="col-md-4 col-sm-6 col-12">
              <q-input
                v-model="searchQuery"
                label="Search projects..."
                outlined
                dense
                clearable
                debounce="300"
                @update:model-value="searchProjects"
              >
                <template v-slot:prepend>
                  <q-icon name="search" />
                </template>
              </q-input>
            </div>

            <!-- Status Filter -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="selectedStatus"
                :options="statusOptions"
                label="Status"
                outlined
                dense
                clearable
                @update:model-value="filterProjects"
              />
            </div>

            <!-- Sort By -->
            <div class="col-md-2 col-sm-6 col-12">
              <q-select
                v-model="sortBy"
                :options="sortOptions"
                label="Sort By"
                outlined
                dense
                @update:model-value="loadProjects"
              />
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

      <!-- Results Summary -->
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-body2 text-grey-6">
            Showing {{ projects.length }} of {{ totalProjects }} projects
            <span v-if="hasActiveFilters">(filtered)</span>
          </div>
        </div>
      </div>

      <!-- Project List View -->
      <div v-if="viewMode === 'list'">
        <q-table
          :rows="projects"
          :columns="tableColumns"
          :loading="loading"
          row-key="id"
          flat
          bordered
          @row-click="openProjectDetails"
          class="projects-table"
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-chip
                :color="getStatusColor(props.value)"
                text-color="white"
                :label="getStatusLabel(props.value)"
                size="sm"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-progress="props">
            <q-td :props="props">
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
          </template>

          <template v-slot:body-cell-budget="props">
            <q-td :props="props">
              <div class="text-right">
                <div class="text-body2">${{ formatCurrency(props.row.budget_spent || 0) }}</div>
                <div class="text-caption text-grey-6" v-if="props.row.budget_allocated">
                  of ${{ formatCurrency(props.row.budget_allocated) }}
                </div>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
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

              <div class="text-body2 text-grey-8 q-mb-md" v-if="project.description">
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
              <div class="row items-center" v-if="project.budget_allocated || project.budget_spent">
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

      <!-- Pagination -->
      <div v-if="totalProjects > pageSize" class="row justify-center q-mt-lg">
        <q-pagination
          v-model="currentPage"
          :max="Math.ceil(totalProjects / pageSize)"
          direction-links
          boundary-links
          @update:model-value="loadProjects"
        />
      </div>
    </div>

    <!-- Create Project Dialog -->
    <q-dialog v-model="showCreateDialog" persistent max-width="600px">
      <ProjectForm
        mode="create"
        @saved="handleProjectSaved"
        @cancelled="showCreateDialog = false"
      />
    </q-dialog>

    <!-- Edit Project Dialog -->
    <q-dialog v-model="showEditDialog" persistent max-width="600px">
      <ProjectForm
        mode="edit"
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
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from '../services/api'
import ProjectForm from '../components/ProjectForm.vue'
import ProjectView from '../components/ProjectView.vue'
import ComponentAllocation from '../components/ComponentAllocation.vue'
import ProjectReports from '../components/ProjectReports.vue'

const router = useRouter()
const $q = useQuasar()

// Reactive data
const projects = ref([])
const totalProjects = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)

// Search and filters
const searchQuery = ref('')
const selectedStatus = ref(null)
const sortBy = ref('created_at')
const viewMode = ref('list')

// Dialog state
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailsDialog = ref(false)
const showAllocationDialog = ref(false)
const showReportsDialog = ref(false)
const selectedProject = ref(null)

// Filter options
const statusOptions = [
  { label: 'All Statuses', value: null },
  { label: 'Planning', value: 'planning' },
  { label: 'Active', value: 'active' },
  { label: 'On Hold', value: 'on_hold' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' }
]

const sortOptions = [
  { label: 'Created Date', value: 'created_at' },
  { label: 'Name', value: 'name' },
  { label: 'Status', value: 'status' },
  { label: 'Budget', value: 'budget_allocated' }
]

// Table columns
const tableColumns = [
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

// Methods
const loadProjects = async () => {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
      sort_by: sortBy.value,
      sort_order: 'desc'
    }

    // Add filters
    if (searchQuery.value) params.search = searchQuery.value
    if (selectedStatus.value) params.status = selectedStatus.value

    const response = await api.get('/projects', { params })
    projects.value = response.data
    totalProjects.value = response.headers['x-total-count'] || response.data.length

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load projects',
      caption: error.response?.data?.detail || error.message
    })
  }
  loading.value = false
}

const searchProjects = () => {
  currentPage.value = 1
  loadProjects()
}

const filterProjects = () => {
  currentPage.value = 1
  loadProjects()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedStatus.value = null
  currentPage.value = 1
  loadProjects()
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

const handleProjectSaved = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  selectedProject.value = null
  loadProjects()
  $q.notify({
    type: 'positive',
    message: 'Project saved successfully'
  })
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
</style>