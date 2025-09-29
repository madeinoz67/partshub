<template>
  <q-select
    v-model="selectedCategory"
    :options="filteredOptions"
    option-value="id"
    option-label="breadcrumb"
    :label="label"
    :outlined="outlined"
    :filled="filled"
    :dense="dense"
    :clearable="clearable"
    :disable="disable"
    :loading="loading"
    :error="error"
    :error-message="errorMessage"
    :hint="hint"
    :rules="rules"
    emit-value
    map-options
    use-input
    input-debounce="300"
    @filter="filterFn"
    @input-value="onInputValue"
    @update:model-value="onUpdateValue"
  >
    <template v-if="prependIcon" #prepend>
      <q-icon :name="prependIcon" />
    </template>

    <template v-if="showCreateButton && canCreate" #append>
      <q-btn
        flat
        round
        dense
        icon="add"
        color="primary"
        :disable="disable || loading"
        @click.stop="createNewCategory"
      >
        <q-tooltip>Create new category</q-tooltip>
      </q-btn>
    </template>

    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section v-if="scope.opt.icon" avatar>
          <q-icon
            :name="scope.opt.icon"
            :color="scope.opt.color || 'primary'"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ scope.opt.name }}</q-item-label>
          <q-item-label caption>{{ scope.opt.breadcrumb }}</q-item-label>
        </q-item-section>
        <q-item-section v-if="scope.opt.component_count !== undefined" side>
          <q-badge
            :color="scope.opt.component_count > 0 ? 'primary' : 'grey-5'"
            :label="scope.opt.component_count"
          />
        </q-item-section>
      </q-item>
    </template>

    <template #no-option>
      <q-item>
        <q-item-section class="text-grey">
          <div v-if="searchInput && canCreate" class="text-center">
            No matching categories found.
            <q-btn
              flat
              color="primary"
              :label="`Create '${searchInput}'`"
              class="q-mt-sm"
              @click="createCategoryFromSearch"
            />
          </div>
          <div v-else>
            No categories available
          </div>
        </q-item-section>
      </q-item>
    </template>

    <template v-if="selectedCategoryData" #selected-item="scope">
      <div class="row items-center q-gutter-xs no-wrap">
        <q-icon
          v-if="selectedCategoryData.icon"
          :name="selectedCategoryData.icon"
          :color="selectedCategoryData.color || 'primary'"
          size="18px"
        />
        <span>{{ selectedCategoryData.name }}</span>
        <span v-if="selectedCategoryData.breadcrumb !== selectedCategoryData.name" class="text-caption text-grey-6">
          ({{ selectedCategoryData.breadcrumb }})
        </span>
      </div>
    </template>
  </q-select>

  <!-- Create Category Dialog -->
  <q-dialog v-model="showCreateDialog" persistent>
    <q-card style="min-width: 400px">
      <q-card-section>
        <div class="text-h6">Create New Category</div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <CategoryForm
          :parent-id="suggestedParentId"
          @success="onCategoryCreated"
          @cancel="showCreateDialog = false"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script>
import { defineComponent, ref, computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'
import CategoryForm from './CategoryForm.vue'

export default defineComponent({
  name: 'CategorySelector',

  components: {
    CategoryForm
  },

  props: {
    modelValue: {
      type: [String, null],
      default: null
    },
    label: {
      type: String,
      default: 'Category'
    },
    outlined: {
      type: Boolean,
      default: true
    },
    filled: {
      type: Boolean,
      default: false
    },
    dense: {
      type: Boolean,
      default: false
    },
    clearable: {
      type: Boolean,
      default: true
    },
    disable: {
      type: Boolean,
      default: false
    },
    error: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    },
    hint: {
      type: String,
      default: ''
    },
    rules: {
      type: Array,
      default: () => []
    },
    prependIcon: {
      type: String,
      default: 'category'
    },
    showCreateButton: {
      type: Boolean,
      default: true
    },
    canCreate: {
      type: Boolean,
      default: true
    },
    includeEmpty: {
      type: Boolean,
      default: true
    },
    suggestedParentId: {
      type: String,
      default: null
    }
  },

  emits: ['update:model-value', 'category-created'],

  setup(props, { emit }) {
    const $q = useQuasar()

    // Data
    const categories = ref([])
    const loading = ref(false)
    const searchInput = ref('')
    const filteredOptions = ref([])
    const showCreateDialog = ref(false)

    // Computed
    const selectedCategory = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:model-value', value)
    })

    const selectedCategoryData = computed(() => {
      if (!selectedCategory.value) return null
      return allCategoriesFlat.value.find(cat => cat.id === selectedCategory.value)
    })

    const allCategoriesFlat = computed(() => {
      const flattenCategories = (cats, prefix = '', depth = 0) => {
        const result = []
        for (const cat of cats) {
          result.push({
            id: cat.id,
            name: cat.name,
            description: cat.description,
            icon: cat.icon,
            color: cat.color,
            component_count: cat.component_count,
            breadcrumb: prefix ? `${prefix} > ${cat.name}` : cat.name,
            depth: depth
          })
          if (cat.children) {
            result.push(...flattenCategories(cat.children, result[result.length - 1].breadcrumb, depth + 1))
          }
        }
        return result
      }
      return flattenCategories(categories.value)
    })

    // Methods
    const loadCategories = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/v1/categories?hierarchy=true&include_empty=' + props.includeEmpty)
        categories.value = response.data
        updateFilteredOptions()
      } catch (error) {
        console.error('Error loading categories:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load categories'
        })
      } finally {
        loading.value = false
      }
    }

    const updateFilteredOptions = () => {
      filteredOptions.value = allCategoriesFlat.value
    }

    const filterFn = (val, update) => {
      update(() => {
        if (val === '') {
          filteredOptions.value = allCategoriesFlat.value
        } else {
          const needle = val.toLowerCase()
          filteredOptions.value = allCategoriesFlat.value.filter(cat => {
            return cat.name.toLowerCase().includes(needle) ||
                   (cat.description && cat.description.toLowerCase().includes(needle)) ||
                   cat.breadcrumb.toLowerCase().includes(needle)
          })
        }
      })
    }

    const onInputValue = (val) => {
      searchInput.value = val
    }

    const onUpdateValue = (value) => {
      selectedCategory.value = value
    }

    const createNewCategory = () => {
      showCreateDialog.value = true
    }

    const createCategoryFromSearch = () => {
      // Pre-fill the form with the search input as the name
      showCreateDialog.value = true
      // Note: We could emit an event with the suggested name if CategoryForm supported it
    }

    const onCategoryCreated = (newCategory) => {
      showCreateDialog.value = false

      // Reload categories to include the new one
      loadCategories().then(() => {
        // Auto-select the newly created category
        selectedCategory.value = newCategory.id
        emit('category-created', newCategory)

        $q.notify({
          type: 'positive',
          message: `Category "${newCategory.name}" created and selected`
        })
      })
    }

    // Watchers
    watch(() => props.includeEmpty, loadCategories)

    // Lifecycle
    onMounted(() => {
      loadCategories()
    })

    return {
      // Data
      loading,
      searchInput,
      filteredOptions,
      showCreateDialog,

      // Computed
      selectedCategory,
      selectedCategoryData,

      // Methods
      filterFn,
      onInputValue,
      onUpdateValue,
      createNewCategory,
      createCategoryFromSearch,
      onCategoryCreated,
      loadCategories
    }
  }
})
</script>

<style scoped>
/* Custom styles for better visual hierarchy */
.q-item__section--avatar {
  min-width: 32px;
}

.q-item__label--caption {
  font-size: 11px;
  opacity: 0.7;
}
</style>