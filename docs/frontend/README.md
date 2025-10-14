# Frontend Documentation

!!! info "This page serves as both the README and the index for MkDocs navigation"

Vue.js frontend documentation for PartsHub.

## Overview

The PartsHub frontend is built with:
- **Vue.js 3** - Progressive JavaScript framework
- **Quasar Framework** - Vue.js based framework for responsive web apps
- **Composition API** - Modern Vue.js component composition
- **TypeScript** - Type-safe JavaScript development

## Development Setup

For frontend development setup, see the main [Getting Started Guide](../user/getting-started.md#3-frontend-setup).

## Architecture

The frontend follows a component-based architecture with:
- **Pages** - Route-level components in `src/pages/`
- **Components** - Reusable UI components in `src/components/`
- **Stores** - Pinia state management in `src/stores/`
- **Services** - API communication in `src/services/`

## Key Features

### Barcode Scanning
Progressive enhancement barcode scanning with fallback support. See [Barcode Scanning Architecture](../architecture/barcode-scanning.md) for details.

### KiCad Integration
Frontend interface for KiCad library management and component export. See [KiCad Integration Guide](../architecture/kicad-integration.md) for details.

### Saved Searches
Save and reuse component search queries. See [Saved Searches Integration](saved-searches-integration.md) for implementation details.

### Responsive Design
Mobile-first responsive design using Quasar's responsive utilities and components.

## Feature Integration Guides

### Saved Searches
Complete Vue 3 + Quasar integration for saved searches functionality.

- [Saved Searches Integration Guide](saved-searches-integration.md) - Developer implementation guide
- [Saved Searches User Guide](../user/saved-searches.md) - End-user documentation

## Component Documentation

_Additional frontend component documentation will be added here as it's developed._

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint code
npm run lint
```

## Contributing

When adding frontend documentation:
1. Document new components and their props/events
2. Include usage examples and best practices
3. Update this README with links to new documentation
4. Consider adding screenshots for UI components
