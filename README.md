# PartsHub - Electronic Parts Inventory Management

[![CI](https://github.com/madeinoz67/partshub/actions/workflows/ci.yml/badge.svg)](https://github.com/madeinoz67/partshub/actions/workflows/ci.yml)
[![CD](https://github.com/madeinoz67/partshub/actions/workflows/cd.yml/badge.svg)](https://github.com/madeinoz67/partshub/actions/workflows/cd.yml)
[![Release](https://github.com/madeinoz67/partshub/actions/workflows/release.yml/badge.svg)](https://github.com/madeinoz67/partshub/actions/workflows/release.yml)

A modern, web-based inventory management system designed specifically for electronic components and parts. PartsHub provides comprehensive tracking of components, storage locations, stock levels, and specifications with both web interface and API access.

**Latest Release**: v0.4.0 (October 2025) - Simplified Component Creation with Wizard & Fuzzy Search!

## Features

### 📦 Component Management
- **Wizard-based component creation** with intuitive two-step workflow (v0.4.0+)
- **Fuzzy search autocomplete** for manufacturers and footprints (v0.4.0+)
- **Provider integration** with LCSC, Digi-Key, and Mouser for linked parts (v0.4.0+)
- **Comprehensive tracking** of electronic components with detailed specifications
- **Stock level monitoring** with low-stock tracking capabilities
- **Inline stock operations** with add/remove/move capabilities (v0.3.0+)
- **Stock transaction history** with pagination and export (v0.3.0+)
- **Storage location management** with hierarchical organization and usage tracking
- **Category and tagging system** for easy organization and searching
- **Bulk operations** for efficient management of multiple components (v0.2.0+)

### 🔐 Tiered Access Control
- **Anonymous browsing** - Read-only access to all inventory data
- **Authenticated users** - Full CRUD operations and stock management
- **Admin users** - API token management and system administration

### 🔍 Advanced Search & Filtering
- **Natural Language Search** - Use plain English queries like "resistors with low stock in A1" (Latest!)
- **Real-time search** across component names, part numbers, and descriptions
- **Multiple filter options** by category, stock status, storage location, price, and specifications
- **Smart confidence scoring** with automatic fallback to full-text search
- **Sorting capabilities** by various fields

### 🌐 Modern Web Interface
- **Responsive design** works on desktop, tablet, and mobile
- **Real-time updates** with optimistic UI updates
- **Intuitive navigation** with breadcrumbs and clear hierarchy
- **Dark/light theme support** (coming soon)

### 🔌 API-First Design
- **RESTful API** with full OpenAPI/Swagger documentation
- **JWT authentication** for secure API access
- **API token management** for service-to-service integration
- **Rate limiting and security** built-in

## Technology Stack

### Frontend
- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Quasar Framework** for UI components
- **Pinia** for state management
- **Vue Router** for navigation

### Backend
- **FastAPI** (Python) for high-performance API
- **SQLAlchemy** ORM with SQLite database
- **Alembic** for database migrations
- **JWT authentication** with bcrypt password hashing
- **Pydantic** for data validation

## Quick Start

### Prerequisites
- **Node.js 20+** (required for frontend build)
- **Python 3.10+** (required for backend)
- **uv** (Python package manager)

### Installation

#### Option 1: Using Makefile (Recommended)
```bash
# Install all dependencies
make install

# Start all development servers
make dev
```

#### Option 2: Manual Setup
```bash
# Install Python dependencies (from project root)
uv sync --extra dev --extra docs

# Backend
cd backend
uv run --project .. alembic upgrade head
uv run --project .. python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

#### Available Make Commands
```bash
make help          # Show all available commands
make install       # Install all dependencies
make dev           # Start all development servers
make test          # Run all tests
make build         # Build all components
make docs          # Start documentation server
make clean         # Clean build artifacts
```

### Natural Language Search (Latest Feature!)

PartsHub now supports searching with conversational queries, making it faster and more intuitive to find components.

#### Quick Examples

Instead of setting multiple filters manually, just type:
- **"find resistors with low stock"** - Get all resistors below minimum stock level
- **"capacitors in location A1"** - Find all capacitors stored in bin A1
- **"10k SMD resistors"** - Search for 10kΩ surface-mount resistors
- **"out of stock transistors"** - List transistors with zero quantity
- **"components under $5"** - Find budget-friendly parts

#### Key Features

- **Plain English queries** - No need to learn complex filter syntax
- **Multi-entity support** - Combine multiple criteria: "10k SMD resistors with low stock in A1"
- **Confidence scoring** - Visual feedback (green/orange/red) shows how well your query was understood
- **Smart fallback** - Automatically uses full-text search for ambiguous queries
- **Search history** - Access your 10 most recent natural language queries
- **Interactive filters** - Click to remove extracted filters and refine results

#### Supported Query Patterns

- **Component types**: resistors, capacitors, LEDs, ICs, transistors, connectors, etc.
- **Stock status**: low stock, out of stock, available, unused, need reorder
- **Locations**: in A1, at Bin-23, from Shelf-A, stored in Cabinet-1
- **Values**: 10k, 100μF, 5V, 16MHz, 0805, DIP8
- **Price**: under $5, cheap, between $1 and $5, less than $10
- **Manufacturers**: Texas Instruments, Murata, Vishay, and more

#### API Example

```bash
# Natural language search via API
curl -X GET "http://localhost:8000/api/v1/components?nl_query=10k%20SMD%20resistors%20with%20low%20stock" \
  -H "accept: application/json"

# Response includes confidence and parsed entities
{
  "components": [...],
  "total": 5,
  "nl_metadata": {
    "query": "10k SMD resistors with low stock",
    "confidence": 0.92,
    "parsed_entities": {
      "component_type": "resistor",
      "resistance": "10kΩ",
      "package": "SMD",
      "stock_status": "low"
    },
    "fallback_to_fts5": false,
    "intent": "search_by_type"
  }
}
```

For complete documentation, see [Natural Language Search Guide](docs/features/search.md).

### Component Creation Wizard (v0.4.0+)

PartsHub introduces a streamlined wizard interface for creating components, making it faster and easier to add new parts to your inventory.

#### Two-Step Workflow

1. **Basic Information**: Enter essential component details with smart autocomplete
2. **Resources (Optional)**: Link to provider data or add custom specifications

#### Key Features

- **Fuzzy Search Autocomplete**: Intelligent search for manufacturers and footprints
  - Real-time suggestions as you type
  - Case-insensitive matching with score-based ranking
  - Option to create new entries inline
- **Dual Creation Modes**:
  - **Linked Parts**: Connect to LCSC, Digi-Key, or Mouser for automatic datasheet fetching
  - **Local Parts**: Create standalone components without provider integration
- **Smart Component Types**: Autocomplete selection for component categories
- **Provider Integration**: Optional connection to supplier APIs for enriched data

#### API Example

```bash
# Create a component using the wizard (linked part)
curl -X POST http://localhost:8000/api/v1/wizard/components \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "10kΩ Resistor",
    "component_type": "resistor",
    "manufacturer_name": "Yageo",
    "footprint": "0603",
    "category_id": "uuid",
    "storage_location_id": "uuid",
    "provider": "LCSC",
    "provider_sku": "C12345"
  }'

# Search for manufacturers with fuzzy matching
curl -X GET "http://localhost:8000/api/v1/wizard/manufacturers/search?q=yag&limit=10" \
  -H "Authorization: Bearer <admin-token>"
```

For detailed documentation, see [Component Creation Guide](docs/user/component-creation.md).

### Bulk Operations for Component Management (v0.2.0+)

PartsHub provides powerful bulk operations for admin users to efficiently manage multiple components simultaneously with atomic transaction safety.

#### Available Operations

- **Add/Remove Tags**: Manage tags across multiple components with preview
- **Add to Project**: Assign components to projects with quantity controls
- **Delete Components**: Permanently remove multiple components atomically
- **Manage Meta-Parts**: Group components into meta-part definitions
- **Purchase Lists**: Queue components for purchasing workflows
- **Stock Updates**: Bulk update inventory quantities
- **Attribution Management**: Track sourcing and attribution data

#### Key Features

- **Cross-Page Selection**: Selection persists across pagination
- **Admin-Only Access**: Secure operations requiring admin authentication
- **Atomic Transactions**: All-or-nothing execution ensures data consistency
- **Concurrent Modification Detection**: Prevents conflicting updates
- **Real-time Preview**: See changes before applying (for tag operations)

#### API Example

```bash
# Add tags to multiple components
curl -X POST http://localhost:8000/api/v1/components/bulk/tags/add \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": ["uuid-1", "uuid-2", "uuid-3"],
    "tags": ["resistor", "SMD"]
  }'
```

For detailed documentation, see [Bulk Operations User Guide](docs/user/bulk-operations.md) and [Bulk Operations API Guide](docs/api/bulk-operations.md).

### Inline Stock Management Operations (v0.3.0+)

PartsHub provides comprehensive inline stock operations accessible directly from the component list, eliminating the need to navigate to separate pages for inventory management.

#### Available Operations

- **Add Stock**: Add inventory to any storage location with lot and pricing tracking
- **Remove Stock**: Safely remove inventory with auto-capping validation
- **Move Stock**: Transfer stock between locations with atomic operations
- **View History**: Access paginated transaction history (10 entries/page)
- **Export History**: Download transaction data in CSV, Excel, or JSON formats

#### Key Features

- **Inline Access**: All operations available from component row expansion menu
- **Pessimistic Locking**: Row-level database locks prevent race conditions
- **Atomic Transactions**: All-or-nothing execution ensures data consistency
- **Location Tracking**: Auto-update `last_used_at` timestamp on all stock movements
- **Pricing Support**: Track lot IDs, unit prices, and total costs
- **Tiered Access**: Admin-only for destructive operations (remove, move, export)
- **Complete Audit Trail**: Full transaction history with pagination and export

#### API Example

```bash
# Add stock to a component
curl -X POST http://localhost:8000/api/v1/components/{id}/stock/add \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "storage-uuid",
    "quantity": 100,
    "lot_id": "LOT-2025-001",
    "price_per_unit": 0.25
  }'

# Export stock history as Excel
curl -X GET "http://localhost:8000/api/v1/components/{id}/stock/history/export?format=excel" \
  -H "Authorization: Bearer <admin-token>" \
  -o component_history.xlsx
```

For detailed documentation, see [Stock Operations User Guide](docs/user/stock-operations.md) and [Stock Operations API Guide](docs/api/stock-operations.md).

### Storage Location Layout Generation (v0.1.1)

PartsHub provides a powerful bulk storage location generation feature to quickly create systematic storage locations with advanced organizational capabilities.

#### Four Layout Types

1. **Single Layout**: Perfect for unique storage needs
2. **Row Layout (1D)**: Create linear sequences (e.g., `box1-a` through `box1-f`)
3. **Grid Layout (2D)**: Create 2D organizational grids (e.g., `drawer-a-1` to `drawer-f-5`)
4. **3D Grid Layout**: Generate multi-level hierarchical storage systems

#### Key Features

- **Real-time Preview**: See location names before creation
- **Bulk Creation**: Create up to 500 locations per batch
- **Flexible Naming**: Letter/number ranges, custom separators
- **Hierarchical Support**: Parent-child location relationships
- **Authentication-Gated**: Preview for all, creation for authenticated users

#### API Preview Example

Preview storage locations without creating them:

```bash
# Preview a row of bins from a-f
curl -X POST http://localhost:8000/api/v1/storage-locations/generate-preview \
  -H "Content-Type: application/json" \
  -d '{
    "layout_type": "row",
    "prefix": "box1-",
    "ranges": [{"range_type": "letters", "start": "a", "end": "f"}],
    "location_type": "bin"
  }'
```

### First Login

1. Check the backend console output for the admin credentials:
   ```
   🔑 DEFAULT ADMIN CREATED:
      Username: admin
      Password: <randomly-generated-password>
   ```

2. Navigate to `http://localhost:3000` and login with these credentials

3. You'll be prompted to change the password on first login

## Documentation

- **[Natural Language Search Guide](docs/features/search.md)** - Complete guide to plain English queries
- **[Getting Started Guide](docs/getting-started.md)** - Complete setup and first-time use
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when backend is running)
- **[Architecture Overview](docs/architecture.md)** - System design and components (coming soon)

## Project Structure

```
partshub/
├── pyproject.toml     # Consolidated Python project configuration
├── uv.lock           # Dependency lock file
├── Makefile          # Development workflow commands
├── backend/          # FastAPI backend application
│   ├── src/          # Application source code
│   ├── migrations/   # Database migrations
│   └── tests/        # Backend tests
├── frontend/         # Vue.js frontend application
│   ├── src/          # Application source code
│   ├── public/       # Static assets
│   └── dist/         # Built application
├── docs/             # Documentation
└── README.md         # This file
```

## Access Levels

### Anonymous Users (No Login Required)
- Browse all components and inventory data
- Search and filter components (including natural language search)
- View detailed specifications and stock levels
- Access storage location information

### Authenticated Users (Login Required)
- All anonymous permissions plus:
- Create, edit, and delete components
- Update stock quantities and manage inventory
- Manage storage locations and organization
- Access personal dashboard and statistics

### Admin Users
- All authenticated permissions plus:
- Create and manage API tokens
- **Bulk operations** for efficient multi-component management
- System administration capabilities
- User management (future feature)

## CI/CD & Deployment

This project uses automated GitHub Actions workflows for continuous integration and deployment:

### 🔄 Continuous Integration (CI)
- **Triggers**: On every push and pull request
- **Tests**: Backend (pytest), Frontend (Vitest), Security scans, Docker builds
- **Quality Gates**: All tests must pass before merging
- **Duration**: ~5-10 minutes

### 🚀 Continuous Deployment (CD)
- **Triggers**: Automatically on main branch merges
- **Process**: Backend → Frontend → Documentation deployment
- **Environment**: Production
- **Manual Override**: Available for emergency deployments

### 📦 Release Automation
- **Triggers**: When git tags (v1.0.0) are created
- **Artifacts**: Docker images, GitHub releases, versioned documentation
- **Registry**: GitHub Container Registry (ghcr.io)
- **Documentation**: Versioned and deployed automatically

### 🛡️ Quality Assurance
- **Required Status Checks**: All CI jobs must pass
- **Branch Protection**: Main branch protected against direct pushes
- **Security Scanning**: Automated dependency and code security checks
- **Coverage Requirements**: Minimum 80% test coverage

For detailed workflow documentation, see:
- [Developer Workflow Guide](docs/workflows/developer-guide.md)
- [Troubleshooting Guide](docs/workflows/troubleshooting.md)

## Contributing

This project follows standard development practices:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes with tests
4. **Submit** a pull request

All pull requests must pass CI checks before merging. See the [Developer Workflow Guide](docs/workflows/developer-guide.md) for detailed instructions.

## License

[License information to be added]

## Support

- **Documentation:** Check `/docs/` directory
- **API Reference:** Visit `/docs` endpoint when backend is running
- **Issues:** Use GitHub issues for bug reports and feature requests

---

**Note:** This is an active development project. Features and documentation are continuously being improved.
