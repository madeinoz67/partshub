<template>
  <q-card>
    <q-card-section>
      <div class="text-h6">{{ editMode ? 'Edit Project' : 'Create New Project' }}</div>
    </q-card-section>

    <q-form @submit="onSubmit" @reset="onReset">
      <q-card-section>
        <div class="row q-gutter-md">
          <div class="col-12">
            <q-input
              v-model="form.name"
              label="Project Name"
              filled
              required
              :rules="[val => !!val || 'Project name is required']"
            />
          </div>

          <div class="col-12">
            <q-input
              v-model="form.description"
              label="Description"
              type="textarea"
              filled
              rows="3"
            />
          </div>

          <div class="col-6">
            <q-input
              v-model="form.version"
              label="Version"
              filled
              placeholder="e.g., 1.0.0"
            />
          </div>

          <div class="col-6">
            <q-select
              v-model="form.status"
              label="Status"
              filled
              :options="statusOptions"
              emit-value
              map-options
            />
          </div>

          <div class="col-12">
            <q-input
              v-model="form.notes"
              label="Notes"
              type="textarea"
              filled
              rows="3"
            />
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancel" @click="onCancel" />
        <q-btn flat label="Reset" type="reset" color="primary" />
        <q-btn
          :label="editMode ? 'Update' : 'Create'"
          type="submit"
          color="primary"
          :loading="loading"
        />
      </q-card-actions>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Project {
  id?: string
  name: string
  description: string
  version: string
  status: string
  notes: string
}

interface Props {
  project?: Project | null
  loading?: boolean
}

interface Emits {
  (e: 'saved', project: Partial<Project>): void
  (e: 'cancelled'): void
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
  loading: false
})

const emit = defineEmits<Emits>()

const editMode = ref(false)

const form = ref({
  name: '',
  description: '',
  version: '',
  status: 'planning',
  notes: ''
})

const statusOptions = [
  { label: 'Planning', value: 'planning' },
  { label: 'Active', value: 'active' },
  { label: 'On Hold', value: 'on_hold' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' }
]

watch(() => props.project, (newProject) => {
  if (newProject) {
    editMode.value = true
    form.value = {
      name: newProject.name || '',
      description: newProject.description || '',
      version: newProject.version || '',
      status: newProject.status || 'planning',
      notes: newProject.notes || ''
    }
  } else {
    editMode.value = false
    onReset()
  }
}, { immediate: true })

function onSubmit() {
  emit('saved', { ...form.value })
}

function onReset() {
  form.value = {
    name: '',
    description: '',
    version: '',
    status: 'planning',
    notes: ''
  }
}

function onCancel() {
  emit('cancelled')
}
</script>