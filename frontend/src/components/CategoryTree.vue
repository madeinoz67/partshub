<template>
  <div class="category-tree">
    <div class="row items-center q-mb-md">
      <div class="col">
        <h6 class="q-my-none">Categories</h6>
      </div>
      <div class="col-auto">
        <q-btn
          flat
          round
          dense
          icon="add"
          color="primary"
          :disable="loading"
          @click="showCreateDialog = true"
        >
          <q-tooltip>Add Category</q-tooltip>
        </q-btn>
        <q-btn
          flat
          round
          dense
          icon="refresh"
          color="primary"
          :loading="loading"
          @click="loadCategories"
        >
          <q-tooltip>Refresh</q-tooltip>
        </q-btn>
      </div>
    </div>

    <!-- Search and filter -->
    <q-input
      v-model="searchQuery"
      placeholder="Search categories..."
      outlined
      dense
      clearable
      class="q-mb-md"
    >
      <template #prepend>
        <q-icon name="search" />
      </template>
    </q-input>

    <!-- Category tree -->
    <q-tree
      :nodes="filteredNodes"
      node-key="id"
      default-expand-all
      :no-nodes-label="loading ? 'Loading...' : 'No categories found'"
      class="category-tree-nodes"
    >
      <template #default-header="prop">
        <div class="row items-center full-width">
          <div class="col">
            <div class="text-body2 text-weight-medium">
              {{ prop.node.name }}
            </div>
            <div
              v-if="prop.node.description"
              class="text-caption text-grey-6"
            >
              {{ prop.node.description }}
            </div>
          </div>

          <!-- Component count badge -->
          <div class="col-auto q-mr-sm">
            <q-badge
              :color="prop.node.component_count > 0 ? 'primary' : 'grey-5'"
              :label="prop.node.component_count"
            />
          </div>

          <!-- Actions -->
          <div class="col-auto">
            <q-btn-group flat>
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="add"
                color="primary"
                @click.stop="createSubcategory(prop.node)"
              >
                <q-tooltip>Add Subcategory</q-tooltip>
              </q-btn>
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="edit"
                color="primary"
                @click.stop="editCategory(prop.node)"
              >
                <q-tooltip>Edit Category</q-tooltip>
              </q-btn>
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="delete"
                color="negative"
                :disable="prop.node.children && prop.node.children.length > 0"
                @click.stop="deleteCategory(prop.node)"
              >
                <q-tooltip>
                  {{ prop.node.children && prop.node.children.length > 0
                     ? 'Cannot delete category with subcategories'
                     : 'Delete Category' }}
                </q-tooltip>
              </q-btn>
            </q-btn-group>
          </div>
        </div>
      </template>
    </q-tree>

    <!-- Create/Edit Category Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">
            {{ editingCategory ? 'Edit Category' : 'Create Category' }}
          </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form class="q-gutter-md" @submit="saveCategory">
            <q-input
              v-model="categoryForm.name"
              label="Category Name"
              outlined
              :rules="[val => !!val || 'Name is required']"
              autofocus
            />

            <q-input
              v-model="categoryForm.description"
              label="Description"
              outlined
              type="textarea"
              rows="3"
            />

            <q-select
              v-model="categoryForm.parent_id"
              :options="parentOptions"
              option-value="id"
              option-label="breadcrumb"
              label="Parent Category"
              outlined
              clearable
              emit-value
              map-options
            />

            <div class="row q-gutter-md">
              <div class="col">
                <q-input
                  v-model="categoryForm.color"
                  label="Color"
                  outlined
                >
                  <template #append>
                    <q-icon name="colorize" class="cursor-pointer">
                      <q-popup-proxy>
                        <q-color
                          v-model="categoryForm.color"
                          format-model="hex"
                        />
                      </q-popup-proxy>
                    </q-icon>
                  </template>
                </q-input>
              </div>
              <div class="col">
                <q-input
                  v-model="categoryForm.icon"
                  label="Icon"
                  outlined
                  placeholder="material-icons name"
                />
              </div>
            </div>

            <q-input
              v-model.number="categoryForm.sort_order"
              label="Sort Order"
              outlined
              type="number"
              min="0"
            />
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel"
            @click="cancelEdit"
          />
          <q-btn
            color="primary"
            label="Save"
            :loading="saving"
            @click="saveCategory"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section>
          <div class="text-h6">Delete Category</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <p>Are you sure you want to delete "{{ deletingCategory?.name }}"?</p>

          <div v-if="deletingCategory?.component_count > 0" class="q-mt-md">
            <q-banner class="bg-warning text-dark">
              <template #avatar>
                <q-icon name="warning" />
              </template>
              This category has {{ deletingCategory.component_count }} components.
              They will need to be reassigned to another category.
            </q-banner>

            <q-select
              v-model="reassignToCategory"
              :options="reassignmentOptions"
              option-value="id"
              option-label="breadcrumb"
              label="Reassign components to"
              outlined
              class="q-mt-md"
              emit-value
              map-options
              :rules="[val => !!val || 'Must select a category for reassignment']"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel"
            @click="cancelDelete"
          />
          <q-btn
            color="negative"
            label="Delete"
            :loading="deleting"
            :disable="deletingCategory?.component_count > 0 && !reassignToCategory"
            @click="confirmDelete"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

export default defineComponent({
  name: 'CategoryTree',

  emits: ['category-selected', 'category-updated'],

  setup(props, { emit }) {
    const $q = useQuasar()

    // Data
    const categories = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const deleting = ref(false)
    const searchQuery = ref('')

    // Dialog states
    const showCreateDialog = ref(false)
    const showDeleteDialog = ref(false)
    const editingCategory = ref(null)
    const deletingCategory = ref(null)
    const reassignToCategory = ref(null)

    // Form data
    const categoryForm = ref({
      name: '',
      description: '',
      parent_id: null,
      color: '#1976d2',
      icon: '',
      sort_order: 0
    })

    // Computed
    const filteredNodes = computed(() => {
      if (!searchQuery.value) return categories.value

      const filterNodes = (nodes) => {
        return nodes.filter(node => {
          const matchesSearch = node.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                               (node.description && node.description.toLowerCase().includes(searchQuery.value.toLowerCase()))

          if (matchesSearch) return true

          // Check if any children match
          if (node.children) {
            const filteredChildren = filterNodes(node.children)
            return filteredChildren.length > 0
          }

          return false
        }).map(node => ({
          ...node,
          children: node.children ? filterNodes(node.children) : []
        }))
      }

      return filterNodes(categories.value)
    })

    const parentOptions = computed(() => {
      const flattenCategories = (cats, prefix = '') => {
        const result = []
        for (const cat of cats) {
          if (!editingCategory.value || cat.id !== editingCategory.value.id) {
            result.push({
              id: cat.id,
              breadcrumb: prefix + cat.name
            })
            if (cat.children) {
              result.push(...flattenCategories(cat.children, prefix + cat.name + ' > '))
            }
          }
        }
        return result
      }
      return flattenCategories(categories.value)
    })

    const reassignmentOptions = computed(() => {
      return parentOptions.value.filter(opt =>
        opt.id !== deletingCategory.value?.id
      )
    })

    // Methods
    const loadCategories = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/v1/categories?hierarchy=true')
        categories.value = response.data
      } catch (error) {
        $q.notify({
          type: 'negative',
          message: 'Failed to load categories'
        })
        console.error('Error loading categories:', error)
      } finally {
        loading.value = false
      }
    }

    const resetForm = () => {
      categoryForm.value = {
        name: '',
        description: '',
        parent_id: null,
        color: '#1976d2',
        icon: '',
        sort_order: 0
      }
    }

    const createSubcategory = (parentNode) => {
      resetForm()
      categoryForm.value.parent_id = parentNode.id
      editingCategory.value = null
      showCreateDialog.value = true
    }

    const editCategory = (node) => {
      editingCategory.value = node
      categoryForm.value = {
        name: node.name,
        description: node.description || '',
        parent_id: node.parent_id,
        color: node.color || '#1976d2',
        icon: node.icon || '',
        sort_order: node.sort_order || 0
      }
      showCreateDialog.value = true
    }

    const cancelEdit = () => {
      showCreateDialog.value = false
      editingCategory.value = null
      resetForm()
    }

    const saveCategory = async () => {
      saving.value = true
      try {
        if (editingCategory.value) {
          // Update existing category
          await axios.put(`/api/v1/categories/${editingCategory.value.id}`, categoryForm.value)
          $q.notify({
            type: 'positive',
            message: 'Category updated successfully'
          })
        } else {
          // Create new category
          await axios.post('/api/v1/categories', categoryForm.value)
          $q.notify({
            type: 'positive',
            message: 'Category created successfully'
          })
        }

        showCreateDialog.value = false
        editingCategory.value = null
        resetForm()
        await loadCategories()
        emit('category-updated')
      } catch (error) {
        $q.notify({
          type: 'negative',
          message: error.response?.data?.detail || 'Failed to save category'
        })
        console.error('Error saving category:', error)
      } finally {
        saving.value = false
      }
    }

    const deleteCategory = (node) => {
      deletingCategory.value = node
      reassignToCategory.value = null
      showDeleteDialog.value = true
    }

    const cancelDelete = () => {
      showDeleteDialog.value = false
      deletingCategory.value = null
      reassignToCategory.value = null
    }

    const confirmDelete = async () => {
      deleting.value = true
      try {
        const params = {}
        if (deletingCategory.value.component_count > 0) {
          params.force = true
          params.reassign_to = reassignToCategory.value
        }

        await axios.delete(`/api/v1/categories/${deletingCategory.value.id}`, { params })

        $q.notify({
          type: 'positive',
          message: 'Category deleted successfully'
        })

        showDeleteDialog.value = false
        deletingCategory.value = null
        reassignToCategory.value = null
        await loadCategories()
        emit('category-updated')
      } catch (error) {
        $q.notify({
          type: 'negative',
          message: error.response?.data?.detail || 'Failed to delete category'
        })
        console.error('Error deleting category:', error)
      } finally {
        deleting.value = false
      }
    }

    // Lifecycle
    onMounted(() => {
      loadCategories()
    })

    return {
      // Data
      categories,
      loading,
      saving,
      deleting,
      searchQuery,
      showCreateDialog,
      showDeleteDialog,
      editingCategory,
      deletingCategory,
      reassignToCategory,
      categoryForm,

      // Computed
      filteredNodes,
      parentOptions,
      reassignmentOptions,

      // Methods
      loadCategories,
      createSubcategory,
      editCategory,
      cancelEdit,
      saveCategory,
      deleteCategory,
      cancelDelete,
      confirmDelete
    }
  }
})
</script>

<style scoped>
.category-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.category-tree-nodes {
  flex: 1;
  overflow: auto;
}

.category-tree-nodes .q-tree__node-header {
  padding: 8px 4px;
}

.category-tree-nodes .q-tree__node-header:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
</style>