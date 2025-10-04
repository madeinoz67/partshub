<template>
  <div v-if="authStore.isAdmin" class="bulk-operation-menu">
    <q-btn-dropdown
      :disable="!selectionStore.hasSelection"
      color="primary"
      :label="`Selected (${selectionStore.selectedCount})`"
      icon="checklist"
    >
      <q-list>
        <q-item
          v-close-popup
          clickable
          @click="$emit('add-tags')"
        >
          <q-item-section avatar>
            <q-icon name="local_offer" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Add/Remove Tags</q-item-label>
            <q-item-label caption>Manage tags for selected components</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          v-close-popup
          clickable
          @click="$emit('add-to-project')"
        >
          <q-item-section avatar>
            <q-icon name="folder" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Add to Project</q-item-label>
            <q-item-label caption>Assign components to a project</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator />

        <q-item
          v-close-popup
          clickable
          @click="$emit('delete')"
        >
          <q-item-section avatar>
            <q-icon name="delete" color="negative" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-negative">Delete</q-item-label>
            <q-item-label caption>Permanently delete selected components</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-btn-dropdown>
  </div>
</template>

<script setup lang="ts">
import { useSelectionStore } from '../stores/selection'
import { useAuthStore } from '../stores/auth'

// Stores
const selectionStore = useSelectionStore()
const authStore = useAuthStore()

// Events
defineEmits<{
  'add-tags': []
  'add-to-project': []
  'delete': []
}>()
</script>

<style scoped>
.bulk-operation-menu {
  display: inline-block;
}
</style>
