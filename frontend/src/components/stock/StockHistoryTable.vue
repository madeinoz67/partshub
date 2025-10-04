<template>
  <div class="stock-history-table">
    <!-- Header with title and export buttons -->
    <div class="row justify-between items-center q-mb-md">
      <div class="text-h6">Stock History</div>
      <div v-if="isAdmin" class="q-gutter-sm">
        <q-btn
          label="CSV"
          icon="download"
          color="primary"
          dense
          outline
          :loading="exportingFormat === 'csv'"
          @click="handleExport('csv')"
        >
          <q-tooltip>Export as CSV</q-tooltip>
        </q-btn>
        <q-btn
          label="Excel"
          icon="download"
          color="primary"
          dense
          outline
          :loading="exportingFormat === 'xlsx'"
          @click="handleExport('xlsx')"
        >
          <q-tooltip>Export as Excel</q-tooltip>
        </q-btn>
        <q-btn
          label="JSON"
          icon="download"
          color="primary"
          dense
          outline
          :loading="exportingFormat === 'json'"
          @click="handleExport('json')"
        >
          <q-tooltip>Export as JSON</q-tooltip>
        </q-btn>
      </div>
    </div>

    <!-- Stock History Table -->
    <q-table
      :rows="historyEntries"
      :columns="columns"
      :loading="loading"
      :pagination="tablePagination"
      row-key="id"
      dense
      flat
      bordered
      @request="onTableRequest"
    >
      <!-- Custom column: Transaction Type with color badge -->
      <template #body-cell-transaction_type="cellProps">
        <q-td :props="cellProps">
          <q-badge :color="getTypeColor(cellProps.row.transaction_type)">
            {{ cellProps.row.transaction_type.toUpperCase() }}
          </q-badge>
        </q-td>
      </template>

      <!-- Custom column: Quantity Change with +/- indicator -->
      <template #body-cell-quantity_change="cellProps">
        <q-td :props="cellProps">
          <span :class="getQuantityClass(cellProps.row.quantity_change)">
            {{ formatQuantity(cellProps.row.quantity_change) }}
          </span>
        </q-td>
      </template>

      <!-- Custom column: From Location -->
      <template #body-cell-from_location="cellProps">
        <q-td :props="cellProps">
          <span v-if="cellProps.row.from_location_name" class="text-grey-8">
            {{ cellProps.row.from_location_name }}
          </span>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Custom column: To Location -->
      <template #body-cell-to_location="cellProps">
        <q-td :props="cellProps">
          <span v-if="cellProps.row.to_location_name" class="text-grey-8">
            {{ cellProps.row.to_location_name }}
          </span>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Custom column: Lot ID -->
      <template #body-cell-lot_id="cellProps">
        <q-td :props="cellProps">
          <span v-if="cellProps.row.lot_id" class="text-grey-8">
            {{ cellProps.row.lot_id }}
          </span>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Custom column: Price (per unit and total) -->
      <template #body-cell-price="cellProps">
        <q-td :props="cellProps">
          <div v-if="cellProps.row.price_per_unit || cellProps.row.total_price">
            <div v-if="cellProps.row.price_per_unit" class="text-caption">
              Unit: ${{ cellProps.row.price_per_unit.toFixed(4) }}
            </div>
            <div v-if="cellProps.row.total_price" class="text-caption text-weight-medium">
              Total: ${{ cellProps.row.total_price.toFixed(2) }}
            </div>
          </div>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Custom column: Comments/Reason -->
      <template #body-cell-comments="cellProps">
        <q-td :props="cellProps">
          <div v-if="cellProps.row.reason || cellProps.row.notes || cellProps.row.comments">
            <div v-if="cellProps.row.reason" class="text-caption text-weight-medium">
              {{ cellProps.row.reason }}
            </div>
            <div v-if="cellProps.row.notes || cellProps.row.comments" class="text-caption text-grey-7">
              {{ cellProps.row.notes || cellProps.row.comments }}
            </div>
          </div>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Custom column: User -->
      <template #body-cell-user_name="cellProps">
        <q-td :props="cellProps">
          <span v-if="cellProps.row.user_name" class="text-grey-8">
            {{ cellProps.row.user_name }}
          </span>
          <span v-else class="text-grey-5">System</span>
        </q-td>
      </template>

      <!-- Custom column: Date -->
      <template #body-cell-created_at="cellProps">
        <q-td :props="cellProps">
          <div class="text-caption">
            {{ formatDate(cellProps.row.created_at) }}
          </div>
          <div class="text-caption text-grey-6">
            {{ formatTime(cellProps.row.created_at) }}
          </div>
        </q-td>
      </template>

      <!-- Empty state -->
      <template #no-data>
        <div class="full-width row flex-center text-center q-py-lg">
          <div>
            <q-icon name="history" size="3rem" color="grey-4" />
            <div class="text-body1 text-grey-6 q-mt-md">No stock history found</div>
            <div class="text-caption text-grey-5">Stock transactions will appear here</div>
          </div>
        </div>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { stockOperationsApi } from '../../services/stockOperations'
import type { StockHistoryEntry } from '../../services/stockOperations'

// Props
interface Props {
  componentId: string
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: false
})

// Emits
const emit = defineEmits<{
  refreshed: []
}>()

// Store
const authStore = useAuthStore()

// Computed
const isAdmin = computed(() => authStore.user?.is_admin || false)

// State
const historyEntries = ref<StockHistoryEntry[]>([])
const loading = ref(false)
const exportingFormat = ref<'csv' | 'xlsx' | 'json' | null>(null)
const tablePagination = ref({
  sortBy: 'created_at',
  descending: true,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0
})

// Table columns configuration
const columns = [
  {
    name: 'created_at',
    label: 'Date',
    field: 'created_at',
    align: 'left' as const,
    sortable: true
  },
  {
    name: 'transaction_type',
    label: 'Type',
    field: 'transaction_type',
    align: 'center' as const,
    sortable: true
  },
  {
    name: 'quantity_change',
    label: 'Quantity',
    field: 'quantity_change',
    align: 'center' as const,
    sortable: true
  },
  {
    name: 'from_location',
    label: 'From Location',
    field: 'from_location_name',
    align: 'left' as const,
    sortable: true
  },
  {
    name: 'to_location',
    label: 'To Location',
    field: 'to_location_name',
    align: 'left' as const,
    sortable: true
  },
  {
    name: 'lot_id',
    label: 'Lot ID',
    field: 'lot_id',
    align: 'left' as const,
    sortable: true
  },
  {
    name: 'price',
    label: 'Price',
    field: 'price_per_unit',
    align: 'right' as const,
    sortable: true
  },
  {
    name: 'comments',
    label: 'Comments',
    field: 'reason',
    align: 'left' as const,
    sortable: false
  },
  {
    name: 'user_name',
    label: 'User',
    field: 'user_name',
    align: 'left' as const,
    sortable: true
  }
]

// Methods
const getTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    add: 'positive',
    remove: 'negative',
    move: 'info',
    adjust: 'warning'
  }
  return colorMap[type.toLowerCase()] || 'grey'
}

const getQuantityClass = (quantity: number): string => {
  if (quantity > 0) return 'text-positive text-weight-bold'
  if (quantity < 0) return 'text-negative text-weight-bold'
  return 'text-grey-8'
}

const formatQuantity = (quantity: number): string => {
  if (quantity > 0) return `+${quantity}`
  return quantity.toString()
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleTimeString()
}

const fetchHistory = async () => {
  if (!props.componentId) return

  loading.value = true
  try {
    const sortOrder = tablePagination.value.descending ? 'desc' : 'asc'
    const response = await stockOperationsApi.getStockHistory(
      props.componentId,
      tablePagination.value.page,
      tablePagination.value.rowsPerPage,
      tablePagination.value.sortBy || 'created_at',
      sortOrder
    )

    historyEntries.value = response.entries
    tablePagination.value.rowsNumber = response.pagination.total_entries
  } catch (error) {
    console.error('Failed to fetch stock history:', error)
    historyEntries.value = []
    tablePagination.value.rowsNumber = 0
  } finally {
    loading.value = false
    emit('refreshed')
  }
}

const onTableRequest = async (props: {
  pagination: {
    sortBy: string
    descending: boolean
    page: number
    rowsPerPage: number
  }
}) => {
  tablePagination.value = {
    ...tablePagination.value,
    ...props.pagination
  }
  await fetchHistory()
}

const handleExport = async (format: 'csv' | 'xlsx' | 'json') => {
  if (!props.componentId) return

  exportingFormat.value = format
  try {
    const sortOrder = tablePagination.value.descending ? 'desc' : 'asc'
    await stockOperationsApi.exportStockHistory(
      props.componentId,
      format,
      tablePagination.value.sortBy || 'created_at',
      sortOrder
    )
  } catch (error) {
    console.error('Failed to export stock history:', error)
  } finally {
    exportingFormat.value = null
  }
}

// Watchers
watch(() => props.autoRefresh, (newVal) => {
  if (newVal) {
    fetchHistory()
  }
})

watch(() => props.componentId, () => {
  if (props.componentId) {
    fetchHistory()
  }
})

// Lifecycle
onMounted(() => {
  if (props.componentId) {
    fetchHistory()
  }
})
</script>

<style scoped>
.stock-history-table {
  width: 100%;
}

.stock-history-table :deep(.q-table) {
  font-size: 0.875rem;
}

.stock-history-table :deep(.q-td) {
  padding: 8px 12px;
}

.stock-history-table :deep(.q-th) {
  padding: 8px 12px;
  font-weight: 600;
}
</style>
