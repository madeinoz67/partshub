<template>
  <div class="file-upload-container">
    <div class="text-h6 q-mb-sm">{{ title }}</div>

    <!-- Drag and Drop Area -->
    <div
      ref="dropZoneRef"
      class="drop-zone"
      :class="{ 'drop-zone--active': isDragActive, 'drop-zone--error': hasError }"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        multiple
        :accept="acceptedTypes"
        @change="onFileSelect"
        style="display: none"
      />

      <div class="drop-zone__content">
        <q-icon
          name="cloud_upload"
          size="3rem"
          :color="isDragActive ? 'primary' : 'grey-6'"
        />
        <div class="text-body1 q-mt-sm">
          {{ isDragActive ? 'Drop files here' : 'Drag & drop files here' }}
        </div>
        <div class="text-body2 text-grey-6 q-mt-xs">
          or <span class="text-primary cursor-pointer">browse files</span>
        </div>
        <div class="text-caption text-grey-5 q-mt-sm">
          Supports: {{ acceptedTypesDisplay }}
        </div>
        <div class="text-caption text-grey-5">
          Max size: {{ maxSizeDisplay }}
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="selectedFiles.length > 0" class="q-mt-md">
      <div class="text-body1 q-mb-sm">Selected Files ({{ selectedFiles.length }})</div>
      <q-list bordered separator>
        <q-item v-for="(file, index) in selectedFiles" :key="index" class="q-pa-md">
          <q-item-section avatar>
            <q-avatar :color="getFileTypeColor(file.type)" text-color="white" size="md">
              <q-icon :name="getFileTypeIcon(file.type)" />
            </q-avatar>
          </q-item-section>

          <q-item-section>
            <q-item-label class="text-body2">{{ file.name }}</q-item-label>
            <q-item-label caption>
              {{ formatFileSize(file.size) }} • {{ file.type || 'Unknown type' }}
            </q-item-label>

            <!-- File metadata inputs -->
            <div class="row q-gutter-sm q-mt-sm" v-if="showMetadataInputs">
              <div class="col-md-4 col-xs-12">
                <q-input
                  v-model="fileMetadata[index].title"
                  label="Title"
                  dense
                  outlined
                  :placeholder="file.name"
                />
              </div>
              <div class="col-md-4 col-xs-12">
                <q-input
                  v-model="fileMetadata[index].description"
                  label="Description"
                  dense
                  outlined
                />
              </div>
              <div class="col-md-4 col-xs-12">
                <q-select
                  v-model="fileMetadata[index].attachmentType"
                  :options="attachmentTypeOptions"
                  label="Type"
                  dense
                  outlined
                  emit-value
                  map-options
                />
              </div>
            </div>

            <!-- Upload progress -->
            <q-linear-progress
              v-if="uploadProgress[index] !== undefined"
              :value="uploadProgress[index] / 100"
              :color="uploadProgress[index] === 100 ? 'positive' : 'primary'"
              class="q-mt-sm"
            />
          </q-item-section>

          <q-item-section side>
            <div class="row items-center q-gutter-xs">
              <!-- Set as primary image button for images -->
              <q-btn
                v-if="isImageFile(file.type) && showMetadataInputs"
                :icon="fileMetadata[index].isPrimary ? 'star' : 'star_border'"
                :color="fileMetadata[index].isPrimary ? 'amber' : 'grey-6'"
                flat
                round
                dense
                @click="setPrimaryImage(index)"
                :title="fileMetadata[index].isPrimary ? 'Primary image' : 'Set as primary'"
              />

              <!-- Upload status -->
              <q-icon
                v-if="uploadStatus[index] === 'success'"
                name="check_circle"
                color="positive"
                size="sm"
              />
              <q-icon
                v-else-if="uploadStatus[index] === 'error'"
                name="error"
                color="negative"
                size="sm"
              />

              <!-- Remove file button -->
              <q-btn
                icon="close"
                color="negative"
                flat
                round
                dense
                @click="removeFile(index)"
                :disable="uploadProgress[index] !== undefined && uploadProgress[index] < 100"
              />
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </div>

    <!-- Error messages -->
    <div v-if="errorMessages.length > 0" class="q-mt-md">
      <q-banner
        v-for="(error, index) in errorMessages"
        :key="index"
        class="bg-negative text-white q-mb-sm"
      >
        <template #avatar>
          <q-icon name="error" />
        </template>
        {{ error }}
      </q-banner>
    </div>

    <!-- Action buttons -->
    <div v-if="selectedFiles.length > 0" class="row q-gutter-md q-mt-md">
      <q-btn
        label="Upload Files"
        icon="upload"
        color="primary"
        @click="uploadFiles"
        :loading="isUploading"
        :disable="selectedFiles.length === 0"
      />
      <q-btn
        label="Clear All"
        icon="clear_all"
        color="grey-6"
        flat
        @click="clearAllFiles"
        :disable="isUploading"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '../boot/axios'

// Props
const props = defineProps({
  componentId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: 'Upload Files'
  },
  acceptedTypes: {
    type: String,
    default: 'image/*,application/pdf'
  },
  maxFileSize: {
    type: Number,
    default: 50 * 1024 * 1024 // 50MB
  },
  showMetadataInputs: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['upload-success', 'upload-error', 'files-added'])

// Quasar
const $q = useQuasar()

// Refs
const dropZoneRef = ref(null)
const fileInputRef = ref(null)

// Reactive state
const isDragActive = ref(false)
const selectedFiles = ref([])
const fileMetadata = ref([])
const uploadProgress = ref({})
const uploadStatus = ref({})
const errorMessages = ref([])
const isUploading = ref(false)
const hasError = ref(false)

// Computed
const acceptedTypesDisplay = computed(() => {
  return props.acceptedTypes.replace(/\*/g, 'all').replace(/,/g, ', ')
})

const maxSizeDisplay = computed(() => {
  const mb = props.maxFileSize / (1024 * 1024)
  return `${mb}MB`
})

const attachmentTypeOptions = [
  { label: 'Auto-detect', value: null },
  { label: 'Datasheet', value: 'datasheet' },
  { label: 'Image', value: 'image' },
  { label: 'Document', value: 'document' }
]

// Methods
const onDragEnter = (e) => {
  isDragActive.value = true
}

const onDragOver = (e) => {
  isDragActive.value = true
}

const onDragLeave = (e) => {
  // Only set to false if we're leaving the drop zone completely
  if (!dropZoneRef.value?.contains(e.relatedTarget)) {
    isDragActive.value = false
  }
}

const onDrop = (e) => {
  isDragActive.value = false
  const files = Array.from(e.dataTransfer.files)
  processFiles(files)
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const onFileSelect = (e) => {
  const files = Array.from(e.target.files)
  processFiles(files)
  // Clear the input so the same file can be selected again
  e.target.value = ''
}

const processFiles = (files) => {
  clearErrors()
  const validFiles = []
  const errors = []

  for (const file of files) {
    // Check file size
    if (file.size > props.maxFileSize) {
      errors.push(`File "${file.name}" exceeds maximum size of ${maxSizeDisplay.value}`)
      continue
    }

    // Check file type
    if (!isValidFileType(file.type)) {
      errors.push(`File "${file.name}" has unsupported type: ${file.type}`)
      continue
    }

    validFiles.push(file)
  }

  if (errors.length > 0) {
    errorMessages.value = errors
    hasError.value = true
    return
  }

  // Add files to selection
  selectedFiles.value.push(...validFiles)

  // Initialize metadata for new files
  validFiles.forEach((file, index) => {
    const metadataIndex = selectedFiles.value.length - validFiles.length + index
    fileMetadata.value[metadataIndex] = {
      title: '',
      description: '',
      attachmentType: detectFileType(file.type),
      isPrimary: false
    }
  })

  emit('files-added', validFiles)

  $q.notify({
    type: 'positive',
    message: `Added ${validFiles.length} file${validFiles.length !== 1 ? 's' : ''}`
  })
}

const isValidFileType = (mimeType) => {
  if (!mimeType) return false

  const accepted = props.acceptedTypes.split(',').map(t => t.trim())
  return accepted.some(type => {
    if (type.includes('/*')) {
      return mimeType.startsWith(type.replace('/*', ''))
    }
    return mimeType === type
  })
}

const detectFileType = (mimeType) => {
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType === 'application/pdf') return 'datasheet'
  return 'document'
}

const isImageFile = (mimeType) => {
  return mimeType && mimeType.startsWith('image/')
}

const getFileTypeIcon = (mimeType) => {
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType === 'application/pdf') return 'picture_as_pdf'
  return 'description'
}

const getFileTypeColor = (mimeType) => {
  if (mimeType.startsWith('image/')) return 'blue'
  if (mimeType === 'application/pdf') return 'red'
  return 'grey'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const setPrimaryImage = (index) => {
  // Clear other primary images
  fileMetadata.value.forEach((metadata, i) => {
    if (i !== index) {
      metadata.isPrimary = false
    }
  })

  // Toggle current one
  fileMetadata.value[index].isPrimary = !fileMetadata.value[index].isPrimary
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
  fileMetadata.value.splice(index, 1)
  delete uploadProgress.value[index]
  delete uploadStatus.value[index]
}

const clearAllFiles = () => {
  selectedFiles.value = []
  fileMetadata.value = []
  uploadProgress.value = {}
  uploadStatus.value = {}
  clearErrors()
}

const clearErrors = () => {
  errorMessages.value = []
  hasError.value = false
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return

  isUploading.value = true
  const promises = []

  selectedFiles.value.forEach((file, index) => {
    promises.push(uploadSingleFile(file, index))
  })

  try {
    const results = await Promise.allSettled(promises)
    const successes = results.filter(r => r.status === 'fulfilled').length
    const failures = results.filter(r => r.status === 'rejected').length

    if (successes > 0) {
      emit('upload-success', { successes, failures })
      $q.notify({
        type: 'positive',
        message: `Successfully uploaded ${successes} file${successes !== 1 ? 's' : ''}`
      })
    }

    if (failures > 0) {
      emit('upload-error', { successes, failures })
      $q.notify({
        type: 'negative',
        message: `Failed to upload ${failures} file${failures !== 1 ? 's' : ''}`
      })
    }
  } finally {
    isUploading.value = false
  }
}

const uploadSingleFile = async (file, index) => {
  const formData = new FormData()
  formData.append('file', file)

  const metadata = fileMetadata.value[index]
  if (metadata.title) formData.append('title', metadata.title)
  if (metadata.description) formData.append('description', metadata.description)
  if (metadata.attachmentType) formData.append('attachment_type', metadata.attachmentType)
  if (metadata.isPrimary) formData.append('is_primary_image', 'true')

  try {
    uploadProgress.value[index] = 0

    const response = await api.post(
      `/api/v1/components/${props.componentId}/attachments`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.lengthComputable) {
            uploadProgress.value[index] = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      }
    )

    uploadStatus.value[index] = 'success'
    return response.data
  } catch (error) {
    uploadStatus.value[index] = 'error'
    console.error('Upload failed:', error)
    throw error
  }
}

// Lifecycle
onMounted(() => {
  // Prevent default drag behaviors on the document
  const preventDefaults = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  document.addEventListener('dragenter', preventDefaults)
  document.addEventListener('dragover', preventDefaults)
  document.addEventListener('dragleave', preventDefaults)
  document.addEventListener('drop', preventDefaults)
})

onUnmounted(() => {
  // Clean up event listeners
  const preventDefaults = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  document.removeEventListener('dragenter', preventDefaults)
  document.removeEventListener('dragover', preventDefaults)
  document.removeEventListener('dragleave', preventDefaults)
  document.removeEventListener('drop', preventDefaults)
})
</script>

<style scoped>
.file-upload-container {
  width: 100%;
}

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.drop-zone:hover {
  border-color: var(--q-primary);
  background-color: #f0f8ff;
}

.drop-zone--active {
  border-color: var(--q-primary);
  background-color: #e3f2fd;
  transform: scale(1.02);
}

.drop-zone--error {
  border-color: var(--q-negative);
  background-color: #ffebee;
}

.drop-zone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.text-primary {
  text-decoration: underline;
}
</style>