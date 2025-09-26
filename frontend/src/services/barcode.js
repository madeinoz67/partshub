/**
 * Frontend barcode capture service using camera API
 * Handles video capture, image processing, and API communication
 */

import { api } from '../boot/axios'

class BarcodeService {
  constructor() {
    this.videoStream = null
    this.canvas = null
    this.isCapturing = false
    this.constraints = {
      video: {
        facingMode: 'environment', // Use back camera on mobile
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    }
  }

  /**
   * Check if camera is supported
   */
  isSupported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  }

  /**
   * Start camera capture
   */
  async startCamera() {
    try {
      if (!this.isSupported()) {
        throw new Error('Camera API not supported in this browser')
      }

      this.videoStream = await navigator.mediaDevices.getUserMedia(this.constraints)
      this.isCapturing = true

      console.log('Camera started successfully')
      return this.videoStream
    } catch (error) {
      console.error('Error starting camera:', error)
      this.isCapturing = false
      throw error
    }
  }

  /**
   * Stop camera capture
   */
  stopCamera() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop())
      this.videoStream = null
      this.isCapturing = false
      console.log('Camera stopped')
    }
  }

  /**
   * Capture image from video element
   */
  captureImage(videoElement) {
    if (!videoElement) {
      throw new Error('Video element not provided')
    }

    // Create canvas if not exists
    if (!this.canvas) {
      this.canvas = document.createElement('canvas')
    }

    const canvas = this.canvas
    const context = canvas.getContext('2d')

    // Set canvas size to match video
    canvas.width = videoElement.videoWidth
    canvas.height = videoElement.videoHeight

    // Draw current frame to canvas
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height)

    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8)

    console.log(`Captured image: ${canvas.width}x${canvas.height}`)
    return imageData
  }

  /**
   * Process barcode scan via API
   */
  async processBarcodeScan(imageData) {
    try {
      const response = await api.post('/api/barcode/scan', {
        image_data: imageData
      })

      if (response.data.success) {
        console.log('Barcode scan processed:', response.data.message)
        return {
          success: true,
          barcodes: response.data.barcodes,
          components: response.data.components,
          message: response.data.message
        }
      } else {
        return {
          success: false,
          message: response.data.message || 'Barcode scan failed',
          barcodes: [],
          components: []
        }
      }
    } catch (error) {
      console.error('Error processing barcode scan:', error)
      return {
        success: false,
        message: error.response?.data?.detail || error.message || 'Network error',
        barcodes: [],
        components: []
      }
    }
  }

  /**
   * Complete barcode scanning workflow
   */
  async scanBarcode(videoElement) {
    try {
      // Capture image from video
      const imageData = this.captureImage(videoElement)

      // Process scan via API
      const result = await this.processBarcodeScan(imageData)

      return result
    } catch (error) {
      console.error('Error in barcode scanning workflow:', error)
      return {
        success: false,
        message: error.message || 'Scanning failed',
        barcodes: [],
        components: []
      }
    }
  }

  /**
   * Get available video input devices
   */
  async getVideoDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      return devices.filter(device => device.kind === 'videoinput')
    } catch (error) {
      console.error('Error getting video devices:', error)
      return []
    }
  }

  /**
   * Switch to specific camera device
   */
  async switchCamera(deviceId) {
    try {
      // Stop current stream
      this.stopCamera()

      // Update constraints with specific device
      this.constraints.video.deviceId = { exact: deviceId }

      // Start new stream
      return await this.startCamera()
    } catch (error) {
      console.error('Error switching camera:', error)
      throw error
    }
  }

  /**
   * Get barcode service info from API
   */
  async getServiceInfo() {
    try {
      const response = await api.get('/api/barcode/info')
      return response.data
    } catch (error) {
      console.error('Error getting barcode service info:', error)
      return {
        pyzbar_available: false,
        supported_formats: [],
        mock_mode: true
      }
    }
  }

  /**
   * Upload image file for barcode scanning
   */
  async scanImageFile(file) {
    try {
      // Convert file to base64
      const imageData = await this.fileToBase64(file)

      // Process scan via API
      return await this.processBarcodeScan(imageData)
    } catch (error) {
      console.error('Error scanning image file:', error)
      return {
        success: false,
        message: error.message || 'File scanning failed',
        barcodes: [],
        components: []
      }
    }
  }

  /**
   * Convert file to base64
   */
  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }

  /**
   * Get current capture status
   */
  getStatus() {
    return {
      isCapturing: this.isCapturing,
      hasVideoStream: !!this.videoStream,
      isSupported: this.isSupported()
    }
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    this.stopCamera()
    if (this.canvas) {
      this.canvas = null
    }
  }
}

// Export singleton instance
export default new BarcodeService()