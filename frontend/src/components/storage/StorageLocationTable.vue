<template>
  <div class="storage-location-table">
    <q-table
      :rows="locations"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="pagination"
      :expanded="expanded"
      flat
      bordered
      @row-click="onRowClick"
    >
      <!-- Expandable Row Icon -->
      <template #body-cell-expand="props">
        <q-td :props="props">
          <q-btn
            flat
            round
            dense
            :icon="expanded.includes(props.row.id) ? 'expand_less' : 'expand_more'"
            @click.stop="toggleExpand(props.row.id)"
          />
        </q-td>
      </template>

      <!-- Location Column with Hierarchy -->
      <template #body-cell-location="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.name }}</div>
          <div v-if="props.row.location_hierarchy" class="text-caption text-grey-7">
            {{ props.row.location_hierarchy }}
          </div>
        </q-td>
      </template>

      <!-- Last Used Column -->
      <template #body-cell-last_used="props">
        <q-td :props="props">
          <span v-if="props.row.updated_at">{{ formatDate(props.row.updated_at) }}</span>
          <span v-else class="text-grey-5">Never</span>
        </q-td>
      </template>

      <!-- Part Count Column -->
      <template #body-cell-part_count="props">
        <q-td :props="props">
          <q-chip
            :color="props.row.component_count > 0 ? 'primary' : 'grey-4'"
            :text-color="props.row.component_count > 0 ? 'white' : 'grey-7'"
            size="sm"
          >
            {{ props.row.component_count || 0 }}
          </q-chip>
        </q-td>
      </template>

      <!-- Description Column -->
      <template #body-cell-description="props">
        <q-td :props="props">
          <div v-if="props.row.description" class="ellipsis" style="max-width: 300px">
            {{ props.row.description }}
          </div>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <!-- Expanded Row Content -->
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
          <q-td v-for="col in props.cols.filter(c => c.name !== 'expand')" :key="col.name" :props="props">
            <component
              :is="getBodyCellComponent(col.name)"
              v-if="hasBodyCellSlot(col.name)"
              :props="props"
            />
            <template v-else>
              {{ col.value }}
            </template>
          </q-td>
        </q-tr>

        <!-- Expanded Details Row -->
        <q-tr v-if="expanded.includes(props.row.id)" :props="props">
          <q-td colspan="100%" class="bg-grey-1">
            <div class="row q-pa-md q-gutter-md">
              <!-- Full Hierarchy Path -->
              <div class="col-12 col-md-6">
                <div class="text-subtitle2 text-grey-7 q-mb-xs">Full Hierarchy</div>
                <div class="text-body2">
                  {{ props.row.location_hierarchy || props.row.name }}
                </div>
              </div>

              <!-- Description (Full) -->
              <div v-if="props.row.description" class="col-12 col-md-6">
                <div class="text-subtitle2 text-grey-7 q-mb-xs">Description</div>
                <div class="text-body2">{{ props.row.description }}</div>
              </div>

              <!-- Metadata -->
              <div class="col-12">
                <div class="text-subtitle2 text-grey-7 q-mb-xs">Metadata</div>
                <div class="row q-gutter-sm">
                  <q-chip
                    outline
                    color="primary"
                    size="sm"
                    :icon="getLocationIcon(props.row.type)"
                  >
                    Type: {{ props.row.type }}
                  </q-chip>
                  <q-chip
                    v-if="props.row.qr_code_id"
                    outline
                    color="secondary"
                    size="sm"
                    icon="qr_code"
                  >
                    QR: {{ props.row.qr_code_id }}
                  </q-chip>
                </div>
              </div>

              <!-- Layout Config (if exists) -->
              <div v-if="props.row.layout_config" class="col-12">
                <div class="text-subtitle2 text-grey-7 q-mb-xs">Layout Configuration</div>
                <div class="row q-gutter-sm">
                  <q-chip
                    outline
                    color="accent"
                    size="sm"
                    icon="grid_view"
                  >
                    Type: {{ props.row.layout_config.layout_type }}
                  </q-chip>
                  <q-chip
                    v-if="props.row.layout_config.prefix"
                    outline
                    color="accent"
                    size="sm"
                    icon="label"
                  >
                    Prefix: {{ props.row.layout_config.prefix }}
                  </q-chip>
                </div>
              </div>
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
}>()

// Expanded rows state (only one row can be expanded at a time)
const expanded = ref<string[]>([])

// Pagination
const pagination = ref({
  rowsPerPage: 25,
  sortBy: 'name',
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

// Date formatter
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return 'Today'
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30)
    return `${months} month${months > 1 ? 's' : ''} ago`
  } else {
    return date.toLocaleDateString()
  }
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

// Helper methods for template component rendering
const getBodyCellComponent = (colName: string) => {
  // This would return the appropriate slot component if needed
  return 'div'
}

const hasBodyCellSlot = (colName: string) => {
  return ['location', 'last_used', 'part_count', 'description'].includes(colName)
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
