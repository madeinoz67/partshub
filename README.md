# PartsHub - Electronic Parts Inventory Management

A modern, web-based inventory management system designed specifically for electronic components and parts. PartsHub provides comprehensive tracking of components, storage locations, stock levels, and specifications with both web interface and API access.

## Features

### 📦 Component Management
- **Comprehensive tracking** of electronic components with detailed specifications
- **Stock level monitoring** with automatic low-stock alerts
- **Storage location management** with hierarchical organization
- **Category and tagging system** for easy organization and searching
- **Stock history tracking** with transaction logs

### 🔐 Tiered Access Control
- **Anonymous browsing** - Read-only access to all inventory data
- **Authenticated users** - Full CRUD operations and stock management
- **Admin users** - API token management and system administration

### 🔍 Advanced Search & Filtering
- **Real-time search** across component names, part numbers, and descriptions
- **Multiple filter options** by category, stock status, storage location
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
- Node.js (v16+)
- Python (3.10+)
- uv (Python package manager)

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
- Search and filter components
- View detailed specifications and stock history
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
- System administration capabilities
- User management (future feature)

## Contributing

This project follows standard development practices:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes with tests
4. **Submit** a pull request

## License

[License information to be added]

## Support

- **Documentation:** Check `/docs/` directory
- **API Reference:** Visit `/docs` endpoint when backend is running
- **Issues:** Use GitHub issues for bug reports and feature requests

---

**Note:** This is an active development project. Features and documentation are continuously being improved.