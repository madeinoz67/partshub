<template>
  <div class="tag-selector">
    <q-select
      v-model="selectedTags"
      :options="searchOptions"
      multiple
      use-input
      use-chips
      input-debounce="300"
      :loading="loading"
      label="Tags"
      hint="Type to search tags or create new ones"
      @filter="filterTags"
      @new-value="createNewTag"
      behavior="menu"
      emit-value
      map-options
      option-value="id"
      option-label="name"
      clearable
    >
      <template v-slot:selected-item="scope">
        <q-chip
          removable
          dense
          :color="scope.opt.color || 'primary'"
          text-color="white"
          :label="scope.opt.name"
          @remove="scope.removeAtIndex(scope.index)"
        />
      </template>

      <template v-slot:option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section avatar>
            <q-icon
              :name="scope.opt.is_system_tag ? 'verified_user' : 'label'"
              :color="scope.opt.color || 'primary'"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ scope.opt.name }}</q-item-label>
            <q-item-label caption v-if="scope.opt.description">
              {{ scope.opt.description }}
            </q-item-label>
            <q-item-label caption v-if="scope.opt.component_count !== undefined">
              Used by {{ scope.opt.component_count }} components
            </q-item-label>
          </q-item-section>
          <q-item-section side v-if="scope.opt.is_system_tag">
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

      <template v-slot:no-option>
        <q-item>
          <q-item-section class="text-grey">
            No tags found
          </q-item-section>
        </q-item>
      </template>
    </q-select>

    <!-- New Tag Creation Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Create New Tag</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-input
            v-model="newTagForm.name"
            label="Tag Name"
            autofocus
            :rules="[val => !!val || 'Tag name is required']"
            ref="tagNameInput"
            @keyup.enter="confirmCreateTag"
          />

          <q-input
            v-model="newTagForm.description"
            label="Description (optional)"
            type="textarea"
            class="q-mt-md"
          />

          <div class="q-mt-md">
            <q-label>Color</q-label>
            <div class="row q-gutter-sm q-mt-xs">
              <q-btn
                v-for="color in colorOptions"
                :key="color.value"
                :color="color.value"
                size="sm"
                round
                :outline="newTagForm.color !== color.value"
                @click="newTagForm.color = color.value"
                :title="color.name"
              >
                <q-icon name="circle" v-if="newTagForm.color === color.value" />
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
            :loading="creatingTag"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { APIService, type Tag } from '../services/api'

interface Props {
  modelValue: string[]
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Data
const allTags = ref<Tag[]>([])
const filteredTags = ref<Tag[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creatingTag = ref(false)
const searchQuery = ref('')

// New tag form
const newTagForm = ref({
  name: '',
  description: '',
  color: 'primary'
})

// Color options for new tags
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
const selectedTags = computed({
  get: () => props.modelValue,
  set: (value: string[]) => emit('update:modelValue', value)
})

const searchOptions = computed(() => {
  const options = filteredTags.value.map(tag => ({
    ...tag,
    value: tag.id
  }))

  // If searching and no exact match found, show option to create new tag
  if (searchQuery.value && searchQuery.value.length >= 2) {
    const exactMatch = allTags.value.find(
      tag => tag.name.toLowerCase() === searchQuery.value.toLowerCase()
    )

    if (!exactMatch) {
      options.push({
        id: `create:${searchQuery.value}`,
        name: `Create "${searchQuery.value}"`,
        description: 'Create a new tag',
        color: 'accent',
        is_system_tag: false,
        component_count: 0,
        created_at: '',
        updated_at: '',
        value: `create:${searchQuery.value}`
      })
    }
  }

  return options
})

// Methods
const loadTags = async () => {
  loading.value = true
  try {
    const response = await APIService.getTags({ limit: 200 })
    allTags.value = response.tags
    filteredTags.value = response.tags
  } catch (error) {
    console.error('Failed to load tags:', error)
  } finally {
    loading.value = false
  }
}

const filterTags = (val: string, update: Function) => {
  searchQuery.value = val

  update(() => {
    if (val === '') {
      filteredTags.value = allTags.value
    } else {
      const needle = val.toLowerCase()
      filteredTags.value = allTags.value.filter(tag =>
        tag.name.toLowerCase().includes(needle) ||
        (tag.description && tag.description.toLowerCase().includes(needle))
      )
    }
  })
}

const createNewTag = (val: string) => {
  // Handle creation of new tag
  if (val.startsWith('create:')) {
    const tagName = val.replace('create:', '')
    newTagForm.value.name = tagName
    showCreateDialog.value = true
    return null // Prevent the option from being added immediately
  }
  return null
}

const confirmCreateTag = async () => {
  if (!newTagForm.value.name.trim()) return

  creatingTag.value = true
  try {
    const newTag = await APIService.createTag({
      name: newTagForm.value.name.trim(),
      description: newTagForm.value.description.trim() || undefined,
      color: newTagForm.value.color
    })

    // Add to local tags list
    allTags.value.push(newTag)
    filteredTags.value = allTags.value

    // Add to selected tags
    const currentTags = [...selectedTags.value]
    currentTags.push(newTag.id)
    emit('update:modelValue', currentTags)

    // Reset form and close dialog
    newTagForm.value = {
      name: '',
      description: '',
      color: 'primary'
    }
    showCreateDialog.value = false

  } catch (error) {
    console.error('Failed to create tag:', error)
  } finally {
    creatingTag.value = false
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

// Watch for changes in selected tags to handle the create option
watch(selectedTags, (newTags, oldTags) => {
  const createOptions = newTags.filter(tagId => typeof tagId === 'string' && tagId.startsWith('create:'))
  if (createOptions.length > 0) {
    const createOption = createOptions[0]
    const tagName = createOption.replace('create:', '')

    // Remove the create option from selection
    const filteredTags = newTags.filter(tagId => !tagId.startsWith('create:'))
    emit('update:modelValue', filteredTags)

    // Show create dialog
    newTagForm.value.name = tagName
    showCreateDialog.value = true
  }
})

// Lifecycle
onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.tag-selector {
  width: 100%;
}
</style>