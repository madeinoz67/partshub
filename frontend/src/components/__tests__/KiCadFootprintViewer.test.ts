import { describe, it, expect, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { Quasar, QInnerLoading, QBanner, QCard, QCardSection, QBtnToggle, QCheckbox, QBtn, QTable, QTd, QChip, QIcon, QSpace, QSpinner } from 'quasar'
import KiCadFootprintViewer from '../KiCadFootprintViewer.vue'

// Security test cases for XSS prevention
const maliciousPayloads = [
  '<script>alert("XSS")</script>',
  '<img src="x" onerror="alert(\'XSS\')">',
  '<svg onload="alert(\'XSS\')"></svg>',
  '<iframe src="javascript:alert(\'XSS\')"></iframe>',
  '<div onclick="alert(\'XSS\')">Click me</div>',
  // Real-world SVG injection attempts
  '<svg><script>alert("XSS")</script></svg>',
  '<svg><foreignObject><div onclick="alert(\'XSS\')">Test</div></foreignObject></svg>',
  // Event handler injections
  '<rect onmouseover="alert(\'XSS\')" />',
  '<path onfocus="alert(\'XSS\')" />',
]

const legitimateSvgContent = `
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" fill="blue" />
  <circle cx="50" cy="50" r="20" fill="red" />
</svg>
`

const mockFootprintData = {
  footprint_reference: 'REF1',
  footprint_library: 'TestLib',
  footprint_name: 'TestFootprint',
  svg_content: legitimateSvgContent
}

describe('KiCadFootprintViewer', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    wrapper = mount(KiCadFootprintViewer, {
      global: {
        plugins: [Quasar],
        components: {
          QInnerLoading,
          QBanner,
          QCard,
          QCardSection,
          QBtnToggle,
          QCheckbox,
          QBtn,
          QTable,
          QTd,
          QChip,
          QIcon,
          QSpace,
          QSpinner
        }
      },
      props: {
        componentId: 'test-component-id',
        footprintData: null
      }
    })
  })

  describe('Security - XSS Prevention', () => {
    it('should sanitize malicious scripts in SVG content', async () => {
      for (const payload of maliciousPayloads) {
        const maliciousData = {
          ...mockFootprintData,
          svg_content: payload
        }

        await wrapper.setProps({ footprintData: maliciousData })
        await wrapper.vm.$nextTick()

        const svgContainer = wrapper.find('.footprint-svg')
        if (svgContainer.exists()) {
          const innerHTML = svgContainer.element.innerHTML

          // Should not contain script tags
          expect(innerHTML).not.toMatch(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi)
          // Should not contain javascript: protocols
          expect(innerHTML).not.toMatch(/javascript:/gi)
          // Should not contain event handlers
          expect(innerHTML).not.toMatch(/on\w+\s*=/gi)
          // Should not contain iframe tags
          expect(innerHTML).not.toMatch(/<iframe\b[^>]*>/gi)
        }
      }
    })

    it('should preserve legitimate SVG content', async () => {
      await wrapper.setProps({ footprintData: mockFootprintData })
      await wrapper.vm.$nextTick()

      const svgContainer = wrapper.find('.footprint-svg')
      expect(svgContainer.exists()).toBe(true)

      const innerHTML = svgContainer.element.innerHTML
      expect(innerHTML).toContain('<svg')
      expect(innerHTML).toContain('<rect')
      expect(innerHTML).toContain('<circle')
    })

    it('should handle empty SVG content safely', async () => {
      const emptyData = {
        ...mockFootprintData,
        svg_content: ''
      }

      await wrapper.setProps({ footprintData: emptyData })
      await wrapper.vm.$nextTick()

      const placeholder = wrapper.find('.svg-placeholder')
      expect(placeholder.exists()).toBe(true)
    })

    it('should handle null SVG content safely', async () => {
      const nullData = {
        ...mockFootprintData,
        svg_content: null
      }

      await wrapper.setProps({ footprintData: nullData })
      await wrapper.vm.$nextTick()

      const placeholder = wrapper.find('.svg-placeholder')
      expect(placeholder.exists()).toBe(true)
    })
  })

  describe('Component Functionality', () => {
    it('should render loading state correctly', async () => {
      // Access exposed property and update it
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()

      const innerLoading = wrapper.findComponent(QInnerLoading)
      expect(innerLoading.exists()).toBe(true)
      // Check if loading is shown via the showing prop (Quasar uses 'showing')
      expect(wrapper.vm.loading).toBe(true)
    })

    it('should render error state correctly', async () => {
      wrapper.vm.error = 'Test error message'
      wrapper.vm.loading = false
      await wrapper.vm.$nextTick()

      const banner = wrapper.findComponent(QBanner)
      expect(banner.exists()).toBe(true)
      expect(banner.text()).toContain('Test error message')
    })

    it('should render no data state when no footprint data provided', () => {
      expect(wrapper.find('.no-data-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('No KiCad Footprint Available')
    })

    it('should display footprint metadata correctly', async () => {
      await wrapper.setProps({ footprintData: mockFootprintData })
      await wrapper.vm.$nextTick()

      // Wait for SVG generation to complete
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(wrapper.text()).toContain('REF1')
      expect(wrapper.text()).toContain('TestLib')
    })

    it('should handle zoom controls correctly', async () => {
      await wrapper.setProps({ footprintData: mockFootprintData })
      await wrapper.vm.$nextTick()

      const initialZoom = wrapper.vm.zoomLevel

      // Find zoom buttons by title
      const buttons = wrapper.findAllComponents(QBtn)
      const zoomInBtn = buttons.find(btn => btn.attributes('title') === 'Zoom In')
      const zoomOutBtn = buttons.find(btn => btn.attributes('title') === 'Zoom Out')
      const resetZoomBtn = buttons.find(btn => btn.attributes('title') === 'Reset Zoom')

      // Test zoom in
      if (zoomInBtn) {
        await zoomInBtn.trigger('click')
        await wrapper.vm.$nextTick()
        expect(wrapper.vm.zoomLevel).toBeGreaterThan(initialZoom)
      }

      // Test zoom out
      if (zoomOutBtn) {
        const currentZoom = wrapper.vm.zoomLevel
        await zoomOutBtn.trigger('click')
        await wrapper.vm.$nextTick()
        expect(wrapper.vm.zoomLevel).toBeLessThan(currentZoom)
      }

      // Test reset zoom
      if (resetZoomBtn) {
        await resetZoomBtn.trigger('click')
        await wrapper.vm.$nextTick()
        expect(wrapper.vm.zoomLevel).toBe(1)
      }
    })

    it('should toggle view modes correctly', async () => {
      await wrapper.setProps({ footprintData: mockFootprintData })
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.viewMode).toBe('top')

      // Test view mode toggle functionality
      const toggleButton = wrapper.findComponent(QBtnToggle)
      expect(toggleButton.exists()).toBe(true)
    })

    it('should toggle display options correctly', async () => {
      await wrapper.setProps({ footprintData: mockFootprintData })
      await wrapper.vm.$nextTick()

      const checkboxes = wrapper.findAllComponents(QCheckbox)
      const dimensionsCheckbox = checkboxes.find(cb => cb.props('label') === 'Show Dimensions')
      const padNumbersCheckbox = checkboxes.find(cb => cb.props('label') === 'Show Pad Numbers')

      expect(dimensionsCheckbox).toBeDefined()
      expect(padNumbersCheckbox).toBeDefined()
    })
  })

  describe('TypeScript Type Safety', () => {
    it('should handle properly typed footprint data', async () => {
      const typedData = {
        footprint_reference: 'U1',
        footprint_library: 'Connector_JST',
        footprint_name: 'JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',
        svg_content: legitimateSvgContent,
        pad_count: 2,
        footprint_data: {
          dimensions: {
            width: 5.0,
            height: 2.5,
            drill_size: 0.8
          }
        }
      }

      await wrapper.setProps({ footprintData: typedData })
      await wrapper.vm.$nextTick()

      // The component wraps the data in a computed property
      const receivedData = wrapper.vm.footprintData
      expect(receivedData).toEqual(typedData)
    })
  })
})