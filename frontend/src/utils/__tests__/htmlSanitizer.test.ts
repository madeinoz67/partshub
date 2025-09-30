import { describe, it, expect } from 'vitest'
import {
  sanitizeSvgContent,
  isValidSvgStructure,
  sanitizeTextContent,
  sanitizeWithDetails
} from '../htmlSanitizer'

describe('htmlSanitizer', () => {
  describe('sanitizeSvgContent', () => {
    it('should preserve legitimate SVG content', () => {
      const legitimateSvg = `
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <rect x="10" y="10" width="80" height="80" fill="blue" />
          <circle cx="50" cy="50" r="20" fill="red" />
          <text x="50" y="30" text-anchor="middle">Label</text>
        </svg>
      `

      const result = sanitizeSvgContent(legitimateSvg)

      expect(result).toContain('<svg')
      expect(result).toContain('<rect')
      expect(result).toContain('<circle')
      expect(result).toContain('<text')
      // Check for fill attribute in a more flexible way
      expect(result).toMatch(/fill\s*=\s*["']blue["']/i)
      expect(result).toMatch(/text-anchor\s*=\s*["']middle["']/i)
    })

    it('should remove script tags', () => {
      const maliciousSvg = `
        <svg>
          <rect width="100" height="100" />
          <script>alert('XSS')</script>
        </svg>
      `

      const result = sanitizeSvgContent(maliciousSvg)

      expect(result).not.toContain('<script')
      expect(result).not.toContain('alert')
      expect(result).toContain('<rect')
    })

    it('should remove event handlers', () => {
      const maliciousSvg = `
        <svg>
          <rect onclick="alert('XSS')" width="100" height="100" />
          <circle onmouseover="alert('XSS')" cx="50" cy="50" r="20" />
        </svg>
      `

      const result = sanitizeSvgContent(maliciousSvg)

      expect(result).not.toContain('onclick')
      expect(result).not.toContain('onmouseover')
      expect(result).not.toContain('alert')
      expect(result).toContain('<rect')
      expect(result).toContain('<circle')
    })

    it('should remove javascript: protocols', () => {
      const maliciousSvg = `
        <svg>
          <use href="javascript:alert('XSS')" />
          <image href="javascript:alert('XSS')" />
        </svg>
      `

      const result = sanitizeSvgContent(maliciousSvg)

      expect(result).not.toContain('javascript:')
      expect(result).not.toContain('alert')
    })

    it('should remove iframe and object tags', () => {
      const maliciousSvg = `
        <svg>
          <rect width="100" height="100" />
          <iframe src="javascript:alert('XSS')"></iframe>
          <object data="malicious.swf"></object>
        </svg>
      `

      const result = sanitizeSvgContent(maliciousSvg)

      expect(result).not.toContain('<iframe')
      expect(result).not.toContain('<object')
      expect(result).toContain('<rect')
    })

    it('should handle null and undefined input', () => {
      expect(sanitizeSvgContent(null)).toBe('')
      expect(sanitizeSvgContent(undefined)).toBe('')
      expect(sanitizeSvgContent('')).toBe('')
    })

    it('should handle non-string input', () => {
      expect(sanitizeSvgContent(123 as unknown as string)).toBe('')
      expect(sanitizeSvgContent({} as unknown as string)).toBe('')
      expect(sanitizeSvgContent([] as unknown as string)).toBe('')
    })

    it('should preserve complex legitimate SVG features', () => {
      const complexSvg = `
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad1">
              <stop offset="0%" stop-color="rgb(255,255,0)" />
              <stop offset="100%" stop-color="rgb(255,0,0)" />
            </linearGradient>
            <clipPath id="clip1">
              <rect x="0" y="0" width="100" height="100" />
            </clipPath>
          </defs>
          <g transform="translate(10,10)">
            <rect fill="url(#grad1)" clip-path="url(#clip1)" width="100" height="100" />
            <path d="M 10 10 L 50 10 L 50 50 Z" stroke="black" fill="none" />
          </g>
        </svg>
      `

      const result = sanitizeSvgContent(complexSvg)

      expect(result).toContain('<defs>')
      expect(result).toContain('<linearGradient')
      expect(result).toContain('<clipPath')
      expect(result).toContain('transform="translate(10,10)"')
      expect(result).toContain('fill="url(#grad1)"')
      expect(result).toContain('clip-path="url(#clip1)"')
    })
  })

  describe('isValidSvgStructure', () => {
    it('should return true for valid SVG', () => {
      const validSvg = '<svg><rect /></svg>'
      expect(isValidSvgStructure(validSvg)).toBe(true)
    })

    it('should return false for content with scripts', () => {
      const invalidSvg = '<svg><script>alert("XSS")</script></svg>'
      expect(isValidSvgStructure(invalidSvg)).toBe(false)
    })

    it('should return false for content with event handlers', () => {
      const invalidSvg = '<svg><rect onclick="alert()" /></svg>'
      expect(isValidSvgStructure(invalidSvg)).toBe(false)
    })

    it('should return false for content with javascript: protocol', () => {
      const invalidSvg = '<svg><use href="javascript:alert()" /></svg>'
      expect(isValidSvgStructure(invalidSvg)).toBe(false)
    })

    it('should return false for malformed SVG', () => {
      expect(isValidSvgStructure('<svg><rect>')).toBe(false)
      expect(isValidSvgStructure('<rect></rect>')).toBe(false)
      expect(isValidSvgStructure('')).toBe(false)
      expect(isValidSvgStructure(null as unknown as string)).toBe(false)
    })
  })

  describe('sanitizeTextContent', () => {
    it('should escape HTML entities', () => {
      const input = '<script>alert("XSS")</script> & "quotes" \'apostrophes\''
      const result = sanitizeTextContent(input)

      expect(result).toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt; &amp; &quot;quotes&quot; &#39;apostrophes&#39;')
    })

    it('should handle null and undefined', () => {
      expect(sanitizeTextContent(null)).toBe('')
      expect(sanitizeTextContent(undefined)).toBe('')
    })

    it('should preserve normal text', () => {
      const input = 'Normal text with numbers 123'
      expect(sanitizeTextContent(input)).toBe(input)
    })
  })

  describe('sanitizeWithDetails', () => {
    it('should provide detailed information for clean content', () => {
      const cleanSvg = '<svg><rect /></svg>'
      const result = sanitizeWithDetails(cleanSvg)

      expect(result.original).toBe(cleanSvg)
      expect(result.sanitized).toContain('<svg>')
      expect(result.isValid).toBe(true)
      // DOMPurify may normalize tags (e.g., <rect /> to <rect></rect>), so this is expected
      // We only flag as malicious if substantial content was removed, not just formatting changes
      expect(result.hasMaliciousContent).toBe(false)
    })

    it('should detect malicious content', () => {
      const maliciousSvg = '<svg><script>alert("XSS")</script><rect /></svg>'
      const result = sanitizeWithDetails(maliciousSvg)

      expect(result.original).toBe(maliciousSvg)
      expect(result.sanitized).not.toContain('<script>')
      expect(result.isValid).toBe(false)
      expect(result.hasMaliciousContent).toBe(true)
    })

    it('should handle empty content', () => {
      const result = sanitizeWithDetails('')

      expect(result.original).toBe('')
      expect(result.sanitized).toBe('')
      expect(result.isValid).toBe(false)
      expect(result.hasMaliciousContent).toBe(false)
    })
  })
})