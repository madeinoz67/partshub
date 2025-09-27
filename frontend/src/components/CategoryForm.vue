<template>
  <q-form @submit="onSubmit" class="q-gutter-md">
    <div class="text-h6 q-mb-md">
      {{ isEditing ? 'Edit Category' : 'Create Category' }}
    </div>

    <!-- Name field -->
    <q-input
      v-model="form.name"
      label="Category Name *"
      outlined
      :rules="[
        val => !!val || 'Name is required',
        val => val.length <= 100 || 'Name must be 100 characters or less'
      ]"
      maxlength="100"
      counter
      autofocus
    />

    <!-- Description field -->
    <q-input
      v-model="form.description"
      label="Description"
      outlined
      type="textarea"
      rows="3"
      hint="Optional description for this category"
    />

    <!-- Parent category selection -->
    <q-select
      v-model="form.parent_id"
      :options="parentOptions"
      option-value="id"
      option-label="breadcrumb"
      label="Parent Category"
      outlined
      clearable
      emit-value
      map-options
      hint="Leave empty to create a top-level category"
      :loading="loadingParents"
    >
      <template v-slot:no-option>
        <q-item>
          <q-item-section class="text-grey">
            No parent categories available
          </q-item-section>
        </q-item>
      </template>
    </q-select>

    <!-- Visual properties -->
    <div class="row q-gutter-md">
      <div class="col">
        <q-input
          v-model="form.color"
          label="Color"
          outlined
          :rules="[
            val => !val || /^#[0-9A-Fa-f]{6}$/.test(val) || 'Invalid hex color format'
          ]"
          hint="Hex color code (e.g., #1976d2)"
        >
          <template v-slot:append>
            <q-icon name="colorize" class="cursor-pointer">
              <q-popup-proxy>
                <q-color
                  v-model="form.color"
                  format-model="hex"
                  no-header
                  no-footer
                />
              </q-popup-proxy>
            </q-icon>
          </template>
          <template v-slot:prepend>
            <q-avatar
              v-if="form.color"
              size="24px"
              :style="{ backgroundColor: form.color }"
            />
          </template>
        </q-input>
      </div>

      <div class="col">
        <q-input
          v-model="form.icon"
          label="Icon"
          outlined
          :rules="[
            val => !val || val.length <= 50 || 'Icon name must be 50 characters or less'
          ]"
          hint="Material Icons name (e.g., category, inventory)"
        >
          <template v-slot:append>
            <q-icon
              v-if="form.icon"
              :name="form.icon"
              class="text-grey-6"
            />
          </template>
        </q-input>
      </div>
    </div>

    <!-- Sort order -->
    <q-input
      v-model.number="form.sort_order"
      label="Sort Order"
      outlined
      type="number"
      min="0"
      step="1"
      hint="Lower numbers appear first within the same parent"
    />

    <!-- Preview section -->
    <q-card v-if="form.name" flat bordered class="q-pa-md">
      <div class="text-subtitle2 q-mb-sm">Preview</div>
      <div class="row items-center q-gutter-sm">
        <q-icon
          v-if="form.icon"
          :name="form.icon"
          :color="form.color ? undefined : 'primary'"
          :style="form.color ? { color: form.color } : {}"
          size="24px"
        />
        <div class="text-body1 text-weight-medium">
          {{ form.name }}
        </div>
        <q-space />
        <q-chip
          v-if="selectedParent"
          :label="selectedParent.breadcrumb"
          size="sm"
          color="grey-3"
          text-color="dark"
        />
      </div>
      <div v-if="form.description" class="text-caption text-grey-6 q-mt-sm">
        {{ form.description }}
      </div>
    </q-card>

    <!-- Action buttons -->
    <div class="row q-gutter-sm justify-end">
      <q-btn
        flat
        label="Cancel"
        @click="onCancel"
        :disable="loading"
      />
      <q-btn
        type="submit"
        color="primary"
        :label="isEditing ? 'Update' : 'Create'"
        :loading="loading"
      />
    </div>

    <!-- Validation summary -->
    <div v-if="validationErrors.length > 0" class="q-mt-md">
      <q-banner class="bg-negative text-white">
        <template v-slot:avatar>
          <q-icon name="error" />
        </template>
        <div class="text-body2">Please fix the following errors:</div>
        <ul class="q-ma-none q-pl-md">
          <li v-for="error in validationErrors" :key="error">{{ error }}</li>
        </ul>
      </q-banner>
    </div>
  </q-form>
</template>

<script>
import { defineComponent, ref, computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

export default defineComponent({
  name: 'CategoryForm',

  props: {
    category: {
      type: Object,
      default: null
    },
    parentId: {
      type: String,
      default: null
    }
  },

  emits: ['success', 'cancel'],

  setup(props, { emit }) {
    const $q = useQuasar()

    // Data
    const loading = ref(false)
    const loadingParents = ref(false)
    const parentCategories = ref([])
    const validationErrors = ref([])

    const form = ref({
      name: '',
      description: '',
      parent_id: null,
      color: '#1976d2',
      icon: '',
      sort_order: 0
    })

    // Computed
    const isEditing = computed(() => !!props.category)

    const parentOptions = computed(() => {
      const flattenCategories = (cats, prefix = '') => {
        let result = []
        for (const cat of cats) {
          // Exclude the current category being edited to prevent circular references
          if (!isEditing.value || cat.id !== props.category.id) {
            result.push({
              id: cat.id,
              name: cat.name,
              breadcrumb: prefix + cat.name
            })
            if (cat.children) {
              result.push(...flattenCategories(cat.children, prefix + cat.name + ' > '))
            }
          }
        }
        return result
      }
      return flattenCategories(parentCategories.value)
    })

    const selectedParent = computed(() => {
      if (!form.value.parent_id) return null
      return parentOptions.value.find(opt => opt.id === form.value.parent_id)
    })

    // Methods
    const loadParentCategories = async () => {
      loadingParents.value = true
      try {
        const response = await axios.get('/api/v1/categories?hierarchy=true')
        parentCategories.value = response.data
      } catch (error) {
        console.error('Error loading parent categories:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load parent categories'
        })
      } finally {
        loadingParents.value = false
      }
    }

    const validateForm = () => {
      validationErrors.value = []

      if (!form.value.name) {
        validationErrors.value.push('Name is required')
      } else if (form.value.name.length > 100) {
        validationErrors.value.push('Name must be 100 characters or less')
      }

      if (form.value.color && !/^#[0-9A-Fa-f]{6}$/.test(form.value.color)) {
        validationErrors.value.push('Invalid hex color format')
      }

      if (form.value.icon && form.value.icon.length > 50) {
        validationErrors.value.push('Icon name must be 50 characters or less')
      }

      return validationErrors.value.length === 0
    }

    const resetForm = () => {
      form.value = {
        name: '',
        description: '',
        parent_id: props.parentId || null,
        color: '#1976d2',
        icon: '',
        sort_order: 0
      }
      validationErrors.value = []
    }

    const populateForm = () => {
      if (props.category) {
        form.value = {
          name: props.category.name || '',
          description: props.category.description || '',
          parent_id: props.category.parent_id || null,
          color: props.category.color || '#1976d2',
          icon: props.category.icon || '',
          sort_order: props.category.sort_order || 0
        }
      } else {
        resetForm()
      }
    }

    const onSubmit = async () => {
      if (!validateForm()) {
        return
      }

      loading.value = true
      try {
        let response
        if (isEditing.value) {
          response = await axios.put(`/api/v1/categories/${props.category.id}`, form.value)
          $q.notify({
            type: 'positive',
            message: 'Category updated successfully'
          })
        } else {
          response = await axios.post('/api/v1/categories', form.value)
          $q.notify({
            type: 'positive',
            message: 'Category created successfully'
          })
        }

        emit('success', response.data)
      } catch (error) {
        let errorMessage = 'Failed to save category'

        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response?.status === 409) {
          errorMessage = 'A category with this name already exists in the selected parent'
        } else if (error.response?.status === 422) {
          errorMessage = 'Invalid category data provided'
        }

        $q.notify({
          type: 'negative',
          message: errorMessage
        })
        console.error('Error saving category:', error)
      } finally {
        loading.value = false
      }
    }

    const onCancel = () => {
      emit('cancel')
    }

    // Watchers
    watch(() => props.category, populateForm, { immediate: true })
    watch(() => props.parentId, (newParentId) => {
      if (!isEditing.value) {
        form.value.parent_id = newParentId
      }
    })

    // Lifecycle
    onMounted(() => {
      loadParentCategories()
      populateForm()
    })

    return {
      // Data
      loading,
      loadingParents,
      form,
      validationErrors,

      // Computed
      isEditing,
      parentOptions,
      selectedParent,

      // Methods
      onSubmit,
      onCancel,
      resetForm,
      validateForm
    }
  }
})
</script>

<style scoped>
.q-form {
  max-width: 600px;
}
</style>