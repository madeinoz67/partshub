# Component Creation Guide

Learn how to add new components to your PartsHub inventory using the streamlined wizard interface.

## Overview

PartsHub v0.4.0+ features a new wizard-based component creation workflow that simplifies adding parts to your inventory. The wizard guides you through a two-step process:

1. **Basic Information** - Essential component details
2. **Resources** (Optional) - Provider integration and additional data

## Creating Components

### Two Creation Modes

PartsHub supports two ways to create components:

#### 1. Linked Parts (Provider Integration)

Create components connected to supplier databases (LCSC, Digi-Key, Mouser) for automatic data enrichment:

- Automatic datasheet URLs
- Real-time pricing (where available)
- Stock availability checking
- Manufacturer part numbers

#### 2. Local Parts

Create standalone components without provider integration:

- Full manual control over all fields
- No external dependencies
- Perfect for custom or salvaged parts
- Ideal for one-off components

## Step-by-Step Instructions

### Step 1: Basic Information

1. Click the **"Add Component"** button in the component list
2. The wizard opens to the **Basic Information** step
3. Fill in the required fields:

#### Required Fields

- **Name**: Descriptive component name (e.g., "10kΩ Resistor 0603")
- **Component Type**: Select from autocomplete list (resistor, capacitor, IC, etc.)
- **Manufacturer**: Start typing to search existing manufacturers with fuzzy matching
  - Matches similar names (e.g., "yag" finds "Yageo")
  - Option to create new manufacturer inline
- **Footprint**: Search for PCB footprint with fuzzy autocomplete
  - Common packages like "0603", "SOT-23", "DIP-8"
  - Create custom footprints as needed
- **Category**: Select from existing categories
- **Storage Location**: Choose where the component is stored

#### Optional Fields

- **Part Number**: Your internal part numbering
- **Manufacturer Part Number**: Official manufacturer part number
- **Value**: Component value (10k, 100nF, etc.)
- **Package**: Physical package type
- **Notes**: Additional information

### Step 2: Resources (Optional)

After completing basic information, optionally add:

#### For Linked Parts

- **Provider**: Select LCSC, Digi-Key, or Mouser
- **Provider SKU**: Enter the supplier's part number
- **Datasheet URL**: Automatically fetched from provider (if available)

#### For Local Parts

- **Datasheet URL**: Manual entry
- **Specifications**: Custom key-value pairs (JSON format)

### Step 3: Review and Create

1. Review all entered information
2. Click **"Create Component"** to save
3. Component is added to inventory and appears in the list

## Fuzzy Search Features

### How Fuzzy Search Works

The wizard's autocomplete uses intelligent fuzzy matching:

```
Input: "yag"
Matches:
  - Yageo (score: 95)
  - Yamaichi (score: 75)
  - Yangjie (score: 70)
```

### Search Tips

- **Partial Matches**: Type part of the name to find matches
- **Case Insensitive**: "YAGEO", "yageo", and "Yageo" all work
- **Typo Tolerant**: Minor spelling mistakes still find results
- **Score Ranking**: Best matches appear first

### Creating New Entries

If your search doesn't find a match:

1. Type the new name in the autocomplete field
2. Click **"Create new: [your text]"** option
3. The new entry is created and selected automatically

## API Usage

### Create a Linked Component

```bash
curl -X POST http://localhost:8000/api/v1/wizard/components \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "10kΩ Resistor 0603",
    "component_type": "resistor",
    "manufacturer_name": "Yageo",
    "footprint": "0603",
    "value": "10kΩ",
    "category_id": "category-uuid",
    "storage_location_id": "location-uuid",
    "provider": "LCSC",
    "provider_sku": "C25804"
  }'
```

### Create a Local Component

```bash
curl -X POST http://localhost:8000/api/v1/wizard/components \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom LED Module",
    "component_type": "led",
    "manufacturer_name": "Generic",
    "footprint": "Custom",
    "category_id": "category-uuid",
    "storage_location_id": "location-uuid",
    "datasheet_url": "https://example.com/datasheet.pdf",
    "notes": "Salvaged from old project"
  }'
```

### Search for Manufacturers

```bash
curl -X GET "http://localhost:8000/api/v1/wizard/manufacturers/search?q=yag&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search for Footprints

```bash
curl -X GET "http://localhost:8000/api/v1/wizard/footprints/search?q=0603&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Best Practices

### Naming Conventions

Use descriptive, searchable names:

- ✅ Good: "10kΩ Resistor 0603 5% 0.1W"
- ❌ Poor: "R1", "Resistor", "10k"

### Manufacturer Selection

- Use fuzzy search to find existing manufacturers first
- Only create new manufacturers when necessary
- Check for variations (e.g., "ST" vs "STMicroelectronics")

### Footprint Consistency

- Use standard footprint names (e.g., "0603", "SOT-23")
- Be consistent with capitalization
- Search before creating custom footprints

### Provider Integration

When to use linked parts:

- ✅ Common components from major suppliers
- ✅ When you need automatic datasheet links
- ✅ Parts you'll reorder regularly

When to use local parts:

- ✅ Custom or one-off components
- ✅ Salvaged or recycled parts
- ✅ Parts without supplier SKUs

## Keyboard Shortcuts

- **Tab**: Move to next field
- **Shift+Tab**: Move to previous field
- **↑/↓**: Navigate autocomplete suggestions
- **Enter**: Select highlighted suggestion
- **Esc**: Close autocomplete dropdown

## Troubleshooting

### Autocomplete Not Working

- **Check Connection**: Ensure backend API is running
- **Verify Authentication**: Make sure you're logged in as admin
- **Clear Cache**: Refresh the page to reload data

### Provider Data Not Fetching

- **Verify SKU**: Double-check the provider part number
- **API Limits**: Some providers have rate limits
- **Network Issues**: Check internet connection

### Component Not Appearing

- **Refresh List**: Click the refresh button
- **Check Filters**: Clear any active filters
- **Verify Creation**: Check for error messages

## Related Documentation

- [Bulk Operations Guide](bulk-operations.md) - Manage multiple components at once
- [Stock Operations Guide](stock-operations.md) - Add and track inventory
- [Getting Started Guide](getting-started.md) - Initial setup and configuration

---

!!! tip "Quick Start"
    New to component creation? Start with local parts to get familiar with the wizard, then explore provider integration for commonly-used components.
