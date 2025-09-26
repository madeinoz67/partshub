<template>
  <div class="attachment-gallery">
    <!-- Gallery Header -->
    <div class="row items-center q-mb-md">
      <div class="text-h6">{{ title }}</div>
      <q-space />
      <q-btn
        v-if="showActions"
        icon="add"
        label="Upload Files"
        color="primary"
        @click="showUploadDialog = true"
        :disable="!componentId"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center q-pa-lg">
      <q-spinner color="primary" size="3em" />
      <div class="q-mt-md">Loading attachments...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="attachments.length === 0" class="text-center q-pa-lg">
      <q-icon name="attachment" size="3em" color="grey-5" />
      <div class="text-body1 text-grey-6 q-mt-md">No attachments yet</div>
      <div class="text-body2 text-grey-5 q-mt-xs">
        Upload datasheets, images, and documents to get started
      </div>
    </div>

    <!-- Attachments Grid -->
    <div v-else class="attachments-grid">
      <!-- Images Section -->
      <div v-if="imageAttachments.length > 0" class="q-mb-lg">
        <div class="text-subtitle1 q-mb-sm flex items-center">
          <q-icon name="image" class="q-mr-sm" />
          Images ({{ imageAttachments.length }})
        </div>
        <div class="row q-gutter-md">
          <div
            v-for="attachment in imageAttachments"
            :key="attachment.id"
            class="attachment-card image-card col-auto"
            @click="openImageViewer(attachment)"
          >
            <div class="image-container">
              <img
                v-if="attachment.thumbnail_path"
                :src="getAttachmentUrl(attachment.id, 'thumbnail')"
                :alt="attachment.title || attachment.original_filename"
                class="attachment-thumbnail"
                @error="onImageError"
              />
              <q-icon v-else name="image" size="3rem" color="grey-5" />

              <!-- Primary image indicator -->
              <div v-if="attachment.is_primary_image" class="primary-badge">
                <q-icon name="star" color="amber" size="sm" />
              </div>

              <!-- Overlay with actions -->
              <div class="image-overlay">
                <q-btn
                  icon="visibility"
                  color="white"
                  flat
                  round
                  dense
                  @click.stop="openImageViewer(attachment)"
                />
                <q-btn
                  icon="download"
                  color="white"
                  flat
                  round
                  dense
                  @click.stop="downloadAttachment(attachment)"
                />
                <q-btn
                  v-if="!attachment.is_primary_image && showActions"
                  icon="star_border"
                  color="white"
                  flat
                  round
                  dense
                  @click.stop="setPrimaryImage(attachment)"
                />
                <q-btn
                  v-if="showActions"
                  icon="delete"
                  color="white"
                  flat
                  round
                  dense
                  @click.stop="confirmDelete(attachment)"
                />
              </div>
            </div>

            <div class="attachment-info">
              <div class="text-body2 ellipsis">
                {{ attachment.title || attachment.original_filename }}
              </div>
              <div class="text-caption text-grey-6">
                {{ formatFileSize(attachment.file_size) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Documents Section -->
      <div v-if="documentAttachments.length > 0">
        <div class="text-subtitle1 q-mb-sm flex items-center">
          <q-icon name="description" class="q-mr-sm" />
          Documents ({{ documentAttachments.length }})
        </div>
        <q-list bordered separator>
          <q-item
            v-for="attachment in documentAttachments"
            :key="attachment.id"
            clickable
            @click="downloadAttachment(attachment)"
          >
            <q-item-section avatar>
              <q-avatar :color="getFileTypeColor(attachment.mime_type)" text-color="white">
                <q-icon :name="getFileTypeIcon(attachment.mime_type)" />
              </q-avatar>
            </q-item-section>

            <q-item-section>
              <q-item-label>{{ attachment.title || attachment.original_filename }}</q-item-label>
              <q-item-label caption>
                {{ formatFileSize(attachment.file_size) }} • {{ attachment.mime_type }}
              </q-item-label>
              <q-item-label caption v-if="attachment.description">
                {{ attachment.description }}
              </q-item-label>
            </q-item-section>

            <q-item-section side v-if="showActions">
              <div class="row q-gutter-xs">
                <q-btn
                  icon="download"
                  color="primary"
                  flat
                  round
                  dense
                  @click.stop="downloadAttachment(attachment)"
                />
                <q-btn
                  icon="edit"
                  color="grey-6"
                  flat
                  round
                  dense
                  @click.stop="editAttachment(attachment)"
                />
                <q-btn
                  icon="delete"
                  color="negative"
                  flat
                  round
                  dense
                  @click.stop="confirmDelete(attachment)"
                />
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>

    <!-- Image Viewer Dialog -->
    <q-dialog v-model="imageViewerOpen" maximized>
      <q-card class="bg-black text-white">
        <q-card-section class="q-pa-none full-height">
          <div class="image-viewer">
            <!-- Header -->
            <div class="image-viewer-header">
              <div class="text-h6">{{ currentImage?.title || currentImage?.original_filename }}</div>
              <q-space />
              <q-btn
                icon="download"
                flat
                round
                @click="downloadAttachment(currentImage)"
                v-if="currentImage"
              />
              <q-btn
                icon="close"
                flat
                round
                @click="imageViewerOpen = false"
              />
            </div>

            <!-- Image -->
            <div class="image-viewer-content">
              <img
                v-if="currentImage"
                :src="getAttachmentUrl(currentImage.id, 'download')"
                :alt="currentImage.title || currentImage.original_filename"
                class="viewer-image"
                @error="onImageError"
              />
            </div>

            <!-- Navigation -->
            <div class="image-viewer-nav" v-if="imageAttachments.length > 1">
              <q-btn
                icon="chevron_left"
                round
                color="white"
                @click="previousImage"
                :disable="currentImageIndex === 0"
              />
              <div class="nav-info">
                {{ currentImageIndex + 1 }} / {{ imageAttachments.length }}
              </div>
              <q-btn
                icon="chevron_right"
                round
                color="white"
                @click="nextImage"
                :disable="currentImageIndex === imageAttachments.length - 1"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- File Upload Dialog -->
    <q-dialog v-model="showUploadDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Upload Attachments</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="showUploadDialog = false" />
        </q-card-section>

        <q-separator />

        <q-card-section>
          <FileUpload
            :component-id="componentId"
            @upload-success="onUploadSuccess"
            @upload-error="onUploadError"
          />
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Edit Attachment Dialog -->
    <q-dialog v-model="editDialogOpen" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Edit Attachment</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="editDialogOpen = false" />
        </q-card-section>

        <q-separator />

        <q-card-section v-if="editingAttachment">
          <q-form @submit="saveAttachment" class="q-gutter-md">
            <q-input
              v-model="editForm.title"
              label="Title"
              outlined
            />
            <q-input
              v-model="editForm.description"
              label="Description"
              type="textarea"
              outlined
              rows="3"
            />
            <q-select
              v-model="editForm.attachment_type"
              :options="attachmentTypeOptions"
              label="Type"
              outlined
              emit-value
              map-options
            />
            <div class="row justify-end q-gutter-sm">
              <q-btn
                label="Cancel"
                color="grey-6"
                flat
                @click="editDialogOpen = false"
              />
              <q-btn
                label="Save"
                color="primary"
                type="submit"
                :loading="saving"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="deleteConfirmOpen" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">Delete this attachment?</span>
        </q-card-section>

        <q-card-section class="q-pt-none">
          This action cannot be undone.
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="deleteConfirmOpen = false" />
          <q-btn
            flat
            label="Delete"
            color="negative"
            @click="deleteAttachment"
            :loading="deleting"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '../boot/axios'
import FileUpload from './FileUpload.vue'

// Props
const props = defineProps({
  componentId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: 'Attachments'
  },
  showUploadButton: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  autoLoad: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['attachment-updated', 'attachment-deleted'])

// Quasar
const $q = useQuasar()

// State
const attachments = ref([])
const loading = ref(false)
const imageViewerOpen = ref(false)
const showUploadDialog = ref(false)
const editDialogOpen = ref(false)
const deleteConfirmOpen = ref(false)
const saving = ref(false)
const deleting = ref(false)

const currentImage = ref(null)
const currentImageIndex = ref(0)
const editingAttachment = ref(null)
const deletingAttachment = ref(null)

const editForm = ref({
  title: '',
  description: '',
  attachment_type: null
})

// Computed
const imageAttachments = computed(() => {
  return attachments.value.filter(att => att.mime_type.startsWith('image/'))
})

const documentAttachments = computed(() => {
  return attachments.value.filter(att => !att.mime_type.startsWith('image/'))
})

const attachmentTypeOptions = [
  { label: 'Auto-detect', value: null },
  { label: 'Datasheet', value: 'datasheet' },
  { label: 'Image', value: 'image' },
  { label: 'Document', value: 'document' }
]

// Methods
const loadAttachments = async () => {
  if (!props.componentId) return

  loading.value = true
  try {
    const response = await api.get(`/api/v1/components/${props.componentId}/attachments`)
    attachments.value = response.data.attachments || []
  } catch (error) {
    console.error('Failed to load attachments:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load attachments'
    })
  } finally {
    loading.value = false
  }
}

const getAttachmentUrl = (attachmentId, type = 'download') => {
  const endpoint = type === 'thumbnail' ? 'thumbnail' : 'download'
  return `http://localhost:8000/api/v1/components/${props.componentId}/attachments/${attachmentId}/${endpoint}`
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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

const openImageViewer = (attachment) => {
  currentImage.value = attachment
  currentImageIndex.value = imageAttachments.value.findIndex(img => img.id === attachment.id)
  imageViewerOpen.value = true
}

const previousImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
    currentImage.value = imageAttachments.value[currentImageIndex.value]
  }
}

const nextImage = () => {
  if (currentImageIndex.value < imageAttachments.value.length - 1) {
    currentImageIndex.value++
    currentImage.value = imageAttachments.value[currentImageIndex.value]
  }
}

const downloadAttachment = (attachment) => {
  const link = document.createElement('a')
  link.href = getAttachmentUrl(attachment.id, 'download')
  link.download = attachment.original_filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const setPrimaryImage = async (attachment) => {
  try {
    await api.post(`/api/v1/components/${props.componentId}/attachments/${attachment.id}/set-primary`)

    // Update local state
    attachments.value.forEach(att => {
      att.is_primary_image = att.id === attachment.id
    })

    emit('attachment-updated', attachment)

    $q.notify({
      type: 'positive',
      message: 'Primary image updated'
    })
  } catch (error) {
    console.error('Failed to set primary image:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to set primary image'
    })
  }
}

const editAttachment = (attachment) => {
  editingAttachment.value = attachment
  editForm.value = {
    title: attachment.title || '',
    description: attachment.description || '',
    attachment_type: attachment.attachment_type
  }
  editDialogOpen.value = true
}

const saveAttachment = async () => {
  if (!editingAttachment.value) return

  saving.value = true
  try {
    const response = await api.put(
      `/api/v1/components/${props.componentId}/attachments/${editingAttachment.value.id}`,
      editForm.value
    )

    // Update local state
    const index = attachments.value.findIndex(att => att.id === editingAttachment.value.id)
    if (index !== -1) {
      attachments.value[index] = { ...attachments.value[index], ...response.data }
    }

    emit('attachment-updated', response.data)
    editDialogOpen.value = false

    $q.notify({
      type: 'positive',
      message: 'Attachment updated'
    })
  } catch (error) {
    console.error('Failed to update attachment:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to update attachment'
    })
  } finally {
    saving.value = false
  }
}

const confirmDelete = (attachment) => {
  deletingAttachment.value = attachment
  deleteConfirmOpen.value = true
}

const deleteAttachment = async () => {
  if (!deletingAttachment.value) return

  deleting.value = true
  try {
    await api.delete(
      `/api/v1/components/${props.componentId}/attachments/${deletingAttachment.value.id}`
    )

    // Remove from local state
    const index = attachments.value.findIndex(att => att.id === deletingAttachment.value.id)
    if (index !== -1) {
      attachments.value.splice(index, 1)
    }

    emit('attachment-deleted', deletingAttachment.value)
    deleteConfirmOpen.value = false

    $q.notify({
      type: 'positive',
      message: 'Attachment deleted'
    })
  } catch (error) {
    console.error('Failed to delete attachment:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to delete attachment'
    })
  } finally {
    deleting.value = false
  }
}

const onUploadSuccess = () => {
  showUploadDialog.value = false
  loadAttachments() // Refresh the attachments list
}

const onUploadError = (error) => {
  console.error('Upload error:', error)
}

const onImageError = (event) => {
  console.error('Image load error:', event)
  // Could show a placeholder image here
}

// Lifecycle
onMounted(() => {
  if (props.autoLoad && props.componentId) {
    loadAttachments()
  }
})

// Watch for component ID changes
watch(() => props.componentId, (newId) => {
  if (newId && props.autoLoad) {
    loadAttachments()
  }
})

// Expose methods for parent components
defineExpose({
  loadAttachments,
  refreshAttachments: loadAttachments
})
</script>

<style scoped>
.attachment-gallery {
  width: 100%;
}

.attachments-grid {
  width: 100%;
}

.attachment-card {
  width: 150px;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.attachment-card:hover {
  transform: translateY(-2px);
}

.image-card {
  border: 1px solid #e0e0e0;
}

.image-container {
  position: relative;
  width: 100%;
  height: 120px;
  overflow: hidden;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.primary-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background-color: rgba(0, 0, 0, 0.7);
  border-radius: 12px;
  padding: 2px 6px;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.attachment-card:hover .image-overlay {
  opacity: 1;
}

.attachment-info {
  padding: 8px;
  border-top: 1px solid #e0e0e0;
}

.image-viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.image-viewer-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.8);
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

.image-viewer-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 16px 80px;
}

.viewer-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-viewer-nav {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.8);
}

.nav-info {
  color: white;
  font-size: 14px;
}
</style>