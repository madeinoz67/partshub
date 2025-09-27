<template>
  <div class="component-detail">
    <!-- Header -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row items-center justify-between">
          <div class="col">
            <div class="text-h5">{{ component?.name || 'Component Details' }}</div>
            <div v-if="component?.part_number" class="text-caption text-grey q-mt-xs">
              Part Number: {{ component.part_number }}
            </div>
          </div>
          <div class="col-auto">
            <q-btn
              flat
              icon="arrow_back"
              label="Back to List"
              @click="$router.push('/components')"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Loading state -->
    <q-inner-loading :showing="loading">
      <q-spinner color="primary" size="50px" />
    </q-inner-loading>

    <!-- Error message -->
    <q-banner v-if="error" class="text-white bg-negative q-mb-md">
      <template v-slot:avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
      <template v-slot:action>
        <q-btn flat color="white" label="Dismiss" @click="clearError" />
      </template>
    </q-banner>

    <!-- Main layout with sidebar -->
    <div v-if="component" class="component-layout">
      <!-- Sidebar -->
      <div class="component-sidebar">
        <q-card class="sidebar-card">
          <q-card-section class="q-pb-none">
            <div class="text-h6 q-mb-md">Actions</div>
          </q-card-section>

          <!-- Quick Actions -->
          <q-list>
            <template v-if="canPerformCrud()">
              <q-item clickable @click="$emit('edit-component', component)">
                <q-item-section avatar>
                  <q-icon name="edit" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Edit Component</q-item-label>
                  <q-item-label caption>Modify details</q-item-label>
                </q-item-section>
              </q-item>

              <q-item clickable @click="$emit('update-stock', component)">
                <q-item-section avatar>
                  <q-icon name="inventory" color="secondary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Update Stock</q-item-label>
                  <q-item-label caption>Adjust quantities</q-item-label>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item clickable @click="duplicateComponent">
                <q-item-section avatar>
                  <q-icon name="content_copy" color="accent" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Duplicate</q-item-label>
                  <q-item-label caption>Create copy</q-item-label>
                </q-item-section>
              </q-item>

              <q-item clickable @click="moveComponent">
                <q-item-section avatar>
                  <q-icon name="drive_file_move" color="info" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Move Location</q-item-label>
                  <q-item-label caption>Change storage</q-item-label>
                </q-item-section>
              </q-item>

              <q-separator />
            </template>

            <q-item clickable @click="printLabel">
              <q-item-section avatar>
                <q-icon name="local_printshop" color="orange" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Print Label</q-item-label>
                <q-item-label caption>Generate barcode</q-item-label>
              </q-item-section>
            </q-item>

            <q-item clickable @click="exportData">
              <q-item-section avatar>
                <q-icon name="download" color="teal" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Export Data</q-item-label>
                <q-item-label caption>CSV/JSON export</q-item-label>
              </q-item-section>
            </q-item>

            <template v-if="canPerformCrud()">
              <q-separator />

              <q-item clickable @click="deleteComponent" class="text-negative">
                <q-item-section avatar>
                  <q-icon name="delete" color="negative" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Delete</q-item-label>
                  <q-item-label caption>Remove component</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-list>

          <!-- Stock Status Card -->
          <q-card-section class="q-pt-lg">
            <div class="text-subtitle2 q-mb-md">Stock Status</div>
            <div class="text-center">
              <q-circular-progress
                :value="getStockPercentage(component)"
                size="80px"
                :color="getStockStatusColor(component)"
                :thickness="0.15"
                class="q-mb-md"
              >
                <div class="text-h6">{{ component.quantity_on_hand }}</div>
                <div class="text-caption">in stock</div>
              </q-circular-progress>
              <div class="text-caption q-mt-sm">
                Min: {{ component.minimum_stock }}
              </div>
              <q-badge
                :color="getStockStatusColor(component)"
                :label="getStockStatusText(component)"
                class="q-mt-xs"
              />
            </div>
          </q-card-section>

          <!-- Quick Stats -->
          <q-card-section class="q-pt-none">
            <div class="text-subtitle2 q-mb-sm">Quick Stats</div>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="text-h6">{{ component.attachments?.length || 0 }}</div>
                <div class="text-caption">Files</div>
              </div>
              <div class="stat-item">
                <div class="text-h6">{{ stockHistory?.length || 0 }}</div>
                <div class="text-caption">Transactions</div>
              </div>
              <div class="stat-item" v-if="component.total_purchase_value">
                <div class="text-h6">${{ component.total_purchase_value.toFixed(0) }}</div>
                <div class="text-caption">Value</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Main Content -->
      <div class="component-main-content">
        <div class="main-content-flex" data-testid="component-detail-main-row">
      <!-- Basic Information -->
      <div class="info-card-container" data-testid="basic-info-card">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md" data-testid="basic-info-title">Basic Information</div>

            <div class="q-gutter-sm">
              <div class="row">
                <div class="col-4 text-weight-medium">Name:</div>
                <div class="col-8">{{ component.name }}</div>
              </div>

              <div class="row" v-if="component.part_number">
                <div class="col-4 text-weight-medium">Part Number:</div>
                <div class="col-8">{{ component.part_number }}</div>
              </div>

              <div class="row" v-if="component.manufacturer">
                <div class="col-4 text-weight-medium">Manufacturer:</div>
                <div class="col-8">{{ component.manufacturer }}</div>
              </div>

              <div class="row" v-if="component.component_type">
                <div class="col-4 text-weight-medium">Type:</div>
                <div class="col-8">{{ component.component_type }}</div>
              </div>

              <div class="row" v-if="component.value">
                <div class="col-4 text-weight-medium">Value:</div>
                <div class="col-8">{{ component.value }}</div>
              </div>

              <div class="row" v-if="component.package">
                <div class="col-4 text-weight-medium">Package:</div>
                <div class="col-8">{{ component.package }}</div>
              </div>

              <div class="row">
                <div class="col-4 text-weight-medium">Category:</div>
                <div class="col-8">
                  <q-chip
                    v-if="component.category"
                    outline
                    color="primary"
                    :label="component.category.name"
                  />
                  <span v-else class="text-grey">Uncategorized</span>
                </div>
              </div>

              <div class="row">
                <div class="col-4 text-weight-medium">Locations:</div>
                <div class="col-8">
                  <div v-if="component.storage_locations && component.storage_locations.length > 0">
                    <div class="storage-locations-compact">
                      <div
                        v-for="storageLocation in component.storage_locations"
                        :key="storageLocation.location.id"
                        class="location-row"
                      >
                        <div class="location-info">
                          <router-link
                            :to="`/storage-locations/${storageLocation.location.id}`"
                            class="location-name location-link"
                            :title="storageLocation.location.location_hierarchy"
                          >
                            {{ storageLocation.location.name }}
                          </router-link>
                          <span class="quantity-info">
                            <strong>{{ storageLocation.quantity_on_hand }}</strong>
                            <span v-if="storageLocation.minimum_stock > 0" class="text-grey">
                              /{{ storageLocation.minimum_stock }}
                            </span>
                            <span v-if="storageLocation.quantity_ordered > 0" class="text-info">
                              (+{{ storageLocation.quantity_ordered }})
                            </span>
                          </span>
                        </div>
                        <div v-if="storageLocation.location_notes" class="location-notes">
                          {{ storageLocation.location_notes }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <span v-else class="text-grey">No location assigned</span>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Stock Information -->
      <div class="info-card-container" data-testid="stock-info-card">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md" data-testid="stock-info-title">Stock Information</div>

            <div class="q-gutter-sm">
              <div class="row items-center">
                <div class="col-6 text-weight-medium">Current Stock:</div>
                <div class="col-6">
                  <q-chip
                    :color="getStockStatusColor(component)"
                    text-color="white"
                    :label="component.quantity_on_hand"
                    size="md"
                  />
                </div>
              </div>

              <div class="row">
                <div class="col-6 text-weight-medium">Minimum Stock:</div>
                <div class="col-6">{{ component.minimum_stock }}</div>
              </div>

              <div class="row" v-if="component.quantity_ordered > 0">
                <div class="col-6 text-weight-medium">On Order:</div>
                <div class="col-6">{{ component.quantity_ordered }}</div>
              </div>

              <div class="row" v-if="component.average_purchase_price">
                <div class="col-6 text-weight-medium">Avg. Price:</div>
                <div class="col-6">${{ component.average_purchase_price.toFixed(2) }}</div>
              </div>

              <div class="row" v-if="component.total_purchase_value">
                <div class="col-6 text-weight-medium">Total Value:</div>
                <div class="col-6">${{ component.total_purchase_value.toFixed(2) }}</div>
              </div>

              <div class="row">
                <div class="col-6 text-weight-medium">Status:</div>
                <div class="col-6">
                  <q-badge
                    :color="getStockStatusColor(component)"
                    :label="getStockStatusText(component)"
                  />
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Full-width sections below -->
    <div v-if="component" class="full-width-sections">
      <!-- Specifications -->
      <div class="col-12 q-mt-md" v-if="component.specifications && Object.keys(component.specifications).length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Specifications</div>
            <div class="row q-gutter-sm">
              <div
                v-for="(value, key) in component.specifications"
                :key="key"
                class="col-md-3 col-sm-6 col-xs-12"
              >
                <q-card flat bordered>
                  <q-card-section class="q-pa-sm">
                    <div class="text-caption text-grey text-uppercase">{{ key.replace('_', ' ') }}</div>
                    <div class="text-body2">{{ formatSpecValue(value) }}</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Custom Fields -->
      <div class="col-12 q-mt-md" v-if="component.custom_fields && Object.keys(component.custom_fields).length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Custom Fields</div>
            <div class="row q-gutter-sm">
              <div
                v-for="(value, key) in component.custom_fields"
                :key="key"
                class="col-md-3 col-sm-6 col-xs-12"
              >
                <q-card flat bordered>
                  <q-card-section class="q-pa-sm">
                    <div class="text-caption text-grey text-uppercase">{{ key.replace('_', ' ') }}</div>
                    <div class="text-body2">{{ formatSpecValue(value) }}</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Tags -->
      <div class="col-12 q-mt-md" v-if="component.tags && component.tags.length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Tags</div>
            <div class="q-gutter-xs">
              <q-chip
                v-for="tag in component.tags"
                :key="tag.id"
                color="secondary"
                text-color="white"
                :label="tag.name"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Notes -->
      <div class="col-12 q-mt-md" v-if="component.notes">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Notes</div>
            <div class="text-body1" style="white-space: pre-wrap;">{{ component.notes }}</div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Stock History -->
      <div class="col-12 q-mt-md">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Stock History</div>

            <q-table
              :rows="stockHistory"
              :columns="stockHistoryColumns"
              row-key="id"
              :loading="stockHistoryLoading"
              dense
              flat
              :pagination="{ rowsPerPage: 10 }"
            >
              <template v-slot:body-cell-transaction_type="props">
                <q-td :props="props">
                  <q-chip
                    :color="getTransactionColor(props.row.transaction_type)"
                    text-color="white"
                    :label="props.row.transaction_type.toUpperCase()"
                    size="sm"
                  />
                </q-td>
              </template>

              <template v-slot:body-cell-quantity_change="props">
                <q-td :props="props">
                  <span :class="props.row.quantity_change > 0 ? 'text-positive' : 'text-negative'">
                    {{ props.row.quantity_change > 0 ? '+' : '' }}{{ props.row.quantity_change }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-created_at="props">
                <q-td :props="props">
                  {{ formatDate(props.row.created_at) }}
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>

      <!-- Attachments -->
      <div class="col-12 q-mt-md">
        <q-card>
          <q-card-section class="q-pb-none">
            <AttachmentGallery
              :component-id="component.id"
              :show-actions="canPerformCrud()"
              @attachment-updated="onAttachmentUpdated"
              @attachment-deleted="onAttachmentDeleted"
            />
          </q-card-section>
        </q-card>
      </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useComponentsStore } from '../stores/components'
import { useAuth } from '../composables/useAuth'
import type { Component } from '../services/api'
import AttachmentGallery from './AttachmentGallery.vue'

interface Props {
  componentId: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'edit-component': [component: Component]
  'update-stock': [component: Component]
}>()

const componentsStore = useComponentsStore()
const { canPerformCrud } = useAuth()
const {
  currentComponent: component,
  stockHistory,
  loading,
  error
} = storeToRefs(componentsStore)

const stockHistoryLoading = ref(false)

const stockHistoryColumns = [
  {
    name: 'transaction_type',
    label: 'Type',
    align: 'left' as const,
    field: 'transaction_type'
  },
  {
    name: 'quantity_change',
    label: 'Change',
    align: 'center' as const,
    field: 'quantity_change'
  },
  {
    name: 'previous_quantity',
    label: 'Previous',
    align: 'center' as const,
    field: 'previous_quantity'
  },
  {
    name: 'new_quantity',
    label: 'New',
    align: 'center' as const,
    field: 'new_quantity'
  },
  {
    name: 'reason',
    label: 'Reason',
    align: 'left' as const,
    field: 'reason'
  },
  {
    name: 'created_at',
    label: 'Date',
    align: 'left' as const,
    field: 'created_at'
  }
]

const getStockStatusColor = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

const getStockStatusText = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'Out of Stock'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'Low Stock'
  return 'Available'
}

const getTransactionColor = (type: string) => {
  switch (type) {
    case 'add': return 'positive'
    case 'remove': return 'negative'
    case 'move': return 'info'
    case 'adjust': return 'warning'
    default: return 'grey'
  }
}

const formatSpecValue = (value: any) => {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return value?.toString() || '—'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const downloadAttachment = (attachment: any) => {
  console.log('Download attachment:', attachment.filename)
}

const onAttachmentUpdated = (attachment: any) => {
  // Optionally refresh component data or handle updated attachment
  console.log('Attachment updated:', attachment)
}

const onAttachmentDeleted = (attachment: any) => {
  // Optionally refresh component data or handle deleted attachment
  console.log('Attachment deleted:', attachment)
}

const clearError = () => {
  componentsStore.clearError()
}

const getStockPercentage = (component: Component) => {
  if (!component.minimum_stock || component.minimum_stock <= 0) {
    return component.quantity_on_hand > 0 ? 100 : 0
  }
  return Math.min((component.quantity_on_hand / component.minimum_stock) * 100, 100)
}

const duplicateComponent = () => {
  console.log('Duplicate component:', component.value?.name)
  // TODO: Implement duplicate functionality
}

const moveComponent = () => {
  console.log('Move component:', component.value?.name)
  // TODO: Implement move functionality
}

const printLabel = () => {
  console.log('Print label for:', component.value?.name)
  // TODO: Implement label printing
}

const exportData = () => {
  console.log('Export data for:', component.value?.name)
  // TODO: Implement data export
}

const deleteComponent = () => {
  console.log('Delete component:', component.value?.name)
  // TODO: Implement delete functionality
}

const loadStockHistory = async () => {
  if (!component.value) return

  stockHistoryLoading.value = true
  try {
    await componentsStore.fetchStockHistory(component.value.id)
  } finally {
    stockHistoryLoading.value = false
  }
}

watch(() => props.componentId, async (newId) => {
  if (newId) {
    await componentsStore.fetchComponent(newId)
    await loadStockHistory()
  }
}, { immediate: true })

onMounted(() => {
  if (props.componentId) {
    componentsStore.fetchComponent(props.componentId)
    loadStockHistory()
  }
})
</script>

<style scoped>
.component-detail {
  max-width: 1400px;
  margin: 0 auto;
}

/* Sidebar Layout */
.component-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.component-sidebar {
  flex: 0 0 280px;
  min-width: 280px;
}

.component-main-content {
  flex: 1;
  min-width: 0; /* Allow content to shrink */
}

.sidebar-card {
  position: sticky;
  top: 24px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  background-color: rgba(0, 0, 0, 0.02);
}

/* Existing flexbox layout for main content */
.main-content-flex {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  gap: 16px !important;
  width: 100% !important;
}

.info-card-container {
  flex: 1 1 calc(50% - 8px) !important;
  min-width: 300px !important;
  max-width: calc(50% - 8px) !important;
  box-sizing: border-box !important;
}

/* Force horizontal layout for medium+ displays */
@media (min-width: 768px) {
  .component-detail .main-content-flex {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 16px !important;
  }

  .component-detail .info-card-container {
    flex: 1 1 50% !important;
    max-width: 50% !important;
    min-width: 400px !important;
  }
}

/* Mobile responsiveness */
@media (max-width: 1024px) {
  .component-layout {
    flex-direction: column;
  }

  .component-sidebar {
    flex: none;
    width: 100%;
    order: -1;
  }

  .sidebar-card {
    position: static;
  }

  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 767px) {
  .main-content-flex {
    flex-direction: column !important;
  }

  .info-card-container {
    flex: 1 1 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Full-width sections styling */
.full-width-sections {
  width: 100%;
}

.full-width-sections .col-12 {
  width: 100% !important;
  max-width: 100% !important;
}

/* Storage Locations Compact Layout */
.storage-locations-compact {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  overflow: hidden;
}

.location-row {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.location-row:last-child {
  border-bottom: none;
}

.location-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.location-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.quantity-info {
  font-size: 14px;
}

.location-notes {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 4px;
  font-style: italic;
}
</style>