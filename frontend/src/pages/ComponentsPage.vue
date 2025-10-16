<template>
  <q-page class="q-pa-md">
    <!-- Page Title and Bulk Operations -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Components</div>
        <div class="text-caption text-grey">Manage your electronic components inventory</div>
      </div>
      <div class="col-auto">
        <!-- Bulk Operations Menu -->
        <BulkOperationMenu
          @add-tags="showTagDialog = true"
          @add-to-project="showProjectDialog = true"
          @delete="handleBulkDelete"
        />
      </div>
    </div>

    <!-- Component List -->
    <ComponentList
      @create-component="handleCreateComponent"
      @view-component="viewComponent"
      @edit-component="editComponent"
      @update-stock="updateStock"
      @configure-reorder="configureReorder"
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

    <!-- Reorder Threshold Dialog -->
    <MultiLocationThresholdDialog
      v-model="showThresholdDialog"
      :component="selectedComponent"
      @saved="onThresholdSaved"
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
          <q-btn v-close-popup flat label="Cancel" color="primary" />
          <q-btn
            flat
            label="Delete"
            color="negative"
            :loading="deleteLoading"
            @click="confirmDelete"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Tag Management Dialog -->
    <TagManagementDialog
      v-model="showTagDialog"
      :component-ids="selectionStore.getSelectedArray()"
      @applied="onTagsApplied"
    />

    <!-- Add to Project Dialog -->
    <AddToProjectDialog
      v-model="showProjectDialog"
      :component-ids="selectionStore.getSelectedArray()"
      @added="onAddedToProject"
    />

    <!-- Bulk Delete Confirmation Dialog -->
    <q-dialog v-model="showBulkDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="delete" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete <strong>{{ selectionStore.selectedCount }}</strong> selected components?
            This action cannot be undone.
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancel" color="primary" />
          <q-btn
            flat
            label="Delete All"
            color="negative"
            :loading="bulkDeleteLoading"
            @click="confirmBulkDelete"
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
import MultiLocationThresholdDialog from '../components/reorder/MultiLocationThresholdDialog.vue'
import BulkOperationMenu from '../components/BulkOperationMenu.vue'
import TagManagementDialog from '../components/TagManagementDialog.vue'
import AddToProjectDialog from '../components/AddToProjectDialog.vue'
import { useComponentsStore } from '../stores/components'
import { useSelectionStore } from '../stores/selection'
import { useAuth } from '../composables/useAuth'
import { bulkOperationsApi } from '../services/bulkOperationsApi'
import type { Component } from '../services/api'

const router = useRouter()
const $q = useQuasar()
const componentsStore = useComponentsStore()
const selectionStore = useSelectionStore()
const { requireAuth } = useAuth()

const selectedComponent = ref<Component | null>(null)
const showCreateDialog = ref(false)
const showStockDialog = ref(false)
const showThresholdDialog = ref(false)
const showDeleteDialog = ref(false)
const showTagDialog = ref(false)
const showProjectDialog = ref(false)
const showBulkDeleteDialog = ref(false)
const isEditMode = ref(false)
const deleteLoading = ref(false)
const bulkDeleteLoading = ref(false)

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

const configureReorder = (component: Component) => {
  if (!requireAuth('configure reorder alerts')) return

  selectedComponent.value = component
  showThresholdDialog.value = true
}

const deleteComponent = (component: Component) => {
  if (!requireAuth('delete components')) return

  selectedComponent.value = component
  showDeleteDialog.value = true
}

const onComponentSaved = (_component: Component) => {
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

const onThresholdSaved = async () => {
  $q.notify({
    type: 'positive',
    message: 'Reorder thresholds updated successfully',
    position: 'top-right'
  })

  // Refresh components to show updated reorder status
  await componentsStore.fetchComponents()
  selectedComponent.value = null
  showThresholdDialog.value = false
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

// Bulk operations handlers
const handleBulkDelete = () => {
  if (!requireAuth('delete components')) return
  showBulkDeleteDialog.value = true
}

const confirmBulkDelete = async () => {
  if (selectionStore.selectedCount === 0) return

  bulkDeleteLoading.value = true
  try {
    const result = await bulkOperationsApi.bulkDelete(selectionStore.getSelectedArray())

    $q.notify({
      type: 'positive',
      message: `${result.deleted_count || 0} components deleted successfully`,
      caption: result.failed_count > 0 ? `${result.failed_count} failed` : undefined,
      position: 'top-right'
    })

    // Clear selection and refresh
    selectionStore.clearSelection()
    await componentsStore.fetchComponents()
    showBulkDeleteDialog.value = false
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete components',
      caption: error instanceof Error ? error.message : 'Unknown error',
      position: 'top-right'
    })
  } finally {
    bulkDeleteLoading.value = false
  }
}

const onTagsApplied = async () => {
  $q.notify({
    type: 'positive',
    message: 'Tags updated successfully',
    position: 'top-right'
  })

  // Refresh components while preserving selection
  await componentsStore.fetchComponents()
}

const onAddedToProject = async () => {
  $q.notify({
    type: 'positive',
    message: 'Components added to project successfully',
    position: 'top-right'
  })

  // Refresh components while preserving selection
  await componentsStore.fetchComponents()
}
</script>