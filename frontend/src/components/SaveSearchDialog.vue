<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card style="min-width: 500px">
      <q-card-section>
        <div class="text-h6">Save Search</div>
        <div class="text-caption text-grey-7">Save your current search parameters for quick access later</div>
      </q-card-section>

      <q-card-section>
        <q-form ref="formRef" @submit="handleSave">
          <div class="q-gutter-md">
            <!-- Search Name -->
            <q-input
              v-model="name"
              label="Search Name *"
              placeholder="e.g., Resistors 0603 in stock"
              outlined
              dense
              :rules="[
                val => !!val || 'Name is required',
                val => val.length >= 1 || 'Name must be at least 1 character',
                val => val.length <= 100 || 'Name must be less than 100 characters'
              ]"
              counter
              maxlength="100"
              autofocus
            />

            <!-- Description (Optional) -->
            <q-input
              v-model="description"
              label="Description (Optional)"
              placeholder="Add details about this search..."
              outlined
              dense
              type="textarea"
              rows="3"
              counter
              maxlength="500"
              :rules="[
                val => !val || val.length <= 500 || 'Description must be less than 500 characters'
              ]"
            />

            <!-- Parameters Preview -->
            <q-expansion-item
              label="Search Parameters Preview"
              icon="preview"
              dense
              header-class="bg-grey-2"
            >
              <q-card flat bordered class="q-pa-md">
                <div v-if="hasParameters" class="q-gutter-sm">
                  <div v-if="searchParameters.search" class="row">
                    <div class="col-4 text-weight-medium">Query:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.search }}</div>
                  </div>
                  <div v-if="searchParameters.searchType" class="row">
                    <div class="col-4 text-weight-medium">Search Type:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.searchType }}</div>
                  </div>
                  <div v-if="searchParameters.limit" class="row">
                    <div class="col-4 text-weight-medium">Limit:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.limit }}</div>
                  </div>
                  <div v-if="searchParameters.providers && searchParameters.providers.length > 0" class="row">
                    <div class="col-4 text-weight-medium">Providers:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.providers.join(', ') }}</div>
                  </div>
                  <div v-if="searchParameters.category" class="row">
                    <div class="col-4 text-weight-medium">Category:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.category }}</div>
                  </div>
                  <div v-if="searchParameters.tags && searchParameters.tags.length > 0" class="row">
                    <div class="col-4 text-weight-medium">Tags:</div>
                    <div class="col-8 text-grey-8">{{ searchParameters.tags.join(', ') }}</div>
                  </div>
                </div>
                <div v-else class="text-center text-grey-6">
                  <q-icon name="info" size="sm" class="q-mr-xs" />
                  No parameters to save
                </div>
              </q-card>
            </q-expansion-item>
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions align="right" class="q-pa-md">
        <q-btn
          label="Cancel"
          color="grey"
          flat
          :disable="saving"
          @click="handleClose"
        />
        <q-btn
          label="Save Search"
          color="primary"
          :loading="saving"
          :disable="!name || !hasParameters"
          @click="handleSave"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { createSavedSearch } from '../services/savedSearchesService'

export default {
  name: 'SaveSearchDialog',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    searchParameters: {
      type: Object,
      required: true
    }
  },
  emits: ['update:modelValue', 'saved'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const formRef = ref(null)
    const name = ref('')
    const description = ref('')
    const saving = ref(false)

    const showDialog = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const hasParameters = computed(() => {
      const params = props.searchParameters
      return params && (
        params.search ||
        params.searchType ||
        params.category ||
        params.providers?.length > 0 ||
        params.tags?.length > 0
      )
    })

    const handleSave = async () => {
      // Validate form
      const isValid = await formRef.value.validate()
      if (!isValid) return

      saving.value = true
      try {
        const savedSearch = await createSavedSearch(
          name.value.trim(),
          props.searchParameters,
          description.value.trim() || null
        )

        $q.notify({
          type: 'positive',
          message: 'Search saved successfully',
          caption: name.value,
          timeout: 3000,
          icon: 'bookmark'
        })

        emit('saved', savedSearch)
        handleClose()
      } catch (error) {
        console.error('Error saving search:', error)
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to save search'
        $q.notify({
          type: 'negative',
          message: 'Failed to save search',
          caption: errorMessage,
          timeout: 5000
        })
      } finally {
        saving.value = false
      }
    }

    const handleClose = () => {
      name.value = ''
      description.value = ''
      showDialog.value = false
    }

    // Reset form when dialog is opened
    watch(() => props.modelValue, (newValue) => {
      if (newValue) {
        name.value = ''
        description.value = ''
      }
    })

    return {
      formRef,
      showDialog,
      name,
      description,
      saving,
      hasParameters,
      handleSave,
      handleClose
    }
  }
}
</script>

<style scoped>
.q-expansion-item {
  border-radius: 4px;
  overflow: hidden;
}
</style>
