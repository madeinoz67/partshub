# PartsHub Features Guide

Welcome to the comprehensive guide to PartsHub features. This document provides an in-depth overview of all the key functionalities to help you effectively manage your electronic components inventory.

## 1. Component Management

### Overview
Component management is the core functionality of PartsHub, allowing you to track, organize, and maintain your electronic parts inventory with precision and ease.

### Key Operations

#### 1.1 Adding Components
- **Methods:**
  - Manual Entry: Use the "+" button in the Components section
  - Barcode Scanning: Quickly add components using a barcode scanner
  - Bulk Import: (Future feature) Import multiple components via CSV or spreadsheet

#### 1.2 Editing Components
- Modify component details by clicking on an existing component
- Update fields such as:
  - Manufacturer
  - Part Number
  - Description
  - Stock Quantity
  - Storage Location
  - Additional Metadata

#### 1.3 Deleting Components
- Remove individual components from your inventory
- Confirmation dialog prevents accidental deletions
- Deletion logs maintained for inventory tracking

#### 1.4 Component Details
- View comprehensive component information including:
  - Technical specifications
  - Stock history
  - Associated storage locations
  - Usage in projects

### Best Practices
- Use consistent naming conventions
- Keep descriptions clear and concise
- Regularly update stock quantities
- Leverage metadata fields for additional tracking

## 2. Storage Location Layout Generator

### Overview
The Storage Location Layout Generator helps you create a hierarchical and organized storage system for your electronic components.

### Features
- Create nested storage locations (e.g., Building > Room > Shelf > Bin)
- Visual representation of storage hierarchy
- Drag-and-drop organization
- QR code generation for quick location tracking

### Example Hierarchy
```
Electronics Lab
├── Main Storage
│   ├── Resistors Cabinet
│   │   ├── Top Drawer
│   │   │   ├── 1% Tolerance Resistors
│   │   │   └── 5% Tolerance Resistors
│   │   └── Bottom Drawer
│   │       ├── High Wattage Resistors
│   │       └── Specialty Resistors
├── Prototype Room
│   ├── Component Testing Area
│   └── Prototype Storage
```

### Use Cases
- Optimize physical inventory organization
- Streamline component retrieval
- Reduce time spent searching for parts

## 3. Search and Filtering Capabilities

### Advanced Search Features
- Powerful, multi-criteria search functionality
- Instant results as you type
- Supports complex query combinations

### Natural Language Search

PartsHub features an intuitive natural language search mode that lets you find components using everyday language.

**Key Features:**
- **Describe what you want**: Use natural phrases like "resistors with low stock" or "capacitors in A1"
- **Pattern-based parsing**: Fast, predictable results without AI dependencies
- **Confidence scoring**: See how well the system understood your query
- **Search history**: Quick access to recent queries
- **Multi-entity queries**: Combine multiple criteria in one search

**Supported Query Patterns:**
- Component types: `resistors`, `capacitors`, `ICs`, `transistors`
- Stock status: `low stock`, `out of stock`, `available`, `unused`
- Locations: `in A1`, `location Bin-23`, `stored in Shelf-A`
- Values: `10k`, `100μF`, `5V`, `3.3V`, `16MHz`
- Packages: `0805`, `1206`, `DIP8`, `SOT-23`
- Manufacturers: `TI`, `Texas Instruments`, `Infineon`, `Murata`
- Price: `cheap`, `under $5`, `less than $10`
- Combinations: `10k SMD resistors with low stock in A1`

**Confidence Levels:**
- **High (80-100%)**: Query well understood, accurate filtering
- **Medium (50-79%)**: Query partially understood, may need refinement
- **Low (<50%)**: Using fallback full-text search

**Learn more:** [Natural Language Search Guide](natural-language-search.md)

### Filter Options
- By Manufacturer
- By Component Type
- Stock Quantity Range
- Date Added/Modified
- Storage Location
- Custom Metadata Fields

### Sorting
- Sort results by multiple criteria
- Ascending/Descending order
- Save and share custom search configurations

### Saved Searches
Save frequently used search queries for quick access:
- Store complex search parameters
- Execute saved searches with one click
- Track usage statistics
- Organize searches by category

**Detailed saved searches guide available in [Saved Searches Guide](saved-searches.md)**

### Examples
- Find all resistors with stock < 10
- List components added in the last 30 days
- Search for specific manufacturers or part numbers
- Natural language: "10k SMD resistors with low stock"

## 4. Barcode Scanning Features

### Quick Component Updates
- Use mobile or desktop barcode scanner
- Instantly retrieve or update component information
- Supports multiple barcode formats (UPC, EAN, Code 128)

### Workflow
1. Scan barcode
2. Confirm or edit component details
3. Update stock quantity
4. Log transaction

### Integration
- Works with most standard barcode scanners
- Mobile app support (future roadmap)
- Minimal manual data entry

## 5. KiCad Integration Overview

### Purpose
Seamlessly transfer component data between PartsHub and KiCad for PCB design workflows.

### Key Features
- Export component libraries
- Generate symbol mappings
- Sync component metadata

### Workflow
1. Select components in PartsHub
2. Export to KiCad format
3. Import into KiCad schematic tool

**Detailed KiCad workflows available in [KiCad Workflows Guide](kicad-workflows.md)**

## 6. Bulk Operations (Admin Only)

### Overview
Bulk operations allow admin users to perform actions on multiple components simultaneously, saving time when managing large inventories.

### Key Capabilities
- **Tag Management**: Add or remove tags from multiple components at once
- **Project Assignment**: Assign components to projects in bulk with custom quantities
- **Mass Deletion**: Delete multiple components with atomic transaction safety
- **Future Features**: Meta-parts, purchase lists, low-stock alerts, attribution management

### Workflow
1. Select multiple components using checkboxes
2. Click "Selected..." button to open bulk operations menu
3. Choose operation (add tags, assign to project, delete, etc.)
4. Configure operation parameters in dialog
5. Preview changes (for tag operations)
6. Execute with automatic all-or-nothing transaction safety

### Transaction Safety
- **Atomic Operations**: All changes succeed or all are rolled back
- **Concurrent Modification Detection**: Prevents conflicts when multiple users edit simultaneously
- **Cross-Page Selection**: Selection persists across pagination
- **Error Reporting**: Detailed failure information for troubleshooting

### Access Control
- Only admin users can perform bulk operations
- Non-admin users will not see bulk operation controls
- JWT authentication required for API access

**Detailed bulk operations guide available in [Bulk Operations Guide](bulk-operations.md)**

## 7. API Access and Token Management

### API Token Generation
- Available for Authenticated and Admin users
- Generate tokens with specific permissions
- Revoke or regenerate tokens as needed

### Token Types
- **Read-only:** View inventory data
- **Write:** Modify components and inventory
- **Admin:** Full system access

### Best Practices
- Rotate tokens periodically
- Use the most restrictive token possible
- Never share tokens publicly

## 8. Authentication and Access Levels

### User Tiers

#### Anonymous Users
- **Permissions:**
  - Browse components
  - Advanced search
  - View detailed specifications
  - Read-only access

#### Authenticated Users
- **All Anonymous Permissions, Plus:**
  - Create/Edit/Delete components
  - Manage stock quantities
  - Update storage locations
  - Generate API tokens
  - Save and manage searches

#### Admin Users
- **All Authenticated Permissions, Plus:**
  - Bulk operations on components
  - API token management
  - User administration (future feature)
  - System-wide configuration

### Authentication Flow
1. Login with username/password
2. Change default password on first login
3. Access features based on user tier

## Conclusion

PartsHub provides a comprehensive, flexible solution for electronic component inventory management. By leveraging these features, you can streamline your workflow, reduce errors, and maintain an organized parts library.

**Feedback Welcome:** Help us improve PartsHub by sharing your experiences and suggestions!
