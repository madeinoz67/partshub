<template>
  <div class="kicad-file-upload">
    <div class="text-h6 q-mb-md">KiCad File Management</div>

    <!-- Source Information Display -->
    <q-card v-if="sourceInfo" flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-subtitle2 q-mb-md">Current Sources</div>
        <div class="row q-gutter-md">
          <!-- Symbol Source -->
          <div class="col">
            <q-card flat class="bg-grey-1">
              <q-card-section class="q-pa-sm">
                <div class="row items-center q-gutter-xs q-mb-xs">
                  <q-icon name="memory" size="sm" />
                  <span class="text-caption font-weight-medium">Symbol</span>
                  <q-space />
                  <q-chip
                    :color="getSourceColor(sourceInfo.symbol.source)"
                    text-color="white"
                    :label="getSourceLabel(sourceInfo.symbol.source)"
                    size="sm"
                  />
                </div>
                <div v-if="sourceInfo.symbol.has_library || sourceInfo.symbol.has_custom" class="text-body2">
                  {{ sourceInfo.symbol.effective_path || 'Available' }}
                </div>
                <div v-else class="text-caption text-grey">
                  No symbol data
                </div>
              </q-card-section>
            </q-card>
          </div>

          <!-- Footprint Source -->
          <div class="col">
            <q-card flat class="bg-grey-1">
              <q-card-section class="q-pa-sm">
                <div class="row items-center q-gutter-xs q-mb-xs">
                  <q-icon name="developer_board" size="sm" />
                  <span class="text-caption font-weight-medium">Footprint</span>
                  <q-space />
                  <q-chip
                    :color="getSourceColor(sourceInfo.footprint.source)"
                    text-color="white"
                    :label="getSourceLabel(sourceInfo.footprint.source)"
                    size="sm"
                  />
                </div>
                <div v-if="sourceInfo.footprint.has_library || sourceInfo.footprint.has_custom" class="text-body2">
                  {{ sourceInfo.footprint.effective_path || 'Available' }}
                </div>
                <div v-else class="text-caption text-grey">
                  No footprint data
                </div>
              </q-card-section>
            </q-card>
          </div>

          <!-- 3D Model Source -->
          <div class="col">
            <q-card flat class="bg-grey-1">
              <q-card-section class="q-pa-sm">
                <div class="row items-center q-gutter-xs q-mb-xs">
                  <q-icon name="view_in_ar" size="sm" />
                  <span class="text-caption font-weight-medium">3D Model</span>
                  <q-space />
                  <q-chip
                    :color="getSourceColor(sourceInfo.model_3d.source)"
                    text-color="white"
                    :label="getSourceLabel(sourceInfo.model_3d.source)"
                    size="sm"
                  />
                </div>
                <div v-if="sourceInfo.model_3d.has_library || sourceInfo.model_3d.has_custom" class="text-body2">
                  {{ sourceInfo.model_3d.effective_path || 'Available' }}
                </div>
                <div v-else class="text-caption text-grey">
                  No 3D model data
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- File Upload Sections -->
    <div class="row q-gutter-md">
      <!-- Symbol Upload -->
      <div class="col-md-4 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-gutter-sm q-mb-md">
              <q-icon name="memory" color="primary" />
              <div class="text-subtitle2">Symbol File</div>
              <q-space />
              <q-btn
                v-if="sourceInfo?.symbol.has_custom"
                size="sm"
                flat
                color="negative"
                icon="refresh"
                label="Reset"
                :loading="resetting.symbol"
                @click="resetSymbol"
              />
            </div>

            <!-- Drop Zone -->
            <div
              class="upload-drop-zone"
              :class="{ 'upload-drop-zone--active': dragStates.symbol }"
              @dragenter.prevent="onDragEnter('symbol')"
              @dragover.prevent="onDragOver('symbol')"
              @dragleave.prevent="onDragLeave('symbol')"
              @drop.prevent="onDrop('symbol', $event)"
              @click="triggerFileInput('symbol')"
            >
              <input
                ref="symbolFileInput"
                type="file"
                accept=".kicad_sym"
                style="display: none"
                @change="onFileSelect('symbol', $event)"
              />

              <div class="upload-drop-zone__content">
                <q-icon
                  name="cloud_upload"
                  size="2rem"
                  :color="dragStates.symbol ? 'primary' : 'grey-6'"
                />
                <div class="text-body2 q-mt-sm">
                  {{ dragStates.symbol ? 'Drop .kicad_sym file' : 'Upload .kicad_sym file' }}
                </div>
                <div class="text-caption text-grey-6">
                  KiCad symbol library file
                </div>
              </div>
            </div>

            <!-- Upload Progress -->
            <q-linear-progress
              v-if="uploadProgress.symbol !== undefined"
              :value="uploadProgress.symbol / 100"
              :color="uploadProgress.symbol === 100 ? 'positive' : 'primary'"
              class="q-mt-sm"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- Footprint Upload -->
      <div class="col-md-4 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-gutter-sm q-mb-md">
              <q-icon name="developer_board" color="primary" />
              <div class="text-subtitle2">Footprint File</div>
              <q-space />
              <q-btn
                v-if="sourceInfo?.footprint.has_custom"
                size="sm"
                flat
                color="negative"
                icon="refresh"
                label="Reset"
                :loading="resetting.footprint"
                @click="resetFootprint"
              />
            </div>

            <!-- Drop Zone -->
            <div
              class="upload-drop-zone"
              :class="{ 'upload-drop-zone--active': dragStates.footprint }"
              @dragenter.prevent="onDragEnter('footprint')"
              @dragover.prevent="onDragOver('footprint')"
              @dragleave.prevent="onDragLeave('footprint')"
              @drop.prevent="onDrop('footprint', $event)"
              @click="triggerFileInput('footprint')"
            >
              <input
                ref="footprintFileInput"
                type="file"
                accept=".kicad_mod"
                style="display: none"
                @change="onFileSelect('footprint', $event)"
              />

              <div class="upload-drop-zone__content">
                <q-icon
                  name="cloud_upload"
                  size="2rem"
                  :color="dragStates.footprint ? 'primary' : 'grey-6'"
                />
                <div class="text-body2 q-mt-sm">
                  {{ dragStates.footprint ? 'Drop .kicad_mod file' : 'Upload .kicad_mod file' }}
                </div>
                <div class="text-caption text-grey-6">
                  KiCad footprint module file
                </div>
              </div>
            </div>

            <!-- Upload Progress -->
            <q-linear-progress
              v-if="uploadProgress.footprint !== undefined"
              :value="uploadProgress.footprint / 100"
              :color="uploadProgress.footprint === 100 ? 'positive' : 'primary'"
              class="q-mt-sm"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- 3D Model Upload -->
      <div class="col-md-4 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-gutter-sm q-mb-md">
              <q-icon name="view_in_ar" color="primary" />
              <div class="text-subtitle2">3D Model File</div>
              <q-space />
              <q-btn
                v-if="sourceInfo?.model_3d.has_custom"
                size="sm"
                flat
                color="negative"
                icon="refresh"
                label="Reset"
                :loading="resetting.model_3d"
                @click="reset3DModel"
              />
            </div>

            <!-- Drop Zone -->
            <div
              class="upload-drop-zone"
              :class="{ 'upload-drop-zone--active': dragStates.model_3d }"
              @dragenter.prevent="onDragEnter('model_3d')"
              @dragover.prevent="onDragOver('model_3d')"
              @dragleave.prevent="onDragLeave('model_3d')"
              @drop.prevent="onDrop('model_3d', $event)"
              @click="triggerFileInput('model_3d')"
            >
              <input
                ref="model3dFileInput"
                type="file"
                accept=".wrl,.step,.stp"
                style="display: none"
                @change="onFileSelect('model_3d', $event)"
              />

              <div class="upload-drop-zone__content">
                <q-icon
                  name="cloud_upload"
                  size="2rem"
                  :color="dragStates.model_3d ? 'primary' : 'grey-6'"
                />
                <div class="text-body2 q-mt-sm">
                  {{ dragStates.model_3d ? 'Drop 3D model file' : 'Upload 3D model file' }}
                </div>
                <div class="text-caption text-grey-6">
                  STEP, VRML, or other 3D model
                </div>
              </div>
            </div>

            <!-- Upload Progress -->
            <q-linear-progress
              v-if="uploadProgress.model_3d !== undefined"
              :value="uploadProgress.model_3d / 100"
              :color="uploadProgress.model_3d === 100 ? 'positive' : 'primary'"
              class="q-mt-sm"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '../boot/axios'

const props = defineProps({
  componentId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['upload-success', 'source-updated'])

const $q = useQuasar()

// Refs
const symbolFileInput = ref(null)
const footprintFileInput = ref(null)
const model3dFileInput = ref(null)

// Reactive state
const sourceInfo = ref(null)
const dragStates = reactive({
  symbol: false,
  footprint: false,
  model_3d: false
})
const uploadProgress = reactive({})
const resetting = reactive({
  symbol: false,
  footprint: false,
  model_3d: false
})

// Methods
const loadSourceInfo = async () => {
  try {
    const response = await api.get(`/api/v1/kicad/components/${props.componentId}/source-info`)
    sourceInfo.value = response.data
  } catch (error) {
    console.error('Failed to load source info:', error)
  }
}

const getSourceColor = (source) => {
  switch (source) {
    case 'custom': return 'purple'
    case 'provider': return 'blue'
    case 'auto': return 'grey'
    default: return 'grey'
  }
}

const getSourceLabel = (source) => {
  switch (source) {
    case 'custom': return 'Custom'
    case 'provider': return 'Provider'
    case 'auto': return 'Auto-Gen'
    default: return 'None'
  }
}

const onDragEnter = (type) => {
  dragStates[type] = true
}

const onDragOver = (type) => {
  dragStates[type] = true
}

const onDragLeave = (type) => {
  dragStates[type] = false
}

const onDrop = (type, event) => {
  dragStates[type] = false
  const files = Array.from(event.dataTransfer.files)
  if (files.length > 0) {
    processFile(type, files[0])
  }
}

const triggerFileInput = (type) => {
  const inputMap = {
    symbol: symbolFileInput,
    footprint: footprintFileInput,
    model_3d: model3dFileInput
  }
  inputMap[type].value?.click()
}

const onFileSelect = (type, event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    processFile(type, files[0])
  }
  // Clear the input
  event.target.value = ''
}

const processFile = async (type, file) => {
  // Validate file type
  const expectedExtensions = {
    symbol: ['.kicad_sym'],
    footprint: ['.kicad_mod'],
    model_3d: ['.wrl', '.step', '.stp', '.stl', '.obj']
  }

  const validExtension = expectedExtensions[type].some(ext =>
    file.name.toLowerCase().endsWith(ext)
  )

  if (!validExtension) {
    $q.notify({
      type: 'negative',
      message: `Invalid file type. Expected: ${expectedExtensions[type].join(', ')}`
    })
    return
  }

  // Upload file
  await uploadFile(type, file)
}

const uploadFile = async (type, file) => {
  const formData = new FormData()
  formData.append('file', file)

  const endpoints = {
    symbol: `upload-symbol`,
    footprint: `upload-footprint`,
    model_3d: `upload-3d-model`
  }

  try {
    uploadProgress[type] = 0

    const response = await api.post(
      `/api/v1/kicad/components/${props.componentId}/${endpoints[type]}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.lengthComputable) {
            uploadProgress[type] = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      }
    )

    $q.notify({
      type: 'positive',
      message: `${type.charAt(0).toUpperCase() + type.slice(1)} file uploaded successfully`
    })

    // Reload source info and emit events
    await loadSourceInfo()
    emit('upload-success', { type, response: response.data })
    emit('source-updated')

  } catch (error) {
    console.error(`Failed to upload ${type} file:`, error)
    $q.notify({
      type: 'negative',
      message: `Failed to upload ${type} file: ${error.response?.data?.detail || error.message}`
    })
  } finally {
    delete uploadProgress[type]
  }
}

const resetSymbol = async () => {
  resetting.symbol = true
  try {
    await api.delete(`/api/v1/kicad/components/${props.componentId}/reset-symbol`)
    await loadSourceInfo()
    emit('source-updated')
    $q.notify({
      type: 'positive',
      message: 'Symbol reset to auto-generated'
    })
  } catch (error) {
    console.error('Failed to reset symbol:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to reset symbol'
    })
  } finally {
    resetting.symbol = false
  }
}

const resetFootprint = async () => {
  resetting.footprint = true
  try {
    await api.delete(`/api/v1/kicad/components/${props.componentId}/reset-footprint`)
    await loadSourceInfo()
    emit('source-updated')
    $q.notify({
      type: 'positive',
      message: 'Footprint reset to auto-generated'
    })
  } catch (error) {
    console.error('Failed to reset footprint:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to reset footprint'
    })
  } finally {
    resetting.footprint = false
  }
}

const reset3DModel = async () => {
  resetting.model_3d = true
  try {
    await api.delete(`/api/v1/kicad/components/${props.componentId}/reset-3d-model`)
    await loadSourceInfo()
    emit('source-updated')
    $q.notify({
      type: 'positive',
      message: '3D model reset to auto-generated'
    })
  } catch (error) {
    console.error('Failed to reset 3D model:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to reset 3D model'
    })
  } finally {
    resetting.model_3d = false
  }
}

onMounted(() => {
  loadSourceInfo()
})
</script>

<style scoped>
.kicad-file-upload {
  width: 100%;
}

.upload-drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-drop-zone:hover {
  border-color: var(--q-primary);
  background-color: #f0f8ff;
}

.upload-drop-zone--active {
  border-color: var(--q-primary);
  background-color: #e3f2fd;
  transform: scale(1.02);
}

.upload-drop-zone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .upload-drop-zone {
    padding: 1rem;
    min-height: 100px;
  }

  .upload-drop-zone .q-icon {
    font-size: 1.5rem !important;
  }
}
</style>