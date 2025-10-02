<template>
  <div class="report-view">
    <!-- Report Type Selection -->
    <div class="row q-mb-md">
      <div class="col-md-6 col-12">
        <q-select
          v-model="selectedReportType"
          :options="reportTypes"
          label="Report Type"
          outlined
          dense
          @update:model-value="loadReportData"
        />
      </div>
      <div class="col-md-3 col-12">
        <q-select
          v-if="selectedReportType?.timeRangeEnabled"
          v-model="timeRange"
          :options="timeRanges"
          label="Time Range"
          outlined
          dense
          @update:model-value="loadReportData"
        />
      </div>
      <div class="col-md-3 col-12 q-pl-md">
        <q-btn
          color="primary"
          icon="refresh"
          label="Refresh"
          :loading="loading"
          dense
          @click="loadReportData"
        />
        <q-btn
          color="secondary"
          icon="download"
          label="Export"
          :disable="!reportData"
          dense
          class="q-ml-sm"
          @click="exportReport"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center q-pa-xl">
      <q-spinner-dots size="3em" color="primary" />
      <div class="text-subtitle1 q-mt-md">Loading report data...</div>
    </div>

    <!-- Error State -->
    <q-banner v-else-if="error" dense class="bg-negative text-white q-mb-md">
      <template #avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
      <template #action>
        <q-btn flat label="Retry" @click="loadReportData" />
      </template>
    </q-banner>

    <!-- Report Content -->
    <div v-else-if="reportData">
      <!-- Dashboard Summary Report -->
      <div v-if="selectedReportType.value === 'dashboard'">
        <div class="text-h6 q-mb-md">System Dashboard</div>
        <div class="row q-col-gutter-md">
          <div v-for="(stat, key) in dashboardStats" :key="key" class="col-lg-3 col-md-6 col-12">
            <q-card class="stat-card">
              <q-card-section>
                <div class="text-h6" :class="stat.color">{{ stat.icon }}</div>
                <div class="text-h4 q-mt-sm">{{ stat.value }}</div>
                <div class="text-caption text-grey-6">{{ stat.label }}</div>
                <div v-if="stat.sublabel" class="text-body2 q-mt-xs">{{ stat.sublabel }}</div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </div>

      <!-- Inventory Breakdown Report -->
      <div v-else-if="selectedReportType.value === 'inventory'">
        <div class="text-h6 q-mb-md">Inventory Breakdown</div>

        <!-- By Category -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">By Category</div>
            <q-table
              :rows="reportData.by_category || []"
              :columns="categoryColumns"
              row-key="category"
              flat
              dense
            />
          </q-card-section>
        </q-card>

        <!-- By Location -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">By Storage Location</div>
            <q-table
              :rows="reportData.by_location || []"
              :columns="locationColumns"
              row-key="location"
              flat
              dense
            />
          </q-card-section>
        </q-card>

        <!-- By Type -->
        <q-card v-if="reportData.by_type">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">By Component Type</div>
            <q-table
              :rows="reportData.by_type"
              :columns="typeColumns"
              row-key="type"
              flat
              dense
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- Usage Analytics Report -->
      <div v-else-if="selectedReportType.value === 'usage'">
        <div class="text-h6 q-mb-md">Usage Analytics ({{ timeRange.label }})</div>

        <!-- Most Used Components -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Most Used Components</div>
            <q-table
              :rows="reportData.most_used_components || []"
              :columns="usageColumns"
              row-key="component_id"
              flat
              dense
            />
          </q-card-section>
        </q-card>

        <!-- Transaction Summary -->
        <q-card v-if="reportData.transaction_summary">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Transaction Summary</div>
            <div class="row q-col-gutter-md">
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.transaction_summary.total_transactions }}</div>
                <div class="text-caption">Total Transactions</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.transaction_summary.components_moved }}</div>
                <div class="text-caption">Components Moved</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.transaction_summary.most_active_day }}</div>
                <div class="text-caption">Most Active Day</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.transaction_summary.avg_per_day }}</div>
                <div class="text-caption">Avg Transactions/Day</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Project Analytics Report -->
      <div v-else-if="selectedReportType.value === 'projects'">
        <div class="text-h6 q-mb-md">Project Analytics</div>

        <!-- Project Status Distribution -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Project Status Distribution</div>
            <q-table
              :rows="reportData.project_status_distribution || []"
              :columns="projectStatusColumns"
              row-key="status"
              flat
              dense
            />
          </q-card-section>
        </q-card>

        <!-- Component Allocation -->
        <q-card v-if="reportData.component_allocation">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Component Allocation Summary</div>
            <div class="row q-col-gutter-md">
              <div class="col-md-4 col-12">
                <div class="text-h5">{{ reportData.component_allocation.total_allocated }}</div>
                <div class="text-caption">Total Components Allocated</div>
              </div>
              <div class="col-md-4 col-12">
                <div class="text-h5">${{ formatCurrency(reportData.component_allocation.total_value) }}</div>
                <div class="text-caption">Total Allocation Value</div>
              </div>
              <div class="col-md-4 col-12">
                <div class="text-h5">{{ reportData.component_allocation.active_projects }}</div>
                <div class="text-caption">Active Projects</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Financial Summary Report -->
      <div v-else-if="selectedReportType.value === 'financial'">
        <div class="text-h6 q-mb-md">Financial Summary</div>

        <!-- Top Value Components -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Top Value Components</div>
            <q-table
              :rows="reportData.top_value_components || []"
              :columns="valueColumns"
              row-key="component_id"
              flat
              dense
            />
          </q-card-section>
        </q-card>

        <!-- Financial Summary -->
        <q-card v-if="reportData.summary">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Inventory Valuation</div>
            <div class="row q-col-gutter-md">
              <div class="col-md-3 col-6">
                <div class="text-h5">${{ formatCurrency(reportData.summary.total_inventory_value) }}</div>
                <div class="text-caption">Total Inventory Value</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">${{ formatCurrency(reportData.summary.average_component_value) }}</div>
                <div class="text-caption">Avg Component Value</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.summary.total_components }}</div>
                <div class="text-caption">Total Components</div>
              </div>
              <div class="col-md-3 col-6">
                <div class="text-h5">{{ reportData.summary.unique_components }}</div>
                <div class="text-caption">Unique Components</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- System Health Report -->
      <div v-else-if="selectedReportType.value === 'system'">
        <div class="text-h6 q-mb-md">System Health</div>

        <!-- Data Quality Metrics -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Data Quality</div>
            <div class="row q-col-gutter-md">
              <div v-for="(metric, key) in reportData.data_quality" :key="key" class="col-md-4 col-12">
                <div class="text-center">
                  <q-circular-progress
                    :value="metric"
                    size="60px"
                    :thickness="0.15"
                    color="primary"
                    track-color="grey-3"
                    class="q-ma-md"
                  >
                    {{ Math.round(metric) }}%
                  </q-circular-progress>
                  <div class="text-caption">{{ formatLabel(key) }}</div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Database Statistics -->
        <q-card v-if="reportData.database_statistics">
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Database Statistics</div>
            <q-table
              :rows="Object.entries(reportData.database_statistics).map(([key, value]) => ({ metric: formatLabel(key), value }))"
              :columns="systemColumns"
              row-key="metric"
              flat
              dense
            />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center q-pa-xl">
      <q-icon name="assessment" size="4em" color="grey-5" />
      <div class="text-h6 q-mt-md text-grey-6">Select a Report Type</div>
      <div class="text-body2 text-grey-5">Choose a report type from the dropdown to view analytics</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

interface ReportType {
  label: string
  value: string
  timeRangeEnabled?: boolean
}

// Report data structure interfaces
interface ComponentStatistics {
  total_components: number
  total_value: number
  low_stock_count: number
  categories_count: number
  unique_parts: number
}

interface ProjectStatistics {
  total_projects: number
  active_projects: number
  completed_projects: number
  total_allocated_value: number
}

interface ActivityStatistics {
  recent_transactions: number
  components_moved: number
  most_active_period: string
}

interface TransactionSummary {
  total_transactions: number
  components_moved: number
  most_active_day: string
  avg_per_day: number
}

interface ComponentAllocation {
  total_allocated: number
  total_value: number
  active_projects: number
}

interface Summary {
  total_inventory_value: number
  average_component_value: number
  total_components: number
  unique_components: number
}

interface CategoryData {
  category: string
  total_value: number
  component_count: number
}

interface LocationData {
  location: string
  component_count: number
  total_value: number
}

interface ComponentData {
  name: string
  part_number: string
  usage_count: number
  total_value: number
}

interface DashboardStats {
  [key: string]: {
    icon: string
    color: string
    value: string
    label: string
  }
}

interface ReportData {
  // Dashboard specific data
  component_statistics?: ComponentStatistics
  project_statistics?: ProjectStatistics
  activity_statistics?: ActivityStatistics

  // Inventory specific data
  by_category?: CategoryData[]
  by_location?: LocationData[]
  by_type?: Array<{ type: string; count: number; value: number }>
  most_used_components?: ComponentData[]
  top_value_components?: ComponentData[]
  summary?: Summary

  // Activity specific data
  transaction_summary?: TransactionSummary

  // Project specific data
  project_status_distribution?: Array<{ status: string; count: number; percentage: number }>
  component_allocation?: ComponentAllocation

  // System specific data
  data_quality?: Record<string, number>
  database_statistics?: Record<string, string | number | boolean>
}

const loading = ref(false)
const error = ref<string | null>(null)
const reportData = ref<ReportData | null>(null)

const selectedReportType = ref<ReportType>({
  label: 'Dashboard Summary',
  value: 'dashboard'
})

const timeRange = ref({
  label: 'Last 30 Days',
  value: 30
})

const reportTypes: ReportType[] = [
  { label: 'Dashboard Summary', value: 'dashboard' },
  { label: 'Inventory Breakdown', value: 'inventory' },
  { label: 'Usage Analytics', value: 'usage', timeRangeEnabled: true },
  { label: 'Project Analytics', value: 'projects' },
  { label: 'Financial Summary', value: 'financial', timeRangeEnabled: true },
  { label: 'System Health', value: 'system' }
]

const timeRanges = [
  { label: 'Last 7 Days', value: 7 },
  { label: 'Last 30 Days', value: 30 },
  { label: 'Last 90 Days', value: 90 },
  { label: 'Last 6 Months', value: 180 },
  { label: 'Last Year', value: 365 }
]

// Table columns for different report types
const categoryColumns = [
  { name: 'category', label: 'Category', field: 'category', align: 'left' },
  { name: 'component_count', label: 'Components', field: 'component_count', align: 'right' },
  { name: 'total_quantity', label: 'Total Quantity', field: 'total_quantity', align: 'right' },
  { name: 'total_value', label: 'Total Value', field: 'total_value', align: 'right', format: (val: number) => `$${formatCurrency(val)}` }
]

const locationColumns = [
  { name: 'location', label: 'Location', field: 'location', align: 'left' },
  { name: 'component_count', label: 'Components', field: 'component_count', align: 'right' },
  { name: 'total_quantity', label: 'Total Quantity', field: 'total_quantity', align: 'right' }
]

const typeColumns = [
  { name: 'type', label: 'Component Type', field: 'type', align: 'left' },
  { name: 'count', label: 'Count', field: 'count', align: 'right' }
]

const usageColumns = [
  { name: 'part_number', label: 'Part Number', field: 'part_number', align: 'left' },
  { name: 'name', label: 'Name', field: 'name', align: 'left' },
  { name: 'transaction_count', label: 'Transactions', field: 'transaction_count', align: 'right' },
  { name: 'total_quantity_moved', label: 'Quantity Moved', field: 'total_quantity_moved', align: 'right' }
]

const projectStatusColumns = [
  { name: 'status', label: 'Status', field: 'status', align: 'left' },
  { name: 'count', label: 'Count', field: 'count', align: 'right' }
]

const valueColumns = [
  { name: 'part_number', label: 'Part Number', field: 'part_number', align: 'left' },
  { name: 'name', label: 'Name', field: 'name', align: 'left' },
  { name: 'inventory_value', label: 'Inventory Value', field: 'inventory_value', align: 'right', format: (val: number) => `$${formatCurrency(val)}` }
]

const systemColumns = [
  { name: 'metric', label: 'Metric', field: 'metric', align: 'left' },
  { name: 'value', label: 'Value', field: 'value', align: 'right' }
]

// Computed properties for dashboard stats
const dashboardStats = computed(() => {
  if (!reportData.value || selectedReportType.value.value !== 'dashboard') return {}

  const stats: DashboardStats = {}

  if (reportData.value.component_statistics) {
    const cs = reportData.value.component_statistics
    stats.components = {
      icon: '📦',
      color: 'text-primary',
      value: cs.total_components || 0,
      label: 'Total Components',
      sublabel: `${cs.available_components || 0} available`
    }
    stats.lowStock = {
      icon: '⚠️',
      color: 'text-warning',
      value: cs.low_stock_components || 0,
      label: 'Low Stock Items',
      sublabel: `${cs.out_of_stock_components || 0} out of stock`
    }
  }

  if (reportData.value.project_statistics) {
    const ps = reportData.value.project_statistics
    stats.projects = {
      icon: '🔧',
      color: 'text-positive',
      value: ps.active_projects || 0,
      label: 'Active Projects',
      sublabel: `of ${ps.total_projects || 0} total`
    }
  }

  if (reportData.value.activity_statistics) {
    const as = reportData.value.activity_statistics
    stats.value = {
      icon: '💰',
      color: 'text-purple',
      value: `$${formatCurrency(as.total_inventory_value || 0)}`,
      label: 'Inventory Value',
      sublabel: `${as.transactions_last_week || 0} transactions this week`
    }
  }

  return stats
})

async function loadReportData() {
  if (!selectedReportType.value) return

  loading.value = true
  error.value = null
  reportData.value = null

  try {
    let response
    const reportType = selectedReportType.value.value

    switch (reportType) {
      case 'dashboard':
        response = await api.get('/api/v1/reports/dashboard')
        break
      case 'inventory':
        response = await api.get('/api/v1/reports/inventory-breakdown')
        break
      case 'usage':
        response = await api.get(`/api/v1/reports/usage-analytics?days=${timeRange.value.value}`)
        break
      case 'projects':
        response = await api.get('/api/v1/reports/project-analytics')
        break
      case 'financial':
        response = await api.get(`/api/v1/reports/financial-summary?months=${Math.floor(timeRange.value.value / 30)}`)
        break
      case 'system':
        response = await api.get('/api/v1/reports/system-health')
        break
      default:
        throw new Error(`Unknown report type: ${reportType}`)
    }

    reportData.value = response.data
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Failed to load report data'
    const hasResponse = typeof err === 'object' && err !== null && 'response' in err
    const apiError = hasResponse ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : undefined
    error.value = apiError || errorMessage
    console.error('Failed to load report data:', err)
  } finally {
    loading.value = false
  }
}

async function exportReport() {
  if (!selectedReportType.value || !reportData.value) return

  try {
    const reportType = selectedReportType.value.value
    let endpoint = ''

    switch (reportType) {
      case 'inventory':
        endpoint = '/api/v1/reports/export/inventory'
        break
      case 'usage':
        endpoint = `/api/v1/reports/export/usage?days=${timeRange.value.value}`
        break
      case 'projects':
        endpoint = '/api/v1/reports/export/projects'
        break
      case 'financial':
        endpoint = `/api/v1/reports/export/financial?months=${Math.floor(timeRange.value.value / 30)}`
        break
      case 'system':
        endpoint = '/api/v1/reports/export/system-health'
        break
      default:
        endpoint = '/api/v1/reports/comprehensive'
    }

    const response = await api.get(endpoint, { responseType: 'blob' })

    // Create download link
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${reportType}-report-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err: unknown) {
    console.error('Failed to export report:', err)
  }
}

function formatCurrency(value: number): string {
  if (typeof value !== 'number') return '0.00'
  return value.toFixed(2)
}

function formatLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

onMounted(() => {
  loadReportData()
})
</script>

<style scoped>
.report-view {
  padding: 16px;
}

.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.text-h6 {
  margin-bottom: 16px;
}
</style>