/**
 * TypeScript interfaces for KiCad components
 * Comprehensive type definitions for CAD data and mathematical operations
 */

// Base geometric types
export interface Point2D {
  x: number
  y: number
}

export interface Point3D extends Point2D {
  z: number
}

export interface Size2D {
  width: number
  height: number
}

export interface BoundingBox {
  min_x: number
  max_x: number
  min_y: number
  max_y: number
  width: number
  height: number
}

// KiCad coordinate system and units
export type KiCadUnit = 'mm' | 'mil' | 'inch'

export interface KiCadDimension {
  value: number
  unit: KiCadUnit
}

// Footprint-specific types
export interface KiCadPadSize {
  width: number
  height: number
  unit: KiCadUnit
}

export interface KiCadPadDrill {
  diameter: number
  shape: 'circle' | 'oval'
  offset?: Point2D
}

export interface KiCadPadPosition extends Point2D {
  rotation: number // degrees
  layer: 'top' | 'bottom' | 'through'
}

export interface KiCadPad {
  number: string
  name?: string
  type: 'smd' | 'through_hole' | 'edge_connector' | 'mechanical'
  shape: 'circle' | 'rect' | 'oval' | 'trapezoid' | 'roundrect' | 'custom'
  size: KiCadPadSize
  position: KiCadPadPosition
  drill?: KiCadPadDrill
  layers: string[]
  net?: string
  zone_connection?: 'inherited' | 'solid' | 'thermal' | 'none'
  thermal_bridge_width?: number
  clearance?: number
  solder_mask_margin?: number
  solder_paste_margin?: number
  solder_paste_ratio?: number
}

export interface KiCadFootprintDimensions {
  overall_width: number
  overall_height: number
  courtyard_width?: number
  courtyard_height?: number
  pad_pitch?: number
  row_spacing?: number
  unit: KiCadUnit
}

export interface KiCadFootprintData {
  footprint_library: string
  footprint_name: string
  footprint_reference: string
  description?: string
  keywords?: string[]
  pads: Record<string, KiCadPad>
  dimensions: KiCadFootprintDimensions
  bounding_box: BoundingBox
  layer_count: number
  mounting_holes?: KiCadPad[]
  courtyard_margin?: number
  fabrication_attributes?: Record<string, string | number | boolean>
  assembly_attributes?: Record<string, string | number | boolean>
  svg_content?: string
  creation_date?: string
  last_modified?: string
}

// Symbol-specific types
export interface KiCadPinPosition extends Point2D {
  orientation: 0 | 90 | 180 | 270 // degrees
  length: number
}

export interface KiCadPin {
  number: string
  name: string
  type: 'input' | 'output' | 'bidirectional' | 'tristate' | 'passive' | 'power_in' | 'power_out' | 'open_collector' | 'open_emitter' | 'unspecified'
  electrical_type: 'input' | 'output' | 'bidirectional' | 'tristate' | 'passive' | 'power' | 'unspecified'
  shape: 'line' | 'inverted' | 'clock' | 'inverted_clock' | 'input_low' | 'output_low' | 'edge_clock_high'
  position: KiCadPinPosition
  visibility: 'visible' | 'invisible'
  name_text_size?: number
  number_text_size?: number
}

export interface KiCadSymbolUnit {
  unit_number: number
  unit_name?: string
  pins: Record<string, KiCadPin>
  bounding_box: BoundingBox
  graphic_elements?: KiCadGraphicElement[]
}

export interface KiCadGraphicElement {
  type: 'line' | 'rectangle' | 'circle' | 'arc' | 'polygon' | 'text'
  coordinates: Point2D[]
  stroke_width: number
  fill: 'none' | 'outline' | 'background'
  layer?: string
  text_content?: string
  text_size?: number
  text_angle?: number
}

export interface KiCadSymbolData {
  symbol_library: string
  symbol_name: string
  symbol_reference: string
  description?: string
  keywords?: string[]
  datasheet_url?: string
  units: Record<number, KiCadSymbolUnit>
  pin_count: number
  power_pins?: string[]
  aliases?: string[]
  properties: Record<string, string>
  svg_content?: string
  creation_date?: string
  last_modified?: string
}

// Mathematical operations for CAD data
export interface TransformMatrix {
  a: number // scale x
  b: number // skew y
  c: number // skew x
  d: number // scale y
  e: number // translate x
  f: number // translate y
}

export interface GeometricTransform {
  translate?: Point2D
  rotate?: number // degrees
  scale?: Point2D | number
  matrix?: TransformMatrix
}

// SVG generation types
export interface SVGRenderOptions {
  width: number
  height: number
  viewbox?: string
  background_color?: string
  show_grid?: boolean
  grid_spacing?: number
  show_origin?: boolean
  show_dimensions?: boolean
  show_pin_numbers?: boolean
  show_pin_names?: boolean
  layer_visibility?: Record<string, boolean>
  color_scheme?: 'default' | 'dark' | 'high_contrast' | 'colorblind'
}

export interface SVGStyleConfig {
  pad_colors: Record<string, string>
  trace_colors: Record<string, string>
  text_colors: Record<string, string>
  background_colors: Record<string, string>
  stroke_widths: Record<string, number>
  font_families: Record<string, string>
  font_sizes: Record<string, number>
}

// Visualization and rendering
export interface FootprintVisualizationConfig {
  view_mode: 'top' | 'bottom' | '3d'
  zoom_level: number
  center_point: Point2D
  show_pads: boolean
  show_silkscreen: boolean
  show_courtyard: boolean
  show_fabrication: boolean
  show_assembly: boolean
  highlight_nets?: string[]
  highlight_pads?: string[]
}

export interface SymbolVisualizationConfig {
  zoom_level: number
  center_point: Point2D
  show_pins: boolean
  show_pin_numbers: boolean
  show_pin_names: boolean
  show_body: boolean
  show_reference: boolean
  show_value: boolean
  unit_display: number | 'all'
  style: 'ieee' | 'iec' | 'demorgan'
}

// Validation and analysis
export interface KiCadValidationRule {
  rule_id: string
  rule_name: string
  severity: 'error' | 'warning' | 'info'
  description: string
  category: 'electrical' | 'physical' | 'manufacturing' | 'documentation'
}

export interface KiCadValidationResult {
  is_valid: boolean
  errors: Array<{
    rule_id: string
    message: string
    location?: Point2D
    affected_objects?: string[]
  }>
  warnings: Array<{
    rule_id: string
    message: string
    location?: Point2D
    affected_objects?: string[]
  }>
}

// Design rule checking (DRC)
export interface DesignRules {
  minimum_trace_width: number
  minimum_via_diameter: number
  minimum_drill_size: number
  minimum_clearance: number
  minimum_pad_size: number
  maximum_pad_size: number
  courtyard_clearance: number
  silkscreen_clearance: number
  solder_mask_clearance: number
  solder_paste_clearance: number
  unit: KiCadUnit
}

// Component placement and routing
export interface PlacementConstraints {
  keep_upright: boolean
  allow_rotation: boolean
  allowed_rotations: number[] // degrees
  placement_layer: 'top' | 'bottom' | 'both'
  component_height?: number
  thermal_considerations?: {
    max_temperature: number
    thermal_resistance: number
    heat_dissipation: number
  }
}

// Manufacturing and assembly
export interface ManufacturingData {
  pick_and_place_data?: {
    component_id: string
    position: Point2D
    rotation: number
    layer: 'top' | 'bottom'
    part_number: string
    value: string
    package: string
  }[]
  bill_of_materials?: {
    reference: string
    value: string
    footprint: string
    part_number?: string
    manufacturer?: string
    supplier?: string
    cost?: number
  }[]
  assembly_notes?: string[]
  special_instructions?: string[]
}

// Import/Export formats
export interface KiCadExportOptions {
  format: 'svg' | 'pdf' | 'png' | 'step' | 'vrml' | 'gerber'
  layers?: string[]
  drill_file?: boolean
  pick_and_place?: boolean
  bill_of_materials?: boolean
  resolution?: number // DPI for raster formats
  scale?: number
  color_mode?: 'color' | 'grayscale' | 'monochrome'
}

// Search and filtering for CAD data
export interface KiCadSearchCriteria {
  library_name?: string
  component_name?: string
  pin_count_min?: number
  pin_count_max?: number
  package_type?: string
  mounting_type?: string
  has_3d_model?: boolean
  keywords?: string[]
  electrical_type?: string
  created_after?: string
  created_before?: string
}

// API response types
export interface KiCadComponentResponse {
  footprint_data?: KiCadFootprintData
  symbol_data?: KiCadSymbolData
  available_libraries: string[]
  related_components: string[]
  compatibility_info?: {
    pin_compatible: string[]
    package_compatible: string[]
    electrical_compatible: string[]
  }
}

export interface KiCadLibraryInfo {
  library_name: string
  library_type: 'symbol' | 'footprint' | '3d_model'
  component_count: number
  description?: string
  version?: string
  last_updated?: string
  maintainer?: string
  license?: string
  categories: string[]
}

// Component analysis and metrics
export interface ComponentAnalytics {
  usage_frequency: number
  cost_trends: Array<{
    date: string
    average_cost: number
    supplier_count: number
  }>
  availability_score: number
  obsolescence_risk: 'low' | 'medium' | 'high'
  alternative_count: number
  design_usage: {
    active_projects: number
    total_projects: number
    first_used: string
    last_used: string
  }
}