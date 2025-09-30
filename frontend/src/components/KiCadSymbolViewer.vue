<template>
  <div class="kicad-symbol-viewer">
    <!-- Header -->
    <div class="viewer-header q-mb-md">
      <div class="text-h6">KiCad Symbol</div>
      <div v-if="symbolData" class="text-caption text-grey">
        {{ symbolData.symbol_library }}/{{ symbolData.symbol_name }}
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
    <div v-if="!symbolData && !loading && !error" class="no-data-state text-center q-pa-lg">
      <q-icon name="memory" size="4em" color="grey-4" />
      <div class="text-h6 text-grey q-mt-md">No KiCad Symbol Available</div>
      <div class="text-grey">
        This component doesn't have KiCad symbol data yet.
      </div>
    </div>

    <!-- Symbol visualization -->
    <div v-if="symbolData && !loading" class="symbol-container">
      <!-- Symbol metadata -->
      <q-card flat bordered class="q-mb-md">
        <q-card-section class="q-pa-sm">
          <div class="row q-gutter-md text-body2">
            <div class="col">
              <strong>Reference:</strong> {{ symbolData.symbol_reference }}
            </div>
            <div v-if="symbolData.symbol_library" class="col">
              <strong>Library:</strong> {{ symbolData.symbol_library }}
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- SVG Symbol Display -->
      <q-card flat bordered>
        <q-card-section class="symbol-display">
          <div ref="svgContainer" class="svg-container">
            <!-- SVG will be dynamically inserted here -->
            <div v-if="!sanitizedSvgContent" class="svg-placeholder">
              <q-icon name="code" size="3em" color="grey-5" />
              <div class="text-body2 text-grey q-mt-sm">
                Symbol visualization will appear here
              </div>
            </div>
            <!-- eslint-disable vue/no-v-html -->
            <div v-else class="symbol-svg" v-html="sanitizedSvgContent"></div>
            <!-- eslint-enable vue/no-v-html -->
          </div>
        </q-card-section>
      </q-card>

      <!-- Pin information -->
      <q-card v-if="pinData && pinData.length > 0" flat bordered class="q-mt-md">
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">Pin Layout</div>
          <q-table
            :rows="pinData"
            :columns="pinColumns"
            dense
            flat
            :pagination="{ rowsPerPage: 10 }"
            class="pin-table"
          >
            <template #body-cell-pin_type="slotProps">
              <q-td :props="slotProps">
                <q-chip
                  :color="getPinTypeColor(slotProps.value)"
                  text-color="white"
                  :label="slotProps.value"
                  size="sm"
                />
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>

      <!-- Symbol properties -->
      <q-card v-if="symbolData.symbol_data" flat bordered class="q-mt-md">
        <q-card-section>
          <div class="text-subtitle2 q-mb-md">Symbol Properties</div>
          <div class="properties-grid">
            <div
              v-for="(value, key) in symbolData.symbol_data"
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
import type { KiCadSymbolData, KiCadPin } from '../types/kicad'

interface Props {
  componentId: string
}

// Using KiCadSymbolData from types/kicad.ts


const props = defineProps<Props>()

// Reactive state
const loading = ref(false)
const error = ref<string | null>(null)
const symbolData = ref<KiCadSymbolData | null>(null)
const svgContent = ref<string | null>(null)
const svgContainer = ref<HTMLElement>()

// Computed properties
const pinData = computed(() => {
  if (!symbolData.value?.symbol_data?.pins) return []

  return Object.entries(symbolData.value.symbol_data.pins).map(([number, pinInfo]: [string, KiCadPin]) => ({
    number,
    name: pinInfo.name || '',
    pin_type: pinInfo.type || 'passive',
    electrical_type: pinInfo.electrical_type || '',
    position: pinInfo.position
  }))
})

// Sanitized SVG content for safe rendering
const sanitizedSvgContent = computed(() => {
  if (!svgContent.value) return ''
  return sanitizeSvgContent(svgContent.value)
})

const pinColumns = [
  {
    name: 'number',
    label: 'Pin #',
    align: 'left' as const,
    field: 'number',
    sortable: true
  },
  {
    name: 'name',
    label: 'Name',
    align: 'left' as const,
    field: 'name',
    sortable: true
  },
  {
    name: 'pin_type',
    label: 'Type',
    align: 'center' as const,
    field: 'pin_type',
    sortable: true
  },
  {
    name: 'electrical_type',
    label: 'Electrical',
    align: 'left' as const,
    field: 'electrical_type'
  }
]

// Methods
const fetchSymbolData = async () => {
  if (!props.componentId) return

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/api/v1/kicad/components/${props.componentId}/symbol`)
    symbolData.value = response.data

    // Generate SVG visualization
    generateSymbolSVG()
  } catch (err: unknown) {
    const hasResponse = typeof err === 'object' && err !== null && 'response' in err
    const response = hasResponse ? (err as { response?: { status?: number; data?: { detail?: string } } }).response : undefined
    if (response?.status === 404) {
      error.value = null // No symbol data is not an error, just show no-data state
    } else {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load symbol data'
      error.value = response?.data?.detail || errorMessage
    }
  } finally {
    loading.value = false
  }
}

const generateSymbolSVG = () => {
  if (!symbolData.value) return

  // Enhanced SVG generation with better pin distribution and visual elements
  const pins = pinData.value
  const pinCount = pins.length

  // Calculate optimal dimensions based on pin count
  const minHeight = 300
  const pinSpacing = 25
  const symbolPadding = 60

  // Determine optimal body size
  const bodyWidth = Math.max(180, Math.min(250, pinCount * 8))
  const bodyHeight = Math.max(120, Math.ceil(pinCount / 2) * pinSpacing + 40)

  const width = bodyWidth + (symbolPadding * 2) + 100
  const height = Math.max(minHeight, bodyHeight + (symbolPadding * 2))

  const bodyX = (width - bodyWidth) / 2
  const bodyY = (height - bodyHeight) / 2

  let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`

  // Add background and grid
  svg += `<defs>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f0f0f0" stroke-width="0.5"/>
    </pattern>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#00000020"/>
    </filter>
  </defs>`

  svg += `<rect width="100%" height="100%" fill="white"/>`
  svg += `<rect width="100%" height="100%" fill="url(#grid)"/>`

  // Draw main symbol body with enhanced styling
  svg += `<rect x="${bodyX}" y="${bodyY}" width="${bodyWidth}" height="${bodyHeight}"
           fill="white" stroke="#2c3e50" stroke-width="2.5" rx="6"
           filter="url(#shadow)"/>`

  // Add internal symbol decoration based on component type
  const centerX = bodyX + bodyWidth / 2
  const centerY = bodyY + bodyHeight / 2

  // Add component type indicator
  if (symbolData.value.symbol_name.toLowerCase().includes('resistor')) {
    // Resistor symbol
    svg += `<path d="M ${centerX - 40} ${centerY} L ${centerX - 20} ${centerY - 15} L ${centerX} ${centerY + 15} L ${centerX + 20} ${centerY - 15} L ${centerX + 40} ${centerY}"
             stroke="#e74c3c" stroke-width="2" fill="none"/>`
  } else if (symbolData.value.symbol_name.toLowerCase().includes('capacitor')) {
    // Capacitor symbol
    svg += `<line x1="${centerX - 8}" y1="${centerY - 20}" x2="${centerX - 8}" y2="${centerY + 20}" stroke="#3498db" stroke-width="3"/>
             <line x1="${centerX + 8}" y1="${centerY - 20}" x2="${centerX + 8}" y2="${centerY + 20}" stroke="#3498db" stroke-width="3"/>`
  } else {
    // Generic IC symbol
    svg += `<circle cx="${centerX}" cy="${centerY}" r="8" fill="none" stroke="#7f8c8d" stroke-width="2"/>
             <path d="M ${centerX - 15} ${centerY - 10} L ${centerX + 15} ${centerY + 10} M ${centerX - 15} ${centerY + 10} L ${centerX + 15} ${centerY - 10}"
                   stroke="#7f8c8d" stroke-width="1.5"/>`
  }

  // Draw component reference with better positioning
  svg += `<text x="${centerX}" y="${bodyY - 15}" text-anchor="middle"
           font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#2c3e50">
           ${symbolData.value.symbol_reference}</text>`

  // Draw component name with better styling
  svg += `<text x="${centerX}" y="${bodyY + bodyHeight + 25}" text-anchor="middle"
           font-family="Arial, sans-serif" font-size="13" fill="#7f8c8d">
           ${symbolData.value.symbol_name}</text>`

  // Enhanced pin distribution algorithm
  const leftPins = []
  const rightPins = []
  const topPins = []
  const bottomPins = []

  // Intelligent pin distribution based on pin type and name
  pins.forEach(pin => {
    if (pin.name.toLowerCase().includes('vcc') || pin.name.toLowerCase().includes('vdd') ||
        pin.name.toLowerCase().includes('power') || pin.pin_type === 'power_in') {
      topPins.push(pin)
    } else if (pin.name.toLowerCase().includes('gnd') || pin.name.toLowerCase().includes('vss') ||
               pin.pin_type === 'power_out') {
      bottomPins.push(pin)
    } else if (pin.name.toLowerCase().includes('clk') || pin.name.toLowerCase().includes('clock') ||
               pin.name.toLowerCase().includes('in') || pin.pin_type === 'input') {
      leftPins.push(pin)
    } else {
      rightPins.push(pin)
    }
  })

  // Draw left pins
  leftPins.forEach((pin, index) => {
    const y = bodyY + 30 + index * pinSpacing
    const pinColor = getPinTypeColor(pin.pin_type)

    // Enhanced pin line with direction indicator
    svg += `<line x1="${bodyX - 30}" y1="${y}" x2="${bodyX}" y2="${y}"
             stroke="${pinColor}" stroke-width="2.5"/>`
    svg += `<circle cx="${bodyX - 35}" cy="${y}" r="3" fill="${pinColor}"/>`

    // Pin number with background
    svg += `<rect x="${bodyX - 55}" y="${y - 8}" width="16" height="16" fill="white" stroke="#ddd" stroke-width="1" rx="2"/>
             <text x="${bodyX - 47}" y="${y + 4}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#333">${pin.number}</text>`

    // Pin name with better positioning
    svg += `<text x="${bodyX + 8}" y="${y + 4}" text-anchor="start"
             font-family="Arial, sans-serif" font-size="11" fill="#555">${pin.name}</text>`
  })

  // Draw right pins
  rightPins.forEach((pin, index) => {
    const y = bodyY + 30 + index * pinSpacing
    const pinColor = getPinTypeColor(pin.pin_type)

    svg += `<line x1="${bodyX + bodyWidth}" y1="${y}" x2="${bodyX + bodyWidth + 30}" y2="${y}"
             stroke="${pinColor}" stroke-width="2.5"/>`
    svg += `<circle cx="${bodyX + bodyWidth + 35}" cy="${y}" r="3" fill="${pinColor}"/>`

    svg += `<rect x="${bodyX + bodyWidth + 39}" y="${y - 8}" width="16" height="16" fill="white" stroke="#ddd" stroke-width="1" rx="2"/>
             <text x="${bodyX + bodyWidth + 47}" y="${y + 4}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#333">${pin.number}</text>`

    svg += `<text x="${bodyX + bodyWidth - 8}" y="${y + 4}" text-anchor="end"
             font-family="Arial, sans-serif" font-size="11" fill="#555">${pin.name}</text>`
  })

  // Draw top pins (power)
  topPins.forEach((pin, index) => {
    const x = bodyX + 30 + index * (bodyWidth - 60) / Math.max(1, topPins.length - 1)
    const pinColor = getPinTypeColor(pin.pin_type)

    svg += `<line x1="${x}" y1="${bodyY - 30}" x2="${x}" y2="${bodyY}"
             stroke="${pinColor}" stroke-width="2.5"/>`
    svg += `<circle cx="${x}" cy="${bodyY - 35}" r="3" fill="${pinColor}"/>`

    svg += `<rect x="${x - 8}" y="${bodyY - 55}" width="16" height="16" fill="white" stroke="#ddd" stroke-width="1" rx="2"/>
             <text x="${x}" y="${bodyY - 43}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#333">${pin.number}</text>`

    svg += `<text x="${x}" y="${bodyY - 10}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="11" fill="#555">${pin.name}</text>`
  })

  // Draw bottom pins (ground)
  bottomPins.forEach((pin, index) => {
    const x = bodyX + 30 + index * (bodyWidth - 60) / Math.max(1, bottomPins.length - 1)
    const pinColor = getPinTypeColor(pin.pin_type)

    svg += `<line x1="${x}" y1="${bodyY + bodyHeight}" x2="${x}" y2="${bodyY + bodyHeight + 30}"
             stroke="${pinColor}" stroke-width="2.5"/>`
    svg += `<circle cx="${x}" cy="${bodyY + bodyHeight + 35}" r="3" fill="${pinColor}"/>`

    svg += `<rect x="${x - 8}" y="${bodyY + bodyHeight + 39}" width="16" height="16" fill="white" stroke="#ddd" stroke-width="1" rx="2"/>
             <text x="${x}" y="${bodyY + bodyHeight + 51}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#333">${pin.number}</text>`

    svg += `<text x="${x}" y="${bodyY + bodyHeight + 15}" text-anchor="middle"
             font-family="Arial, sans-serif" font-size="11" fill="#555">${pin.name}</text>`
  })

  // Add pin count indicator
  svg += `<text x="${width - 20}" y="20" text-anchor="end"
           font-family="Arial, sans-serif" font-size="12" fill="#999">
           ${pinCount} pins</text>`

  svg += '</svg>'
  svgContent.value = svg
}

const getPinTypeColor = (pinType: string) => {
  const colorMap: Record<string, string> = {
    'input': '#2196F3',
    'output': '#4CAF50',
    'bidirectional': '#FF9800',
    'tri_state': '#9C27B0',
    'passive': '#757575',
    'power_in': '#F44336',
    'power_out': '#E91E63',
    'open_collector': '#00BCD4',
    'open_emitter': '#795548',
    'unspecified': '#607D8B'
  }
  return colorMap[pinType] || '#757575'
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

// Watchers
watch(() => props.componentId, fetchSymbolData, { immediate: true })

// Lifecycle
onMounted(() => {
  fetchSymbolData()
})
</script>

<style scoped>
.kicad-symbol-viewer {
  max-width: 100%;
}

.viewer-header {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
}

.symbol-container {
  width: 100%;
}

.symbol-display {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.svg-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 250px;
}

.svg-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #999;
}

.symbol-svg {
  max-width: 100%;
  height: auto;
}

.symbol-svg svg {
  max-width: 100%;
  height: auto;
}

.pin-table {
  max-height: 300px;
}

.properties-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 16px;
  max-height: 300px;
  overflow-y: auto;
}

.property-row {
  display: contents;
}

.property-key {
  font-weight: 500;
  color: #555;
  text-align: right;
  padding-right: 8px;
}

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
  .properties-grid {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .property-key {
    text-align: left;
    font-weight: 600;
    margin-bottom: 2px;
  }

  .property-value {
    margin-bottom: 12px;
    padding-left: 8px;
    border-left: 3px solid #e0e0e0;
  }
}
</style>