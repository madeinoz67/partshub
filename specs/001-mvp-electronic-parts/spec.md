# Feature Specification: MVP Electronic Parts Management Application

**Feature Branch**: `001-mvp-electronic-parts`
**Created**: 2025-09-25
**Updated**: 2025-09-26
**Status**: In Development
**Input**: User description: "mvp electronic parts management application, mimicking https://partsbox.io infunctionality"

## Implementation Status

**Current Progress**: ~75% Complete
- ✅ **Backend**: Complete data models, API endpoints, authentication system
- ✅ **Frontend**: Authentication system with tiered access (anonymous read, admin CRUD)
- ✅ **Database**: All core models implemented with migrations
- ⚠️ **Missing**: Provider integrations, some frontend pages, advanced features

### Recent Updates (2025-09-26)
- Implemented Supplier and Purchase tracking models (T031-T032)
- Added Provider Integration models for external data sources (T036-T037)
- Enhanced authentication with tiered access control:
  - Anonymous users: Full read access to inventory
  - Admin users: Full CRUD + administrative features
  - Login only required for data modifications
- Fixed navigation order: Components → Storage Locations → Dashboard
- **Enhanced API Token Management**:
  - Added industry-standard expiry presets (24h, 1 week, 1 month, 3 months, 6 months, 1 year)
  - Added "Never expires" option with security warning
  - Improved UX with descriptive dropdown options and contextual hints
- **Improved Logout UX**: Logout now redirects to main landing page instead of login screen
- **Authentication System Refinements**:
  - Fixed Pydantic serialization issues for datetime fields
  - Implemented forced password change dialog for first-time admin users
  - Added comprehensive user profile management with anytime password changes
  - Enhanced authentication state management and UI responsiveness

## User Scenarios & Testing

### Primary User Story

As an electronics hobbyist or engineer, I need to track my electronic component inventory so I can quickly find parts for projects, avoid duplicate purchases, and maintain an organized workspace. I want to scan barcodes, search by specifications, track quantities, and see where components are physically stored.

### Acceptance Scenarios

1. **Given** I have a new electronic component, **When** I scan its barcode or manually enter details, **Then** the part is added to my inventory with specifications, quantity, and storage location
2. **Given** I'm working on a project, **When** I search for "capacitor 100uF 25V", **Then** I see all matching components in my inventory with quantities and locations
3. **Given** I use a component for a project, **When** I update the quantity, **Then** the inventory reflects the new count and alerts me when stock is low
4. **Given** I have components in different storage locations, **When** I view a component, **Then** I can see exactly which box/drawer/shelf it's stored in
5. **Given** I want to order more components, **When** I generate a shopping list, **Then** I see parts that are low in stock with supplier information
6. **Given** I'm browsing the components table, **When** I click the expand arrow on a component row, **Then** I see detailed specifications, stock information, and attachments inline without navigating to a separate page
7. **Given** I'm viewing a component's details, **When** I click on the KiCad tab, **Then** I see graphical representations of the component's symbol and footprint with pin/pad layouts for PCB design reference
8. **Given** I have a custom KiCad symbol file for a component, **When** I upload it via the KiCad tab, **Then** the custom symbol overrides the auto-generated one and is displayed in the preview
9. **Given** I want to use a provider's KiCad data, **When** the component is imported from LCSC or similar provider, **Then** the provider's symbol and footprint take precedence over auto-generated versions

### Edge Cases

- What happens when scanning a barcode that doesn't exist in the parts database?
- How does the system handle duplicate part entries with slightly different specifications?
- What occurs when trying to subtract more quantity than available in stock?
- How does the system behave when storage locations are reorganized or renamed?

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow users to add electronic components to inventory manually or via barcode scanning
- **FR-002**: System MUST store component specifications including type, value, voltage rating, tolerance, package, and manufacturer
- **FR-003**: System MUST track quantity on hand for each component with increment/decrement operations
- **FR-004**: System MUST support hierarchical storage locations (cabinet > drawer > box)
- **FR-005**: System MUST provide search functionality across all component fields with filtering
- **FR-006**: System MUST support categorization of components (resistors, capacitors, ICs, connectors, etc.)
- **FR-007**: System MUST track low stock alerts with configurable minimum quantities per component
- **FR-008**: System MUST maintain supplier information and purchase history for components
- **FR-009**: System MUST generate shopping lists based on low stock items
- **FR-010**: System MUST support bulk import/export of component data
- **FR-011**: System MUST provide project-based component allocation and tracking
- **FR-012**: System MUST store and display component datasheets and images
- **FR-013**: Users MUST be able to organize components using custom tags and notes
- **FR-014**: System MUST support barcode generation for storage containers and labels
- **FR-015**: System MUST provide inventory reports showing total value, stock levels, and usage patterns
- **FR-016**: System MUST track detailed stock history with timestamps and operation types (add, remove, move)
- **FR-017**: System MUST support component substitutes and alternative part recommendations
- **FR-018**: System MUST track average purchase prices and estimated total inventory value per component
- **FR-019**: System MUST support custom data fields for component-specific attributes
- **FR-020**: System MUST track component usage in meta-parts (assemblies/BOMs)
- **FR-021**: System MUST provide detailed component view with all specifications, stock operations, and relationships
- **FR-022**: System MUST support file attachments (datasheets, images, documents) per component with drag-and-drop upload interface
- **FR-058**: System MUST store files in local filesystem using hashed directory structure based on component ID for organized storage
- **FR-059**: System MUST support PDF and standard image formats (JPEG, PNG) with file type validation and size limits
- **FR-060**: System MUST provide nested API endpoints for component attachments supporting multiple file uploads per request
- **FR-061**: System MUST automatically generate 64x64 pixel thumbnails for images to display as primary component images in table views
- **FR-062**: System MUST allow users to select a primary image from multiple uploaded images for component identification
- **FR-063**: System MUST display primary image thumbnails and datasheet icons in component table for quick visual identification
- **FR-064**: System MUST provide image gallery view in component details with click-to-expand full-size viewing capability
- **FR-065**: System MUST expose file storage through Docker volume mount for persistent data across container restarts
- **FR-066**: System MUST integrate with component data providers to automatically download datasheets and images with user selection interface
- **FR-067**: System MUST implement rate limiting for provider API requests with token bucket algorithm (1 request/second per domain) to avoid hitting API limits and be respectful to external services
- **FR-068**: System MUST implement download caching (1 hour duration) to prevent duplicate downloads of the same URLs within short time periods
- **FR-069**: System MUST limit concurrent provider downloads (maximum 2 simultaneous requests) to avoid overloading external services and maintain good API citizenship
- **FR-023**: System MUST track ordered stock quantities separate from actual stock on hand
- **FR-024**: System MUST provide a comprehensive dashboard with parts, storage, and project statistics
- **FR-025**: System MUST calculate and display total inventory value across all components
- **FR-026**: System MUST track storage utilization metrics (total locations, occupied locations, archived locations)
- **FR-027**: System MUST distinguish between distinct parts and linked parts in reporting
- **FR-028**: System MUST provide specialized reports for low stock, part attrition, and storage location values

- **FR-029**: System MUST support tiered authentication: anonymous access for search/view operations, JWT-based admin login for CRUD operations via web interface, and API token authentication for CRUD API endpoints
- **FR-030**: System MUST create a default admin user on first run requiring password change on initial login
- **FR-031**: System MUST provide admin dashboard for managing API tokens with individual tokens per application requiring CRUD access
- **FR-054**: System MUST provide industry-standard API token expiry options (24h, 1 week, 1 month, 3 months, 6 months, 1 year) with "never expires" option including security warnings
- **FR-055**: System MUST redirect users to main landing page after logout instead of login screen to maintain continuity with anonymous browsing capability
- **FR-056**: System MUST display contextual hints and security warnings in API token creation interface to guide users toward secure choices
- **FR-057**: System MUST provide dedicated logout route that clears authentication state and redirects to root path (/) for seamless transition from authenticated to anonymous browsing

- **FR-078**: System MUST enforce unique part numbers across all components to prevent duplicate entries and maintain data integrity
- **FR-079**: System MUST support intelligent search ranking that prioritizes results by field relevance (component name > type > part number > value > package > manufacturer > tags > notes)
- **FR-080**: System MUST support multiple storage locations per component with per-location quantity tracking for flexible inventory distribution
- **FR-081**: System MUST track quantity on hand, quantity ordered, and minimum stock levels separately for each storage location
- **FR-082**: System MUST calculate total component quantities by aggregating values across all storage locations where the component is stored
- **FR-083**: System MUST provide a primary storage location property based on the location with the highest quantity on hand
- **FR-084**: System MUST support location-specific notes and unit costs for components stored in multiple locations

- **FR-032**: System MUST retain component data indefinitely with no automatic deletion or expiration policies

- **FR-033**: System MUST support hobbyist/maker scale inventory (10-10,000 components) as a self-contained application with architecture allowing future scaling
- **FR-034**: System MUST support pluggable component data providers with LCSC as the default provider
- **FR-035**: System MUST automatically pull component specifications, datasheets, and images from selected provider when adding components
- **FR-036**: System MUST provide provider selection interface during component creation with support for multiple providers (LCSC, Octopart, Mouser, DigiKey)
- **FR-037**: System MUST implement standardized provider interface allowing future addition of new component data sources
- **FR-038**: System MUST provide KiCad integration allowing KiCad to query and retrieve component data via API
- **FR-039**: System MUST support KiCad-specific data formats for component symbols, footprints, and 3D models
- **FR-040**: System MUST enable component selection and library synchronization between KiCad and PartsHub inventory
- **FR-070**: System MUST display graphical representations of KiCad symbols and footprints in component detail view
- **FR-071**: System MUST provide dedicated KiCad tab in component details showing visual symbol preview with pin layouts
- **FR-072**: System MUST show footprint graphics with pad layouts and physical dimensions for PCB design reference
- **FR-073**: System MUST render KiCad library data in user-friendly format showing component electrical and physical properties
- **FR-074**: System MUST allow users to upload custom KiCad symbol and footprint files to override auto-generated versions
- **FR-075**: System MUST support provider-downloaded KiCad symbols and footprints with preference over auto-generated ones
- **FR-076**: System MUST provide symbol/footprint source priority: custom upload > provider download > auto-generated
- **FR-077**: System MUST allow users to reset to auto-generated symbols/footprints and manage custom overrides
- **FR-041**: System MUST support bulk storage location creation with configurable prefix and naming patterns
- **FR-042**: System MUST provide multiple storage layout options (Single, Row, Grid, 3D Grid) for location organization
- **FR-043**: System MUST support flexible location naming with letter ranges (a-z), number ranges (1-999), and capitalization options
- **FR-044**: System MUST generate multi-dimensional storage grids with rows and columns for systematic organization
- **FR-045**: System MUST preview generated storage locations before creation with confirmation warnings
- **FR-046**: System MUST support single-part-only location restrictions to prevent multiple components per location
- **FR-047**: System MUST prevent deletion of storage locations once created to maintain data integrity

### User Interface Requirements

- **FR-070**: System MUST provide expandable table rows in the main components list for detailed component preview without full page navigation
- **FR-071**: System MUST use standard directional expand icons (right arrow for collapsed, down arrow for expanded) following UI conventions
- **FR-072**: System MUST display attachment type indicators (PDF for datasheets, image thumbnails) in the table Files column for quick visual identification
- **FR-073**: System MUST show component details including specifications, stock information, storage location, and quick actions in the expanded table row
- **FR-074**: System MUST maintain expand/collapse state per component allowing multiple rows to be expanded simultaneously for comparison

### Deployment & Operations Requirements

- **FR-048**: System MUST be deployable as a single Docker container that includes both frontend (Vue.js development server on port 3000) and backend (FastAPI on port 8000) services
- **FR-049**: System MUST use a multi-stage Docker build that combines Node.js for frontend and Python for backend in a single container
- **FR-050**: System MUST support containerized deployment with persistent data volumes for SQLite database storage
- **FR-051**: System MUST provide automatic database seeding with realistic mock electronic components for development and testing
- **FR-052**: System MUST enable database seeding via environment variable (SEED_DB=true) during container startup
- **FR-053**: System MUST run both frontend and backend services concurrently within the same container using a startup script

### Key Entities

- **Component**: Represents an electronic part with specifications, unique part numbers, and relationships to projects and meta-parts (quantities now tracked per location)
- **ComponentLocation**: Junction entity tracking component quantities, costs, and notes for specific storage locations, enabling multiple locations per component
- **Storage Location**: Hierarchical storage system (cabinet/room > shelf/drawer > container/box) where components are physically stored with location codes
- **Category**: Component classification system (passive components, active components, connectors, mechanical, etc.)
- **Supplier**: Vendor information including name, part numbers, pricing, and ordering details
- **Project**: Collection of components allocated for specific builds or designs with usage tracking
- **Stock Transaction**: Detailed record of component operations (add, remove, move) with timestamps, quantities, and reasons
- **Purchase**: Record of component acquisitions including supplier, cost, date, quantities, and pricing history
- **Meta-Part**: Assembly or Bill of Materials (BOM) that contains other components as sub-parts
- **Substitute**: Alternative components that can replace a primary component with compatibility notes
- **Attachment**: Files (datasheets, images, documents) associated with components
- **Custom Field**: User-defined attributes for component-specific data beyond standard specifications
- **Component Data Provider**: External service interface for retrieving component specifications, datasheets, and images (LCSC, Octopart, Mouser, DigiKey)
- **KiCad Library Data**: Component symbols, footprints, and 3D models formatted for KiCad integration with API endpoints for library synchronization

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Technical Architecture (Current Implementation)

### Backend Stack
- **Framework**: FastAPI with Python 3.12
- **Database**: SQLite with SQLAlchemy ORM and Alembic migrations
- **Authentication**: JWT + API tokens with BCrypt password hashing
- **API**: RESTful endpoints with OpenAPI documentation

### Frontend Stack
- **Framework**: Vue.js 3 + TypeScript
- **UI Library**: Quasar Framework
- **State Management**: Pinia stores
- **HTTP Client**: Axios with request/response interceptors

### Key Features Implemented
- **Tiered Access Control**: Anonymous read access, admin CRUD operations
- **Complete Data Models**: Components, Storage Locations, Categories, Projects, Suppliers, Purchases, Provider Integration
- **Authentication System**: Login/logout, API token management, password change requirements
- **Database Migrations**: Versioned schema changes with rollback support
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

### Database Models
- `Component`: Core inventory items with JSON specifications
- `StorageLocation`: Hierarchical storage organization
- `Category`: Component classification system
- `Project`: Component allocation and project tracking
- `StockTransaction`: Audit trail for quantity changes
- `Supplier`: Vendor information and contacts
- `Purchase`/`PurchaseItem`: Purchase history and line items
- `ComponentDataProvider`: External service configuration
- `ComponentProviderData`: Cached provider data
- `User`: Authentication with admin privileges
- `APIToken`: Programmatic API access

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Core backend implementation completed
- [x] Authentication system implemented
- [x] Basic frontend structure created
- [ ] Provider integrations completed
- [ ] All frontend pages implemented
- [ ] Review checklist passed