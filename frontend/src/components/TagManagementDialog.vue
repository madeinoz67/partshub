<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card style="min-width: 600px; max-width: 800px">
      <q-card-section>
        <div class="text-h6">Add or Remove Tags ({{ componentIds.length }})</div>
      </q-card-section>

      <q-card-section>
        <!-- Add Tags Section -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm">Add Tags</div>
          <q-input
            v-model="tagsToAdd"
            outlined
            dense
            placeholder="Enter comma-separated tags"
            hint="Separate tags with commas"
          />
        </div>

        <!-- Remove Tags Section -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm">Remove Tags</div>
          <q-input
            v-model="tagsToRemove"
            outlined
            dense
            placeholder="Enter comma-separated tags to remove"
            hint="Separate tags with commas"
          />
        </div>

        <!-- Preview Section -->
        <div v-if="preview.length > 0" class="q-mt-md">
          <div class="text-subtitle2 q-mb-sm">Preview Changes</div>
          <q-table
            :rows="preview"
            :columns="previewColumns"
            row-key="component_id"
            flat
            dense
            :rows-per-page-options="[5, 10, 20]"
          >
            <template #body-cell-current_user_tags="props">
              <q-td :props="props">
                <q-chip
                  v-for="tag in props.row.current_user_tags"
                  :key="tag"
                  dense
                  size="sm"
                  color="blue"
                  text-color="white"
                >
                  {{ tag }}
                </q-chip>
              </q-td>
            </template>
            <template #body-cell-proposed_user_tags="props">
              <q-td :props="props">
                <q-chip
                  v-for="tag in props.row.proposed_user_tags"
                  :key="tag"
                  dense
                  size="sm"
                  color="green"
                  text-color="white"
                >
                  {{ tag }}
                </q-chip>
              </q-td>
            </template>
          </q-table>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          flat
          label="Cancel"
          color="primary"
          @click="handleCancel"
        />
        <q-btn
          flat
          label="Preview"
          color="primary"
          :loading="loadingPreview"
          :disable="!hasChanges"
          @click="loadPreview"
        />
        <q-btn
          flat
          label="Apply"
          color="primary"
          :loading="loadingApply"
          :disable="preview.length === 0"
          @click="handleApply"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { bulkOperationsApi, type TagPreview } from '../services/bulkOperationsApi'

// Props
interface Props {
  modelValue: boolean
  componentIds: number[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'applied': []
}>()

// State
const $q = useQuasar()
const tagsToAdd = ref('')
const tagsToRemove = ref('')
const preview = ref<TagPreview[]>([])
const loadingPreview = ref(false)
const loadingApply = ref(false)

// Computed
const showDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const hasChanges = computed(() => {
  return tagsToAdd.value.trim().length > 0 || tagsToRemove.value.trim().length > 0
})

const previewColumns = [
  {
    name: 'component_name',
    label: 'Part',
    field: 'component_name',
    align: 'left' as const,
  },
  {
    name: 'current_user_tags',
    label: 'Current Tags',
    field: 'current_user_tags',
    align: 'left' as const,
  },
  {
    name: 'proposed_user_tags',
    label: 'Proposed Tags',
    field: 'proposed_user_tags',
    align: 'left' as const,
  },
]

// Methods
function parseTags(input: string): string[] {
  return input
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
}

async function loadPreview() {
  loadingPreview.value = true
  try {
    const addTags = parseTags(tagsToAdd.value)
    const removeTags = parseTags(tagsToRemove.value)

    const response = await bulkOperationsApi.previewTagChanges(
      props.componentIds,
      addTags,
      removeTags
    )

    preview.value = response.previews
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load preview',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  } finally {
    loadingPreview.value = false
  }
}

async function handleApply() {
  loadingApply.value = true
  try {
    const addTags = parseTags(tagsToAdd.value)
    const removeTags = parseTags(tagsToRemove.value)

    // Apply tag additions
    if (addTags.length > 0) {
      await bulkOperationsApi.bulkAddTags(props.componentIds, addTags)
    }

    // Apply tag removals
    if (removeTags.length > 0) {
      await bulkOperationsApi.bulkRemoveTags(props.componentIds, removeTags)
    }

    $q.notify({
      type: 'positive',
      message: 'Tags updated successfully',
    })

    emit('applied')
    handleCancel()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update tags',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  } finally {
    loadingApply.value = false
  }
}

function handleCancel() {
  tagsToAdd.value = ''
  tagsToRemove.value = ''
  preview.value = []
  showDialog.value = false
}
</script>
