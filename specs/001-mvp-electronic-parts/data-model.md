# Data Model: MVP Electronic Parts Management Application

## Entity Relationship Overview

The PartsHub data model consists of interconnected entities that support comprehensive electronic component inventory management, from basic part storage to advanced project integration and KiCad synchronization.

## Core Entities

### Component
**Purpose**: Central entity representing electronic parts with specifications, quantities, and relationships

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Component name/description
- `part_number` (String): Manufacturer part number
- `manufacturer` (String): Component manufacturer
- `category_id` (UUID): Foreign key to Category
- `storage_location_id` (UUID): Foreign key to StorageLocation
- `component_type` (String): Basic type (resistor, capacitor, IC, etc.)
- `value` (String): Component value (10kΩ, 100μF, etc.)
- `package` (String): Physical package (0805, DIP8, SOT-23, etc.)
- `quantity_on_hand` (Integer): Current stock quantity
- `quantity_ordered` (Integer): Outstanding order quantity
- `minimum_stock` (Integer): Low stock alert threshold
- `average_purchase_price` (Decimal): Rolling average purchase cost
- `total_purchase_value` (Decimal): Total value of inventory
- `notes` (Text): User notes and comments
- `specifications` (JSON): Component-specific electrical/mechanical parameters
- `custom_fields` (JSON): User-defined attributes and metadata
- `provider_data` (JSON): Cached data from component providers (LCSC, Octopart, etc.)
- `created_at` (Timestamp): Creation timestamp
- `updated_at` (Timestamp): Last modification timestamp

**JSON Field Examples**:
```json
// specifications for a microcontroller
{
  "voltage_supply": "3.3V",
  "current_consumption": "15mA",
  "flash_memory": "64KB",
  "ram": "20KB",
  "frequency": "16MHz",
  "io_pins": 23,
  "interfaces": ["SPI", "I2C", "UART"],
  "temperature_range": "-40°C to +85°C"
}

// specifications for a resistor
{
  "resistance": "10kΩ",
  "tolerance": "±1%",
  "power_rating": "0.125W",
  "temperature_coefficient": "±100ppm/°C",
  "voltage_rating": "150V"
}

// custom_fields examples
{
  "project_tags": ["arduino", "sensor"],
  "purchase_date": "2025-01-15",
  "vendor_part_code": "VENDOR-12345",
  "bin_location": "A3-small-parts",
  "last_used_project": "Temperature Logger v2"
}
```

**Relationships**:
- Belongs to one Category
- Located in one StorageLocation
- Has many StockTransactions
- Has many Purchases
- Has many ComponentTags (many-to-many with Tag)
- Has many Attachments
- Has many CustomFieldValues
- Used in many MetaParts (many-to-many)
- Has many Substitutes
- Used in many Projects (many-to-many through ProjectComponent)

**Validation Rules**:
- `quantity_on_hand` >= 0
- `quantity_ordered` >= 0
- `minimum_stock` >= 0
- `part_number` unique within manufacturer
- `name` required, max 255 characters

### StorageLocation
**Purpose**: Hierarchical storage system supporting physical organization

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Location identifier (box1-a1, drawer-3, etc.)
- `description` (String): Human-readable description
- `parent_location_id` (UUID): Self-referencing foreign key for hierarchy
- `location_type` (String): cabinet, shelf, drawer, box, compartment
- `is_single_part_only` (Boolean): Restricts to one component type
- `created_at` (Timestamp): Creation timestamp

**Relationships**:
- Has many child StorageLocations (self-referencing)
- Belongs to one parent StorageLocation (optional)
- Contains many Components

**Validation Rules**:
- `name` unique within parent location
- Cannot delete location with components
- Hierarchy depth limited to 5 levels

### Category
**Purpose**: Component classification system

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Category name
- `parent_category_id` (UUID): Self-referencing for subcategories
- `description` (Text): Category description
- `icon` (String): UI icon identifier

**Relationships**:
- Has many child Categories (self-referencing)
- Belongs to one parent Category (optional)
- Contains many Components

**Validation Rules**:
- `name` unique within parent category
- Hierarchy depth limited to 3 levels

### Project
**Purpose**: Component allocation and usage tracking

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Project name
- `description` (Text): Project description
- `status` (String): active, completed, archived
- `created_at` (Timestamp): Creation timestamp
- `completed_at` (Timestamp): Completion timestamp (optional)

**Relationships**:
- Has many ProjectComponents (allocation records)
- Through ProjectComponents, uses many Components

**Validation Rules**:
- `name` unique
- `status` must be valid enum value

### ProjectComponent
**Purpose**: Junction table tracking component allocation to projects

**Fields**:
- `id` (UUID): Primary key
- `project_id` (UUID): Foreign key to Project
- `component_id` (UUID): Foreign key to Component
- `quantity_allocated` (Integer): Quantity reserved for project
- `quantity_used` (Integer): Quantity actually consumed
- `allocated_at` (Timestamp): Allocation timestamp

**Relationships**:
- Belongs to one Project
- Belongs to one Component

**Validation Rules**:
- `quantity_allocated` >= `quantity_used`
- `quantity_allocated` > 0

## Transaction and History Entities

### StockTransaction
**Purpose**: Detailed audit trail of all inventory changes

**Fields**:
- `id` (UUID): Primary key
- `component_id` (UUID): Foreign key to Component
- `transaction_type` (String): add, remove, move, adjust
- `quantity_change` (Integer): Quantity delta (positive or negative)
- `previous_quantity` (Integer): Quantity before transaction
- `new_quantity` (Integer): Quantity after transaction
- `reason` (String): Transaction reason/description
- `reference_id` (UUID): Optional reference to related entity
- `created_at` (Timestamp): Transaction timestamp

**Relationships**:
- Belongs to one Component

**Validation Rules**:
- `new_quantity` = `previous_quantity` + `quantity_change`
- `new_quantity` >= 0
- `transaction_type` must be valid enum

### Purchase
**Purpose**: Component acquisition history and pricing

**Fields**:
- `id` (UUID): Primary key
- `supplier_id` (UUID): Foreign key to Supplier
- `purchase_date` (Date): Purchase date
- `total_cost` (Decimal): Total purchase amount
- `currency` (String): Currency code (USD, EUR, etc.)
- `order_reference` (String): Supplier order number
- `notes` (Text): Purchase notes

**Relationships**:
- Belongs to one Supplier
- Has many PurchaseItems

**Validation Rules**:
- `total_cost` >= 0
- `purchase_date` <= current date

### PurchaseItem
**Purpose**: Individual component items within a purchase

**Fields**:
- `id` (UUID): Primary key
- `purchase_id` (UUID): Foreign key to Purchase
- `component_id` (UUID): Foreign key to Component
- `quantity` (Integer): Quantity purchased
- `unit_price` (Decimal): Price per unit
- `total_price` (Decimal): Line item total

**Relationships**:
- Belongs to one Purchase
- Belongs to one Component

**Validation Rules**:
- `quantity` > 0
- `unit_price` >= 0
- `total_price` = `quantity` * `unit_price`

## Supporting Entities

### Supplier
**Purpose**: Vendor information and purchasing history

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Supplier name
- `website` (String): Supplier website URL
- `contact_email` (String): Contact email
- `notes` (Text): Supplier notes

**Relationships**:
- Has many Purchases

**Validation Rules**:
- `name` unique
- `website` valid URL format if provided
- `contact_email` valid email format if provided

### Tag
**Purpose**: Flexible component labeling system

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Tag name
- `color` (String): UI color code

**Relationships**:
- Applied to many Components (many-to-many through ComponentTag)

**Validation Rules**:
- `name` unique
- `color` valid hex color code

### ComponentTag
**Purpose**: Junction table for component-tag relationships

**Fields**:
- `component_id` (UUID): Foreign key to Component
- `tag_id` (UUID): Foreign key to Tag

**Relationships**:
- Belongs to one Component
- Belongs to one Tag

### Attachment
**Purpose**: File attachments for components

**Fields**:
- `id` (UUID): Primary key
- `component_id` (UUID): Foreign key to Component
- `filename` (String): Original filename
- `file_path` (String): Storage file path
- `file_type` (String): MIME type
- `file_size` (Integer): File size in bytes
- `description` (String): File description
- `uploaded_at` (Timestamp): Upload timestamp

**Relationships**:
- Belongs to one Component

**Validation Rules**:
- `file_size` > 0
- `file_type` in allowed MIME types
- `filename` required

### CustomField
**Purpose**: User-defined component attributes

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Field name
- `data_type` (String): text, number, boolean, date
- `description` (Text): Field description

**Relationships**:
- Has many CustomFieldValues

**Validation Rules**:
- `name` unique
- `data_type` must be valid enum

### CustomFieldValue
**Purpose**: Values for custom fields per component

**Fields**:
- `id` (UUID): Primary key
- `component_id` (UUID): Foreign key to Component
- `custom_field_id` (UUID): Foreign key to CustomField
- `value` (Text): Field value stored as text

**Relationships**:
- Belongs to one Component
- Belongs to one CustomField

**Validation Rules**:
- Value format must match CustomField data_type
- Unique combination of component_id and custom_field_id

## Advanced Features

### MetaPart
**Purpose**: Assembly/BOM management

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Assembly name
- `description` (Text): Assembly description
- `version` (String): Assembly version

**Relationships**:
- Contains many Components (many-to-many through MetaPartComponent)

### MetaPartComponent
**Purpose**: Junction table for assembly composition

**Fields**:
- `meta_part_id` (UUID): Foreign key to MetaPart
- `component_id` (UUID): Foreign key to Component
- `quantity_required` (Integer): Required quantity in assembly

**Relationships**:
- Belongs to one MetaPart
- Belongs to one Component

### Substitute
**Purpose**: Alternative component recommendations

**Fields**:
- `id` (UUID): Primary key
- `primary_component_id` (UUID): Foreign key to primary Component
- `substitute_component_id` (UUID): Foreign key to substitute Component
- `compatibility_notes` (Text): Usage compatibility notes

**Relationships**:
- References one primary Component
- References one substitute Component

**Validation Rules**:
- Primary and substitute components must be different
- No circular substitution chains

## Provider Integration

### ComponentDataProvider
**Purpose**: External service configuration

**Fields**:
- `id` (UUID): Primary key
- `name` (String): Provider name (LCSC, Octopart, etc.)
- `api_url` (String): Provider API base URL
- `api_key_encrypted` (String): Encrypted API credentials
- `is_enabled` (Boolean): Provider activation status
- `priority` (Integer): Search priority order

**Relationships**:
- Has many ComponentProviderData records

**Validation Rules**:
- `name` unique
- `api_url` valid URL format
- `priority` unique among enabled providers

### ComponentProviderData
**Purpose**: Cached provider data per component

**Fields**:
- `id` (UUID): Primary key
- `component_id` (UUID): Foreign key to Component
- `provider_id` (UUID): Foreign key to ComponentDataProvider
- `provider_part_id` (String): Provider's part identifier
- `datasheet_url` (String): Cached datasheet URL
- `image_url` (String): Cached component image URL
- `specifications_json` (JSON): Provider specifications data
- `cached_at` (Timestamp): Cache timestamp

**Relationships**:
- Belongs to one Component
- Belongs to one ComponentDataProvider

**Validation Rules**:
- Unique combination of component_id and provider_id
- `cached_at` used for cache invalidation

## KiCad Integration

### KiCadLibraryData
**Purpose**: KiCad-specific component data

**Fields**:
- `id` (UUID): Primary key
- `component_id` (UUID): Foreign key to Component
- `symbol_library` (String): KiCad symbol library name
- `symbol_name` (String): Symbol identifier
- `footprint_library` (String): Footprint library name
- `footprint_name` (String): Footprint identifier
- `model_3d_path` (String): 3D model file path
- `kicad_fields_json` (JSON): Additional KiCad-specific fields

**Relationships**:
- Belongs to one Component

**Validation Rules**:
- `symbol_name` required if `symbol_library` provided
- `footprint_name` required if `footprint_library` provided

## Database Indexes

### Primary Indexes
- All primary keys (UUID) automatically indexed
- Foreign key relationships indexed for join performance

### Search Optimization
- Full-text search index on Component (name, part_number, description)
- Composite index on Component (category_id, component_type)
- Index on Component (manufacturer, part_number) for uniqueness
- Index on StockTransaction (component_id, created_at) for history queries

### Performance Indexes
- Index on StorageLocation (parent_location_id) for hierarchy queries
- Index on ProjectComponent (project_id, component_id) for allocation queries
- Index on ComponentProviderData (component_id, cached_at) for cache management

## Data Integrity Constraints

### Referential Integrity
- Cascade delete for dependent records (StockTransaction when Component deleted)
- Restrict delete for referenced entities (prevent Category deletion if Components exist)
- Soft delete for audit trail preservation (Component marked inactive vs deleted)

### Business Logic Constraints
- Stock quantities cannot be negative
- Purchase prices must be non-negative
- Allocation quantities cannot exceed available stock
- Storage location hierarchy cannot be circular

### Audit Requirements
- All changes to Component quantities logged in StockTransaction
- Purchase history maintained indefinitely
- Component creation/modification timestamps tracked
- User actions logged with authentication context

## Migration Strategy

### Initial Schema
- Create all tables with proper constraints and indexes
- Populate default Categories (Resistors, Capacitors, ICs, etc.)
- Create default admin user and authentication tokens
- Initialize ComponentDataProvider entries (LCSC enabled by default)

### Data Import Support
- Bulk import API for existing inventory data
- CSV import with field mapping interface
- Validation and error reporting for import process
- Rollback capability for failed imports

This data model provides a comprehensive foundation for electronic component inventory management while maintaining flexibility for future enhancements and integrations.