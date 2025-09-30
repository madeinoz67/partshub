import DOMPurify from 'dompurify'

/**
 * Configuration for SVG sanitization specifically for KiCad content
 * Uses DOMPurify's built-in SVG profile with additional security restrictions
 */
const SVG_SANITIZE_CONFIG: DOMPurify.Config = {
  // Use DOMPurify's built-in SVG profile
  USE_PROFILES: { svg: true, svgFilters: true },

  // Add specific restrictions for security
  ADD_TAGS: [], // Don't add any additional tags
  ADD_ATTR: [], // Don't add any additional attributes

  // Forbid dangerous elements
  FORBID_TAGS: ['script', 'object', 'embed', 'iframe', 'applet', 'form', 'input', 'meta', 'link'],

  // Forbid all event handlers
  FORBID_ATTR: [
    // Mouse events
    'onclick', 'onmouseover', 'onmouseout', 'onmousedown', 'onmouseup', 'onmousemove',
    // Keyboard events
    'onkeydown', 'onkeyup', 'onkeypress',
    // Focus events
    'onfocus', 'onblur',
    // Form events
    'onchange', 'onsubmit', 'onreset', 'oninput',
    // Window events
    'onload', 'onunload', 'onresize', 'onscroll',
    // Touch events
    'ontouchstart', 'ontouchend', 'ontouchmove', 'ontouchcancel',
    // Animation events
    'onanimationstart', 'onanimationend', 'onanimationiteration',
    // Transition events
    'ontransitionstart', 'ontransitionend', 'ontransitioncancel',
    // Other events
    'onerror', 'onwheel', 'oncontextmenu'
  ],

  // Security settings
  ALLOW_DATA_ATTR: false,
  ALLOW_UNKNOWN_PROTOCOLS: false,
  SANITIZE_DOM: true,
  KEEP_CONTENT: false
}

/**
 * Sanitizes SVG content to prevent XSS attacks while preserving
 * legitimate SVG functionality for KiCad footprint and symbol visualization
 *
 * @param svgContent Raw SVG content that may contain malicious code
 * @returns Sanitized SVG content safe for v-html rendering
 */
export function sanitizeSvgContent(svgContent: string | null | undefined): string {
  // Handle null, undefined, or empty content
  if (!svgContent || typeof svgContent !== 'string') {
    return ''
  }

  // Trim whitespace
  const trimmedContent = svgContent.trim()

  if (!trimmedContent) {
    return ''
  }

  try {
    // Use DOMPurify with strict SVG configuration
    const sanitized = DOMPurify.sanitize(trimmedContent, SVG_SANITIZE_CONFIG)

    // Additional validation: ensure result is still valid SVG structure
    if (!sanitized || !sanitized.includes('<svg')) {
      console.warn('SVG content was completely sanitized - may have contained malicious content')
      return ''
    }

    return sanitized
  } catch (error) {
    console.error('Error sanitizing SVG content:', error)
    return ''
  }
}

/**
 * Additional validation for SVG content structure
 * Checks for basic SVG validity without parsing
 */
export function isValidSvgStructure(svgContent: string): boolean {
  if (!svgContent || typeof svgContent !== 'string') {
    return false
  }

  const trimmed = svgContent.trim()

  // Basic structural checks
  return (
    trimmed.includes('<svg') &&
    trimmed.includes('</svg>') &&
    !trimmed.includes('<script') &&
    !trimmed.includes('javascript:') &&
    !/on\w+\s*=/i.test(trimmed)
  )
}

/**
 * Sanitizes text content for safe display in component properties
 * This is more permissive than SVG sanitization but still secure
 */
export function sanitizeTextContent(textContent: string | null | undefined): string {
  if (!textContent || typeof textContent !== 'string') {
    return ''
  }

  // Simple HTML escape for text content
  return textContent
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Type-safe wrapper for component properties that may contain user content
 */
export interface SanitizedContent {
  original: string
  sanitized: string
  isValid: boolean
  hasMaliciousContent: boolean
}

/**
 * Comprehensive sanitization with detailed result information
 */
export function sanitizeWithDetails(content: string | null | undefined): SanitizedContent {
  const original = content || ''
  const sanitized = sanitizeSvgContent(content)
  const isValid = isValidSvgStructure(original)

  // Check if content was modified by sanitization (more intelligent comparison)
  // We consider content malicious if:
  // 1. Tags were completely removed (length significantly reduced)
  // 2. Dangerous attributes were removed (script, onclick, etc.)
  const lengthReduction = original.length - sanitized.length
  const hasDangerousContent = (
    original.includes('<script') ||
    original.includes('javascript:') ||
    /on\w+\s*=/.test(original) ||
    original.includes('<iframe') ||
    original.includes('<object')
  )

  // Only flag as malicious if we removed dangerous content or significantly reduced length
  const hasMaliciousContent = hasDangerousContent || (lengthReduction > original.length * 0.1 && original.length > 0)

  return {
    original,
    sanitized,
    isValid,
    hasMaliciousContent
  }
}