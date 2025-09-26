<template>
  <q-page class="q-pa-md">
    <!-- Page Title -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Components</div>
        <div class="text-caption text-grey">Manage your electronic components inventory</div>
      </div>
    </div>

    <!-- Component List -->
    <ComponentList
      @create-component="handleCreateComponent"
      @view-component="viewComponent"
      @edit-component="editComponent"
      @update-stock="updateStock"
      @delete-component="deleteComponent"
    />

    <!-- Component Form Dialog -->
    <ComponentForm
      v-model="showCreateDialog"
      :component="selectedComponent"
      :is-edit="isEditMode"
      @saved="onComponentSaved"
    />

    <!-- Stock Update Dialog -->
    <StockUpdateDialog
      v-model="showStockDialog"
      :component="selectedComponent"
      @updated="onStockUpdated"
    />

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="delete" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete <strong>{{ selectedComponent?.name }}</strong>?
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Delete"
            color="negative"
            @click="confirmDelete"
            :loading="deleteLoading"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import ComponentList from '../components/ComponentList.vue'
import ComponentForm from '../components/ComponentForm.vue'
import StockUpdateDialog from '../components/StockUpdateDialog.vue'
import { useComponentsStore } from '../stores/components'
import { useAuth } from '../composables/useAuth'
import type { Component } from '../services/api'

const router = useRouter()
const $q = useQuasar()
const componentsStore = useComponentsStore()
const { requireAuth } = useAuth()

const selectedComponent = ref<Component | null>(null)
const showCreateDialog = ref(false)
const showStockDialog = ref(false)
const showDeleteDialog = ref(false)
const isEditMode = ref(false)
const deleteLoading = ref(false)

const viewComponent = (component: Component) => {
  router.push(`/components/${component.id}`)
}

const handleCreateComponent = () => {
  if (!requireAuth('create components')) return

  selectedComponent.value = null
  isEditMode.value = false
  showCreateDialog.value = true
}

const editComponent = (component: Component) => {
  if (!requireAuth('edit components')) return

  selectedComponent.value = component
  isEditMode.value = true
  showCreateDialog.value = true
}

const updateStock = (component: Component) => {
  if (!requireAuth('update stock quantities')) return

  selectedComponent.value = component
  showStockDialog.value = true
}

const deleteComponent = (component: Component) => {
  if (!requireAuth('delete components')) return

  selectedComponent.value = component
  showDeleteDialog.value = true
}

const onComponentSaved = (component: Component) => {
  $q.notify({
    type: 'positive',
    message: isEditMode.value ? 'Component updated successfully' : 'Component created successfully',
    position: 'top-right'
  })

  // Reset state
  selectedComponent.value = null
  isEditMode.value = false
  showCreateDialog.value = false
}

const onStockUpdated = () => {
  $q.notify({
    type: 'positive',
    message: 'Stock updated successfully',
    position: 'top-right'
  })

  selectedComponent.value = null
  showStockDialog.value = false
}

const confirmDelete = async () => {
  if (!selectedComponent.value) return

  deleteLoading.value = true
  try {
    await componentsStore.deleteComponent(selectedComponent.value.id)

    $q.notify({
      type: 'positive',
      message: 'Component deleted successfully',
      position: 'top-right'
    })

    showDeleteDialog.value = false
    selectedComponent.value = null
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete component',
      position: 'top-right'
    })
  } finally {
    deleteLoading.value = false
  }
}
</script>