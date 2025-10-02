<template>
  <div class="location-preview">
    <!-- Loading State -->
    <div
      v-if="loading"
      data-testid="preview-loading"
      class="text-center q-pa-lg"
    >
      <q-spinner color="primary" size="50px" />
      <div class="text-caption text-grey q-mt-md">Generating preview...</div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!previewData"
      data-testid="preview-empty"
      class="text-center q-pa-lg"
    >
      <q-icon name="preview" size="3em" color="grey-5" />
      <div class="text-body2 text-grey q-mt-md">
        Configure the layout to see a preview
      </div>
    </div>

    <!-- Preview Content -->
    <div
      v-else
      data-testid="preview-content"
      class="preview-content"
      :class="{
        'preview-valid': previewData.is_valid,
        'preview-invalid': !previewData.is_valid
      }"
    >
      <!-- Errors (displayed first) -->
      <q-banner
        v-if="previewData.errors && previewData.errors.length > 0"
        data-testid="preview-errors"
        class="error bg-negative text-white q-mb-md"
        dense
      >
        <template #avatar>
          <q-icon name="error" color="white" />
        </template>
        <div class="text-weight-medium">Validation Errors</div>
        <ul class="q-my-sm q-pl-md">
          <li
            v-for="(error, index) in previewData.errors"
            :key="index"
            :data-testid="`error-message-${index}`"
          >
            {{ error }}
          </li>
        </ul>
      </q-banner>

      <!-- Warnings -->
      <q-banner
        v-if="previewData.warnings && previewData.warnings.length > 0"
        data-testid="preview-warnings"
        class="warning bg-warning text-white q-mb-md"
        dense
      >
        <template #avatar>
          <q-icon name="warning" color="white" />
        </template>
        <div class="text-weight-medium">Warnings</div>
        <ul class="q-my-sm q-pl-md">
          <li
            v-for="(warning, index) in previewData.warnings"
            :key="index"
            :data-testid="`warning-message-${index}`"
          >
            {{ warning }}
          </li>
        </ul>
      </q-banner>

      <!-- Total Count -->
      <div data-testid="total-count" class="text-h6 q-mb-md">
        <q-icon name="location_on" class="q-mr-xs" />
        {{ previewData.total_count }} {{ previewData.total_count === 1 ? 'location' : 'locations' }}
      </div>

      <!-- Sample Names (only if valid and has samples) -->
      <div
        v-if="previewData.is_valid && previewData.sample_names.length > 0"
        data-testid="sample-names-list"
        class="sample-names q-mb-md"
      >
        <div class="text-caption text-weight-medium text-grey-7 q-mb-xs">
          Preview:
        </div>
        <q-table
          data-testid="preview-table"
          :rows="previewRows"
          :columns="previewColumns"
          flat
          bordered
          dense
          hide-pagination
          :rows-per-page-options="[0]"
          class="preview-table"
        >
          <template #body="bodyProps">
            <q-tr :props="bodyProps">
              <q-td
                key="name"
                :props="bodyProps"
                :data-testid="getNameTestId(bodyProps.rowIndex)"
              >
                <span class="q-mono">{{ bodyProps.row.name }}</span>
              </q-td>
              <q-td
                key="code"
                :props="bodyProps"
                :data-testid="getCodeTestId(bodyProps.rowIndex)"
              >
                <span class="text-primary text-weight-bold">{{ bodyProps.row.code }}</span>
              </q-td>
            </q-tr>
          </template>
        </q-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface PreviewData {
  sample_names: string[]
  location_codes: string[]
  last_name: string
  total_count: number
  warnings: string[]
  errors: string[]
  is_valid: boolean
}

interface Props {
  loading?: boolean
  previewData: PreviewData | null
}

interface PreviewRow {
  name: string
  code: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const previewColumns = [
  {
    name: 'name',
    label: 'Location Name',
    field: 'name',
    align: 'left' as const,
    style: 'width: 60%'
  },
  {
    name: 'code',
    label: 'Location Code',
    field: 'code',
    align: 'left' as const,
    style: 'width: 40%'
  }
]

const previewRows = computed((): PreviewRow[] => {
  if (!props.previewData?.sample_names) return []

  const rows: PreviewRow[] = props.previewData.sample_names.map((name, index) => ({
    name,
    code: props.previewData?.location_codes?.[index] || 'N/A'
  }))

  // Add ellipsis row if more than 5
  if (props.previewData.total_count > 5) {
    rows.push({ name: '...', code: '...' })

    // Add last row
    if (props.previewData.last_name) {
      const lastIndex = (props.previewData.location_codes?.length || 1) - 1
      rows.push({
        name: props.previewData.last_name,
        code: props.previewData.location_codes?.[lastIndex] || 'N/A'
      })
    }
  }

  return rows
})

// Helper functions for test IDs
const getNameTestId = (rowIndex: number): string => {
  if (!props.previewData) return ''

  const totalSampleNames = props.previewData.sample_names.length

  // Check if this is the ellipsis row (comes after sample names)
  if (rowIndex === totalSampleNames && props.previewData.total_count > 5) {
    return 'preview-ellipsis'
  }

  // Check if this is the last name row (comes after ellipsis)
  if (rowIndex === totalSampleNames + 1 && props.previewData.total_count > 5) {
    return 'last-name'
  }

  // Regular sample name row
  return `sample-name-${rowIndex}`
}

const getCodeTestId = (rowIndex: number): string => {
  if (!props.previewData) return ''

  const totalSampleNames = props.previewData.sample_names.length

  // Check if this is the ellipsis row
  if (rowIndex === totalSampleNames && props.previewData.total_count > 5) {
    return 'preview-ellipsis-code'
  }

  // Check if this is the last code row
  if (rowIndex === totalSampleNames + 1 && props.previewData.total_count > 5) {
    return 'last-code'
  }

  // Regular location code row
  return `location-code-${rowIndex}`
}
</script>

<style scoped lang="scss">
.location-preview {
  min-height: 200px;

  .preview-content {
    &.preview-valid {
      // Success styling if needed
    }

    &.preview-invalid {
      // Error styling if needed
    }
  }

  .sample-names {
    .q-mono {
      font-family: 'Courier New', Courier, monospace;
    }

    .preview-table {
      // Ensure table is responsive and clean
      :deep(thead th) {
        font-weight: 600;
      }

      :deep(tbody td) {
        vertical-align: middle;
      }
    }
  }
}
</style>
