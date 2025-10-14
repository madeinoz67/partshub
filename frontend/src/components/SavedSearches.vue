<template>
  <div class="saved-searches">
    <!-- Loading State -->
    <div v-if="loading && !searches.length" class="text-center q-pa-lg">
      <q-spinner color="primary" size="3em" />
      <div class="text-body2 text-grey-6 q-mt-md">Loading saved searches...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && searches.length === 0" class="text-center q-pa-lg">
      <q-icon name="bookmark_border" size="4em" color="grey-5" />
      <div class="text-h6 q-mt-md text-grey-6">No saved searches yet</div>
      <div class="text-body2 text-grey-5 q-mt-sm">
        Save your searches for quick access later
      </div>
    </div>

    <!-- Searches List -->
    <div v-else>
      <!-- Sorting Controls (for non-compact mode) -->
      <div v-if="!compact" class="row items-center q-mb-md">
        <div class="text-subtitle2 text-grey-7 q-mr-md">Sort by:</div>
        <q-btn-group flat>
          <q-btn
            label="Name"
            :color="sortBy === 'name' ? 'primary' : 'grey-6'"
            flat
            dense
            @click="changeSorting('name')"
          />
          <q-btn
            label="Created"
            :color="sortBy === 'created_at' ? 'primary' : 'grey-6'"
            flat
            dense
            @click="changeSorting('created_at')"
          />
          <q-btn
            label="Last Used"
            :color="sortBy === 'last_used_at' ? 'primary' : 'grey-6'"
            flat
            dense
            @click="changeSorting('last_used_at')"
          />
        </q-btn-group>
        <q-btn
          :icon="sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward'"
          flat
          dense
          round
          color="grey-7"
          @click="toggleSortOrder"
        >
          <q-tooltip>{{ sortOrder === 'asc' ? 'Ascending' : 'Descending' }}</q-tooltip>
        </q-btn>
      </div>

      <!-- Compact List (for dropdown) -->
      <q-list v-if="compact" separator>
        <q-item
          v-for="search in searches"
          :key="search.id"
          clickable
          @click="$emit('execute', search.id)"
        >
          <q-item-section>
            <q-item-label>{{ search.name }}</q-item-label>
            <q-item-label caption v-if="search.description">
              {{ search.description }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-icon name="play_arrow" color="primary" />
          </q-item-section>
        </q-item>
        <q-item v-if="total > searches.length" clickable @click="$emit('view-all')">
          <q-item-section>
            <q-item-label class="text-primary text-center">
              View all {{ total }} searches
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <!-- Full List (for page view) -->
      <q-list v-else bordered separator>
        <q-item
          v-for="search in searches"
          :key="search.id"
          class="q-pa-md"
        >
          <q-item-section>
            <q-item-label class="text-weight-medium">
              {{ search.name }}
            </q-item-label>
            <q-item-label caption v-if="search.description" class="q-mt-xs">
              {{ search.description }}
            </q-item-label>
            <div class="row q-gutter-sm q-mt-sm">
              <q-chip
                v-if="search.created_at"
                size="sm"
                dense
                icon="event"
              >
                Created: {{ formatDate(search.created_at) }}
              </q-chip>
              <q-chip
                v-if="search.last_used_at"
                size="sm"
                dense
                icon="history"
                color="primary"
                text-color="white"
              >
                Used: {{ formatDate(search.last_used_at) }}
              </q-chip>
            </div>
          </q-item-section>

          <q-item-section side>
            <div class="row q-gutter-xs">
              <q-btn
                icon="play_arrow"
                color="primary"
                flat
                round
                dense
                @click="$emit('execute', search.id)"
              >
                <q-tooltip>Execute search</q-tooltip>
              </q-btn>
              <q-btn
                icon="edit"
                color="grey-7"
                flat
                round
                dense
                @click="handleEdit(search)"
              >
                <q-tooltip>Edit name/description</q-tooltip>
              </q-btn>
              <q-btn
                icon="content_copy"
                color="grey-7"
                flat
                round
                dense
                @click="handleDuplicate(search.id)"
              >
                <q-tooltip>Duplicate</q-tooltip>
              </q-btn>
              <q-btn
                icon="delete"
                color="negative"
                flat
                round
                dense
                @click="handleDeleteConfirm(search)"
              >
                <q-tooltip>Delete</q-tooltip>
              </q-btn>
            </div>
          </q-item-section>
        </q-item>
      </q-list>

      <!-- Pagination (for non-compact mode) -->
      <div v-if="!compact && total > limit" class="q-mt-md flex flex-center">
        <q-pagination
          v-model="currentPage"
          :max="totalPages"
          :max-pages="7"
          boundary-numbers
          direction-links
          @update:model-value="loadSearches"
        />
      </div>
    </div>

    <!-- Edit Dialog -->
    <q-dialog v-model="showEditDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Edit Saved Search</div>
        </q-card-section>

        <q-card-section>
          <q-form ref="editFormRef" @submit="handleSaveEdit">
            <div class="q-gutter-md">
              <q-input
                v-model="editForm.name"
                label="Search Name *"
                outlined
                dense
                :rules="[
                  val => !!val || 'Name is required',
                  val => val.length >= 1 || 'Name must be at least 1 character',
                  val => val.length <= 100 || 'Name must be less than 100 characters'
                ]"
                counter
                maxlength="100"
              />
              <q-input
                v-model="editForm.description"
                label="Description (Optional)"
                outlined
                dense
                type="textarea"
                rows="3"
                counter
                maxlength="500"
              />
            </div>
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            label="Cancel"
            color="grey"
            flat
            :disable="updating"
            @click="showEditDialog = false"
          />
          <q-btn
            label="Save"
            color="primary"
            :loading="updating"
            @click="handleSaveEdit"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog">
      <q-card>
        <q-card-section class="row items-center">
          <q-icon name="warning" color="warning" size="3em" class="q-mr-md" />
          <div>
            <div class="text-h6">Delete Saved Search?</div>
            <div class="text-body2 q-mt-sm">
              Are you sure you want to delete "<strong>{{ deleteTarget?.name }}</strong>"?
            </div>
            <div class="text-caption text-grey-7 q-mt-xs">This action cannot be undone.</div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            label="Cancel"
            color="grey"
            flat
            :disable="deleting"
            @click="showDeleteDialog = false"
          />
          <q-btn
            label="Delete"
            color="negative"
            :loading="deleting"
            @click="handleDelete"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import {
  listSavedSearches,
  updateSavedSearch,
  deleteSavedSearch,
  duplicateSavedSearch
} from '../services/savedSearchesService'

export default {
  name: 'SavedSearches',
  props: {
    compact: {
      type: Boolean,
      default: false
    },
    maxItems: {
      type: Number,
      default: 5
    }
  },
  emits: ['execute', 'view-all', 'updated'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const searches = ref([])
    const total = ref(0)
    const loading = ref(false)
    const sortBy = ref('created_at')
    const sortOrder = ref('desc')
    const currentPage = ref(1)
    const limit = computed(() => props.compact ? props.maxItems : 20)

    // Edit state
    const showEditDialog = ref(false)
    const editFormRef = ref(null)
    const editTarget = ref(null)
    const editForm = ref({
      name: '',
      description: ''
    })
    const updating = ref(false)

    // Delete state
    const showDeleteDialog = ref(false)
    const deleteTarget = ref(null)
    const deleting = ref(false)

    const totalPages = computed(() => Math.ceil(total.value / limit.value))

    const loadSearches = async () => {
      loading.value = true
      try {
        const skip = (currentPage.value - 1) * limit.value
        const response = await listSavedSearches({
          skip,
          limit: limit.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value
        })
        searches.value = response.searches
        total.value = response.total
      } catch (error) {
        console.error('Error loading saved searches:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load saved searches',
          timeout: 3000
        })
      } finally {
        loading.value = false
      }
    }

    const changeSorting = (field) => {
      if (sortBy.value === field) {
        sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortBy.value = field
        sortOrder.value = 'desc'
      }
      currentPage.value = 1
      loadSearches()
    }

    const toggleSortOrder = () => {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
      loadSearches()
    }

    const handleEdit = (search) => {
      editTarget.value = search
      editForm.value = {
        name: search.name,
        description: search.description || ''
      }
      showEditDialog.value = true
    }

    const handleSaveEdit = async () => {
      const isValid = await editFormRef.value.validate()
      if (!isValid) return

      updating.value = true
      try {
        await updateSavedSearch(editTarget.value.id, {
          name: editForm.value.name.trim(),
          description: editForm.value.description.trim() || null
        })

        $q.notify({
          type: 'positive',
          message: 'Search updated successfully',
          timeout: 2000
        })

        showEditDialog.value = false
        loadSearches()
        emit('updated')
      } catch (error) {
        console.error('Error updating search:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to update search',
          timeout: 3000
        })
      } finally {
        updating.value = false
      }
    }

    const handleDuplicate = async (searchId) => {
      try {
        const duplicated = await duplicateSavedSearch(searchId)
        $q.notify({
          type: 'positive',
          message: 'Search duplicated successfully',
          caption: duplicated.name,
          timeout: 3000,
          icon: 'content_copy'
        })
        loadSearches()
        emit('updated')
      } catch (error) {
        console.error('Error duplicating search:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to duplicate search',
          timeout: 3000
        })
      }
    }

    const handleDeleteConfirm = (search) => {
      deleteTarget.value = search
      showDeleteDialog.value = true
    }

    const handleDelete = async () => {
      deleting.value = true
      try {
        await deleteSavedSearch(deleteTarget.value.id)
        $q.notify({
          type: 'positive',
          message: 'Search deleted successfully',
          timeout: 2000
        })
        showDeleteDialog.value = false
        loadSearches()
        emit('updated')
      } catch (error) {
        console.error('Error deleting search:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to delete search',
          timeout: 3000
        })
      } finally {
        deleting.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      return date.toLocaleDateString()
    }

    onMounted(() => {
      loadSearches()
    })

    return {
      searches,
      total,
      loading,
      sortBy,
      sortOrder,
      currentPage,
      limit,
      totalPages,
      showEditDialog,
      editFormRef,
      editForm,
      updating,
      showDeleteDialog,
      deleteTarget,
      deleting,
      loadSearches,
      changeSorting,
      toggleSortOrder,
      handleEdit,
      handleSaveEdit,
      handleDuplicate,
      handleDeleteConfirm,
      handleDelete,
      formatDate
    }
  }
}
</script>

<style scoped>
.saved-searches {
  width: 100%;
}
</style>
