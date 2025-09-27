# KiCad Field Mappings

This document describes how PartsHub component data maps to KiCad component fields and library references.

## Component Data to KiCad Field Mapping

### Core Component Fields

| PartsHub Field | KiCad Field | Description | Example |
|---|---|---|---|
| `part_number` | `Value` | Component value/part number | `RC0805FR-0710KL` |
| `part_number` | `MPN` | Manufacturer part number | `RC0805FR-0710KL` |
| `manufacturer` | `Manufacturer` | Component manufacturer | `Yageo` |
| `notes` | `Description` | Component description/notes | `10kΩ ±1% 0805 resistor` |
| `component_type` | Determines `Reference` | Reference designator prefix | `resistor` → `R` |

### Reference Designator Mapping

Component types automatically map to appropriate reference designators:

| Component Type | Reference | Description |
|---|---|---|
| `resistor` | `R` | Resistors |
| `capacitor` | `C` | Capacitors |
| `inductor` | `L` | Inductors |
| `ic` | `U` | Integrated circuits |
| `microcontroller` | `U` | Microcontrollers |
| `diode` | `D` | Diodes, LEDs |
| `transistor` | `Q` | Transistors |
| `connector` | `J` | Connectors |
| `crystal` | `Y` | Crystals, oscillators |
| *default* | `U` | Unknown/other components |

### Specifications to KiCad Fields

Component specifications are automatically mapped to custom KiCad fields:

| Specification Key | KiCad Field | Description | Example |
|---|---|---|---|
| `voltage_rating` | `Voltage` | Maximum voltage rating | `250V` |
| `tolerance` | `Tolerance` | Component tolerance | `±1%` |
| `power_rating` | `Power` | Power rating | `0.125W` |
| `temperature_range` | `TempRange` | Operating temperature range | `-55°C to +125°C` |
| `current_rating` | `Current` | Current rating | `3A` |
| `forward_voltage` | `Forward Voltage` | LED/diode forward voltage | `2.4V` |
| `reverse_voltage` | `Reverse Voltage` | Maximum reverse voltage | `200V` |
| `resistance` | `Resistance` | Resistance value | `10kΩ` |
| `capacitance` | `Capacitance` | Capacitance value | `100μF` |
| `inductance` | `Inductance` | Inductance value | `10μH` |

### Package to Footprint Mapping

| Package | KiCad Footprint Library | Footprint Name | Type |
|---|---|---|---|
| `0603` | `Resistors` | `R_0603_1608Metric` | SMD |
| `0805` | `Resistors` | `R_0805_2012Metric` | SMD |
| `1206` | `Resistors` | `R_1206_3216Metric` | SMD |
| `DIP8` | `Package_DIP` | `DIP-8_W7.62mm` | Through-hole |
| `SOIC8` | `Package_SO` | `SOIC-8_3.9x4.9mm_P1.27mm` | SMD |
| `QFN48` | `Package_DFN_QFN` | `QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm` | SMD |

## KiCad Library Data Model

### KiCadLibraryData Fields

The `KiCadLibraryData` model stores KiCad-specific information for each component:

| Field | Type | Description | Example |
|---|---|---|---|
| `component_id` | UUID | Reference to component | `a06a4a38-040f-4539-be8a-9a6ea55adb8a` |
| `symbol_library` | String | Symbol library name | `PartsHub_Resistors` |
| `symbol_name` | String | Symbol name within library | `R_Generic` |
| `footprint_library` | String | Footprint library name | `PartsHub_Resistors.pretty` |
| `footprint_name` | String | Footprint name | `R_0805_2012Metric` |
| `model_3d_path` | String | Path to 3D model | `resistors/R_0805.step` |
| `kicad_fields_json` | JSON | Additional KiCad fields | `{"Pin1": "Anode", "Pin2": "Cathode"}` |

### API Response Format

KiCad API endpoints return standardized component data:

```json
{
  "component_id": "uuid",
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
    "Voltage": "150V",
    "Manufacturer": "Yageo",
    "MPN": "RC0805FR-0710KL"
  },
  "specifications": {
    "tolerance": "±1%",
    "power_rating": "0.125W",
    "voltage_rating": "150V"
  },
  "manufacturer": "Yageo",
  "part_number": "RC0805FR-0710KL",
  "datasheet_url": null
}
```

## Library Generation Process

### Symbol Generation

1. **Component Type Detection**: Analyze `component_type` and `specifications`
2. **Template Selection**: Choose appropriate symbol template
3. **Field Population**: Map specifications to KiCad fields
4. **Symbol Creation**: Generate KiCad symbol format

### Footprint Generation

1. **Package Detection**: Extract package from `package` field
2. **Template Lookup**: Find matching footprint template
3. **Pad Generation**: Create pads based on package specifications
4. **Footprint Creation**: Generate KiCad footprint format

### 3D Model Association

1. **Model Lookup**: Search for matching 3D models
2. **Path Generation**: Create relative path to model file
3. **Scale/Rotation**: Apply model transformations
4. **Association**: Link model to footprint

## Custom Field Mapping

### Adding Custom Specifications

To add new specification mappings, update the field mapping in the KiCad service:

```python
SPEC_FIELD_MAPPING = {
    "new_spec": "New KiCad Field",
    "another_spec": "Another Field"
}
```

### Custom Symbol Templates

Add new component type templates:

```python
SYMBOL_TEMPLATES = {
    "new_component_type": {
        "reference": "X",
        "pins": [
            {"number": "1", "name": "Pin1", "type": "passive"},
            {"number": "2", "name": "Pin2", "type": "passive"}
        ],
        "graphics": "custom_symbol"
    }
}
```

### Custom Footprint Templates

Add new package mappings:

```python
FOOTPRINT_TEMPLATES = {
    "custom_package": {
        "type": "smd",
        "size": (2.0, 1.0),
        "pads": [
            {"number": "1", "position": (-1.0, 0), "size": (0.8, 1.0)},
            {"number": "2", "position": (1.0, 0), "size": (0.8, 1.0)}
        ]
    }
}
```

## Data Validation

### Required Fields

For successful KiCad export, components should have:

- `part_number`: Used for Value field
- `component_type`: Determines reference designator
- `package`: Used for footprint generation
- `manufacturer`: Added as Manufacturer field

### Field Validation Rules

| Field | Validation | Notes |
|---|---|---|
| `part_number` | Required, non-empty | Used as primary identifier |
| `component_type` | Should match known types | Falls back to "ic" if unknown |
| `package` | Should match known packages | Falls back to "0805" for passives |
| `specifications` | Valid JSON object | Each key becomes a KiCad field |

## Migration Notes

### Database Schema Changes

When updating field mappings, consider:

1. **Backward Compatibility**: Ensure existing data remains valid
2. **Migration Scripts**: Update existing components if needed
3. **Default Values**: Provide sensible defaults for new fields

### KiCad Version Compatibility

- **File Format**: KiCad 6.0+ format (version 20231120)
- **Symbol Format**: Uses modern property-based format
- **Footprint Format**: Compatible with KiCad 6.0+ footprint format

## Troubleshooting

### Common Issues

1. **Missing Footprints**: Component package not recognized
   - Solution: Add package mapping or use generic footprint

2. **Invalid Reference**: Component type not mapped
   - Solution: Add component type or use default "U"

3. **Missing Fields**: Specifications not mapped to KiCad fields
   - Solution: Add specification key to field mapping

4. **Invalid Symbols**: Generated symbol format errors
   - Solution: Check component data completeness

### Debug Information

Enable debug logging to trace field mapping:

```python
import logging
logging.getLogger('src.services.kicad_library').setLevel(logging.DEBUG)
```

This will show detailed information about:
- Component type detection
- Field mapping process
- Template selection
- Symbol/footprint generation