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

### Natural Language Search
Intuitive component search using everyday language with pattern-based parsing.

**Implementation:**
- Search mode toggle in `ComponentSearch.vue`
- Natural language input with example queries
- Confidence scoring display with color-coded badges
- Parsed entity chips showing extracted filters
- Search history with localStorage persistence
- Fallback to full-text search for low confidence queries

**Key Components:**
- `ComponentSearch.vue` - Main search interface with NL mode toggle
- Backend integration via `/api/v1/components?nl_query=...`
- Response includes `nl_metadata` with confidence and parsed entities

See [Natural Language Search User Guide](../user/natural-language-search.md) for user documentation.

### Saved Searches
Save and reuse component search queries. See [Saved Searches Integration](saved-searches-integration.md) for implementation details.

### Responsive Design
Mobile-first responsive design using Quasar's responsive utilities and components.

## Feature Integration Guides

### Natural Language Search

The natural language search feature provides an intuitive search interface that understands component queries in plain English.

**Frontend Implementation:**
- **Search Mode Toggle**: Switch between standard and natural language search modes
- **Example Queries**: Pre-populated chips showing common query patterns
- **Confidence Display**: Badge showing query understanding confidence (80-100% = high, 50-79% = medium, <50% = low)
- **Parsed Entities**: Chips displaying extracted filters (component type, stock status, location, value, etc.)
- **Search History**: Last 10 queries stored in localStorage for quick re-use
- **Fallback Warnings**: Banner shown when falling back to full-text search

**API Integration:**
```javascript
// Natural language search request
const response = await api.get('/api/v1/components', {
  params: {
    nl_query: 'resistors with low stock',
    limit: 20
  }
});

// Response structure
{
  components: [...],
  nl_metadata: {
    confidence: 0.85,
    parsed_entities: {
      component_type: 'resistor',
      stock_status: 'low'
    },
    fallback_to_fts5: false
  }
}
```

**UI Components:**
- Search mode toggle (`q-btn-toggle`)
- Natural language input field with psychology icon
- Example query chips (clickable)
- Confidence badge with tooltip
- Parsed filter chips (removable)
- Fallback warning banner
- History dropdown with clear option

**State Management:**
```javascript
const searchMode = ref('standard')  // 'standard' or 'nl'
const nlQuery = ref('')
const nlMetadata = ref(null)
const nlSearchHistory = ref([])
```

**User Experience Features:**
- Inline help text explaining NL search
- Color-coded confidence badges (green/yellow/red)
- Removable filter chips for query refinement
- Search history for frequently used queries
- Smooth mode switching with state preservation

See [Natural Language Search User Guide](../user/natural-language-search.md) for end-user documentation.

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
