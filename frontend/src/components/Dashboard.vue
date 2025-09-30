<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Dashboard</div>
        <div class="text-subtitle1 text-grey-6">
          System Overview and Key Metrics
        </div>
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          icon="refresh"
          label="Refresh"
          :loading="loading"
          @click="loadDashboardData"
        />
      </div>
    </div>

    <!-- Key Statistics Cards -->
    <div class="row q-col-gutter-md q-mb-lg">
      <!-- Total Components -->
      <div class="col-lg-3 col-md-4 col-sm-6 col-12">
        <q-card class="stat-card text-center q-pa-md">
          <q-icon name="inventory" size="48px" color="primary" class="q-mb-sm" />
          <div class="text-h3 text-primary">{{ summary?.component_statistics?.total_components || 0 }}</div>
          <div class="text-subtitle2">Total Components</div>
          <div class="text-caption text-grey-6">
            {{ summary?.component_statistics?.available_components || 0 }} available
          </div>
        </q-card>
      </div>

      <!-- Inventory Value -->
      <div class="col-lg-3 col-md-4 col-sm-6 col-12">
        <q-card class="stat-card text-center q-pa-md">
          <q-icon name="attach_money" size="48px" color="green" class="q-mb-sm" />
          <div class="text-h3 text-green">{{ formatCurrency(summary?.activity_statistics?.total_inventory_value || 0) }}</div>
          <div class="text-subtitle2">Inventory Value</div>
          <div class="text-caption text-grey-6">Estimated total</div>
        </q-card>
      </div>

      <!-- Low Stock Alerts -->
      <div class="col-lg-3 col-md-4 col-sm-6 col-12">
        <q-card class="stat-card text-center q-pa-md">
          <q-icon name="warning" size="48px" color="orange" class="q-mb-sm" />
          <div class="text-h3 text-orange">{{ summary?.component_statistics?.low_stock_components || 0 }}</div>
          <div class="text-subtitle2">Low Stock</div>
          <div class="text-caption text-grey-6">Need attention</div>
        </q-card>
      </div>

      <!-- Active Projects -->
      <div class="col-lg-3 col-md-4 col-sm-6 col-12">
        <q-card class="stat-card text-center q-pa-md">
          <q-icon name="folder" size="48px" color="purple" class="q-mb-sm" />
          <div class="text-h3 text-purple">{{ summary?.project_statistics?.active_projects || 0 }}</div>
          <div class="text-subtitle2">Active Projects</div>
          <div class="text-caption text-grey-6">
            {{ summary?.project_statistics?.total_projects || 0 }} total
          </div>
        </q-card>
      </div>
    </div>

    <!-- Charts and Analytics Row -->
    <div class="row q-col-gutter-md q-mb-lg">
      <!-- Inventory Breakdown Chart -->
      <div class="col-md-6 col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Inventory by Category</div>
          </q-card-section>
          <q-card-section>
            <div v-if="breakdown?.by_category?.length" class="category-breakdown">
              <div
                v-for="category in breakdown.by_category.slice(0, 8)"
                :key="category.category"
                class="category-item q-mb-sm"
              >
                <div class="row items-center">
                  <div class="col">
                    <div class="text-weight-medium">{{ category.category || 'Uncategorized' }}</div>
                    <div class="text-caption text-grey-6">
                      {{ category.component_count }} components
                    </div>
                  </div>
                  <div class="col-auto">
                    <q-chip color="blue" text-color="white" size="sm">
                      {{ category.total_quantity }}
                    </q-chip>
                  </div>
                </div>
                <q-linear-progress
                  :value="category.component_count / (summary?.component_statistics?.total_components || 1)"
                  color="primary"
                  size="4px"
                  class="q-mt-xs"
                />
              </div>
            </div>
            <div v-else class="text-center text-grey-6 q-py-lg">
              No category data available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Activity -->
      <div class="col-md-6 col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Activity</div>
          </q-card-section>
          <q-card-section>
            <div v-if="recentActivity?.length" class="activity-list">
              <div
                v-for="(activity, index) in recentActivity.slice(0, 10)"
                :key="index"
                class="activity-item q-mb-sm"
              >
                <div class="row items-center">
                  <div class="col-auto q-mr-sm">
                    <q-icon
                      :name="getActivityIcon(activity.transaction_type)"
                      :color="getActivityColor(activity.transaction_type)"
                      size="20px"
                    />
                  </div>
                  <div class="col">
                    <div class="text-weight-medium">
                      {{ activity.component?.part_number || 'Unknown Component' }}
                    </div>
                    <div class="text-caption text-grey-6">
                      {{ formatActivityDescription(activity) }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <div class="text-caption text-grey-6">
                      {{ formatRelativeTime(activity.created_at) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-grey-6 q-py-lg">
              No recent activity
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Quick Actions Row -->
    <div class="row q-col-gutter-md q-mb-lg">
      <!-- Quick Actions -->
      <div class="col-md-6 col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Quick Actions</div>
          </q-card-section>
          <q-card-section>
            <div class="row q-col-gutter-sm">
              <div class="col-6">
                <q-btn
                  color="primary"
                  icon="add"
                  label="Add Component"
                  size="md"
                  class="full-width"
                  @click="$router.push('/inventory?action=add')"
                />
              </div>
              <div class="col-6">
                <q-btn
                  color="secondary"
                  icon="create_new_folder"
                  label="New Project"
                  size="md"
                  class="full-width"
                  @click="$router.push('/projects?action=create')"
                />
              </div>
              <div class="col-6">
                <q-btn
                  color="green"
                  icon="place"
                  label="Add Location"
                  size="md"
                  class="full-width"
                  @click="$router.push('/storage?action=add')"
                />
              </div>
              <div class="col-6">
                <q-btn
                  color="orange"
                  icon="search"
                  label="Search Parts"
                  size="md"
                  class="full-width"
                  @click="$router.push('/inventory')"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- System Health -->
      <div class="col-md-6 col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">System Health</div>
          </q-card-section>
          <q-card-section>
            <div class="health-metrics">
              <!-- Database Status -->
              <div class="health-item q-mb-sm">
                <div class="row items-center">
                  <div class="col">
                    <div class="text-weight-medium">Database</div>
                    <div class="text-caption text-grey-6">{{ health?.database_statistics?.total_components || 0 }} components stored</div>
                  </div>
                  <div class="col-auto">
                    <q-chip
                      :color="health?.system_metrics?.database_health === 'good' ? 'green' : 'orange'"
                      text-color="white"
                      size="sm"
                    >
                      {{ health?.system_metrics?.database_health || 'Unknown' }}
                    </q-chip>
                  </div>
                </div>
              </div>

              <!-- Data Quality -->
              <div class="health-item q-mb-sm">
                <div class="row items-center">
                  <div class="col">
                    <div class="text-weight-medium">Data Quality</div>
                    <div class="text-caption text-grey-6">{{ Math.round(health?.data_quality?.category_coverage || 0) }}% categorized</div>
                  </div>
                  <div class="col-auto">
                    <q-circular-progress
                      :value="health?.data_quality?.category_coverage || 0"
                      size="40px"
                      :thickness="0.15"
                      color="primary"
                      track-color="grey-3"
                      show-value
                      class="text-primary"
                    />
                  </div>
                </div>
              </div>

              <!-- Last Activity -->
              <div class="health-item">
                <div class="row items-center">
                  <div class="col">
                    <div class="text-weight-medium">Recent Activity</div>
                    <div class="text-caption text-grey-6">{{ summary?.activity_statistics?.transactions_last_week || 0 }} transactions this week</div>
                  </div>
                  <div class="col-auto">
                    <q-icon
                      :name="summary?.activity_statistics?.transactions_last_week > 0 ? 'trending_up' : 'trending_flat'"
                      :color="summary?.activity_statistics?.transactions_last_week > 0 ? 'green' : 'grey'"
                      size="24px"
                    />
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Alerts and Notifications -->
    <div v-if="alerts?.low_stock?.length || alerts?.out_of_stock?.length" class="row q-col-gutter-md">
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6 text-orange">
              <q-icon name="warning" class="q-mr-sm" />
              Stock Alerts
            </div>
          </q-card-section>
          <q-card-section>
            <div class="row q-col-gutter-md">
              <!-- Low Stock -->
              <div v-if="alerts?.low_stock?.length" class="col-md-6 col-12">
                <div class="text-subtitle2 text-orange q-mb-sm">Low Stock Components</div>
                <div class="alert-list">
                  <div
                    v-for="component in alerts.low_stock.slice(0, 5)"
                    :key="component.id"
                    class="alert-item q-mb-xs"
                  >
                    <div class="row items-center">
                      <div class="col">
                        <div class="text-weight-medium">{{ component.part_number }}</div>
                        <div class="text-caption text-grey-6">{{ component.name }}</div>
                      </div>
                      <div class="col-auto">
                        <q-chip color="orange" text-color="white" size="sm">
                          {{ component.quantity_on_hand }}/{{ component.minimum_stock }}
                        </q-chip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Out of Stock -->
              <div v-if="alerts?.out_of_stock?.length" class="col-md-6 col-12">
                <div class="text-subtitle2 text-negative q-mb-sm">Out of Stock Components</div>
                <div class="alert-list">
                  <div
                    v-for="component in alerts.out_of_stock.slice(0, 5)"
                    :key="component.id"
                    class="alert-item q-mb-xs"
                  >
                    <div class="row items-center">
                      <div class="col">
                        <div class="text-weight-medium">{{ component.part_number }}</div>
                        <div class="text-caption text-grey-6">{{ component.name }}</div>
                      </div>
                      <div class="col-auto">
                        <q-chip color="negative" text-color="white" size="sm">
                          0
                        </q-chip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// Router import removed - not currently used
import { useQuasar } from 'quasar'
import { api } from '../services/api'

// Router available for future navigation needs
const $q = useQuasar()

// Reactive data
const loading = ref(false)
const summary = ref(null)
const breakdown = ref(null)
const recentActivity = ref([])
const alerts = ref(null)
const health = ref(null)

// Methods
const loadDashboardData = async () => {
  loading.value = true
  try {
    // Load dashboard summary
    const summaryResponse = await api.get('/reports/dashboard-summary')
    summary.value = summaryResponse.data

    // Load inventory breakdown
    const breakdownResponse = await api.get('/reports/inventory-breakdown')
    breakdown.value = breakdownResponse.data

    // Load recent activity (last 20 transactions)
    const activityResponse = await api.get('/stock/movements', {
      params: { limit: 20 }
    })
    recentActivity.value = activityResponse.data

    // Load stock alerts
    const alertsResponse = await api.get('/stock/alerts')
    alerts.value = alertsResponse.data

    // Load system health
    const healthResponse = await api.get('/reports/system-health')
    health.value = healthResponse.data

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load dashboard data',
      caption: error.response?.data?.detail || error.message
    })
  }
  loading.value = false
}

// Utility functions
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const formatRelativeTime = (dateString) => {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) {
    return `${diffDays}d ago`
  } else if (diffHours > 0) {
    return `${diffHours}h ago`
  } else {
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    return `${Math.max(1, diffMinutes)}m ago`
  }
}

const getActivityIcon = (transactionType) => {
  const icons = {
    'add': 'add_circle',
    'remove': 'remove_circle',
    'adjust': 'tune',
    'transfer': 'swap_horiz'
  }
  return icons[transactionType] || 'circle'
}

const getActivityColor = (transactionType) => {
  const colors = {
    'add': 'green',
    'remove': 'red',
    'adjust': 'blue',
    'transfer': 'purple'
  }
  return colors[transactionType] || 'grey'
}

const formatActivityDescription = (activity) => {
  const type = activity.transaction_type
  const quantity = Math.abs(activity.quantity_change || 0)
  const reason = activity.reason || 'Unknown reason'

  if (type === 'add') {
    return `Added ${quantity} • ${reason}`
  } else if (type === 'remove') {
    return `Removed ${quantity} • ${reason}`
  } else if (type === 'adjust') {
    return `Adjusted to ${activity.new_quantity || 0} • ${reason}`
  } else {
    return `${type} ${quantity} • ${reason}`
  }
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.stat-card {
  height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.category-breakdown,
.activity-list,
.alert-list,
.health-metrics {
  max-height: 300px;
  overflow-y: auto;
}

.category-item,
.activity-item,
.alert-item,
.health-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.category-item:last-child,
.activity-item:last-child,
.alert-item:last-child,
.health-item:last-child {
  border-bottom: none;
}
</style>