<template>
  <q-page class="q-pa-md">
    <!-- Page Header -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Reorder Alert Management</div>
        <div class="text-caption text-grey">Operational tool for managing low stock alerts and reorder workflows</div>
      </div>
      <div class="col-auto row q-gutter-sm">
        <q-btn
          outline
          color="primary"
          icon="analytics"
          label="View Analytics"
          @click="$router.push('/analytics')"
        />
        <q-btn
          color="primary"
          icon="refresh"
          label="Refresh"
          :loading="loading"
          @click="loadData"
        />
      </div>
    </div>

    <!-- Tabs for Different Views -->
    <q-card flat bordered>
      <q-tabs
        v-model="activeTab"
        dense
        class="text-grey"
        active-color="primary"
        indicator-color="primary"
        align="left"
      >
        <q-tab name="active" label="Active Alerts" />
        <q-tab name="history" label="History" />
        <q-tab name="low-stock" label="Low Stock Report" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="activeTab" animated>
        <!-- Active Alerts Tab -->
        <q-tab-panel name="active">
          <!-- Filters -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-12 col-sm-6 col-md-3">
              <q-input
                v-model="filters.componentSearch"
                outlined
                dense
                placeholder="Search components..."
                clearable
                @update:model-value="loadAlerts"
              >
                <template #prepend>
                  <q-icon name="search" />
                </template>
              </q-input>
            </div>

            <div class="col-12 col-sm-6 col-md-3">
              <q-select
                v-model="filters.severity"
                outlined
                dense
                :options="severityOptions"
                label="Severity"
                clearable
                emit-value
                map-options
                @update:model-value="loadAlerts"
              />
            </div>

            <div class="col-12 col-sm-6 col-md-3">
              <q-input
                v-model.number="filters.minShortage"
                outlined
                dense
                type="number"
                label="Min Shortage"
                clearable
                @update:model-value="loadAlerts"
              />
            </div>
          </div>

          <!-- Alerts Table -->
          <q-table
            :rows="alerts"
            :columns="alertColumns"
            row-key="id"
            :loading="loading"
            :pagination="pagination"
            flat
            bordered
            @request="onTableRequest"
          >
            <template #body-cell-component="props">
              <q-td :props="props">
                <div class="text-weight-medium">{{ props.row.component_name }}</div>
                <div v-if="props.row.component_part_number" class="text-caption text-grey">
                  {{ props.row.component_part_number }}
                </div>
              </q-td>
            </template>

            <template #body-cell-location="props">
              <q-td :props="props">
                {{ props.row.location_name }}
              </q-td>
            </template>

            <template #body-cell-severity="props">
              <q-td :props="props">
                <q-badge
                  :color="getSeverityColor(props.row.severity)"
                  :label="props.row.severity.toUpperCase()"
                />
              </q-td>
            </template>

            <template #body-cell-stock="props">
              <q-td :props="props">
                <div class="text-weight-medium">
                  {{ props.row.current_quantity }} / {{ props.row.reorder_threshold }}
                </div>
                <div class="text-caption text-grey">
                  Short: {{ props.row.shortage_amount }}
                  ({{ Math.round(props.row.shortage_percentage) }}%)
                </div>
              </q-td>
            </template>

            <template #body-cell-created_at="props">
              <q-td :props="props">
                {{ formatDate(props.row.created_at) }}
              </q-td>
            </template>

            <template #body-cell-actions="props">
              <q-td :props="props">
                <q-btn
                  flat
                  dense
                  round
                  icon="shopping_cart"
                  color="positive"
                  size="sm"
                  @click="showMarkOrderedDialog(props.row)"
                >
                  <q-tooltip>Mark as Ordered</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  dense
                  round
                  icon="close"
                  color="grey"
                  size="sm"
                  @click="showDismissDialog(props.row)"
                >
                  <q-tooltip>Dismiss</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  dense
                  round
                  icon="tune"
                  color="primary"
                  size="sm"
                  @click="showThresholdDialog(props.row)"
                >
                  <q-tooltip>Update Threshold</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-tab-panel>

        <!-- History Tab -->
        <q-tab-panel name="history">
          <!-- History Filters -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-12 col-sm-6 col-md-4">
              <q-select
                v-model="historyFilters.status"
                outlined
                dense
                :options="historyStatusOptions"
                label="Status"
                clearable
                emit-value
                map-options
                @update:model-value="loadHistory"
              />
            </div>
          </div>

          <!-- History Table -->
          <q-table
            :rows="historyAlerts"
            :columns="historyColumns"
            row-key="id"
            :loading="historyLoading"
            flat
            bordered
          >
            <template #body-cell-component="props">
              <q-td :props="props">
                <div class="text-weight-medium">{{ props.row.component_name }}</div>
                <div v-if="props.row.component_part_number" class="text-caption text-grey">
                  {{ props.row.component_part_number }}
                </div>
              </q-td>
            </template>

            <template #body-cell-status="props">
              <q-td :props="props">
                <q-chip
                  :color="getStatusColor(props.row.status)"
                  text-color="white"
                  size="sm"
                  :label="props.row.status.toUpperCase()"
                />
              </q-td>
            </template>

            <template #body-cell-resolved="props">
              <q-td :props="props">
                <div v-if="props.row.ordered_at">
                  {{ formatDate(props.row.ordered_at) }}
                </div>
                <div v-else-if="props.row.dismissed_at">
                  {{ formatDate(props.row.dismissed_at) }}
                </div>
                <div v-else-if="props.row.resolved_at">
                  {{ formatDate(props.row.resolved_at) }}
                </div>
                <div v-else class="text-grey">
                  -
                </div>
              </q-td>
            </template>

            <template #body-cell-notes="props">
              <q-td :props="props">
                <div v-if="props.row.notes" class="text-caption">
                  {{ props.row.notes }}
                </div>
                <div v-else class="text-grey">
                  -
                </div>
              </q-td>
            </template>
          </q-table>
        </q-tab-panel>

        <!-- Low Stock Report Tab -->
        <q-tab-panel name="low-stock">
          <div v-if="lowStockReport" class="q-mb-md">
            <div class="text-subtitle1 q-mb-md">
              Total Items: <strong>{{ lowStockReport.total_items }}</strong> |
              Total Shortage: <strong>{{ lowStockReport.total_shortage }}</strong> units
            </div>

            <q-table
              :rows="lowStockReport.items"
              :columns="lowStockColumns"
              row-key="component_id"
              :loading="lowStockLoading"
              flat
              bordered
            >
              <template #body-cell-component="props">
                <q-td :props="props">
                  <div class="text-weight-medium">{{ props.row.component_name }}</div>
                  <div v-if="props.row.component_part_number" class="text-caption text-grey">
                    {{ props.row.component_part_number }}
                  </div>
                </q-td>
              </template>

              <template #body-cell-stock="props">
                <q-td :props="props">
                  <div class="text-weight-medium">
                    {{ props.row.current_quantity }} / {{ props.row.reorder_threshold }}
                  </div>
                  <div class="text-caption text-grey">
                    Short: {{ props.row.shortage_amount }}
                    ({{ Math.round(props.row.shortage_percentage) }}%)
                  </div>
                </q-td>
              </template>

              <template #body-cell-has_active_alert="props">
                <q-td :props="props">
                  <q-icon
                    :name="props.row.has_active_alert ? 'warning' : 'check_circle'"
                    :color="props.row.has_active_alert ? 'warning' : 'positive'"
                    size="sm"
                  />
                </q-td>
              </template>

              <template #body-cell-actions="props">
                <q-td :props="props">
                  <q-btn
                    flat
                    dense
                    round
                    icon="tune"
                    color="primary"
                    size="sm"
                    @click="showThresholdDialogFromReport(props.row)"
                  >
                    <q-tooltip>Update Threshold</q-tooltip>
                  </q-btn>
                </q-td>
              </template>
            </q-table>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>

    <!-- Alert Action Dialog -->
    <AlertActionDialog
      v-model="showActionDialog"
      :alert="selectedAlert"
      :action="dialogAction"
      @action-completed="onActionCompleted"
    />

    <!-- Threshold Update Dialog -->
    <ThresholdUpdateDialog
      v-model="showThresholdUpdateDialog"
      :component-id="thresholdDialogData.componentId"
      :location-id="thresholdDialogData.locationId"
      :component-name="thresholdDialogData.componentName"
      :current-quantity="thresholdDialogData.currentQuantity"
      :current-threshold="thresholdDialogData.currentThreshold"
      @updated="onThresholdUpdated"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { reorderAlertsApi } from '../services/reorderAlertsService'
import AlertActionDialog from '../components/AlertActionDialog.vue'
import ThresholdUpdateDialog from '../components/ThresholdUpdateDialog.vue'
import type {
  ReorderAlert,
  AlertStatistics,
  LowStockReport,
  LowStockItem,
} from '../services/reorderAlertsService'

const $q = useQuasar()

// State
const activeTab = ref('active')
const loading = ref(false)
const historyLoading = ref(false)
const lowStockLoading = ref(false)

const alerts = ref<ReorderAlert[]>([])
const historyAlerts = ref<ReorderAlert[]>([])
const lowStockReport = ref<LowStockReport | null>(null)
const statistics = ref<AlertStatistics | null>(null)

const showActionDialog = ref(false)
const showThresholdUpdateDialog = ref(false)
const selectedAlert = ref<ReorderAlert | null>(null)
const dialogAction = ref<'dismiss' | 'ordered'>('dismiss')

const thresholdDialogData = ref({
  componentId: '',
  locationId: '',
  componentName: '',
  currentQuantity: 0,
  currentThreshold: 0,
})

// Filters
const filters = ref({
  componentSearch: '',
  severity: null as 'critical' | 'high' | 'medium' | 'low' | null,
  minShortage: null as number | null,
})

const historyFilters = ref({
  status: null as 'dismissed' | 'ordered' | 'resolved' | null,
})

// Pagination
const pagination = ref({
  sortBy: 'created_at',
  descending: true,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
})

// Options
const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const historyStatusOptions = [
  { label: 'Dismissed', value: 'dismissed' },
  { label: 'Ordered', value: 'ordered' },
  { label: 'Resolved', value: 'resolved' },
]

// Table columns
const alertColumns = [
  {
    name: 'component',
    label: 'Component',
    field: 'component_name',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'location',
    label: 'Location',
    field: 'location_name',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'severity',
    label: 'Severity',
    field: 'severity',
    align: 'center' as const,
    sortable: true,
  },
  {
    name: 'stock',
    label: 'Stock Level',
    field: 'current_quantity',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'actions',
    label: 'Actions',
    field: 'actions',
    align: 'center' as const,
  },
]

const historyColumns = [
  {
    name: 'component',
    label: 'Component',
    field: 'component_name',
    align: 'left' as const,
  },
  {
    name: 'location',
    label: 'Location',
    field: 'location_name',
    align: 'left' as const,
  },
  {
    name: 'status',
    label: 'Status',
    field: 'status',
    align: 'center' as const,
  },
  {
    name: 'resolved',
    label: 'Resolved At',
    field: 'resolved_at',
    align: 'left' as const,
  },
  {
    name: 'notes',
    label: 'Notes',
    field: 'notes',
    align: 'left' as const,
  },
]

const lowStockColumns = [
  {
    name: 'component',
    label: 'Component',
    field: 'component_name',
    align: 'left' as const,
  },
  {
    name: 'location',
    label: 'Location',
    field: 'location_name',
    align: 'left' as const,
  },
  {
    name: 'stock',
    label: 'Stock Level',
    field: 'current_quantity',
    align: 'left' as const,
  },
  {
    name: 'has_active_alert',
    label: 'Alert',
    field: 'has_active_alert',
    align: 'center' as const,
  },
  {
    name: 'actions',
    label: 'Actions',
    field: 'actions',
    align: 'center' as const,
  },
]

// Methods
const loadData = async () => {
  await Promise.all([loadAlerts(), loadStatistics()])

  if (activeTab.value === 'history') {
    await loadHistory()
  } else if (activeTab.value === 'low-stock') {
    await loadLowStockReport()
  }
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const response = await reorderAlertsApi.getAlerts({
      status: 'active',
      severity: filters.value.severity || undefined,
      min_shortage: filters.value.minShortage || undefined,
    })

    alerts.value = response.alerts
    pagination.value.rowsNumber = response.total
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load alerts',
      position: 'top-right',
    })
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await reorderAlertsApi.getHistory({
      status: historyFilters.value.status || undefined,
    })

    historyAlerts.value = response.alerts
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load history',
      position: 'top-right',
    })
  } finally {
    historyLoading.value = false
  }
}

const loadLowStockReport = async () => {
  lowStockLoading.value = true
  try {
    lowStockReport.value = await reorderAlertsApi.getLowStockReport()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load low stock report',
      position: 'top-right',
    })
  } finally {
    lowStockLoading.value = false
  }
}

const loadStatistics = async () => {
  try {
    statistics.value = await reorderAlertsApi.getStatistics()
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const onTableRequest = async (props: { pagination: typeof pagination.value }) => {
  pagination.value = props.pagination
  await loadAlerts()
}

const showDismissDialog = (alert: ReorderAlert) => {
  selectedAlert.value = alert
  dialogAction.value = 'dismiss'
  showActionDialog.value = true
}

const showMarkOrderedDialog = (alert: ReorderAlert) => {
  selectedAlert.value = alert
  dialogAction.value = 'ordered'
  showActionDialog.value = true
}

const showThresholdDialog = (alert: ReorderAlert) => {
  thresholdDialogData.value = {
    componentId: alert.component_id,
    locationId: alert.location_id,
    componentName: alert.component_name,
    currentQuantity: alert.current_quantity,
    currentThreshold: alert.reorder_threshold,
  }
  showThresholdUpdateDialog.value = true
}

const showThresholdDialogFromReport = (item: LowStockItem) => {
  thresholdDialogData.value = {
    componentId: item.component_id,
    locationId: item.location_id,
    componentName: item.component_name,
    currentQuantity: item.current_quantity,
    currentThreshold: item.reorder_threshold,
  }
  showThresholdUpdateDialog.value = true
}

const onActionCompleted = async () => {
  showActionDialog.value = false
  selectedAlert.value = null
  await loadData()

  $q.notify({
    type: 'positive',
    message: `Alert ${dialogAction.value === 'dismiss' ? 'dismissed' : 'marked as ordered'} successfully`,
    position: 'top-right',
  })
}

const onThresholdUpdated = async () => {
  showThresholdUpdateDialog.value = false
  await loadData()

  $q.notify({
    type: 'positive',
    message: 'Threshold updated successfully',
    position: 'top-right',
  })
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'negative'
    case 'high':
      return 'warning'
    case 'medium':
      return 'orange-5'
    case 'low':
      return 'info'
    default:
      return 'grey'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'warning'
    case 'dismissed':
      return 'grey'
    case 'ordered':
      return 'positive'
    case 'resolved':
      return 'positive'
    default:
      return 'grey'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>
