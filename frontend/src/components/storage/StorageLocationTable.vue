<template>
  <div class="storage-location-table">
    <!-- Search Bar -->
    <div class="q-mb-md">
      <q-input
        v-model="searchQuery"
        outlined
        dense
        placeholder="Search locations..."
        clearable
        data-testid="location-search"
      >
        <template #prepend>
          <q-icon name="search" />
        </template>
      </q-input>
    </div>

    <q-table
      :rows="filteredLocations"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="pagination"
      :expanded="expanded"
      flat
      bordered
      @row-click="onRowClick"
    >
      <!-- Custom Body with Expandable Rows -->
      <template #body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn
              flat
              round
              dense
              :icon="expanded.includes(props.row.id) ? 'expand_less' : 'expand_more'"
              @click.stop="toggleExpand(props.row.id)"
            />
          </q-td>
          <q-td key="location" :props="props">
            <div class="text-weight-medium">{{ props.row.name }}</div>
          </q-td>
          <q-td key="last_used" :props="props">
            <span v-if="hasBeenUsed(props.row)">{{ formatDate(props.row.updated_at) }}</span>
            <span v-else class="text-grey-5">—</span>
          </q-td>
          <q-td key="part_count" :props="props">
            <q-chip
              :color="props.row.component_count > 0 ? 'primary' : 'grey-4'"
              :text-color="props.row.component_count > 0 ? 'white' : 'grey-7'"
              size="sm"
            >
              {{ props.row.component_count || 0 }}
            </q-chip>
          </q-td>
          <q-td key="description" :props="props">
            <div v-if="props.row.description" class="ellipsis" style="max-width: 300px">
              {{ props.row.description }}
            </div>
            <span v-else class="text-grey-5">—</span>
          </q-td>
        </q-tr>

        <!-- Expanded Details Row -->
        <q-tr v-if="expanded.includes(props.row.id)" :props="props">
          <q-td colspan="100%" class="bg-grey-1">
            <div class="q-pa-lg">
              <!-- Header with location name and icon -->
              <div class="row items-center q-mb-lg">
                <q-icon name="archive" size="32px" color="primary" class="q-mr-md" />
                <div class="text-h5">
                  Storage location: {{ props.row.name }}
                  <span class="text-grey-7">(parts: {{ props.row.component_count || 0 }})</span>
                </div>
                <q-space />
                <q-btn
                  outline
                  color="primary"
                  icon="edit"
                  label="Edit"
                  @click="emit('editLocation', props.row)"
                />
              </div>

              <!-- Location Info Card -->
              <q-card flat bordered class="q-mb-md">
                <q-card-section>
                  <div class="text-subtitle1 text-weight-medium q-mb-md">
                    <q-icon name="info" class="q-mr-sm" />
                    Location Info
                  </div>

                  <div class="row q-col-gutter-md">
                    <!-- Left column with details -->
                    <div class="col-12 col-md-8">
                      <div class="row q-col-gutter-md">
                        <!-- Storage location name -->
                        <div class="col-12 col-md-6">
                          <div class="text-caption text-grey-7">Storage location name:</div>
                          <div class="text-body1">{{ props.row.name }}</div>
                        </div>

                        <!-- Physical Location (Parent) -->
                        <div class="col-12 col-md-6">
                          <div class="text-caption text-grey-7">Physical Location:</div>
                          <div class="text-body1">{{ getParentLocationName(props.row) || '—' }}</div>
                        </div>

                        <!-- Type -->
                        <div class="col-12 col-md-6">
                          <div class="text-caption text-grey-7">Location Type:</div>
                          <div class="text-body1">{{ props.row.type }}</div>
                        </div>

                        <!-- QR Code ID -->
                        <div class="col-12 col-md-6">
                          <div class="text-caption text-grey-7">QR Code ID:</div>
                          <div class="text-body1">{{ props.row.qr_code_id || '—' }}</div>
                        </div>

                        <!-- Description -->
                        <div class="col-12">
                          <div class="text-caption text-grey-7">Description:</div>
                          <div class="text-body1">{{ props.row.description || '—' }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- Right column with QR code -->
                    <div v-if="props.row.qr_code_id" class="col-12 col-md-4 flex flex-center">
                      <div class="text-center">
                        <div class="text-caption text-grey-7 q-mb-sm">QR Code</div>
                        <QrcodeVue
                          :value="getQRCodeValue(props.row)"
                          :size="150"
                          level="H"
                          render-as="svg"
                        />
                        <div class="text-caption text-grey-7 q-mt-xs">{{ props.row.qr_code_id }}</div>
                      </div>
                    </div>
                  </div>
                </q-card-section>
              </q-card>

              <!-- Parts stored in this location -->
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle1 text-weight-medium q-mb-md">
                    <q-icon name="inventory" class="q-mr-sm" />
                    Parts stored in this location
                  </div>

                  <div v-if="props.row.component_count === 0" class="row items-center q-pa-md bg-blue-1 rounded-borders">
                    <q-icon name="info" size="48px" color="blue-7" class="q-mr-md" />
                    <div>
                      <div class="text-subtitle1 text-weight-medium">Storage location is empty</div>
                      <div class="text-body2 text-grey-8">There are no parts in this storage location.</div>
                    </div>
                  </div>

                  <div v-else class="text-body2 text-grey-7">
                    {{ props.row.component_count }} part{{ props.row.component_count !== 1 ? 's' : '' }} stored here
                    <div class="text-caption q-mt-sm">Click "Go to storage location" above to view and manage parts</div>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </q-td>
        </q-tr>
      </template>

      <!-- Loading State -->
      <template #loading>
        <q-inner-loading showing>
          <q-spinner-dots size="50px" color="primary" />
        </q-inner-loading>
      </template>

      <!-- Empty State -->
      <template #no-data>
        <div class="full-width column flex-center q-pa-xl">
          <q-icon name="inventory_2" size="4em" color="grey-4" />
          <div class="text-h6 text-grey-6 q-mt-md">No storage locations</div>
          <div class="text-grey-5">Create your first location to get started</div>
        </div>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import QrcodeVue from 'qrcode.vue'
import type { StorageLocation } from '../../services/api'
import type { QTableColumn } from 'quasar'

interface Props {
  locations: StorageLocation[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  refresh: []
  locationSelected: [location: StorageLocation]
  editLocation: [location: StorageLocation]
}>()

// Expanded rows state (only one row can be expanded at a time)
const expanded = ref<string[]>([])

// Search query for filtering locations
const searchQuery = ref('')

// Filtered locations based on search query
const filteredLocations = computed(() => {
  if (!searchQuery.value) {
    return props.locations
  }

  const query = searchQuery.value.toLowerCase().trim()
  return props.locations.filter(location => {
    return (
      location.name.toLowerCase().includes(query) ||
      location.type.toLowerCase().includes(query) ||
      location.description?.toLowerCase().includes(query) ||
      location.location_hierarchy?.toLowerCase().includes(query)
    )
  })
})

// Pagination with default sorting by name
const pagination = ref({
  rowsPerPage: 25,
  sortBy: 'location',
  descending: false
})

// Column definitions with responsive classes
const columns = computed<QTableColumn[]>(() => [
  {
    name: 'expand',
    label: '',
    field: '',
    align: 'left',
    required: true,
    sortable: false,
    style: 'width: 50px'
  },
  {
    name: 'location',
    label: 'Location',
    field: 'name',
    align: 'left',
    sortable: true,
    required: true,
    classes: 'text-weight-medium',
    headerClasses: 'bg-grey-3'
  },
  {
    name: 'last_used',
    label: 'Last Used',
    field: 'updated_at',
    align: 'left',
    sortable: true,
    classes: 'lt-md-hide',
    headerClasses: 'bg-grey-3 lt-md-hide'
  },
  {
    name: 'part_count',
    label: 'Parts',
    field: (row: StorageLocation) => row.component_count || 0,
    align: 'center',
    sortable: true,
    required: true,
    headerClasses: 'bg-grey-3'
  },
  {
    name: 'description',
    label: 'Description',
    field: 'description',
    align: 'left',
    sortable: false,
    classes: 'lt-lg-hide',
    headerClasses: 'bg-grey-3 lt-lg-hide'
  }
])

// Toggle row expansion (single-row expansion)
const toggleExpand = (locationId: string) => {
  if (expanded.value.includes(locationId)) {
    // Collapse if already expanded
    expanded.value = []
  } else {
    // Expand this row and collapse others
    expanded.value = [locationId]
  }
}

// Row click handler
const onRowClick = (_evt: Event, row: StorageLocation) => {
  emit('locationSelected', row)
}

// Date formatter - format as "YYYY-MM-DD HH:MM"
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// Location type icon mapping
const getLocationIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    building: 'domain',
    room: 'room',
    cabinet: 'inventory_2',
    shelf: 'shelves',
    drawer: 'inbox',
    bin: 'archive',
    container: 'storage'
  }
  return iconMap[type] || 'folder'
}

// Get parent location name from parent_id
const getParentLocationName = (location: StorageLocation): string | null => {
  if (!location.parent_id) return null

  // Find parent in the locations list
  const parent = props.locations.find(loc => loc.id === location.parent_id)
  return parent ? parent.name : null
}

// Check if location has been used (has parts or had parts moved in/out)
const hasBeenUsed = (location: StorageLocation): boolean => {
  // Location is considered "used" if:
  // 1. It currently has parts (component_count > 0), OR
  // 2. It has an updated_at timestamp that differs from created_at (indicating activity)

  if (location.component_count && location.component_count > 0) {
    return true
  }

  // If no parts currently, check if updated_at differs from created_at
  // This would indicate parts were added/removed at some point
  if (location.updated_at && location.created_at) {
    return location.updated_at !== location.created_at
  }

  return false
}

// Generate QR code value for location
const getQRCodeValue = (location: StorageLocation): string => {
  // Generate a URL that could be scanned to navigate to this location
  // Format: partshub://location/{id} or use the qr_code_id
  return location.qr_code_id || location.id
}
</script>

<style scoped lang="scss">
.storage-location-table {
  width: 100%;

  :deep(.q-table) {
    // Responsive table adjustments for mobile (< 768px)
    @media (max-width: 767px) {
      // Hide last_used column on mobile
      .lt-md-hide {
        display: none !important;
      }

      // Adjust table padding for mobile
      thead tr th,
      tbody tr td {
        padding: 8px 4px;
        font-size: 14px;
      }

      // Touch-friendly expand button
      .q-btn {
        padding: 12px;
        min-width: 48px;
        min-height: 48px;
      }

      // Ensure location column takes available space
      thead tr th:nth-child(2),
      tbody tr td:nth-child(2) {
        width: auto;
        min-width: 120px;
      }

      // Part count column fixed width
      thead tr th:nth-child(3),
      tbody tr td:nth-child(3) {
        width: 80px;
        text-align: center;
      }
    }

    // Responsive table adjustments for tablet (768px - 1023px)
    @media (min-width: 768px) and (max-width: 1023px) {
      // Hide description column on tablet
      .lt-lg-hide {
        display: none !important;
      }

      // Adjust table padding for tablet
      thead tr th,
      tbody tr td {
        padding: 12px 8px;
        font-size: 14px;
      }

      // Column widths for tablet
      thead tr th:nth-child(2),
      tbody tr td:nth-child(2) {
        width: 40%;
      }

      thead tr th:nth-child(3),
      tbody tr td:nth-child(3) {
        width: 20%;
      }

      thead tr th:nth-child(4),
      tbody tr td:nth-child(4) {
        width: 15%;
        text-align: center;
      }
    }

    // Desktop layout (>= 1024px)
    @media (min-width: 1024px) {
      thead tr th,
      tbody tr td {
        padding: 16px 12px;
      }

      // Column widths for desktop
      thead tr th:nth-child(2),
      tbody tr td:nth-child(2) {
        width: 30%;
      }

      thead tr th:nth-child(3),
      tbody tr td:nth-child(3) {
        width: 15%;
      }

      thead tr th:nth-child(4),
      tbody tr td:nth-child(4) {
        width: 12%;
        text-align: center;
      }

      thead tr th:nth-child(5),
      tbody tr td:nth-child(5) {
        width: 30%;
      }
    }

    // Horizontal scrolling for overflow
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;

    // Sticky expand column on scroll
    thead tr th:first-child,
    tbody tr td:first-child {
      position: sticky;
      left: 0;
      z-index: 1;
      background-color: white;
    }

    thead tr th:first-child {
      z-index: 2;
    }
  }

  // Expanded row styling
  :deep(.q-tr) {
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: rgba(0, 0, 0, 0.02);
    }

    // Active/expanded row highlight
    &.expanded {
      background-color: rgba(25, 118, 210, 0.08);
    }
  }

  // Expanded details section responsive padding
  :deep(.q-td[colspan]) {
    @media (max-width: 767px) {
      padding: 12px 8px !important;

      .row {
        margin: 0 -4px;

        > div {
          padding: 4px;
        }
      }

      .q-chip {
        font-size: 11px;
        padding: 4px 8px;
      }
    }

    @media (min-width: 768px) and (max-width: 1023px) {
      padding: 16px 12px !important;

      .q-chip {
        font-size: 12px;
      }
    }
  }

  // Ellipsis for long text
  .ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  // Touch feedback for mobile
  @media (hover: none) {
    :deep(.q-tr) {
      &:active {
        background-color: rgba(0, 0, 0, 0.05);
      }
    }
  }
}
</style>
