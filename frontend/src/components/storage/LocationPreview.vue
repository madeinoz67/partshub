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
        <q-list dense bordered separator class="rounded-borders">
          <q-item
            v-for="(name, index) in previewData.sample_names"
            :key="index"
            :data-testid="`sample-name-${index}`"
          >
            <q-item-section>
              <q-item-label class="text-body2 q-mono">{{ name }}</q-item-label>
            </q-item-section>
          </q-item>

          <!-- Ellipsis if more than 5 -->
          <q-item v-if="previewData.total_count > 5" data-testid="preview-ellipsis">
            <q-item-section>
              <q-item-label class="text-center text-grey">...</q-item-label>
            </q-item-section>
          </q-item>

          <!-- Last Name -->
          <q-item v-if="previewData.last_name && previewData.total_count > 5" data-testid="last-name">
            <q-item-section>
              <q-item-label class="text-body2 q-mono">{{ previewData.last_name }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PreviewData {
  sample_names: string[]
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

withDefaults(defineProps<Props>(), {
  loading: false
})
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
  }
}
</style>
