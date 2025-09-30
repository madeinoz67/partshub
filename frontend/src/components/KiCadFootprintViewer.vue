<template>
  <div class="kicad-footprint-viewer">
    <!-- Header -->
    <div class="viewer-header q-mb-md">
      <div class="text-h6">KiCad Footprint</div>
      <div v-if="footprintData" class="text-caption text-grey">
        {{ footprintData.footprint_library }}/{{ footprintData.footprint_name }}
      </div>
    </div>

    <!-- Loading state -->
    <q-inner-loading :showing="loading">
      <q-spinner color="primary" size="50px" />
    </q-inner-loading>

    <!-- Error state -->
    <q-banner v-if="error && !loading" class="text-white bg-negative q-mb-md">
      <template #avatar>
        <q-icon name="error" />
      </template>
      {{ error }}
    </q-banner>

    <!-- No data state -->
    <div v-if="!footprintData && !loading && !error" class="no-data-state text-center q-pa-lg">
      <q-icon name="developer_board" size="4em" color="grey-4" />
      <div class="text-h6 text-grey q-mt-md">No KiCad Footprint Available</div>
      <div class="text-grey">
        This component doesn't have KiCad footprint data yet.
      </div>
    </div>

    <!-- Footprint visualization -->
    <div v-if="footprintData && !loading" class="footprint-container">
      <!-- Footprint metadata -->
      <q-card flat bordered class="q-mb-md">
        <q-card-section class="q-pa-sm">
          <div class="row q-gutter-md text-body2">
            <div class="col">
              <strong>Reference:</strong> {{ footprintData.footprint_reference }}
            </div>
            <div v-if="footprintData.footprint_library" class="col">
              <strong>Library:</strong> {{ footprintData.footprint_library }}
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Controls -->
      <q-card flat bordered class="q-mb-md">
        <q-card-section class="q-pa-sm">
          <div class="row items-center q-gutter-md">
            <div class="col-auto">
              <q-btn-toggle
                v-model="viewMode"
                push
                glossy
                toggle-color="primary"
                :options="[
                  {label: 'Top', value: 'top'},
                  {label: 'Bottom', value: 'bottom'}
                ]"
                size="sm"
              />
            </div>
            <div class="col-auto">
              <q-checkbox v-model="showDimensions" label="Show Dimensions" />
            </div>
            <div class="col-auto">
              <q-checkbox v-model="showPadNumbers" label="Show Pad Numbers" />
            </div>
            <q-space />
            <div class="col-auto">
              <q-btn
                flat
                icon="zoom_in"
                size="sm"
                title="Zoom In"
                @click="zoomIn"
              />
              <q-btn
                flat
                icon="zoom_out"
                size="sm"
                title="Zoom Out"
                @click="zoomOut"
              />
              <q-btn
                flat
                icon="center_focus_strong"
                size="sm"
                title="Reset Zoom"
                @click="resetZoom"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- SVG Footprint Display -->
      <q-card flat bordered>
        <q-card-section class="footprint-display">
          <div ref="svgContainer" class="svg-container">
            <div v-if="!sanitizedSvgContent" class="svg-placeholder">
              <q-icon name="memory" size="3em" color="grey-5" />
              <div class="text-body2 text-grey q-mt-sm">
                Footprint visualization will appear here
              </div>
            </div>
            <!-- eslint-disable vue/no-v-html -->
            <div
              v-else
              class="footprint-svg"
              :style="{ transform: `scale(${zoomLevel})` }"
              v-html="sanitizedSvgContent"
            ></div>
            <!-- eslint-enable vue/no-v-html -->
          </div>
        </q-card-section>
      </q-card>

      <!-- Pad information -->
      <q-card v-if="padData && padData.length > 0" flat bordered class="q-mt-md">
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">Pad Layout ({{ padData.length }} pads)</div>
          <q-table
            :rows="padData"
            :columns="padColumns"
            dense
            flat
            :pagination="{ rowsPerPage: 15 }"
            class="pad-table"
          >
            <template #body-cell-pad_type="slotProps">
              <q-td :props="slotProps">
                <q-chip
                  :color="getPadTypeColor(slotProps.value)"
                  text-color="white"
                  :label="slotProps.value"
                  size="sm"
                />
              </q-td>
            </template>
            <template #body-cell-drill="slotProps">
              <q-td :props="slotProps">
                <span v-if="slotProps.value">{{ slotProps.value }}mm</span>
                <span v-else class="text-grey">—</span>
              </q-td>
            </template>
            <template #body-cell-size="slotProps">
              <q-td :props="slotProps">
                {{ slotProps.value }}
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>

      <!-- Footprint dimensions -->
      <q-card v-if="footprintData.footprint_data?.dimensions" flat bordered class="q-mt-md">
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">Package Dimensions</div>
          <div class="dimensions-grid">
            <div
              v-for="(value, key) in footprintData.footprint_data.dimensions"
              :key="key"
              class="dimension-row"
            >
              <div class="dimension-key">{{ formatDimensionKey(key) }}:</div>
              <div class="dimension-value">{{ formatDimensionValue(value) }}</div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Footprint properties -->
      <q-card v-if="footprintData.footprint_data" flat bordered class="q-mt-md">
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">Footprint Properties</div>
          <div class="properties-grid">
            <div
              v-for="(value, key) in filteredProperties"
              :key="key"
              class="property-row"
            >
              <div class="property-key">{{ formatPropertyKey(key) }}:</div>
              <div class="property-value">{{ formatPropertyValue(value) }}</div>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../boot/axios'
import { sanitizeSvgContent } from '../utils/htmlSanitizer'
import type { KiCadFootprintData, KiCadPad } from '../types/kicad'

interface Props {
  componentId: string
  footprintData?: KiCadFootprintData | null
}

// Using KiCadFootprintData from types/kicad.ts


const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'error', error: string): void
  (e: 'loaded', data: KiCadFootprintData): void
}>()

// Reactive state
const loading = ref(false)
const error = ref<string | null>(null)
const internalFootprintData = ref<KiCadFootprintData | null>(null)
const svgContent = ref<string | null>(null)

// Use prop data if provided, otherwise use internal data
const footprintData = computed(() => props.footprintData ?? internalFootprintData.value)
const svgContainer = ref<HTMLElement>()
const viewMode = ref('top')
const showDimensions = ref(true)
const showPadNumbers = ref(true)
const zoomLevel = ref(1)

// Computed properties
const padData = computed(() => {
  if (!footprintData.value?.footprint_data?.pads) return []

  return Object.entries(footprintData.value.footprint_data.pads).map(([number, padInfo]: [string, KiCadPad]) => ({
    number,
    pad_type: padInfo.type || 'smd',
    size: formatPadSize(padInfo.size),
    drill: padInfo.drill,
    position: padInfo.position || { x: 0, y: 0 },
    shape: padInfo.shape || 'rect'
  }))
})

const filteredProperties = computed(() => {
  if (!footprintData.value?.footprint_data) return {}

  const data = { ...footprintData.value.footprint_data }
  // Remove complex objects we handle separately
  delete data.pads
  delete data.dimensions
  return data
})

// Sanitized SVG content for safe rendering
const sanitizedSvgContent = computed(() => {
  if (!svgContent.value) return ''
  return sanitizeSvgContent(svgContent.value)
})

const padColumns = [
  {
    name: 'number',
    label: 'Pad #',
    align: 'left' as const,
    field: 'number',
    sortable: true
  },
  {
    name: 'pad_type',
    label: 'Type',
    align: 'center' as const,
    field: 'pad_type',
    sortable: true
  },
  {
    name: 'size',
    label: 'Size (mm)',
    align: 'center' as const,
    field: 'size',
    sortable: true
  },
  {
    name: 'drill',
    label: 'Drill',
    align: 'center' as const,
    field: 'drill'
  },
  {
    name: 'shape',
    label: 'Shape',
    align: 'center' as const,
    field: 'shape'
  }
]

// Methods
const fetchFootprintData = async () => {
  // Skip fetch if footprintData prop is provided (testing mode)
  if (props.footprintData !== undefined) {
    generateFootprintSVG()
    return
  }

  if (!props.componentId) return

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/api/v1/kicad/components/${props.componentId}/footprint`)
    internalFootprintData.value = response.data
    emit('loaded', response.data)

    // Generate SVG visualization
    generateFootprintSVG()
  } catch (err: unknown) {
    const hasResponse = typeof err === 'object' && err !== null && 'response' in err
    const response = hasResponse ? (err as { response?: { status?: number; data?: { detail?: string } } }).response : undefined
    if (response?.status === 404) {
      error.value = null // No footprint data is not an error, just show no-data state
    } else {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load footprint data'
      const errorMsg = response?.data?.detail || errorMessage
      error.value = errorMsg
      emit('error', errorMsg)
    }
  } finally {
    loading.value = false
  }
}

const generateFootprintSVG = () => {
  if (!footprintData.value) return

  // If footprint has svg_content, use it directly
  if (footprintData.value.svg_content) {
    svgContent.value = footprintData.value.svg_content
    return
  }

  const pads = padData.value
  if (pads.length === 0) {
    svgContent.value = '<div class="text-center q-pa-md text-grey">No pad data available</div>'
    return
  }

  // Enhanced SVG generation for professional footprint visualization
  const padCount = pads.length

  // Calculate optimal dimensions and footprint type detection
  const isQFP = footprintData.value.footprint_name.toLowerCase().includes('qfp')
  const isBGA = footprintData.value.footprint_name.toLowerCase().includes('bga')
  const isDIP = footprintData.value.footprint_name.toLowerCase().includes('dip')
  const isSOP = footprintData.value.footprint_name.toLowerCase().includes('sop')

  // Calculate precise bounds with padding
  const margin = 40
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity

  pads.forEach(pad => {
    const size = parsePadSize(pad.size)
    minX = Math.min(minX, pad.position.x - size.width / 2)
    maxX = Math.max(maxX, pad.position.x + size.width / 2)
    minY = Math.min(minY, pad.position.y - size.height / 2)
    maxY = Math.max(maxY, pad.position.y + size.height / 2)
  })

  const contentWidth = maxX - minX
  const contentHeight = maxY - minY
  const width = contentWidth + 2 * margin + 100
  const height = contentHeight + 2 * margin + 80
  const offsetX = -minX + margin + 50
  const offsetY = -minY + margin + 40

  let svg = `<svg width="500" height="400" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`

  // Enhanced definitions for professional PCB visualization
  svg += `<defs>
    <pattern id="pcbTexture" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="4" fill="#1a4c22"/>
      <circle cx="2" cy="2" r="0.3" fill="#2d5016"/>
    </pattern>
    <filter id="metallic" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="0.5"/>
      <feColorMatrix type="matrix" values="1 0 0 0 0  0 0.9 0 0 0  0 0 0.7 0 0  0 0 0 1 0"/>
    </filter>
    <filter id="padShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="1" dy="1" stdDeviation="1.5" flood-color="#00000060"/>
    </filter>
    <linearGradient id="copperGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ffd700;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#ffed4e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#cd853f;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="silkscreenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.9" />
      <stop offset="100%" style="stop-color:#f0f0f0;stop-opacity:0.9" />
    </linearGradient>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
      <polygon points="0,0 0,6 9,3" fill="#ffff00"/>
    </marker>
  </defs>`

  // Draw PCB background with realistic texture
  svg += `<rect width="100%" height="100%" fill="url(#pcbTexture)"/>`

  // Draw measurement grid if enabled
  if (showDimensions.value) {
    const gridStep = 5 // 5mm major grid
    const minorStep = 1 // 1mm minor grid

    // Major grid lines
    for (let x = margin; x < width - margin; x += gridStep) {
      svg += `<line x1="${x}" y1="${margin}" x2="${x}" y2="${height - margin}" stroke="#ffffff15" stroke-width="1"/>`
    }
    for (let y = margin; y < height - margin; y += gridStep) {
      svg += `<line x1="${margin}" y1="${y}" x2="${width - margin}" y2="${y}" stroke="#ffffff15" stroke-width="1"/>`
    }

    // Minor grid lines
    for (let x = margin; x < width - margin; x += minorStep) {
      if (x % gridStep !== 0) {
        svg += `<line x1="${x}" y1="${margin}" x2="${x}" y2="${height - margin}" stroke="#ffffff08" stroke-width="0.5"/>`
      }
    }
    for (let y = margin; y < height - margin; y += minorStep) {
      if (y % gridStep !== 0) {
        svg += `<line x1="${margin}" y1="${y}" x2="${width - margin}" y2="${y}" stroke="#ffffff08" stroke-width="0.5"/>`
      }
    }
  }

  // Calculate and draw component body outline based on footprint type
  let bodyPadding = 15
  if (isQFP || isSOP) bodyPadding = 20
  if (isBGA) bodyPadding = 10
  if (isDIP) bodyPadding = 25

  const bodyX = minX + offsetX - bodyPadding
  const bodyY = minY + offsetY - bodyPadding
  const bodyWidth = contentWidth + (bodyPadding * 2)
  const bodyHeight = contentHeight + (bodyPadding * 2)

  // Component body with enhanced styling
  if (viewMode.value === 'top') {
    svg += `<rect x="${bodyX}" y="${bodyY}" width="${bodyWidth}" height="${bodyHeight}"
             fill="#1c1c1c" stroke="#333" stroke-width="2" rx="6"
             filter="url(#padShadow)"/>`

    // Add component type-specific markings
    const centerX = bodyX + bodyWidth / 2
    const centerY = bodyY + bodyHeight / 2

    // Pin 1 indicator (always top-left)
    svg += `<circle cx="${bodyX + 12}" cy="${bodyY + 12}" r="5" fill="#ff4444" stroke="#ffffff" stroke-width="1.5"/>`
    svg += `<text x="${bodyX + 12}" y="${bodyY + 16}" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="white">1</text>`

    // Component name/part number
    svg += `<text x="${centerX}" y="${centerY}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="url(#silkscreenGradient)">
             ${footprintData.value.footprint_name}</text>`

    // Package outline corners
    const cornerSize = 8
    svg += `<path d="M ${bodyX + cornerSize} ${bodyY} L ${bodyX} ${bodyY} L ${bodyX} ${bodyY + cornerSize}"
             stroke="#ffffff60" stroke-width="1.5" fill="none"/>`
    svg += `<path d="M ${bodyX + bodyWidth - cornerSize} ${bodyY} L ${bodyX + bodyWidth} ${bodyY} L ${bodyX + bodyWidth} ${bodyY + cornerSize}"
             stroke="#ffffff60" stroke-width="1.5" fill="none"/>`
    svg += `<path d="M ${bodyX} ${bodyY + bodyHeight - cornerSize} L ${bodyX} ${bodyY + bodyHeight} L ${bodyX + cornerSize} ${bodyY + bodyHeight}"
             stroke="#ffffff60" stroke-width="1.5" fill="none"/>`
    svg += `<path d="M ${bodyX + bodyWidth - cornerSize} ${bodyY + bodyHeight} L ${bodyX + bodyWidth} ${bodyY + bodyHeight} L ${bodyX + bodyWidth} ${bodyY + bodyHeight - cornerSize}"
             stroke="#ffffff60" stroke-width="1.5" fill="none"/>`
  }

  // Header information
  svg += `<text x="20" y="25" text-anchor="start"
           font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="white">
           ${footprintData.value.footprint_name}</text>`

  svg += `<text x="20" y="45" text-anchor="start"
           font-family="Arial, sans-serif" font-size="11" fill="#cccccc">
           ${viewMode.value.toUpperCase()} View • ${padCount} pads</text>`

  // Enhanced pad rendering with realistic appearance
  pads.forEach(pad => {
    const size = parsePadSize(pad.size)
    const x = pad.position.x + offsetX - size.width / 2
    const y = pad.position.y + offsetY - size.height / 2
    const centerX = pad.position.x + offsetX
    const centerY = pad.position.y + offsetY

    // Pad with realistic copper appearance
    if (pad.shape === 'circle' || pad.shape === 'oval') {
      const rx = size.width / 2
      const ry = size.height / 2
      svg += `<ellipse cx="${centerX}" cy="${centerY}" rx="${rx}" ry="${ry}"
               fill="url(#copperGradient)" stroke="#cd853f" stroke-width="1"
               filter="url(#padShadow)"/>`

      // Add metallic shine effect
      svg += `<ellipse cx="${centerX - rx * 0.3}" cy="${centerY - ry * 0.3}" rx="${rx * 0.3}" ry="${ry * 0.3}"
               fill="#ffffff40" filter="url(#metallic)"/>`
    } else {
      const cornerRadius = Math.min(size.width, size.height) * 0.1
      svg += `<rect x="${x}" y="${y}" width="${size.width}" height="${size.height}"
               fill="url(#copperGradient)" stroke="#cd853f" stroke-width="1" rx="${cornerRadius}"
               filter="url(#padShadow)"/>`

      // Add metallic shine effect
      svg += `<rect x="${x + size.width * 0.1}" y="${y + size.height * 0.1}"
               width="${size.width * 0.4}" height="${size.height * 0.4}"
               fill="#ffffff40" rx="${cornerRadius * 0.5}" filter="url(#metallic)"/>`
    }

    // Draw drill hole for through-hole pads with enhanced visualization
    if (pad.drill && parseFloat(pad.drill) > 0) {
      const drillRadius = parseFloat(pad.drill) / 2
      // Drill hole with depth effect
      svg += `<circle cx="${centerX}" cy="${centerY}" r="${drillRadius + 0.5}"
               fill="#000000" filter="url(#padShadow)"/>`
      svg += `<circle cx="${centerX}" cy="${centerY}" r="${drillRadius}"
               fill="#ffffff" stroke="#333" stroke-width="1"/>`
      svg += `<circle cx="${centerX - drillRadius * 0.3}" cy="${centerY - drillRadius * 0.3}" r="${drillRadius * 0.2}"
               fill="#ffffff80"/>`
    }

    // Enhanced pad numbers with better visibility
    if (showPadNumbers.value) {
      const fontSize = Math.max(8, Math.min(12, Math.min(size.width, size.height) * 0.6))
      const textColor = pad.drill ? '#000000' : '#000000'

      // Text background for better readability
      svg += `<circle cx="${centerX}" cy="${centerY}" r="${fontSize * 0.7}"
               fill="#ffffff90" stroke="none"/>`
      svg += `<text x="${centerX}" y="${centerY + fontSize * 0.3}" text-anchor="middle"
               font-family="Arial, sans-serif" font-size="${fontSize}" font-weight="bold" fill="${textColor}">
               ${pad.number}</text>`
    }
  })

  // Add measurement dimensions if enabled
  if (showDimensions.value) {
    addEnhancedMeasurements(svg, bodyX, bodyY, bodyWidth, bodyHeight, contentWidth, contentHeight)
  }

  // Add scale reference
  svg += `<line x1="${width - 80}" y1="${height - 30}" x2="${width - 30}" y2="${height - 30}"
           stroke="#ffff00" stroke-width="2" marker-end="url(#arrow)"/>`
  svg += `<text x="${width - 55}" y="${height - 35}" text-anchor="middle"
           font-family="Arial, sans-serif" font-size="10" fill="#ffff00">5mm</text>`

  svg += '</svg>'
  svgContent.value = svg
}

const addEnhancedMeasurements = (svg: string, bodyX: number, bodyY: number, bodyWidth: number, bodyHeight: number, _contentWidth: number, _contentHeight: number) => {
  const measurementColor = '#ffff00'
  const offset = 25

  // Package width measurement
  svg += `<line x1="${bodyX}" y1="${bodyY + bodyHeight + offset}"
           x2="${bodyX + bodyWidth}" y2="${bodyY + bodyHeight + offset}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<line x1="${bodyX}" y1="${bodyY + bodyHeight + offset - 5}"
           x2="${bodyX}" y2="${bodyY + bodyHeight + offset + 5}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<line x1="${bodyX + bodyWidth}" y1="${bodyY + bodyHeight + offset - 5}"
           x2="${bodyX + bodyWidth}" y2="${bodyY + bodyHeight + offset + 5}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<text x="${bodyX + bodyWidth/2}" y="${bodyY + bodyHeight + offset + 18}" text-anchor="middle"
           font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="${measurementColor}">
           ${bodyWidth.toFixed(1)}mm</text>`

  // Package height measurement
  svg += `<line x1="${bodyX + bodyWidth + offset}" y1="${bodyY}"
           x2="${bodyX + bodyWidth + offset}" y2="${bodyY + bodyHeight}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<line x1="${bodyX + bodyWidth + offset - 5}" y1="${bodyY}"
           x2="${bodyX + bodyWidth + offset + 5}" y2="${bodyY}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<line x1="${bodyX + bodyWidth + offset - 5}" y1="${bodyY + bodyHeight}"
           x2="${bodyX + bodyWidth + offset + 5}" y2="${bodyY + bodyHeight}"
           stroke="${measurementColor}" stroke-width="1.5"/>`
  svg += `<text x="${bodyX + bodyWidth + offset + 20}" y="${bodyY + bodyHeight/2 + 4}" text-anchor="start"
           font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="${measurementColor}"
           transform="rotate(90, ${bodyX + bodyWidth + offset + 20}, ${bodyY + bodyHeight/2 + 4})">
           ${bodyHeight.toFixed(1)}mm</text>`
}

const parsePadSize = (sizeStr: string) => {
  const parts = sizeStr.split('×').map(s => parseFloat(s.trim()))
  return {
    width: parts[0] || 1,
    height: parts[1] || parts[0] || 1
  }
}

const formatPadSize = (size: { width: number; height: number } | string | number | undefined) => {
  if (typeof size === 'object' && size.width && size.height) {
    return `${size.width}×${size.height}`
  }
  return String(size || '1×1')
}

const getPadTypeColor = (padType: string) => {
  const colorMap: Record<string, string> = {
    'smd': '#4CAF50',
    'thru_hole': '#2196F3',
    'np_thru_hole': '#FF9800',
    'connect': '#9C27B0',
    'aperture': '#607D8B'
  }
  return colorMap[padType] || '#757575'
}

const formatDimensionKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDimensionValue = (value: string | number | undefined) => {
  if (typeof value === 'number') {
    return `${value}mm`
  }
  return String(value)
}

const formatPropertyKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatPropertyValue = (value: unknown) => {
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value * 1.2, 3)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.5)
}

const resetZoom = () => {
  zoomLevel.value = 1
}

// Watchers
watch(() => props.componentId, fetchFootprintData, { immediate: true })
watch(() => props.footprintData, () => {
  if (props.footprintData !== undefined) {
    generateFootprintSVG()
  }
}, { immediate: true })
watch([viewMode, showDimensions, showPadNumbers], generateFootprintSVG)

// Lifecycle
onMounted(() => {
  fetchFootprintData()
})

// Expose refs for testing
defineExpose({
  loading,
  error,
  footprintData,
  zoomLevel,
  viewMode,
  showDimensions,
  showPadNumbers
})
</script>

<style scoped>
.kicad-footprint-viewer {
  max-width: 100%;
}

.viewer-header {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
}

.footprint-container {
  width: 100%;
}

.footprint-display {
  min-height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.svg-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  overflow: auto;
}

.svg-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 250px;
  color: #999;
}

.footprint-svg {
  max-width: 100%;
  height: auto;
  transition: transform 0.2s ease;
}

.footprint-svg svg {
  max-width: 100%;
  height: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: white;
}

.pad-table {
  max-height: 400px;
}

.dimensions-grid,
.properties-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 16px;
  max-height: 300px;
  overflow-y: auto;
}

.dimension-row,
.property-row {
  display: contents;
}

.dimension-key,
.property-key {
  font-weight: 500;
  color: #555;
  text-align: right;
  padding-right: 8px;
}

.dimension-value,
.property-value {
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  word-break: break-word;
}

.no-data-state {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  background-color: #fafafa;
}

/* Responsive design */
@media (max-width: 768px) {
  .dimensions-grid,
  .properties-grid {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .dimension-key,
  .property-key {
    text-align: left;
    font-weight: 600;
    margin-bottom: 2px;
  }

  .dimension-value,
  .property-value {
    margin-bottom: 12px;
    padding-left: 8px;
    border-left: 3px solid #e0e0e0;
  }
}
</style>