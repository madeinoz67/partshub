import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import KiCadSymbolViewer from '../KiCadSymbolViewer.vue'

// Security test cases for XSS prevention
const maliciousPayloads = [
  '<script>alert("XSS")</script>',
  '<img src="x" onerror="alert(\'XSS\')">',
  '<svg onload="alert(\'XSS\')"></svg>',
  '<iframe src="javascript:alert(\'XSS\')"></iframe>',
  '<div onclick="alert(\'XSS\')">Click me</div>',
  // Symbol-specific injection attempts
  '<symbol><script>alert("XSS")</script></symbol>',
  '<use href="javascript:alert(\'XSS\')" />',
  '<text onclick="alert(\'XSS\')">Malicious Text</text>',
  // Advanced SVG injections
  '<svg><defs><script>alert("XSS")</script></defs></svg>',
  '<g onmouseover="alert(\'XSS\')"><rect /></g>',
]

const legitimateSymbolSvg = `
<svg width="100" height="80" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="60" fill="none" stroke="black" stroke-width="2" />
  <text x="50" y="25" text-anchor="middle" font-family="Arial" font-size="12">IC1</text>
  <circle cx="5" cy="20" r="2" fill="black" />
  <circle cx="95" cy="20" r="2" fill="black" />
  <text x="2" y="18" font-family="Arial" font-size="8">1</text>
  <text x="98" y="18" font-family="Arial" font-size="8">8</text>
</svg>
`

const mockSymbolData = {
  symbol_reference: 'U1',
  symbol_library: 'MCU_Microchip_PIC',
  symbol_name: 'PIC12F508-I_P',
  svg_content: legitimateSymbolSvg
}

const mockPinData = [
  { pin_number: '1', pin_name: 'VDD', pin_type: 'power_in', position: { x: 0, y: 20 } },
  { pin_number: '2', pin_name: 'GP5/T1CKI/OSC1/CLKIN', pin_type: 'bidirectional', position: { x: 0, y: 40 } },
  { pin_number: '3', pin_name: 'GP4/T1G/OSC2/CLKOUT', pin_type: 'bidirectional', position: { x: 0, y: 60 } },
  { pin_number: '4', pin_name: 'GP3/MCLR/VPP', pin_type: 'input', position: { x: 100, y: 20 } },
]

describe('KiCadSymbolViewer', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    wrapper = mount(KiCadSymbolViewer, {
      global: {
        plugins: [Quasar],
      },
      props: {
        componentId: 'test-component-id'
      }
    })
  })

  describe('Security - XSS Prevention', () => {
    it('should sanitize malicious scripts in symbol SVG content', async () => {
      for (const payload of maliciousPayloads) {
        const maliciousData = {
          ...mockSymbolData,
          svg_content: payload
        }

        await wrapper.setProps({ symbolData: maliciousData })
        await wrapper.vm.$nextTick()

        const svgContainer = wrapper.find('.symbol-svg')
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
          // Should not contain use elements with javascript href
          expect(innerHTML).not.toMatch(/<use\s+[^>]*href\s*=\s*["']javascript:/gi)
        }
      }
    })

    it('should preserve legitimate symbol SVG content', async () => {
      await wrapper.setProps({ symbolData: mockSymbolData })
      await wrapper.vm.$nextTick()

      const svgContainer = wrapper.find('.symbol-svg')
      expect(svgContainer.exists()).toBe(true)

      const innerHTML = svgContainer.element.innerHTML
      expect(innerHTML).toContain('<svg')
      expect(innerHTML).toContain('<rect')
      expect(innerHTML).toContain('<text')
      expect(innerHTML).toContain('<circle')
    })

    it('should handle empty symbol SVG content safely', async () => {
      const emptyData = {
        ...mockSymbolData,
        svg_content: ''
      }

      await wrapper.setProps({ symbolData: emptyData })
      await wrapper.vm.$nextTick()

      const placeholder = wrapper.find('.svg-placeholder')
      expect(placeholder.exists()).toBe(true)
    })

    it('should handle null symbol SVG content safely', async () => {
      const nullData = {
        ...mockSymbolData,
        svg_content: null
      }

      await wrapper.setProps({ symbolData: nullData })
      await wrapper.vm.$nextTick()

      const placeholder = wrapper.find('.svg-placeholder')
      expect(placeholder.exists()).toBe(true)
    })

    it('should sanitize malicious content in pin data tooltips', async () => {
      const maliciousPinData = [
        {
          pin_number: '<script>alert("XSS")</script>',
          pin_name: 'Normal<img src="x" onerror="alert(\'XSS\')">',
          pin_type: 'input',
          position: { x: 0, y: 20 }
        }
      ]

      await wrapper.setProps({
        symbolData: mockSymbolData,
        pinData: maliciousPinData
      })
      await wrapper.vm.$nextTick()

      // Pin data should be displayed safely in the table
      const table = wrapper.find('q-table')
      if (table.exists()) {
        const tableText = table.text()
        expect(tableText).not.toContain('<script>')
        expect(tableText).not.toContain('<img')
      }
    })
  })

  describe('Component Functionality', () => {
    it('should render loading state correctly', () => {
      wrapper.vm.loading = true
      expect(wrapper.find('q-inner-loading').exists()).toBe(true)
    })

    it('should render error state correctly', async () => {
      wrapper.vm.error = 'Test error message'
      wrapper.vm.loading = false
      await wrapper.vm.$nextTick()

      const banner = wrapper.find('q-banner')
      expect(banner.exists()).toBe(true)
      expect(banner.text()).toContain('Test error message')
    })

    it('should render no data state when no symbol data provided', () => {
      expect(wrapper.find('.no-data-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('No KiCad Symbol Available')
    })

    it('should display symbol metadata correctly', async () => {
      await wrapper.setProps({ symbolData: mockSymbolData })
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('U1')
      expect(wrapper.text()).toContain('MCU_Microchip_PIC')
    })

    it('should display pin information table when pin data provided', async () => {
      await wrapper.setProps({
        symbolData: mockSymbolData,
        pinData: mockPinData
      })
      await wrapper.vm.$nextTick()

      const table = wrapper.find('q-table')
      expect(table.exists()).toBe(true)
      expect(wrapper.text()).toContain('Pin Layout')
      expect(wrapper.text()).toContain('VDD')
      expect(wrapper.text()).toContain('power_in')
    })

    it('should not display pin table when no pin data provided', async () => {
      await wrapper.setProps({
        symbolData: mockSymbolData,
        pinData: []
      })
      await wrapper.vm.$nextTick()

      const table = wrapper.find('q-table')
      expect(table.exists()).toBe(false)
    })

    it('should handle symbol properties display correctly', async () => {
      const symbolWithProperties = {
        ...mockSymbolData,
        properties: {
          'Reference': 'U',
          'Value': 'PIC12F508',
          'Footprint': 'Package_DIP:DIP-8_W7.62mm',
          'Datasheet': 'http://ww1.microchip.com/downloads/en/DeviceDoc/41236E.pdf'
        }
      }

      await wrapper.setProps({ symbolData: symbolWithProperties })
      await wrapper.vm.$nextTick()

      // Properties should be displayed if the component supports them
      const symbolContainer = wrapper.find('.symbol-container')
      expect(symbolContainer.exists()).toBe(true)
    })
  })

  describe('TypeScript Type Safety', () => {
    it('should handle properly typed symbol data', async () => {
      const typedSymbolData = {
        symbol_reference: 'IC1',
        symbol_library: 'Logic_74xx',
        symbol_name: '74HC00',
        svg_content: legitimateSymbolSvg,
        pin_count: 14,
        package_type: 'DIP',
        properties: {
          'Value': '74HC00',
          'Footprint': 'Package_DIP:DIP-14_W7.62mm'
        }
      }

      const typedPinData = mockPinData.map(pin => ({
        ...pin,
        electrical_type: pin.pin_type,
        description: `Pin ${pin.pin_number} - ${pin.pin_name}`
      }))

      await wrapper.setProps({
        symbolData: typedSymbolData,
        pinData: typedPinData
      })
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.symbolData).toEqual(typedSymbolData)
      expect(wrapper.vm.pinData).toEqual(typedPinData)
    })

    it('should handle coordinate and geometric data types', async () => {
      const geometricPinData = [
        {
          pin_number: '1',
          pin_name: 'A1',
          pin_type: 'input',
          position: { x: 0.0, y: 2.54 },
          orientation: 0,
          length: 2.54,
          shape: 'line'
        }
      ]

      await wrapper.setProps({
        symbolData: mockSymbolData,
        pinData: geometricPinData
      })
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.pinData[0].position.x).toBe(0.0)
      expect(wrapper.vm.pinData[0].position.y).toBe(2.54)
    })
  })
})