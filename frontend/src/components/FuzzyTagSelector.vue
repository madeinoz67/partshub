<script setup lang="ts">
/**
 * FuzzyTagSelector Component
 * Tag selector with fuzzy search and ability to create new tags
 */

import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { APIService } from '../services/api'

interface Tag {
  id: string
  name: string
  description?: string | null
  color?: string | null
  is_system_tag?: boolean
  component_count?: number
  score?: number
}

interface Props {
  modelValue: string[]
  label?: string
  placeholder?: string
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Tags',
  placeholder: 'Start typing to search tags...'
})

const emit = defineEmits<Emits>()
const $q = useQuasar()

// State
const searchResults = ref<Tag[]>([])
const selectedTags = ref<Tag[]>([])
const isLoading = ref(false)
const showCreateDialog = ref(false)
const pendingTagName = ref('')

// New tag form
const newTagForm = ref({
  name: '',
  description: '',
  color: 'primary'
})

// Color options
const colorOptions = [
  { name: 'Primary', value: 'primary' },
  { name: 'Secondary', value: 'secondary' },
  { name: 'Accent', value: 'accent' },
  { name: 'Positive', value: 'positive' },
  { name: 'Negative', value: 'negative' },
  { name: 'Info', value: 'info' },
  { name: 'Warning', value: 'warning' },
  { name: 'Purple', value: 'purple' },
  { name: 'Pink', value: 'pink' },
  { name: 'Orange', value: 'orange' },
]

// Computed
const internalValue = computed({
  get: () => props.modelValue,
  set: (value: string[]) => emit('update:modelValue', value)
})

// Methods
const searchTags = async (val: string, update: (callback: () => void) => void) => {
  if (!val || val.length < 1) {
    update(() => {
      searchResults.value = []
    })
    return
  }

  isLoading.value = true

  try {
    const response = await fetch(
      `/api/wizard/tags/search?query=${encodeURIComponent(val)}&limit=20`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (!response.ok) throw new Error('Search failed')

    const results = await response.json()

    update(() => {
      searchResults.value = results
    })
  } catch (error) {
    console.error('Tag search failed:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to search tags',
      position: 'top'
    })
  } finally {
    isLoading.value = false
  }
}

const onTagsSelected = async (tagIds: string[]) => {
  // Load full tag data for newly selected tags
  const newTagIds = tagIds.filter(id => !selectedTags.value.find(t => t.id === id))

  if (newTagIds.length > 0) {
    for (const tagId of newTagIds) {
      const existingTag = searchResults.value.find(t => t.id === tagId)
      if (existingTag && !selectedTags.value.find(t => t.id === tagId)) {
        selectedTags.value.push(existingTag)
      }
    }
  }

  // Remove deselected tags
  selectedTags.value = selectedTags.value.filter(t => tagIds.includes(t.id))

  emit('update:modelValue', tagIds)
}

const createNewTag = (val: string) => {
  if (!val || val.length < 2) return

  pendingTagName.value = val
  newTagForm.value.name = val
  showCreateDialog.value = true
}

const confirmCreateTag = async () => {
  if (!newTagForm.value.name.trim()) return

  try {
    const newTag = await APIService.createTag({
      name: newTagForm.value.name.trim(),
      description: newTagForm.value.description.trim() || undefined,
      color: newTagForm.value.color
    })

    // Add to selected tags
    selectedTags.value.push(newTag)
    const currentTags = [...internalValue.value, newTag.id]
    emit('update:modelValue', currentTags)

    // Reset and close
    newTagForm.value = {
      name: '',
      description: '',
      color: 'primary'
    }
    showCreateDialog.value = false

    $q.notify({
      type: 'positive',
      message: `Tag "${newTag.name}" created successfully`,
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to create tag:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to create tag',
      position: 'top'
    })
  }
}

const cancelCreateTag = () => {
  newTagForm.value = {
    name: '',
    description: '',
    color: 'primary'
  }
  showCreateDialog.value = false
}
</script>

<template>
  <div class="fuzzy-tag-selector">
    <q-select
      :model-value="internalValue"
      :options="searchResults"
      :label="label"
      :placeholder="placeholder"
      :loading="isLoading"
      multiple
      use-input
      use-chips
      input-debounce="300"
      option-value="id"
      option-label="name"
      emit-value
      map-options
      clearable
      @filter="searchTags"
      @update:model-value="onTagsSelected"
      @new-value="createNewTag"
    >
      <template #prepend>
        <q-icon name="label" />
      </template>

      <template #selected-item="scope">
        <q-chip
          removable
          dense
          :color="scope.opt.color || 'primary'"
          text-color="white"
          :label="scope.opt.name"
          @remove="scope.removeAtIndex(scope.index)"
        />
      </template>

      <template #option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section avatar>
            <q-icon
              :name="scope.opt.is_system_tag ? 'verified_user' : 'label'"
              :color="scope.opt.color || 'primary'"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ scope.opt.name }}</q-item-label>
            <q-item-label v-if="scope.opt.description" caption>
              {{ scope.opt.description }}
            </q-item-label>
            <q-item-label v-if="scope.opt.component_count !== undefined" caption>
              Used by {{ scope.opt.component_count }} components
            </q-item-label>
          </q-item-section>
          <q-item-section v-if="scope.opt.is_system_tag" side>
            <q-chip
              dense
              color="info"
              text-color="white"
              label="System"
              size="sm"
            />
          </q-item-section>
        </q-item>
      </template>

      <template #no-option>
        <q-item>
          <q-item-section class="text-grey-7">
            <div>No tags found</div>
            <div class="text-caption">Type to create a new tag</div>
          </q-item-section>
        </q-item>
      </template>

      <template #hint>
        Type to search tags or press Enter to create new
      </template>
    </q-select>

    <!-- Create New Tag Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Create New Tag</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-input
            v-model="newTagForm.name"
            label="Tag Name *"
            autofocus
            :rules="[val => !!val || 'Tag name is required']"
            @keyup.enter="confirmCreateTag"
          />

          <q-input
            v-model="newTagForm.description"
            label="Description (optional)"
            type="textarea"
            rows="3"
            class="q-mt-md"
          />

          <div class="q-mt-md">
            <div class="text-caption q-mb-xs">Color</div>
            <div class="row q-gutter-sm q-mt-xs">
              <q-btn
                v-for="color in colorOptions"
                :key="color.value"
                :color="color.value"
                size="sm"
                round
                :outline="newTagForm.color !== color.value"
                :title="color.name"
                @click="newTagForm.color = color.value"
              >
                <q-icon v-if="newTagForm.color === color.value" name="circle" />
              </q-btn>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="cancelCreateTag" />
          <q-btn
            flat
            label="Create"
            color="primary"
            @click="confirmCreateTag"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<style scoped>
.fuzzy-tag-selector {
  width: 100%;
}
</style>
