<template>
  <div class="component-list">
    <!-- Header with search and filters -->
    <q-card class="q-mb-sm">
      <q-card-section class="q-pa-sm">
        <div class="row q-gutter-md items-center">
          <div class="col-md-4 col-xs-12">
            <q-input
              v-model="searchQuery"
              outlined
              dense
              placeholder="Search components..."
              debounce="300"
              @update:model-value="onSearch"
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
              <template v-slot:append v-if="searchQuery">
                <q-icon
                  name="clear"
                  class="cursor-pointer"
                  @click="clearSearch"
                />
              </template>
            </q-input>
          </div>

          <div class="col-md-2 col-xs-12">
            <q-select
              v-model="selectedCategory"
              outlined
              dense
              emit-value
              map-options
              clearable
              label="Category"
              :options="categoryOptions"
              @update:model-value="onCategoryFilter"
            />
          </div>

          <div class="col-md-2 col-xs-12">
            <q-select
              v-model="selectedStockStatus"
              outlined
              dense
              emit-value
              map-options
              clearable
              label="Stock Status"
              :options="stockStatusOptions"
              @update:model-value="onStockFilter"
            />
          </div>


          <div class="col-md-1 col-xs-12" v-if="canPerformCrud()">
            <q-btn
              color="primary"
              icon="add"
              dense
              @click="$emit('create-component')"
            >
              Add Component
            </q-btn>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Statistics Cards -->
    <div class="row q-gutter-xs q-mb-sm no-wrap">
      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 q-mb-none">{{ totalComponents }}</div>
            <div class="text-overline text-grey">Total</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-orange q-mb-none">{{ lowStockComponents.length }}</div>
            <div class="text-overline text-grey">Low Stock</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-red q-mb-none">{{ outOfStockComponents.length }}</div>
            <div class="text-overline text-grey">Out of Stock</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-green q-mb-none">{{ components.length - outOfStockComponents.length }}</div>
            <div class="text-overline text-grey">Available</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

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

    <!-- Components Table -->
    <q-table
      :rows="components"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="{ sortBy: 'updated_at', descending: true, page: 1, rowsPerPage: 25 }"
      :rows-per-page-options="[25, 50, 100]"
      v-model:expanded="expanded"
      dense
      @row-click="onRowClick"
      class="compact-table"
    >
      <!-- Use body slot for internal expansion model -->
      <template v-slot:body="props">
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
              @click="props.expand = !props.expand"
              :icon="props.expand ? 'keyboard_arrow_down' : 'keyboard_arrow_right'"
            />
          </q-td>

          <!-- Component name column -->
          <q-td key="name" :props="props">
            <div class="text-weight-medium">{{ props.row.name }}</div>
            <div v-if="props.row.part_number" class="text-caption text-grey">
              PN: {{ props.row.part_number }}
            </div>
          </q-td>

          <!-- Stock column -->
          <q-td key="stock" :props="props">
            <q-chip
              :color="getStockStatusColor(props.row)"
              text-color="white"
              :label="props.row.quantity_on_hand"
              size="sm"
            />
            <div class="text-caption text-grey">
              Min: {{ props.row.minimum_stock }}
            </div>
          </q-td>

          <!-- Location column -->
          <q-td key="location" :props="props">
            <div v-if="props.row.storage_location">
              <q-chip
                outline
                :label="props.row.storage_location.name"
                size="sm"
                class="q-mb-xs"
              />
              <div class="text-caption text-grey">
                {{ props.row.storage_location.location_hierarchy }}
              </div>
            </div>
            <div v-else class="text-caption text-grey">
              No location assigned
            </div>
          </q-td>

          <!-- Category column -->
          <q-td key="category" :props="props">
            <q-chip
              v-if="props.row.category"
              outline
              color="primary"
              :label="props.row.category.name"
              size="sm"
            />
            <span v-else class="text-caption text-grey">Uncategorized</span>
          </q-td>

          <!-- Value column -->
          <q-td key="value" :props="props">
            <div v-if="props.row.value || props.row.component_type">
              <div v-if="props.row.value" class="text-weight-medium">
                {{ props.row.value }}
              </div>
              <div v-if="props.row.component_type" class="text-caption text-grey">
                {{ props.row.component_type }}
              </div>
            </div>
            <span v-else class="text-caption text-grey">—</span>
          </q-td>

          <!-- Manufacturer column -->
          <q-td key="manufacturer" :props="props">
            {{ props.row.manufacturer || '—' }}
          </q-td>

          <!-- Attachments column -->
          <q-td key="attachments" :props="props">
            <div class="row justify-center q-gutter-xs">
              <q-icon
                v-for="attachment in getAttachmentIcons(props.row.attachments)"
                :key="attachment.type"
                :name="attachment.icon"
                :color="attachment.color"
                size="sm"
                :title="attachment.tooltip"
              />
              <span v-if="!props.row.attachments?.length" class="text-caption text-grey">—</span>
            </div>
          </q-td>

          <!-- Updated at column -->
          <q-td key="updated_at" :props="props">
            {{ new Date(props.row.updated_at).toLocaleDateString() }}
          </q-td>

          <!-- Actions column -->
          <q-td key="actions" :props="props" @click.stop>
            <q-btn-dropdown
              flat
              dense
              icon="more_vert"
              size="sm"
              @click.stop
            >
              <q-list>
                <q-item
                  clickable
                  v-close-popup
                  @click="$emit('view-component', props.row)"
                >
                  <q-item-section avatar>
                    <q-icon name="visibility" />
                  </q-item-section>
                  <q-item-section>View Details</q-item-section>
                </q-item>

                <template v-if="canPerformCrud()">
                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('edit-component', props.row)"
                  >
                    <q-item-section avatar>
                      <q-icon name="edit" />
                    </q-item-section>
                    <q-item-section>Edit</q-item-section>
                  </q-item>

                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('update-stock', props.row)"
                  >
                    <q-item-section avatar>
                      <q-icon name="inventory" />
                    </q-item-section>
                    <q-item-section>Update Stock</q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('delete-component', props.row)"
                    class="text-negative"
                  >
                    <q-item-section avatar>
                      <q-icon name="delete" />
                    </q-item-section>
                    <q-item-section>Delete</q-item-section>
                  </q-item>
                </template>
              </q-list>
            </q-btn-dropdown>
          </q-td>
        </q-tr>

        <!-- Expansion row -->
        <q-tr v-if="props.expand" :props="props">
          <q-td colspan="100%" style="padding: 0;">
            <div style="background: #f0f8ff; border-left: 4px solid #1976d2; padding: 16px; margin: 0;">
              <!-- Component Detail Preview -->
              <div class="row q-gutter-md">
                <!-- Basic Info -->
                <div class="col-md-4 col-xs-12">
                  <q-card flat bordered>
                    <q-card-section>
                      <div class="text-h6 q-mb-md">Basic Information</div>
                      <div class="q-gutter-sm">
                        <div class="row">
                          <div class="col-4 text-weight-medium">Name:</div>
                          <div class="col-8">{{ props.row.name }}</div>
                        </div>
                        <div v-if="props.row.part_number" class="row">
                          <div class="col-4 text-weight-medium">Part Number:</div>
                          <div class="col-8">{{ props.row.part_number }}</div>
                        </div>
                        <div v-if="props.row.manufacturer" class="row">
                          <div class="col-4 text-weight-medium">Manufacturer:</div>
                          <div class="col-8">{{ props.row.manufacturer }}</div>
                        </div>
                        <div v-if="props.row.component_type" class="row">
                          <div class="col-4 text-weight-medium">Type:</div>
                          <div class="col-8">{{ props.row.component_type }}</div>
                        </div>
                        <div v-if="props.row.value" class="row">
                          <div class="col-4 text-weight-medium">Value:</div>
                          <div class="col-8">{{ props.row.value }}</div>
                        </div>
                        <div v-if="props.row.package" class="row">
                          <div class="col-4 text-weight-medium">Package:</div>
                          <div class="col-8">{{ props.row.package }}</div>
                        </div>
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Stock & Location -->
                <div class="col-md-4 col-xs-12">
                  <q-card flat bordered>
                    <q-card-section>
                      <div class="text-h6 q-mb-md">Stock & Location</div>
                      <div class="q-gutter-sm">
                        <div class="row items-center">
                          <div class="col-6 text-weight-medium">Current Stock:</div>
                          <div class="col-6">
                            <q-chip
                              :color="getStockStatusColor(props.row)"
                              text-color="white"
                              :label="props.row.quantity_on_hand"
                              size="md"
                            />
                          </div>
                        </div>
                        <div class="row">
                          <div class="col-6 text-weight-medium">Minimum Stock:</div>
                          <div class="col-6">{{ props.row.minimum_stock }}</div>
                        </div>
                        <div class="row">
                          <div class="col-6 text-weight-medium">Location:</div>
                          <div class="col-6">
                            <div v-if="props.row.storage_location">
                              <q-chip outline :label="props.row.storage_location.name" size="sm" />
                              <div class="text-caption text-grey">
                                {{ props.row.storage_location.location_hierarchy }}
                              </div>
                            </div>
                            <span v-else class="text-grey">No location assigned</span>
                          </div>
                        </div>
                        <div class="row">
                          <div class="col-6 text-weight-medium">Category:</div>
                          <div class="col-6">
                            <q-chip
                              v-if="props.row.category"
                              outline
                              color="primary"
                              :label="props.row.category.name"
                              size="sm"
                            />
                            <span v-else class="text-grey">Uncategorized</span>
                          </div>
                        </div>
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Files & Actions -->
                <div class="col-md-4 col-xs-12">
                  <q-card flat bordered>
                    <q-card-section>
                      <div class="text-h6 q-mb-md">Files & Actions</div>

                      <!-- Attachments -->
                      <div v-if="props.row.attachments && props.row.attachments.length > 0" class="q-mb-md">
                        <div class="text-weight-medium q-mb-sm">Attachments ({{ props.row.attachments.length }})</div>
                        <div class="row q-gutter-xs">
                          <q-chip
                            v-for="attachment in props.row.attachments"
                            :key="attachment.id"
                            outline
                            :icon="getAttachmentIcon(attachment)"
                            :label="attachment.filename"
                            size="sm"
                            clickable
                            @click="downloadAttachment(attachment)"
                          />
                        </div>
                      </div>

                      <!-- Action Buttons -->
                      <div class="column q-gutter-sm">
                        <q-btn
                          outline
                          color="primary"
                          icon="visibility"
                          label="View Full Details"
                          @click="$emit('view-component', props.row)"
                          size="sm"
                        />
                        <template v-if="canPerformCrud()">
                          <q-btn
                            outline
                            color="secondary"
                            icon="edit"
                            label="Edit"
                            @click="$emit('edit-component', props.row)"
                            size="sm"
                          />
                          <q-btn
                            outline
                            color="accent"
                            icon="inventory"
                            label="Update Stock"
                            @click="$emit('update-stock', props.row)"
                            size="sm"
                          />
                        </template>
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>

              <!-- Description & Notes -->
              <div v-if="props.row.description || props.row.notes" class="q-mt-md">
                <q-card flat bordered>
                  <q-card-section>
                    <div v-if="props.row.description">
                      <div class="text-h6 q-mb-sm">Description</div>
                      <div class="text-body2 q-mb-md">{{ props.row.description }}</div>
                    </div>
                    <div v-if="props.row.notes">
                      <div class="text-h6 q-mb-sm">Notes</div>
                      <div class="text-body2" style="white-space: pre-wrap;">{{ props.row.notes }}</div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-td>
        </q-tr>
      </template>


      <!-- No data message -->
      <template v-slot:no-data="{ message }">
        <div class="full-width row flex-center q-gutter-sm">
          <q-icon size="2em" name="inventory_2" />
          <span>{{ message || 'No components found' }}</span>
        </div>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useComponentsStore } from '../stores/components'
import { useAuth } from '../composables/useAuth'
import type { Component } from '../services/api'

// Component props
interface Props {
  embedded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  embedded: false
})

// Component emits
const emit = defineEmits<{
  'create-component': []
  'view-component': [component: Component]
  'edit-component': [component: Component]
  'update-stock': [component: Component]
  'delete-component': [component: Component]
}>()

// Store
const componentsStore = useComponentsStore()
const { canPerformCrud } = useAuth()
const {
  components,
  loading,
  error,
  totalComponents,
  currentPage,
  totalPages,
  itemsPerPage,
  lowStockComponents,
  outOfStockComponents
} = storeToRefs(componentsStore)

// Local state
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedStockStatus = ref('')
const sortBy = ref('updated_at')
const sortOrder = ref<'asc' | 'desc'>('desc')
const expanded = ref<string[]>([])

// Table configuration
const columns = [
  {
    name: 'expand',
    label: '',
    field: 'expand',
    sortable: false,
    required: true,
    align: 'left' as const,
    style: 'width: 40px',
    headerStyle: 'width: 40px'
  },
  {
    name: 'name',
    required: true,
    label: 'Component',
    align: 'left' as const,
    field: 'name',
    sortable: true
  },
  {
    name: 'stock',
    label: 'Stock',
    align: 'center' as const,
    field: 'quantity_on_hand',
    sortable: true
  },
  {
    name: 'location',
    label: 'Location',
    align: 'left' as const,
    field: (row: Component) => row.storage_location?.name || '',
    sortable: true
  },
  {
    name: 'category',
    label: 'Category',
    align: 'left' as const,
    field: (row: Component) => row.category?.name || '',
    sortable: true
  },
  {
    name: 'value',
    label: 'Value/Type',
    align: 'left' as const,
    field: 'value',
    sortable: true
  },
  {
    name: 'manufacturer',
    label: 'Manufacturer',
    align: 'left' as const,
    field: 'manufacturer',
    sortable: true
  },
  {
    name: 'attachments',
    label: 'Files',
    align: 'center' as const,
    field: (row: Component) => row.attachments?.length || 0,
    sortable: true
  },
  {
    name: 'updated_at',
    label: 'Last Updated',
    align: 'center' as const,
    field: 'updated_at',
    sortable: true,
    format: (val: string) => new Date(val).toLocaleDateString(),
    sort: (a: Component, b: Component) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center' as const
  }
]

// Using client-side pagination and sorting

// Options for filters
const categoryOptions = computed(() => {
  const categories = new Set(
    components.value
      .map(c => c.category?.name)
      .filter(Boolean)
  )
  return Array.from(categories).map(cat => ({
    label: cat,
    value: cat
  }))
})

const stockStatusOptions = [
  { label: 'Low Stock', value: 'low' },
  { label: 'Out of Stock', value: 'out' },
  { label: 'Available', value: 'available' }
]

// Methods
const getStockStatusColor = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

const getAttachmentIcons = (attachments: any[] = []) => {
  if (!attachments || attachments.length === 0) return []

  const icons = []

  // Check for datasheet/PDF files
  const hasDatasheet = attachments.some(att =>
    att.filename?.toLowerCase().includes('.pdf') ||
    att.attachment_type === 'datasheet'
  )
  if (hasDatasheet) {
    icons.push({
      type: 'datasheet',
      icon: 'picture_as_pdf',
      color: 'red',
      tooltip: 'Has datasheet'
    })
  }

  // Check for image files
  const hasImages = attachments.some(att =>
    att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/i) ||
    att.attachment_type === 'image'
  )
  if (hasImages) {
    icons.push({
      type: 'image',
      icon: 'image',
      color: 'blue',
      tooltip: 'Has images'
    })
  }

  // Check for other documents
  const hasDocuments = attachments.some(att =>
    att.attachment_type === 'document' &&
    !att.filename?.toLowerCase().includes('.pdf')
  )
  if (hasDocuments) {
    icons.push({
      type: 'document',
      icon: 'description',
      color: 'grey',
      tooltip: 'Has documents'
    })
  }

  return icons
}

const onSearch = (query: string) => {
  componentsStore.searchComponents(query)
}

const clearSearch = () => {
  searchQuery.value = ''
  componentsStore.searchComponents('')
}

const onCategoryFilter = (category: string) => {
  componentsStore.filterByCategory(category)
}

const onStockFilter = (status: 'low' | 'out' | 'available' | undefined) => {
  componentsStore.filterByStockStatus(status)
}

// Client-side table with no server-side requests needed for sorting

const getAttachmentIcon = (attachment: any) => {
  const filename = attachment.filename?.toLowerCase() || ''
  if (filename.includes('.pdf') || attachment.attachment_type === 'datasheet') {
    return 'picture_as_pdf'
  }
  if (filename.match(/\.(jpg|jpeg|png|gif|webp)$/i) || attachment.attachment_type === 'image') {
    return 'image'
  }
  return 'description'
}

const downloadAttachment = (attachment: any) => {
  // This would typically trigger a download
  console.log('Download attachment:', attachment.filename)
  // emit('download-attachment', attachment) // Could emit to parent if needed
}


const onRowClick = (evt: Event, row: Component) => {
  // Don't navigate to detail page on row click when we have expandable rows
  // User can click "View Full Details" button instead
}

const clearError = () => {
  componentsStore.clearError()
}

// Lifecycle
onMounted(() => {
  componentsStore.fetchComponents()
})
</script>

<style scoped>
.component-list {
  min-height: 400px;
}

.compact-table {
  font-size: 0.875rem;
}

.compact-table :deep(.q-table__top) {
  padding: 8px 16px;
}

.compact-table :deep(.q-td) {
  padding: 2px 6px;
  font-size: 0.8rem;
  height: 24px;
}

.compact-table :deep(.q-th) {
  padding: 3px 6px;
  font-size: 0.8rem;
  font-weight: 600;
  height: 28px;
}

.compact-table :deep(tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s;
  height: 24px;
}

.compact-table :deep(tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.04);
}

.compact-table :deep(.q-chip) {
  font-size: 0.7rem;
  padding: 1px 4px;
  min-height: 16px;
}

.mini-stats {
  border-radius: 8px;
  min-height: 60px;
  max-height: 60px;
}

.mini-stats .q-card__section {
  padding: 8px 12px !important;
}

.mini-stats .text-subtitle2 {
  font-size: 1.1rem;
  line-height: 1.2;
  font-weight: 600;
}

.mini-stats .text-overline {
  font-size: 0.75rem;
  line-height: 1;
  letter-spacing: 0.5px;
  margin-top: 2px;
}
</style>