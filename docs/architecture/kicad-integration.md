# KiCad Integration Guide

PartsHub provides comprehensive integration with KiCad EDA software, enabling seamless component library generation, automatic footprint creation, and bidirectional workflow between your parts inventory and PCB design projects.

## Table of Contents

- [Overview](#overview)
- [Setup and Configuration](#setup-and-configuration)
- [Component Data Management](#component-data-management)
- [Library Generation](#library-generation)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Overview

### What's Included

PartsHub's KiCad integration provides:

- **📚 Automatic Library Generation**: Create complete KiCad libraries from your component database
- **🔗 Symbol & Footprint Management**: Automatic generation based on component specifications
- **📦 3D Model Integration**: Link and manage 3D models for realistic PCB visualization
- **🔄 Bidirectional Sync**: Keep your inventory and KiCad libraries synchronized
- **🎯 Smart Mapping**: Intelligent component-to-symbol/footprint matching
- **📋 Field Population**: Automatic datasheet, manufacturer, and specification fields

### Architecture

```
PartsHub Database ──────► KiCad Export Service ──────► Library Files
      │                           │                           │
   Components                 Templates &                 .kicad_sym
   Specifications             Generators                  .pretty/
   Attachments                                           .3dshapes/
```

## Setup and Configuration

### Prerequisites

- PartsHub server running (backend + frontend)
- KiCad 7.0+ installed
- Admin access to PartsHub for library generation
- Write access to KiCad library directories

### Initial Configuration

1. **Access KiCad Settings**
   - Navigate to PartsHub admin panel
   - Go to Integrations → KiCad Configuration

2. **Set Library Paths**
   ```bash
   # Example KiCad library paths
   Windows: C:\Users\<username>\Documents\KiCad\7.0\libraries\
   macOS: ~/Documents/KiCad/7.0/libraries/
   Linux: ~/.local/share/kicad/7.0/libraries/
   ```

3. **Configure Export Settings**
   - Symbol library naming convention
   - Footprint library organization
   - 3D model path preferences

## Component Data Management

### Required Component Fields

For optimal KiCad integration, ensure components have:

| Field | Required | Purpose | Example |
|-------|----------|---------|---------|
| `part_number` | ✅ | Component identification | `RC0805FR-0710KL` |
| `manufacturer` | ✅ | Library organization | `Yageo` |
| `package` | ✅ | Footprint generation | `0805` |
| `component_type` | ✅ | Symbol selection | `resistor` |
| `value` | Recommended | KiCad Value field | `10kΩ` |
| `specifications` | Recommended | Custom fields | `{"tolerance": "±1%"}` |

### Package Types Supported

#### SMD Components
- **Resistors/Capacitors**: 0402, 0603, 0805, 1206, 1210, 1812, 2010, 2512
- **ICs**: QFN, QFP, LQFP, BGA, CSP
- **Connectors**: Custom footprint generation

#### Through-Hole Components
- **Resistors**: Axial packages (0.25W, 0.5W, 1W, 2W)
- **Capacitors**: Radial, axial configurations
- **ICs**: DIP, SIP, custom pin layouts

### Specification Mapping

Component specifications are automatically mapped to KiCad fields:

```json
{
  "specifications": {
    "voltage_rating": "250V",     // → KiCad "Voltage" field
    "tolerance": "±1%",           // → KiCad "Tolerance" field
    "power_rating": "0.125W",     // → KiCad "Power" field
    "temperature_range": "-55°C to +125°C"  // → KiCad "TempRange" field
  }
}
```

## Library Generation

### Quick Start

1. **Select Components**
   ```http
   GET /api/v1/components?category=resistors&manufacturer=Yageo
   ```

2. **Generate Library**
   ```http
   POST /api/v1/kicad/libraries/sync
   {
     "library_path": "/path/to/kicad/libraries",
     "categories": ["Resistors", "Capacitors"],
     "include_symbols": true,
     "include_footprints": true,
     "include_3d_models": true
   }
   ```

3. **Import to KiCad**
   - Open KiCad → Preferences → Manage Symbol Libraries
   - Add generated `.kicad_sym` file
   - Add footprint library `.pretty` directory

### Library Organization

PartsHub generates organized libraries:

```
PartsHub_Libraries/
├── symbols/
│   ├── PartsHub_Resistors.kicad_sym
│   ├── PartsHub_Capacitors.kicad_sym
│   └── PartsHub_ICs.kicad_sym
├── footprints/
│   ├── PartsHub_Resistors.pretty/
│   │   ├── R_0805_2012Metric.kicad_mod
│   │   └── R_1206_3216Metric.kicad_mod
│   └── PartsHub_Capacitors.pretty/
└── 3dmodels/
    ├── resistors/
    └── capacitors/
```

### Generation Options

#### By Category
```bash
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -H "Content-Type: application/json" \
  -d '{
    "categories": ["Resistors", "Capacitors"],
    "library_path": "./kicad_libs",
    "include_symbols": true,
    "include_footprints": true
  }'
```

#### By Manufacturer
```bash
curl -X GET "http://localhost:8000/api/v1/kicad/components?manufacturer=STMicroelectronics&limit=100"
```

#### Complete Database Export
```bash
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -d '{"library_path": "./complete_lib"}'
```

## API Reference

### Endpoints

#### Component Search for KiCad
```http
GET /api/v1/kicad/components
```

**Parameters:**
- `search`: Component name/part number search
- `package`: Filter by package (0805, LQFP-48, etc.)
- `category_id`: Filter by category UUID
- `manufacturer`: Filter by manufacturer name
- `limit`: Maximum results (default: 50, max: 200)
- `offset`: Pagination offset

**Response:**
```json
[
  {
    "component_id": "a06a4a38-040f-4539-be8a-9a6ea55adb8a",
    "reference": "R",
    "value": "10kΩ",
    "footprint": "Resistors:R_0805_2012Metric",
    "symbol_library": "PartsHub_Resistors",
    "symbol_name": "R_Generic",
    "footprint_library": "PartsHub_Resistors.pretty",
    "footprint_name": "R_0805_2012Metric",
    "model_3d_path": "resistors/R_0805.step",
    "fields": {
      "Tolerance": "±1%",
      "Power": "0.125W",
      "Voltage": "150V"
    },
    "manufacturer": "Yageo",
    "part_number": "RC0805FR-0710KL",
    "datasheet_url": "https://..."
  }
]
```

#### Component Details
```http
GET /api/v1/kicad/components/{component_id}
```

Returns detailed KiCad-formatted component data including all specifications and library references.

#### Symbol Data
```http
GET /api/v1/kicad/components/{component_id}/symbol
```

Returns KiCad symbol library reference and metadata.

#### Footprint Data
```http
GET /api/v1/kicad/components/{component_id}/footprint
```

Returns KiCad footprint library reference and pad information.

#### Library Synchronization
```http
POST /api/v1/kicad/libraries/sync
```

**Request:**
```json
{
  "library_path": "/absolute/path/to/libraries",
  "categories": ["Resistors", "ICs"],  // Optional: filter by categories
  "include_symbols": true,
  "include_footprints": true,
  "include_3d_models": false
}
```

**Response:**
```json
{
  "success": true,
  "components_exported": 1247,
  "symbols_created": 1247,
  "footprints_created": 1247,
  "models_created": 0,
  "library_path": "/absolute/path/to/libraries",
  "message": "Successfully synchronized 1247 components to KiCad libraries"
}
```

### Authentication

Most KiCad API endpoints are read-only and don't require authentication. Library generation requires admin authentication:

```bash
# Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  | jq -r '.access_token')

# Use token for library generation
curl -X POST http://localhost:8000/api/v1/kicad/libraries/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"library_path": "./libs"}'
```

## Advanced Features

### Custom Symbol Templates

Define custom symbol templates for specific component types:

```python
# In KiCad service configuration
SYMBOL_TEMPLATES = {
    "microcontroller": {
        "reference": "U",
        "pins": "auto",  # Auto-generate from specifications
        "graphics": "ic_rectangle"
    },
    "resistor": {
        "reference": "R",
        "pins": 2,
        "graphics": "resistor_zigzag"
    }
}
```

### Footprint Generation Rules

Automatic footprint generation based on package specifications:

```python
FOOTPRINT_RULES = {
    "0805": {
        "pad_size": (1.2, 1.2),
        "pad_spacing": 2.0,
        "pad_type": "smd",
        "courtyard": (2.8, 2.0)
    },
    "LQFP-48": {
        "pin_count": 48,
        "pin_pitch": 0.5,
        "body_size": (7.0, 7.0),
        "pad_type": "smd"
    }
}
```

### 3D Model Management

#### Model Association
Components can reference 3D models stored in PartsHub or external libraries:

```json
{
  "kicad_data": {
    "model_3d_path": "models/resistors/R_0805.step",
    "model_scale": [1.0, 1.0, 1.0],
    "model_rotation": [0, 0, 0],
    "model_offset": [0, 0, 0]
  }
}
```

#### Model Sources
- **Built-in Models**: Common components (resistors, capacitors, basic ICs)
- **Manufacturer Models**: Downloaded from component providers
- **Custom Models**: User-uploaded STEP/WRL files
- **Library Models**: KiCad standard library references

### Batch Operations

#### Bulk Component Import
Import components with KiCad data from CSV:

```csv
part_number,manufacturer,package,symbol_lib,footprint_lib,model_path
RC0805FR-0710KL,Yageo,0805,Resistors,Resistors.pretty,resistors/R_0805.step
CC0805KRX7R9BB104,Yageo,0805,Capacitors,Capacitors.pretty,capacitors/C_0805.step
```

#### Library Validation
Validate generated libraries against KiCad standards:

```bash
curl -X GET http://localhost:8000/api/v1/kicad/libraries/validate \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Common Issues

#### 1. Library Generation Fails
**Problem**: Library sync returns error
**Solution**:
- Check library path permissions
- Verify component data completeness
- Check server logs for detailed errors

```bash
# Check library path
ls -la /path/to/kicad/libraries/
# Verify permissions
chmod 755 /path/to/kicad/libraries/
```

#### 2. Missing Footprints
**Problem**: Components appear in symbols but no footprints generated
**Solution**:
- Verify package field is populated
- Check supported package types
- Add custom footprint templates if needed

#### 3. Invalid Component References
**Problem**: KiCad shows "Component not found" errors
**Solution**:
- Ensure component IDs are UUIDs, not integers
- Check component exists in database
- Verify library paths in KiCad

#### 4. 3D Models Not Loading
**Problem**: 3D models don't appear in KiCad 3D viewer
**Solution**:
- Check model file paths are correct
- Verify file formats (STEP, WRL supported)
- Ensure KiCad can access model directories

### Debug Mode

Enable detailed logging for KiCad operations:

```bash
# Set environment variable
export KICAD_DEBUG=true

# Check debug logs
curl -X GET http://localhost:8000/api/v1/kicad/libraries/status
```

### Performance Optimization

For large component databases:

1. **Incremental Sync**: Only sync modified components
2. **Category Filtering**: Generate libraries by category
3. **Caching**: Enable library caching for repeated exports
4. **Parallel Processing**: Use multiple workers for large exports

```python
# Configuration example
KICAD_CONFIG = {
    "enable_caching": True,
    "cache_ttl": 3600,  # 1 hour
    "parallel_workers": 4,
    "incremental_sync": True
}
```

## Best Practices

### Component Data Quality
- Always populate package field accurately
- Include comprehensive specifications
- Attach datasheets when available
- Use consistent manufacturer names

### Library Organization
- Group components by category or manufacturer
- Use descriptive library names
- Maintain separate development/production libraries
- Regular library validation and cleanup

### Workflow Integration
- Set up automated library updates
- Version control for generated libraries
- Document custom templates and rules
- Regular backup of library configurations

---

For additional support, consult the PartsHub API documentation or contact your system administrator.