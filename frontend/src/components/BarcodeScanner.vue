<template>
  <div class="barcode-scanner">
    <!-- Scanner Dialog -->
    <q-dialog v-model="showScanner" persistent position="right">
      <q-card style="width: 400px; max-width: 50vw; height: 100vh; max-height: 100vh;" class="scanner-card">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Barcode Scanner</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="scanner-container">
            <!-- Camera Feed -->
            <div v-if="showScanner" class="camera-wrapper">
              <video
                ref="videoElement"
                autoplay
                playsinline
                class="camera-video"
                :style="{ display: cameraActive ? 'block' : 'none' }"
              ></video>
              <canvas
                ref="canvasElement"
                class="scanner-overlay"
              ></canvas>

              <!-- Scanner Frame Overlay -->
              <div class="scanner-frame">
                <div class="scanner-corners">
                  <div class="corner top-left"></div>
                  <div class="corner top-right"></div>
                  <div class="corner bottom-left"></div>
                  <div class="corner bottom-right"></div>
                </div>
                <div class="scanner-line" :class="{ scanning: isScanning }"></div>
              </div>

              <!-- Instructions -->
              <div class="scanner-instructions">
                <div class="text-body2 text-white">
                  {{ isScanning ? 'Scanning for barcode...' : 'Position barcode within the frame' }}
                </div>
              </div>
            </div>

            <!-- Camera Error/Loading State -->
            <div v-else class="camera-placeholder">
              <div v-if="cameraError" class="text-center">
                <q-icon name="videocam_off" size="4em" color="grey-5" />
                <div class="text-h6 q-mt-md text-grey-6">Camera Error</div>
                <div class="text-body2 text-grey-5 q-mb-md">{{ cameraError }}</div>
                <q-btn color="primary" @click="startCamera" label="Retry Camera" />
                <br />
                <q-btn flat @click="showManualInput = true" label="Enter Manually" class="q-mt-sm" />
              </div>
              <div v-else class="text-center">
                <q-spinner-dots size="3em" color="primary" />
                <div class="text-h6 q-mt-md text-grey-6">Starting Camera...</div>
                <div class="text-body2 text-grey-5">Please allow camera access</div>
              </div>
            </div>

            <!-- Scan Results -->
            <div v-if="scanResult" class="scan-result q-mt-md">
              <q-banner class="bg-positive text-white">
                <template v-slot:avatar>
                  <q-icon name="qr_code_scanner" />
                </template>
                <div class="text-subtitle1">Barcode Detected!</div>
                <div class="text-body2">{{ scanResult.data }}</div>
                <div class="text-caption">Format: {{ scanResult.format }}</div>
                <template v-slot:action>
                  <q-btn flat label="Use This" @click="useBarcode" />
                  <q-btn flat label="Scan Again" @click="clearResult" />
                </template>
              </q-banner>
            </div>

            <!-- Manual Input Option -->
            <div v-if="showManualInput" class="manual-input q-mt-md">
              <q-input
                v-model="manualBarcode"
                label="Enter Barcode Manually"
                outlined
                dense
                @keyup.enter="useManualBarcode"
              >
                <template v-slot:append>
                  <q-btn
                    flat
                    dense
                    icon="check"
                    @click="useManualBarcode"
                    :disable="!manualBarcode"
                  />
                </template>
              </q-input>
            </div>

            <!-- Scan History -->
            <div v-if="scanHistory.length > 0" class="scan-history q-mt-md">
              <div class="text-subtitle2 q-mb-sm">Recent Scans</div>
              <q-list dense>
                <q-item
                  v-for="(scan, index) in scanHistory.slice(0, 5)"
                  :key="index"
                  clickable
                  @click="selectFromHistory(scan)"
                >
                  <q-item-section>
                    <q-item-label>{{ scan.data }}</q-item-label>
                    <q-item-label caption>{{ scan.format }} • {{ formatTime(scan.timestamp) }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-btn flat round dense icon="content_copy" @click.stop="copyToClipboard(scan.data)" />
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Manual Input" @click="showManualInput = !showManualInput" />
          <q-btn flat label="Cancel" v-close-popup @click="stopScanning" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Component Search Results (if enabled) -->
    <q-dialog v-model="showSearchResults" v-if="searchComponents">
      <q-card style="width: 800px; max-width: 90vw;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Component Search Results</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <div v-if="searchLoading" class="text-center q-pa-lg">
            <q-spinner-dots size="2em" color="primary" />
            <div class="text-body2 q-mt-md">Searching for components...</div>
          </div>

          <div v-else-if="searchResults.length > 0">
            <div class="text-body2 q-mb-md">Found {{ searchResults.length }} component(s) for: <strong>{{ lastScannedCode }}</strong></div>
            <q-list bordered separator>
              <q-item
                v-for="component in searchResults"
                :key="component.id"
                clickable
                @click="selectComponent(component)"
              >
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white">
                    {{ component.component_type?.charAt(0).toUpperCase() || 'C' }}
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ component.name }}</q-item-label>
                  <q-item-label caption>{{ component.part_number }} • {{ component.manufacturer }}</q-item-label>
                  <q-item-label caption>Stock: {{ component.quantity_on_hand }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-chip :color="component.quantity_on_hand > 0 ? 'positive' : 'negative'" text-color="white" dense>
                    {{ component.quantity_on_hand > 0 ? 'In Stock' : 'Out of Stock' }}
                  </q-chip>
                </q-item-section>
              </q-item>
            </q-list>
          </div>

          <div v-else class="text-center q-pa-lg">
            <q-icon name="search_off" size="3em" color="grey-5" />
            <div class="text-h6 q-mt-md text-grey-6">No Components Found</div>
            <div class="text-body2 text-grey-5">No components match the scanned barcode: {{ lastScannedCode }}</div>
            <q-btn color="primary" @click="createNewComponent" label="Create New Component" class="q-mt-md" />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Scan Again" @click="showSearchResults = false; startScanning()" />
          <q-btn flat label="Close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useQuasar } from 'quasar'
import api from '../services/api'

interface ScanResult {
  data: string
  format: string
  timestamp: Date
}

interface Component {
  id: string
  name: string
  part_number: string
  manufacturer: string
  component_type: string
  quantity_on_hand: number
}

interface Props {
  searchComponents?: boolean
  autoStart?: boolean
}

interface Emits {
  (e: 'scan-result', result: ScanResult): void
  (e: 'component-selected', component: Component): void
  (e: 'create-component', barcode: string): void
}

const props = withDefaults(defineProps<Props>(), {
  searchComponents: false,
  autoStart: false
})

const emit = defineEmits<Emits>()
const $q = useQuasar()

// Scanner state
const showScanner = ref(false)
const cameraActive = ref(false)
const cameraError = ref<string | null>(null)
const isScanning = ref(false)
const scanResult = ref<ScanResult | null>(null)

// Manual input
const showManualInput = ref(false)
const manualBarcode = ref('')

// Component search
const showSearchResults = ref(false)
const searchLoading = ref(false)
const searchResults = ref<Component[]>([])
const lastScannedCode = ref('')

// Scan history
const scanHistory = ref<ScanResult[]>([])

// Camera and scanning elements
const videoElement = ref<HTMLVideoElement>()
const canvasElement = ref<HTMLCanvasElement>()
let mediaStream: MediaStream | null = null
let scanningInterval: NodeJS.Timeout | null = null

// BarcodeDetector API (if available)
let barcodeDetector: any = null

// Exposed methods
defineExpose({
  startScanning,
  stopScanning
})

onMounted(() => {
  // Load scan history from localStorage
  const saved = localStorage.getItem('barcode-scan-history')
  if (saved) {
    try {
      scanHistory.value = JSON.parse(saved).map((item: any) => ({
        ...item,
        timestamp: new Date(item.timestamp)
      }))
    } catch (error) {
      console.warn('Failed to load scan history:', error)
    }
  }

  // Check for Barcode Detection API support
  if ('BarcodeDetector' in window) {
    try {
      barcodeDetector = new (window as any).BarcodeDetector({
        formats: ['code_128', 'code_39', 'ean_13', 'ean_8', 'upc_a', 'upc_e', 'qr_code', 'data_matrix']
      })
      console.log('✅ BarcodeDetector initialized successfully')
    } catch (error) {
      console.warn('❌ BarcodeDetector not supported:', error)
    }
  } else {
    console.warn('❌ BarcodeDetector API not available in this browser')
  }

  if (props.autoStart) {
    startScanning()
  }
})

onUnmounted(() => {
  stopScanning()
})

async function startScanning() {
  showScanner.value = true
  clearResult()

  // Wait for dialog to render before starting camera
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 500))

  startCamera()
}

function stopScanning() {
  showScanner.value = false
  stopCamera()
  if (scanningInterval) {
    clearInterval(scanningInterval)
    scanningInterval = null
  }
  isScanning.value = false
}

async function startCamera() {
  cameraError.value = null
  cameraActive.value = false

  try {
    // Request camera permission
    const constraints = {
      video: {
        facingMode: 'environment', // Prefer back camera
        width: { ideal: 640 },
        height: { ideal: 480 }
      }
    }

    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)

    await nextTick()

    // Wait for dialog and video element to be fully rendered
    let retries = 0
    while (!videoElement.value && retries < 10) {
      console.log(`⏳ Waiting for video element... attempt ${retries + 1}/10`)
      await new Promise(resolve => setTimeout(resolve, 100))
      retries++
    }

    if (!videoElement.value) {
      console.error('❌ Video element still not found after retries')
    } else {
      console.log('✅ Video element found after', retries, 'retries')
    }

    if (videoElement.value) {
      console.log('Setting video srcObject...', mediaStream)
      videoElement.value.srcObject = mediaStream

      try {
        console.log('Starting video play...')
        await videoElement.value.play()
        console.log('Video playing successfully, setting cameraActive to true')
        cameraActive.value = true
        startBarcodeDetection()
      } catch (playError) {
        console.error('Video play error:', playError)
        cameraError.value = `Failed to start video: ${playError.message}`
      }
    } else {
      console.error('Video element not found')
      cameraError.value = 'Video element not available'
    }
  } catch (error: any) {
    console.error('Camera access error:', error)

    if (error.name === 'NotAllowedError') {
      cameraError.value = 'Camera access denied. Please allow camera permission and try again.'
    } else if (error.name === 'NotFoundError') {
      cameraError.value = 'No camera found. Please connect a camera and try again.'
    } else {
      cameraError.value = `Camera error: ${error.message}`
    }
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  cameraActive.value = false

  if (scanningInterval) {
    clearInterval(scanningInterval)
    scanningInterval = null
  }
}

function startBarcodeDetection() {
  if (!videoElement.value || !canvasElement.value) return

  isScanning.value = true

  // Set up canvas
  const canvas = canvasElement.value
  const video = videoElement.value
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480

  // Start scanning interval
  scanningInterval = setInterval(async () => {
    if (scanResult.value || !cameraActive.value) return

    try {
      await detectBarcode()
    } catch (error) {
      console.warn('Barcode detection error:', error)
    }
  }, 500) // Scan every 500ms
}

async function detectBarcode() {
  if (!videoElement.value || !canvasElement.value) return

  const canvas = canvasElement.value
  const video = videoElement.value
  const ctx = canvas.getContext('2d')

  if (!ctx) return

  // Draw current video frame to canvas
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  // Try native BarcodeDetector API first
  if (barcodeDetector) {
    try {
      const barcodes = await barcodeDetector.detect(canvas)
      if (barcodes.length > 0) {
        const barcode = barcodes[0]
        handleScanSuccess({
          data: barcode.rawValue,
          format: barcode.format,
          timestamp: new Date()
        })
        return
      }
    } catch (error) {
      console.warn('BarcodeDetector failed:', error)
    }
  }

  // Fallback to manual pattern detection (basic implementation)
  // This is a simplified approach - in production, you'd use a library like QuaggaJS
  // For now, we'll implement basic QR code pattern detection
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const detected = detectSimplePattern(imageData)

  if (detected) {
    handleScanSuccess(detected)
  }
}

function detectSimplePattern(imageData: ImageData): ScanResult | null {
  // This is a very basic pattern detection for demonstration
  // In a real implementation, you'd use a proper barcode detection library

  // For demo purposes, let's simulate finding a barcode pattern
  // This would be replaced with actual barcode detection logic
  return null
}

function handleScanSuccess(result: ScanResult) {
  isScanning.value = false
  scanResult.value = result

  // Add to history
  scanHistory.value.unshift(result)
  if (scanHistory.value.length > 50) {
    scanHistory.value = scanHistory.value.slice(0, 50)
  }

  // Save to localStorage
  localStorage.setItem('barcode-scan-history', JSON.stringify(scanHistory.value))

  // Emit result
  emit('scan-result', result)

  // Stop scanning
  if (scanningInterval) {
    clearInterval(scanningInterval)
    scanningInterval = null
  }

  // Search for components if enabled
  if (props.searchComponents) {
    searchForComponents(result.data)
  }
}

function clearResult() {
  scanResult.value = null
  showManualInput.value = false
  manualBarcode.value = ''
}

function useBarcode() {
  if (scanResult.value) {
    stopScanning()
    // Component search or direct usage is handled by parent
  }
}

function useManualBarcode() {
  if (manualBarcode.value.trim()) {
    const result: ScanResult = {
      data: manualBarcode.value.trim(),
      format: 'manual',
      timestamp: new Date()
    }
    handleScanSuccess(result)
  }
}

function selectFromHistory(scan: ScanResult) {
  scanResult.value = scan
  emit('scan-result', scan)

  if (props.searchComponents) {
    searchForComponents(scan.data)
  }
}

async function searchForComponents(barcode: string) {
  searchLoading.value = true
  showSearchResults.value = true
  lastScannedCode.value = barcode
  searchResults.value = []

  try {
    // Search by part number, barcode, or any other identifier
    const response = await api.get(`/api/v1/components?search=${encodeURIComponent(barcode)}&limit=20`)
    searchResults.value = response.data.components || []
  } catch (error) {
    console.error('Component search error:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to search for components',
      position: 'top'
    })
  } finally {
    searchLoading.value = false
  }
}

function selectComponent(component: Component) {
  emit('component-selected', component)
  showSearchResults.value = false
  stopScanning()
}

function createNewComponent() {
  emit('create-component', lastScannedCode.value)
  showSearchResults.value = false
  stopScanning()
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    $q.notify({
      type: 'positive',
      message: 'Copied to clipboard',
      position: 'top',
      timeout: 1000
    })
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
  }
}
</script>

<style scoped>
.scanner-card {
  display: flex;
  flex-direction: column;
}

.scanner-container {
  position: relative;
  width: 100%;
  max-width: 350px;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.camera-wrapper {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: auto;
  display: block;
}

.scanner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.scanner-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 200px;
  height: 120px;
  transform: translate(-50%, -50%);
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 8px;
}

.scanner-corners {
  position: absolute;
  width: 100%;
  height: 100%;
}

.corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #fff;
}

.corner.top-left {
  top: -3px;
  left: -3px;
  border-right: none;
  border-bottom: none;
}

.corner.top-right {
  top: -3px;
  right: -3px;
  border-left: none;
  border-bottom: none;
}

.corner.bottom-left {
  bottom: -3px;
  left: -3px;
  border-right: none;
  border-top: none;
}

.corner.bottom-right {
  bottom: -3px;
  right: -3px;
  border-left: none;
  border-top: none;
}

.scanner-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #ff6b6b, transparent);
  opacity: 0;
}

.scanner-line.scanning {
  animation: scanLine 2s ease-in-out infinite;
  opacity: 1;
}

@keyframes scanLine {
  0% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(118px);
  }
  100% {
    transform: translateY(0);
  }
}

.scanner-instructions {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  background: rgba(0, 0, 0, 0.7);
  padding: 8px 16px;
  border-radius: 16px;
}

.camera-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: #f5f5f5;
  border-radius: 8px;
}

.scan-result {
  margin-top: 16px;
}

.manual-input {
  margin-top: 16px;
}

.scan-history {
  margin-top: 16px;
  max-height: 200px;
  overflow-y: auto;
}
</style>