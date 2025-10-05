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
          <TagSelector v-model="tagsToAddIds" />
        </div>

        <!-- Remove Tags Section -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm">Remove Tags</div>
          <TagSelector v-model="tagsToRemoveIds" />
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
            <template #body-cell-current_tags="props">
              <q-td :props="props">
                <q-chip
                  v-for="tag in props.row.current_tags"
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
            <template #body-cell-resulting_tags="props">
              <q-td :props="props">
                <q-chip
                  v-for="tag in props.row.resulting_tags"
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
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { bulkOperationsApi, type TagPreview } from '../services/bulkOperationsApi'
import { APIService, type Tag } from '../services/api'
import TagSelector from './TagSelector.vue'

// Props
interface Props {
  modelValue: boolean
  componentIds: string[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'applied': []
}>()

// State
const $q = useQuasar()
const allTags = ref<Tag[]>([])
const tagsToAddIds = ref<string[]>([])
const tagsToRemoveIds = ref<string[]>([])
const preview = ref<TagPreview[]>([])
const loadingPreview = ref(false)
const loadingApply = ref(false)

// Load all tags on mount
onMounted(async () => {
  try {
    const response = await APIService.getTags()
    allTags.value = response.tags
  } catch (error) {
    console.error('Failed to load tags:', error)
  }
})

// Computed
const showDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const hasChanges = computed(() => {
  return tagsToAddIds.value.length > 0 || tagsToRemoveIds.value.length > 0
})

const previewColumns = [
  {
    name: 'component_name',
    label: 'Part',
    field: 'component_name',
    align: 'left' as const,
  },
  {
    name: 'current_tags',
    label: 'Current Tags',
    field: 'current_tags',
    align: 'left' as const,
  },
  {
    name: 'resulting_tags',
    label: 'Resulting Tags',
    field: 'resulting_tags',
    align: 'left' as const,
  },
]

// Methods
function convertTagIdsToNames(tagIds: string[]): string[] {
  return tagIds
    .map(id => allTags.value.find(tag => tag.id === id)?.name)
    .filter((name): name is string => name !== undefined)
}

async function loadPreview() {
  loadingPreview.value = true
  try {
    const addTagNames = convertTagIdsToNames(tagsToAddIds.value)
    const removeTagNames = convertTagIdsToNames(tagsToRemoveIds.value)

    const response = await bulkOperationsApi.previewTagChanges(
      props.componentIds,
      addTagNames,
      removeTagNames
    )

    preview.value = response.components
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
    const addTagNames = convertTagIdsToNames(tagsToAddIds.value)
    const removeTagNames = convertTagIdsToNames(tagsToRemoveIds.value)

    // Apply tag additions
    if (addTagNames.length > 0) {
      await bulkOperationsApi.bulkAddTags(props.componentIds, addTagNames)
    }

    // Apply tag removals
    if (removeTagNames.length > 0) {
      await bulkOperationsApi.bulkRemoveTags(props.componentIds, removeTagNames)
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
  tagsToAddIds.value = []
  tagsToRemoveIds.value = []
  preview.value = []
  showDialog.value = false
}
</script>
