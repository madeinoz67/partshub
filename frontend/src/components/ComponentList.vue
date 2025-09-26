<template>
  <div class="component-list">
    <!-- Header with search and filters -->
    <q-card class="q-mb-sm">
      <q-card-section class="q-pa-sm">
        <div class="row q-gutter-md items-center">
          <div class="col-md-4 col-xs-12">
            <q-input
              v-model="searchQuery"
              outlined
              dense
              placeholder="Search components..."
              debounce="300"
              @update:model-value="onSearch"
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
              <template v-slot:append>
                <q-btn
                  v-if="!searchQuery"
                  icon="qr_code_scanner"
                  flat
                  round
                  dense
                  @click="openBarcodeScanner"
                  color="primary"
                  class="q-mr-xs"
                >
                  <q-tooltip>Scan barcode to search components</q-tooltip>
                </q-btn>
                <q-icon
                  v-if="searchQuery"
                  name="clear"
                  class="cursor-pointer"
                  @click="clearSearch"
                />
              </template>
            </q-input>
          </div>

          <div class="col-md-2 col-xs-12">
            <q-select
              v-model="selectedCategory"
              outlined
              dense
              emit-value
              map-options
              clearable
              label="Category"
              :options="categoryOptions"
              @update:model-value="onCategoryFilter"
            />
          </div>

          <div class="col-md-2 col-xs-12">
            <q-select
              v-model="selectedStockStatus"
              outlined
              dense
              emit-value
              map-options
              clearable
              label="Stock Status"
              :options="stockStatusOptions"
              @update:model-value="onStockFilter"
            />
          </div>


          <div class="col-md-1 col-xs-12" v-if="canPerformCrud()">
            <q-btn
              color="primary"
              icon="add"
              dense
              @click="$emit('create-component')"
            >
              Add Component
            </q-btn>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Statistics Cards -->
    <div class="row q-gutter-xs q-mb-sm no-wrap">
      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 q-mb-none">{{ totalComponents }}</div>
            <div class="text-overline text-grey">Total</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-orange q-mb-none">{{ lowStockComponents.length }}</div>
            <div class="text-overline text-grey">Low Stock</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-red q-mb-none">{{ outOfStockComponents.length }}</div>
            <div class="text-overline text-grey">Out of Stock</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col">
        <q-card class="mini-stats">
          <q-card-section class="q-pa-xs text-center">
            <div class="text-subtitle2 text-green q-mb-none">{{ components.length - outOfStockComponents.length }}</div>
            <div class="text-overline text-grey">Available</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Loading state -->
    <q-inner-loading :showing="loading">
      <q-spinner color="primary" size="50px" />
    </q-inner-loading>

    <!-- Error message -->
    <q-banner v-if="error" class="text-white bg-negative q-mb-md">
      <template v-slot:avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
      <template v-slot:action>
        <q-btn flat color="white" label="Dismiss" @click="clearError" />
      </template>
    </q-banner>

    <!-- Components Table -->
    <q-table
      :rows="components"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="{ sortBy: 'updated_at', descending: true, page: 1, rowsPerPage: 25 }"
      :rows-per-page-options="[25, 50, 100]"
      v-model:expanded="expanded"
      dense
      @row-click="onRowClick"
      class="compact-table"
    >
      <!-- Use body slot for internal expansion model -->
      <template v-slot:body="props">
        <!-- Regular row -->
        <q-tr :props="props">
          <!-- Expand button column -->
          <q-td auto-width>
            <q-btn
              size="sm"
              color="accent"
              round
              dense
              flat
              @click="toggleExpand(props)"
              :icon="props.expand ? 'keyboard_arrow_down' : 'keyboard_arrow_right'"
            />
          </q-td>

          <!-- Component name column -->
          <q-td key="name" :props="props">
            <div class="text-weight-medium">{{ props.row.name }}</div>
            <div v-if="props.row.part_number" class="text-caption text-grey">
              PN: {{ props.row.part_number }}
            </div>
          </q-td>

          <!-- Stock column -->
          <q-td key="stock" :props="props">
            <q-chip
              :color="getStockStatusColor(props.row)"
              text-color="white"
              :label="props.row.quantity_on_hand"
              size="sm"
            />
            <div class="text-caption text-grey">
              Min: {{ props.row.minimum_stock }}
            </div>
          </q-td>

          <!-- Location column -->
          <q-td key="location" :props="props">
            <div v-if="props.row.storage_location">
              <q-chip
                outline
                :label="props.row.storage_location.name"
                size="sm"
                class="q-mb-xs"
              />
              <div class="text-caption text-grey">
                {{ props.row.storage_location.location_hierarchy }}
              </div>
            </div>
            <div v-else class="text-caption text-grey">
              No location assigned
            </div>
          </q-td>

          <!-- Category column -->
          <q-td key="category" :props="props">
            <q-chip
              v-if="props.row.category"
              outline
              color="primary"
              :label="props.row.category.name"
              size="sm"
            />
            <span v-else class="text-caption text-grey">Uncategorized</span>
          </q-td>

          <!-- Value column -->
          <q-td key="value" :props="props">
            <div v-if="props.row.value || props.row.component_type">
              <div v-if="props.row.value" class="text-weight-medium">
                {{ props.row.value }}
              </div>
              <div v-if="props.row.component_type" class="text-caption text-grey">
                {{ props.row.component_type }}
              </div>
            </div>
            <span v-else class="text-caption text-grey">—</span>
          </q-td>

          <!-- Manufacturer column -->
          <q-td key="manufacturer" :props="props">
            {{ props.row.manufacturer || '—' }}
          </q-td>

          <!-- Attachments column -->
          <q-td key="attachments" :props="props">
            <div class="row justify-center q-gutter-xs">
              <q-icon
                v-for="attachment in getAttachmentIcons(props.row.attachments)"
                :key="attachment.type"
                :name="attachment.icon"
                :color="attachment.color"
                size="sm"
                :title="attachment.tooltip"
              />
              <span v-if="!props.row.attachments?.length" class="text-caption text-grey">—</span>
            </div>
          </q-td>

          <!-- Updated at column -->
          <q-td key="updated_at" :props="props">
            {{ new Date(props.row.updated_at).toLocaleDateString() }}
          </q-td>

          <!-- Actions column -->
          <q-td key="actions" :props="props" @click.stop>
            <q-btn-dropdown
              flat
              dense
              icon="more_vert"
              size="sm"
              @click.stop
            >
              <q-list>
                <q-item
                  clickable
                  v-close-popup
                  @click="$emit('view-component', props.row)"
                >
                  <q-item-section avatar>
                    <q-icon name="visibility" />
                  </q-item-section>
                  <q-item-section>View Details</q-item-section>
                </q-item>

                <template v-if="canPerformCrud()">
                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('edit-component', props.row)"
                  >
                    <q-item-section avatar>
                      <q-icon name="edit" />
                    </q-item-section>
                    <q-item-section>Edit</q-item-section>
                  </q-item>

                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('update-stock', props.row)"
                  >
                    <q-item-section avatar>
                      <q-icon name="inventory" />
                    </q-item-section>
                    <q-item-section>Update Stock</q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item
                    clickable
                    v-close-popup
                    @click="$emit('delete-component', props.row)"
                    class="text-negative"
                  >
                    <q-item-section avatar>
                      <q-icon name="delete" />
                    </q-item-section>
                    <q-item-section>Delete</q-item-section>
                  </q-item>
                </template>
              </q-list>
            </q-btn-dropdown>
          </q-td>
        </q-tr>

        <!-- Expansion row -->
        <q-tr v-if="props.expand" :props="props">
          <q-td colspan="100%" style="padding: 0;">
            <div style="background: #f8f9fa; border-left: 4px solid #1976d2; margin: 0;">
              <div class="row no-wrap" style="min-height: 400px;">
                <!-- PartsBox-style Menu -->
                <div class="col-auto" style="width: 200px; background: #ffffff; border-right: 1px solid #e0e0e0;">
                  <q-list separator>
                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'info')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'info' }">
                      <q-item-section avatar>
                        <q-icon name="info" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Part info</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'images')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'images' }">
                      <q-item-section avatar>
                        <q-icon name="image" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Images</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'datasheets')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'datasheets' }">
                      <q-item-section avatar>
                        <q-icon name="description" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Files</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'stock')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'stock' }">
                      <q-item-section avatar>
                        <q-icon name="inventory_2" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Stock</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'add-stock')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'add-stock' }">
                      <q-item-section avatar>
                        <q-icon name="add_box" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Add Stock</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'remove-stock')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'remove-stock' }">
                      <q-item-section avatar>
                        <q-icon name="remove_circle" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Remove Stock</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'move-stock')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'move-stock' }">
                      <q-item-section avatar>
                        <q-icon name="move_up" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Move Stock</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'history')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'history' }">
                      <q-item-section avatar>
                        <q-icon name="history" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Stock History</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item clickable v-ripple @click="setActiveTab(props.row.id, 'purchasing')" :class="{ 'bg-blue-1': getActiveTab(props.row.id) === 'purchasing' }">
                      <q-item-section avatar>
                        <q-icon name="shopping_cart" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Purchasing</q-item-label>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>

                <!-- Content Area -->
                <div class="col" style="padding: 16px; background: #ffffff;">
                  <!-- Part Info Tab -->
                  <div v-if="getActiveTab(props.row.id) === 'info'">
                    <div class="text-h6 q-mb-md">{{ props.row.name }}</div>
                    <div class="text-subtitle2 text-grey q-mb-md">{{ props.row.part_number || 'No part number' }}</div>

                    <div class="row q-gutter-md no-wrap">
                      <div class="col-8">
                        <div class="q-gutter-sm">
                          <div class="row" v-if="props.row.manufacturer">
                            <div class="col-4 text-weight-medium">Manufacturer:</div>
                            <div class="col-8">{{ props.row.manufacturer }}</div>
                          </div>
                          <div class="row" v-if="props.row.component_type">
                            <div class="col-4 text-weight-medium">Type:</div>
                            <div class="col-8">{{ props.row.component_type }}</div>
                          </div>
                          <div class="row" v-if="props.row.value">
                            <div class="col-4 text-weight-medium">Value:</div>
                            <div class="col-8">{{ props.row.value }}</div>
                          </div>
                          <div class="row" v-if="props.row.package">
                            <div class="col-4 text-weight-medium">Package:</div>
                            <div class="col-8">{{ props.row.package }}</div>
                          </div>
                          <div class="row">
                            <div class="col-4 text-weight-medium">Category:</div>
                            <div class="col-8">
                              <q-chip
                                v-if="props.row.category"
                                outline
                                color="primary"
                                :label="props.row.category.name"
                                size="sm"
                              />
                              <span v-else class="text-grey">Uncategorized</span>
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-4 text-weight-medium">Tags:</div>
                            <div class="col-8">
                              <div v-if="props.row.tags && props.row.tags.length > 0" class="q-gutter-xs">
                                <q-chip
                                  v-for="tag in props.row.tags"
                                  :key="tag.id"
                                  outline
                                  color="secondary"
                                  :label="tag.name"
                                  size="sm"
                                />
                              </div>
                              <span v-else class="text-grey">No tags</span>
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-4 text-weight-medium">Location:</div>
                            <div class="col-8">
                              <div v-if="props.row.storage_location">
                                <q-chip outline :label="props.row.storage_location.name" size="sm" />
                                <div class="text-caption text-grey">
                                  {{ props.row.storage_location.location_hierarchy }}
                                </div>
                              </div>
                              <span v-else class="text-grey">No location assigned</span>
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-4 text-weight-medium">Total Stock:</div>
                            <div class="col-8">
                              <q-chip
                                :color="getStockStatusColor(props.row)"
                                text-color="white"
                                :label="props.row.quantity_on_hand"
                                size="md"
                              />
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-4 text-weight-medium">Min Stock:</div>
                            <div class="col-8">{{ props.row.minimum_stock }}</div>
                          </div>
                        </div>
                      </div>

                      <!-- Primary Image Column -->
                      <div class="col-4">
                        <div class="text-center">
                          <div v-if="getPrimaryImage(props.row.id, props.row.attachments)" class="primary-image-container">
                            <q-card flat bordered>
                              <div class="relative-position" style="height: 200px; overflow: hidden;">
                                <img
                                  :src="getThumbnailUrl(getPrimaryImage(props.row.id, props.row.attachments).id, props.row.id)"
                                  :alt="getPrimaryImage(props.row.id, props.row.attachments).filename"
                                  class="absolute-center"
                                  style="width: 100%; height: 100%; object-fit: contain; background: #f5f5f5;"
                                  @click="viewImage(getPrimaryImage(props.row.id, props.row.attachments))"
                                  @error="() => console.log('Primary image load error:', getPrimaryImage(props.row.id, props.row.attachments), 'URL:', getThumbnailUrl(getPrimaryImage(props.row.id, props.row.attachments).id, props.row.id))"
                                />
                              </div>
                              <q-card-section class="q-pa-xs">
                                <div class="text-caption text-center text-weight-medium">
                                  Primary Image
                                </div>
                              </q-card-section>
                            </q-card>
                          </div>
                          <div v-else class="primary-image-placeholder">
                            <q-card flat bordered>
                              <div class="relative-position" style="height: 200px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;">
                                <div class="text-center text-grey-5">
                                  <q-icon name="image" size="3rem" />
                                  <div class="q-mt-sm">No primary image</div>
                                </div>
                              </div>
                              <q-card-section class="q-pa-xs">
                                <div class="text-caption text-center text-grey">
                                  No Image
                                </div>
                              </q-card-section>
                            </q-card>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div v-if="props.row.description || props.row.notes" class="q-mt-md">
                      <div v-if="props.row.description">
                        <div class="text-h6 q-mb-sm">Description</div>
                        <div class="text-body2 q-mb-md">{{ props.row.description }}</div>
                      </div>
                      <div v-if="props.row.notes">
                        <div class="text-h6 q-mb-sm">Notes</div>
                        <div class="text-body2" style="white-space: pre-wrap;">{{ props.row.notes }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Images Tab -->
                  <div v-else-if="getActiveTab(props.row.id) === 'images'">
                    <div class="text-h6 text-weight-medium q-mb-md">Images</div>
                    <div v-if="getImageAttachments(props.row.id, props.row.attachments).length > 0">
                      <div class="row q-gutter-md">
                        <div
                          v-for="image in getImageAttachments(props.row.id, props.row.attachments)"
                          :key="image.id"
                          class="col-md-3 col-xs-6"
                        >
                          <q-card flat bordered class="cursor-pointer image-card" @click="viewImage(image)">
                            <div class="relative-position" style="height: 150px; overflow: hidden;">
                              <img
                                :src="getThumbnailUrl(image.id, props.row.id)"
                                :alt="image.filename"
                                class="absolute-center"
                                style="width: 100%; height: 100%; object-fit: cover;"
                                @error="(event) => console.log('Image load error:', event, 'URL:', getThumbnailUrl(image.id, props.row.id))"
                              />

                              <!-- Admin Delete Button Overlay -->
                              <div v-if="canPerformCrud()" class="image-overlay absolute-full flex flex-center">
                                <q-btn
                                  round
                                  color="negative"
                                  icon="delete"
                                  size="sm"
                                  @click.stop="confirmDeleteAttachment(image, props.row.id)"
                                  class="delete-btn"
                                >
                                  <q-tooltip>Delete Image</q-tooltip>
                                </q-btn>
                              </div>

                              <q-tooltip>{{ image.filename }}</q-tooltip>
                            </div>
                            <q-card-section class="q-pa-xs">
                              <div class="text-caption text-center text-weight-medium">
                                {{ getFileDisplayName(image.filename) }}
                              </div>
                              <div class="text-caption text-center text-grey">
                                {{ formatFileSize(image.file_size || image.size || image.fileSize || 0) }}
                              </div>
                            </q-card-section>
                          </q-card>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-grey text-center q-pa-lg">
                      <q-icon name="image" size="3rem" color="grey-4" />
                      <div class="q-mt-md">No images</div>
                    </div>

                    <!-- File Upload for Images - Admin Only -->
                    <div v-if="canPerformCrud()" class="q-mt-lg">
                      <FileUpload
                        :component-id="props.row.id"
                        title="Upload Images"
                        accepted-types="image/*"
                        @upload-success="() => handleUploadSuccess({ componentId: props.row.id })"
                      />
                    </div>
                  </div>

                  <!-- Datasheets Tab -->
                  <div v-else-if="getActiveTab(props.row.id) === 'datasheets'">
                    <div class="text-h6 text-weight-medium q-mb-md">Data sheets</div>
                    <div v-if="getDatasheetAttachments(props.row.id, props.row.attachments).length > 0">
                      <q-list bordered separator>
                        <q-item
                          v-for="datasheet in getDatasheetAttachments(props.row.id, props.row.attachments)"
                          :key="datasheet.id"
                          clickable
                          @click="downloadAttachment(datasheet)"
                        >
                          <q-item-section avatar>
                            <q-avatar color="red" text-color="white">
                              <q-icon name="picture_as_pdf" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>{{ getFileDisplayName(datasheet.filename) }}</q-item-label>
                            <q-item-label caption>
                              {{ datasheet.title || 'Datasheet' }} • {{ formatFileSize(datasheet.file_size || 0) }}
                            </q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <div class="row q-gutter-xs">
                              <q-btn
                                flat
                                round
                                icon="download"
                                color="primary"
                                size="sm"
                                @click.stop="downloadAttachment(datasheet)"
                              >
                                <q-tooltip>Download</q-tooltip>
                              </q-btn>
                              <q-btn
                                v-if="canPerformCrud()"
                                flat
                                round
                                icon="delete"
                                color="negative"
                                size="sm"
                                @click.stop="confirmDeleteAttachment(datasheet, props.row.id)"
                              >
                                <q-tooltip>Delete File</q-tooltip>
                              </q-btn>
                            </div>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </div>
                    <div v-else class="text-grey text-center q-pa-lg">
                      <q-icon name="picture_as_pdf" size="3rem" color="grey-4" />
                      <div class="q-mt-md">No data sheets</div>
                    </div>

                    <!-- Other Documents Section - Only Show in Datasheets tab if Files Exist -->
                    <div v-if="props.row.attachments && getOtherAttachments(props.row.attachments).length > 0" class="q-mt-lg">
                      <div class="text-h6 text-weight-medium q-mb-md">Other Documents</div>
                      <q-list bordered separator>
                        <q-item
                          v-for="document in getOtherAttachments(props.row.attachments)"
                          :key="document.id"
                          clickable
                          @click="downloadAttachment(document)"
                        >
                          <q-item-section avatar>
                            <q-avatar color="grey" text-color="white">
                              <q-icon name="description" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>{{ getFileDisplayName(document.filename) }}</q-item-label>
                            <q-item-label caption>
                              {{ document.title || 'Document' }} • {{ formatFileSize(document.file_size || document.size || 0) }}
                            </q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <div class="row q-gutter-xs">
                              <q-btn
                                flat
                                round
                                icon="download"
                                color="primary"
                                size="sm"
                                @click.stop="downloadAttachment(document)"
                              >
                                <q-tooltip>Download</q-tooltip>
                              </q-btn>
                              <q-btn
                                v-if="canPerformCrud()"
                                flat
                                round
                                icon="delete"
                                color="negative"
                                size="sm"
                                @click.stop="confirmDeleteAttachment(document, props.row.id)"
                              >
                                <q-tooltip>Delete Document</q-tooltip>
                              </q-btn>
                            </div>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </div>

                    <!-- File Upload for Files - Admin Only -->
                    <div v-if="canPerformCrud()" class="q-mt-lg">
                      <FileUpload
                        :component-id="props.row.id"
                        title="Upload Files"
                        accepted-types="image/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        @upload-success="() => handleUploadSuccess({ componentId: props.row.id })"
                      />
                    </div>
                  </div>

                  <!-- Stock Tab -->
                  <div v-else-if="getActiveTab(props.row.id) === 'stock'">
                    <div class="text-h6 q-mb-md">Current Stock</div>
                    <div class="row q-gutter-md">
                      <div class="col-md-6 col-xs-12">
                        <q-card flat bordered>
                          <q-card-section>
                            <div class="text-center">
                              <div class="text-h3" :class="getStockStatusColor(props.row) === 'negative' ? 'text-red' : getStockStatusColor(props.row) === 'warning' ? 'text-orange' : 'text-green'">
                                {{ props.row.quantity_on_hand }}
                              </div>
                              <div class="text-caption text-grey">Total Stock</div>
                            </div>
                          </q-card-section>
                        </q-card>
                      </div>
                      <div class="col-md-6 col-xs-12">
                        <q-card flat bordered>
                          <q-card-section>
                            <div class="text-center">
                              <div class="text-h4 text-grey">{{ props.row.minimum_stock }}</div>
                              <div class="text-caption text-grey">Minimum Stock</div>
                            </div>
                          </q-card-section>
                        </q-card>
                      </div>
                    </div>
                  </div>

                  <!-- Other tabs placeholder -->
                  <div v-else>
                    <div class="text-h6 q-mb-md">{{ getActiveTab(props.row.id).replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</div>
                    <div class="text-grey">This feature is coming soon...</div>
                  </div>
                </div>
              </div>
            </div>
          </q-td>
        </q-tr>
      </template>


      <!-- No data message -->
      <template v-slot:no-data="{ message }">
        <div class="full-width row flex-center q-gutter-sm">
          <q-icon size="2em" name="inventory_2" />
          <span>{{ message || 'No components found' }}</span>
        </div>
      </template>
    </q-table>

    <!-- Barcode Scanner Component -->
    <BarcodeScanner
      ref="barcodeScannerRef"
      @scan-result="handleBarcodeScanned"
      :search-components="false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useQuasar } from 'quasar'
import { useComponentsStore } from '../stores/components'
import { useAuth } from '../composables/useAuth'
import FileUpload from './FileUpload.vue'
import BarcodeScanner from './BarcodeScanner.vue'
import { api } from '../boot/axios'
import type { Component } from '../services/api'

// Component props
interface Props {
  embedded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  embedded: false
})

// Component emits
const emit = defineEmits<{
  'create-component': []
  'view-component': [component: Component]
  'edit-component': [component: Component]
  'update-stock': [component: Component]
  'delete-component': [component: Component]
}>()

// Store
const componentsStore = useComponentsStore()
const { canPerformCrud } = useAuth()
const $q = useQuasar()
const {
  components,
  loading,
  error,
  totalComponents,
  currentPage,
  totalPages,
  itemsPerPage,
  lowStockComponents,
  outOfStockComponents
} = storeToRefs(componentsStore)

// Local state
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedStockStatus = ref('')
const sortBy = ref('updated_at')
const sortOrder = ref<'asc' | 'desc'>('desc')
const expanded = ref<string[]>([])
const activeTab = ref<Record<string, string>>({}) // Tab state per component ID
const detailedAttachments = ref<Record<string, any[]>>({})
const barcodeScannerRef = ref()

// Table configuration
const columns = [
  {
    name: 'expand',
    label: '',
    field: 'expand',
    sortable: false,
    required: true,
    align: 'left' as const,
    style: 'width: 40px',
    headerStyle: 'width: 40px'
  },
  {
    name: 'name',
    required: true,
    label: 'Component',
    align: 'left' as const,
    field: 'name',
    sortable: true
  },
  {
    name: 'stock',
    label: 'Stock',
    align: 'center' as const,
    field: 'quantity_on_hand',
    sortable: true
  },
  {
    name: 'location',
    label: 'Location',
    align: 'left' as const,
    field: (row: Component) => row.storage_location?.name || '',
    sortable: true
  },
  {
    name: 'category',
    label: 'Category',
    align: 'left' as const,
    field: (row: Component) => row.category?.name || '',
    sortable: true
  },
  {
    name: 'value',
    label: 'Value/Type',
    align: 'left' as const,
    field: 'value',
    sortable: true
  },
  {
    name: 'manufacturer',
    label: 'Manufacturer',
    align: 'left' as const,
    field: 'manufacturer',
    sortable: true
  },
  {
    name: 'attachments',
    label: 'Files',
    align: 'center' as const,
    field: (row: Component) => row.attachments?.length || 0,
    sortable: true
  },
  {
    name: 'updated_at',
    label: 'Last Updated',
    align: 'center' as const,
    field: 'updated_at',
    sortable: true,
    format: (val: string) => new Date(val).toLocaleDateString(),
    sort: (a: Component, b: Component) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center' as const
  }
]

// Using client-side pagination and sorting

// Options for filters
const categoryOptions = computed(() => {
  const categories = new Set(
    components.value
      .map(c => c.category?.name)
      .filter(Boolean)
  )
  return Array.from(categories).map(cat => ({
    label: cat,
    value: cat
  }))
})

const stockStatusOptions = [
  { label: 'Low Stock', value: 'low' },
  { label: 'Out of Stock', value: 'out' },
  { label: 'Available', value: 'available' }
]

// Methods
const getStockStatusColor = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

const getAttachmentIcons = (attachments: any[] = []) => {
  if (!attachments || attachments.length === 0) return []

  const icons = []

  // Check for datasheet/PDF files
  const hasDatasheet = attachments.some(att =>
    att.filename?.toLowerCase().includes('.pdf') ||
    att.attachment_type === 'datasheet'
  )
  if (hasDatasheet) {
    icons.push({
      type: 'datasheet',
      icon: 'picture_as_pdf',
      color: 'red',
      tooltip: 'Has datasheet'
    })
  }

  // Check for image files
  const hasImages = attachments.some(att =>
    att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/i) ||
    att.attachment_type === 'image'
  )
  if (hasImages) {
    icons.push({
      type: 'image',
      icon: 'image',
      color: 'blue',
      tooltip: 'Has images'
    })
  }

  // Check for other documents
  const hasDocuments = attachments.some(att =>
    att.attachment_type === 'document' &&
    !att.filename?.toLowerCase().includes('.pdf')
  )
  if (hasDocuments) {
    icons.push({
      type: 'document',
      icon: 'description',
      color: 'grey',
      tooltip: 'Has documents'
    })
  }

  return icons
}

const onSearch = (query: string) => {
  componentsStore.searchComponents(query)
}

const clearSearch = () => {
  searchQuery.value = ''
  componentsStore.searchComponents('')
}

const onCategoryFilter = (category: string) => {
  componentsStore.filterByCategory(category)
}

const onStockFilter = (status: 'low' | 'out' | 'available' | undefined) => {
  componentsStore.filterByStockStatus(status)
}

// Client-side table with no server-side requests needed for sorting

const getAttachmentIcon = (attachment: any) => {
  const filename = attachment.filename?.toLowerCase() || ''
  if (filename.includes('.pdf') || attachment.attachment_type === 'datasheet') {
    return 'picture_as_pdf'
  }
  if (filename.match(/\.(jpg|jpeg|png|gif|webp)$/i) || attachment.attachment_type === 'image') {
    return 'image'
  }
  return 'description'
}

const downloadAttachment = (attachment: any) => {
  // This would typically trigger a download
  console.log('Download attachment:', attachment.filename)
  // emit('download-attachment', attachment) // Could emit to parent if needed
}

const setActiveTab = (componentId: string, tab: string) => {
  activeTab.value[componentId] = tab
}

const getActiveTab = (componentId: string) => {
  return activeTab.value[componentId] || 'info'
}

const getDetailedAttachments = (componentId: string) => {
  return detailedAttachments.value[componentId] || []
}

const getImageAttachments = (componentId: string, basicAttachments?: any[]) => {
  const detailed = getDetailedAttachments(componentId)

  // If we don't have detailed attachments, fetch them now
  if (detailed.length === 0 && basicAttachments && basicAttachments.length > 0) {
    fetchDetailedAttachments(componentId)
  }

  const attachments = detailed.length > 0 ? detailed : (basicAttachments || [])
  console.log('Getting image attachments for component', componentId)
  console.log('- detailed:', detailed)
  console.log('- basic:', basicAttachments)
  console.log('- final attachments:', attachments)

  // Log each attachment structure
  if (attachments) {
    attachments.forEach((att, index) => {
      console.log(`Attachment ${index}:`, {
        id: att.id,
        filename: att.filename,
        file_size: att.file_size,
        size: att.size,
        fileSize: att.fileSize,
        attachment_type: att.attachment_type,
        mime_type: att.mime_type,
        allProperties: Object.keys(att)
      })
    })
  }

  return attachments.filter(att =>
    att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i) ||
    att.attachment_type === 'image'
  )
}

const getDatasheetAttachments = (componentId: string, basicAttachments?: any[]) => {
  const detailed = getDetailedAttachments(componentId)
  const attachments = detailed.length > 0 ? detailed : (basicAttachments || [])
  return attachments.filter(att =>
    att.filename?.toLowerCase().includes('.pdf') ||
    att.attachment_type === 'datasheet'
  )
}

const getOtherAttachments = (attachments: any[]) => {
  return attachments.filter(att => {
    const isImage = att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i) || att.attachment_type === 'image'
    const isDatasheet = att.filename?.toLowerCase().includes('.pdf') || att.attachment_type === 'datasheet'
    return !isImage && !isDatasheet
  })
}

const getPrimaryImage = (componentId: string, basicAttachments?: any[]) => {
  const detailed = getDetailedAttachments(componentId)
  const attachments = detailed.length > 0 ? detailed : (basicAttachments || [])

  console.log('getPrimaryImage for component', componentId, 'detailed:', detailed, 'basic:', basicAttachments, 'using:', attachments)

  // If we don't have detailed attachments but have basic ones, fetch detailed data
  if (detailed.length === 0 && basicAttachments && basicAttachments.length > 0) {
    console.log('No detailed attachments, fetching...')
    fetchDetailedAttachments(componentId)
    return null // Return null for now, will update reactively once data loads
  }

  // First try to find an image marked as primary
  const primaryImage = attachments.find(att =>
    att.is_primary_image &&
    (att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i) || att.attachment_type === 'image')
  )

  if (primaryImage) {
    console.log('Found primary image:', primaryImage)
    return primaryImage
  }

  // If no primary image, return the first available image
  const firstImage = attachments.find(att =>
    att.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i) || att.attachment_type === 'image'
  )

  console.log('Using first image:', firstImage)
  return firstImage || null
}

const getFileDisplayName = (filename: string) => {
  if (!filename) return 'Unnamed file'
  // Remove file extension and clean up the name
  const nameWithoutExt = filename.replace(/\.[^/.]+$/, '')
  return nameWithoutExt.length > 20 ? nameWithoutExt.substring(0, 20) + '...' : nameWithoutExt
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getThumbnailUrl = (attachmentId: string, componentId: string) => {
  return `http://localhost:8000/api/v1/components/${componentId}/attachments/${attachmentId}/thumbnail`
}

const handleImageError = (image: any) => {
  // Set error flag on the image object to trigger Vue's reactivity
  image.hasError = true
}

// Barcode scanner functions
const openBarcodeScanner = () => {
  if (barcodeScannerRef.value) {
    barcodeScannerRef.value.startScanning()
  }
}

const handleBarcodeScanned = (scanResult: any) => {
  // Set the scanned data as search query
  if (scanResult && scanResult.data) {
    // Use the scanned barcode data directly
    searchQuery.value = scanResult.data
  }

  // Trigger search through the store
  onSearch(searchQuery.value)

  // Show notification
  $q.notify({
    type: 'positive',
    message: `Barcode scanned: ${scanResult.data}`,
    timeout: 2000
  })
}

const toggleExpand = async (props: any) => {
  console.log('Toggle expand called for component:', props.row.id, 'current expand state:', props.expand)
  props.expand = !props.expand
  console.log('New expand state:', props.expand)

  // If expanding and we don't have detailed attachments, fetch them
  if (props.expand && !detailedAttachments.value[props.row.id]) {
    console.log('Fetching detailed attachments because row is expanding and no cached data exists')
    await fetchDetailedAttachments(props.row.id)
  } else if (props.expand) {
    console.log('Row expanding but detailed attachments already cached:', detailedAttachments.value[props.row.id])
  } else {
    console.log('Row collapsing, no API call needed')
  }
}

const fetchDetailedAttachments = async (componentId: string) => {
  try {
    console.log('Fetching detailed attachments for component:', componentId)
    const response = await api.get(`/api/v1/components/${componentId}/attachments`)
    console.log('API response:', response)
    console.log('Response data:', response.data)
    const attachments = response.data.attachments || response.data || []
    console.log('Parsed attachments:', attachments)
    detailedAttachments.value[componentId] = attachments
  } catch (error) {
    console.error('Failed to fetch detailed attachments for component', componentId, ':', error)
    console.error('Error details:', error.response?.data, error.response?.status)
    detailedAttachments.value[componentId] = []
  }
}

const viewImage = (image: any) => {
  // This would typically open an image viewer/lightbox
  console.log('View image:', image.filename)
  // For now, just download it
  downloadAttachment(image)
}


const onRowClick = (evt: Event, row: Component) => {
  // Don't navigate to detail page on row click when we have expandable rows
  // User can click "View Full Details" button instead
}

const clearError = () => {
  componentsStore.clearError()
}

const handleUploadSuccess = async (data: any) => {
  // Refresh the component data to show newly uploaded files
  await componentsStore.fetchComponents()

  // Also refresh detailed attachments for the specific component if it's currently expanded
  if (data && data.componentId) {
    await fetchDetailedAttachments(data.componentId)
  }
}

const confirmDeleteAttachment = (attachment: any, componentId: string) => {
  // Use Quasar's Dialog plugin for confirmation
  $q.dialog({
    title: 'Delete Attachment',
    message: `Are you sure you want to delete "${attachment.filename || attachment.original_filename}"? This action cannot be undone.`,
    cancel: true,
    persistent: true,
    color: 'negative'
  }).onOk(() => {
    deleteAttachment(attachment, componentId)
  })
}

const deleteAttachment = async (attachment: any, componentId: string) => {
  try {
    await api.delete(`/api/v1/components/${componentId}/attachments/${attachment.id}`)

    // Refresh the component data
    await componentsStore.fetchComponents()

    // Refresh detailed attachments for this component
    await fetchDetailedAttachments(componentId)

    // Show success message
    $q.notify({
      type: 'positive',
      message: 'Attachment deleted successfully',
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to delete attachment:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to delete attachment',
      position: 'top'
    })
  }
}

// Lifecycle
onMounted(() => {
  componentsStore.fetchComponents()
})
</script>

<style scoped>
.component-list {
  min-height: 400px;
}

.compact-table {
  font-size: 0.875rem;
}

.compact-table :deep(.q-table__top) {
  padding: 8px 16px;
}

.compact-table :deep(.q-td) {
  padding: 2px 6px;
  font-size: 0.8rem;
  height: 24px;
}

.compact-table :deep(.q-th) {
  padding: 3px 6px;
  font-size: 0.8rem;
  font-weight: 600;
  height: 28px;
}

.compact-table :deep(tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s;
  height: 24px;
}

.compact-table :deep(tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.04);
}

.compact-table :deep(.q-chip) {
  font-size: 0.7rem;
  padding: 1px 4px;
  min-height: 16px;
}

.mini-stats {
  border-radius: 8px;
  min-height: 60px;
  max-height: 60px;
}

.mini-stats .q-card__section {
  padding: 8px 12px !important;
}

.mini-stats .text-subtitle2 {
  font-size: 1.1rem;
  line-height: 1.2;
  font-weight: 600;
}

.mini-stats .text-overline {
  font-size: 0.75rem;
  line-height: 1;
  letter-spacing: 0.5px;
  margin-top: 2px;
}

/* Image card with delete overlay */
.image-card {
  position: relative;
}

.image-overlay {
  background: rgba(0, 0, 0, 0.7);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-card:hover .image-overlay {
  opacity: 1;
}

.delete-btn {
  background: rgba(244, 67, 54, 0.9) !important;
}

/* Primary image styling */
.primary-image-container .q-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
}

.primary-image-container .q-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
}

.primary-image-placeholder .q-card {
  border-radius: 8px;
  border: 2px dashed #e0e0e0;
}
</style>