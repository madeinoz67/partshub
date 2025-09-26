# Tasks: MVP Electronic Parts Management Application

**Input**: Design documents from `/specs/001-mvp-electronic-parts/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow Summary

This task list implements a comprehensive electronic parts inventory management system using:
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue.js 3 + Quasar Framework
- **Integrations**: Component data providers (LCSC), KiCad, barcode scanning
- **Architecture**: Web application (frontend + backend + API)

## Path Conventions
- **Backend**: `backend/src/` at repository root
- **Frontend**: `frontend/src/` at repository root
- **Tests**: `backend/tests/` and `frontend/tests/`
- **Database**: SQLite with JSON fields for flexible component specifications

## Phase 3.1: Project Setup

- [x] T001 Create FastAPI backend project structure with src/, tests/, and pyproject.toml in backend/
- [x] T002 Initialize Vue.js 3 + Quasar frontend project with components/, pages/, and services/ in frontend/
- [x] T003 [P] Configure Python development environment with ruff, black, mypy, and pre-commit hooks
- [x] T004 [P] Configure frontend linting with ESLint, prettier, and TypeScript for Vue.js components
- [x] T005 Setup SQLite database with SQLAlchemy models and Alembic migrations in backend/src/database/
- [x] T006 Create Docker Compose configuration for self-contained deployment with mounted SQLite volume
- [x] T007 [P] Initialize backend testing framework with pytest and FastAPI test client configuration

## Phase 3.2: Contract Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Components API Contract Tests
- [x] T008 [P] Contract test GET /api/v1/components in backend/tests/contract/test_components_list.py
- [x] T009 [P] Contract test POST /api/v1/components in backend/tests/contract/test_components_create.py
- [x] T010 [P] Contract test GET /api/v1/components/{id} in backend/tests/contract/test_components_get.py
- [x] T011 [P] Contract test PUT /api/v1/components/{id} in backend/tests/contract/test_components_update.py
- [x] T012 [P] Contract test DELETE /api/v1/components/{id} in backend/tests/contract/test_components_delete.py
- [x] T013 [P] Contract test POST /api/v1/components/{id}/stock in backend/tests/contract/test_components_stock.py
- [x] T014 [P] Contract test GET /api/v1/components/{id}/history in backend/tests/contract/test_components_history.py

### Storage API Contract Tests
- [x] T015 [P] Contract test GET /api/v1/storage-locations in backend/tests/contract/test_storage_list.py
- [x] T016 [P] Contract test POST /api/v1/storage-locations in backend/tests/contract/test_storage_create.py
- [x] T017 [P] Contract test POST /api/v1/storage-locations/bulk-create in backend/tests/contract/test_storage_bulk.py
- [x] T018 [P] Contract test GET /api/v1/storage-locations/{id} in backend/tests/contract/test_storage_get.py
- [x] T019 [P] Contract test PUT /api/v1/storage-locations/{id} in backend/tests/contract/test_storage_update.py
- [x] T020 [P] Contract test GET /api/v1/storage-locations/{id}/components in backend/tests/contract/test_storage_components.py

### KiCad API Contract Tests
- [x] T021 [P] Contract test GET /api/v1/kicad/components in backend/tests/contract/test_kicad_search.py
- [x] T022 [P] Contract test GET /api/v1/kicad/components/{id} in backend/tests/contract/test_kicad_component.py
- [x] T023 [P] Contract test GET /api/v1/kicad/components/{id}/symbol in backend/tests/contract/test_kicad_symbol.py
- [x] T024 [P] Contract test GET /api/v1/kicad/components/{id}/footprint in backend/tests/contract/test_kicad_footprint.py
- [x] T025 [P] Contract test POST /api/v1/kicad/libraries/sync in backend/tests/contract/test_kicad_sync.py

## Phase 3.3: Data Models (ONLY after contract tests are failing)

### Core Entity Models
- [x] T026 [P] Component model with JSON specifications field in backend/src/models/component.py
- [x] T027 [P] StorageLocation model with hierarchy support in backend/src/models/storage_location.py
- [x] T028 [P] Category model with tree structure in backend/src/models/category.py
- [x] T029 [P] Project model and ProjectComponent junction in backend/src/models/project.py
- [x] T030 [P] StockTransaction audit model in backend/src/models/stock_transaction.py

### Supporting Models
- [x] T031 [P] Purchase and PurchaseItem models in backend/src/models/purchase.py
- [x] T032 [P] Supplier model in backend/src/models/supplier.py
- [x] T033 [P] Tag and ComponentTag junction models in backend/src/models/tag.py
- [x] T034 [P] Attachment model for component files in backend/src/models/attachment.py
- [x] T035 [P] CustomField and CustomFieldValue models in backend/src/models/custom_field.py

### Provider and Integration Models
- [x] T036 [P] ComponentDataProvider model in backend/src/models/provider.py
- [x] T037 [P] ComponentProviderData cache model in backend/src/models/provider_data.py
- [ ] T038 [P] KiCadLibraryData model in backend/src/models/kicad_data.py ⚠️ NOT IMPLEMENTED
- [ ] T039 [P] MetaPart and MetaPartComponent models in backend/src/models/meta_part.py ⚠️ NOT IMPLEMENTED
- [x] T040 [P] Substitute model for alternative components in backend/src/models/substitute.py

### Database Setup
- [x] T041 Database initialization with default categories and admin user in backend/src/database/init_data.py
- [ ] T042 SQLite FTS5 full-text search setup for component search in backend/src/database/search.py ⚠️ NOT IMPLEMENTED

## Phase 3.4: Authentication and Core Services

### Authentication System
- [x] T043 JWT authentication with tiered access (anonymous, admin, API tokens) in backend/src/auth/
- [x] T044 API token management service in backend/src/auth/api_tokens.py
- [x] T045 Default admin user creation and password change requirement in backend/src/auth/admin.py
- [x] T051 Create login page component in frontend/src/pages/LoginPage.vue with username/password form
- [x] T052 Create API token management page in frontend/src/pages/ApiTokensPage.vue (admin-only access)

### Authentication Enhancements (2025-09-26)
- [x] T057 Fix Pydantic serialization issues for datetime fields in authentication endpoints
- [x] T058 Implement forced password change dialog for first-time admin users in frontend/src/components/PasswordChangeDialog.vue
- [x] T059 Add comprehensive user profile management with anytime password changes
- [x] T060 Enhance API token management with industry-standard expiry presets (24h, 1 week, 1 month, 3 months, 6 months, 1 year)
- [x] T061 Add "Never expires" option with security warnings for API tokens
- [x] T062 Improve API token creation UX with descriptive dropdown options and contextual hints
- [x] T063 Update logout functionality to redirect to main landing page instead of login screen

### Business Logic Services
- [x] T046 ComponentService with CRUD and search operations in backend/src/services/component_service.py
- [x] T047 StorageLocationService with hierarchy and bulk creation in backend/src/services/storage_service.py
- [ ] T048 ProjectService with component allocation tracking in backend/src/services/project_service.py ⚠️ NOT IMPLEMENTED
- [ ] T049 StockService for inventory transactions and history in backend/src/services/stock_service.py ⚠️ NOT IMPLEMENTED
- [ ] T050 ReportService for dashboard statistics and analytics in backend/src/services/report_service.py ⚠️ NOT IMPLEMENTED

## Phase 3.5: API Endpoint Implementation

### Components API Endpoints
- [ ] T051 GET /api/v1/components endpoint with search and filtering in backend/src/api/components.py
- [ ] T052 POST /api/v1/components endpoint with validation in backend/src/api/components.py
- [ ] T053 GET /api/v1/components/{id} endpoint with details in backend/src/api/components.py
- [ ] T054 PUT /api/v1/components/{id} endpoint with updates in backend/src/api/components.py
- [ ] T055 DELETE /api/v1/components/{id} endpoint in backend/src/api/components.py
- [ ] T056 POST /api/v1/components/{id}/stock stock transaction endpoint in backend/src/api/components.py
- [ ] T057 GET /api/v1/components/{id}/history stock history endpoint in backend/src/api/components.py

### Storage API Endpoints
- [ ] T058 GET /api/v1/storage-locations endpoint with hierarchy in backend/src/api/storage.py
- [ ] T059 POST /api/v1/storage-locations endpoint in backend/src/api/storage.py
- [ ] T060 POST /api/v1/storage-locations/bulk-create bulk creation endpoint in backend/src/api/storage.py
- [ ] T061 GET /api/v1/storage-locations/{id} endpoint with details in backend/src/api/storage.py
- [ ] T062 PUT /api/v1/storage-locations/{id} endpoint in backend/src/api/storage.py
- [ ] T063 GET /api/v1/storage-locations/{id}/components endpoint in backend/src/api/storage.py

### KiCad API Endpoints
- [ ] T064 GET /api/v1/kicad/components search endpoint in backend/src/api/kicad.py
- [ ] T065 GET /api/v1/kicad/components/{id} component details endpoint in backend/src/api/kicad.py
- [ ] T066 GET /api/v1/kicad/components/{id}/symbol endpoint in backend/src/api/kicad.py
- [ ] T067 GET /api/v1/kicad/components/{id}/footprint endpoint in backend/src/api/kicad.py
- [ ] T068 POST /api/v1/kicad/libraries/sync library synchronization in backend/src/api/kicad.py

## Phase 3.6: Frontend Implementation

### Core Vue.js Components
- [ ] T069 [P] ComponentList component with search and filtering in frontend/src/components/ComponentList.vue
- [ ] T070 [P] ComponentDetail component with specifications and stock in frontend/src/components/ComponentDetail.vue
- [ ] T071 [P] ComponentForm component for creating/editing in frontend/src/components/ComponentForm.vue
- [ ] T072 [P] StorageLocationTree component with hierarchy display in frontend/src/components/StorageLocationTree.vue
- [ ] T073 [P] StorageLocationForm component with bulk creation in frontend/src/components/StorageLocationForm.vue
- [ ] T074 [P] ProjectView component with component allocation in frontend/src/components/ProjectView.vue

### Dashboard and Reports
- [ ] T075 [P] Dashboard component with statistics cards in frontend/src/components/Dashboard.vue
- [ ] T076 [P] ReportView component for inventory analytics in frontend/src/components/ReportView.vue
- [ ] T077 [P] BarcodeScanner component for component input in frontend/src/components/BarcodeScanner.vue

### Main Pages
- [ ] T078 [P] InventoryPage with component management in frontend/src/pages/InventoryPage.vue
- [ ] T079 [P] StoragePage with location management in frontend/src/pages/StoragePage.vue
- [ ] T080 [P] ProjectsPage with project tracking in frontend/src/pages/ProjectsPage.vue
- [ ] T081 [P] AdminPage with system settings in frontend/src/pages/AdminPage.vue

## Phase 3.7: External Integrations

### Component Data Providers
- [x] T082 [P] Abstract ComponentDataProvider interface in backend/src/providers/base_provider.py
- [x] T083 [P] LCSC provider implementation with API integration in backend/src/providers/lcsc_provider.py
- [x] T084 [P] Provider service for managing multiple providers in backend/src/services/provider_service.py
- [x] T085 [P] Component import from provider functionality in backend/src/services/import_service.py

### Provider SKU Search Enhancement (New Tasks)
- [ ] T107 [P] Add provider SKU search method to ComponentDataProvider interface in backend/src/providers/base_provider.py
- [ ] T108 [P] Implement provider SKU search in LCSCProvider with SKU format detection in backend/src/providers/lcsc_provider.py
- [ ] T109 [P] Enhance ProviderService with unified search (manufacturer PN + provider SKU) in backend/src/services/provider_service.py
- [ ] T110 [P] Add provider SKU search API endpoint POST /api/v1/providers/search-sku in backend/src/api/integrations.py
- [ ] T111 [P] Update ComponentSearchResult model to include provider_part_id field in backend/src/providers/base_provider.py
- [ ] T112 [P] Create provider SKU search frontend component in frontend/src/components/ProviderSkuSearch.vue
- [ ] T113 [P] Enhance component search UI with search type selection (PN vs SKU) in frontend/src/components/ComponentSearch.vue
- [ ] T114 [P] Add BOM generation service with provider SKU integration in backend/src/services/bom_service.py
- [ ] T115 [P] Create BOM export functionality for KiCad integration with provider SKUs in backend/src/api/bom.py

### Barcode Processing
- [ ] T086 [P] Barcode scanning service with pyzbar integration in backend/src/services/barcode_service.py
- [ ] T087 [P] Frontend barcode capture with camera API in frontend/src/services/barcode.js

### KiCad Integration
- [ ] T088 KiCad library export service in backend/src/services/kicad_service.py
- [ ] T089 Component symbol and footprint management in backend/src/services/kicad_library.py

## Phase 3.8: Integration Tests

**Based on quickstart.md scenarios**
- [ ] T090 [P] First-time setup and component addition integration test in backend/tests/integration/test_setup.py
- [ ] T091 [P] Component search and inventory management integration test in backend/tests/integration/test_inventory.py
- [ ] T092 [P] Project-based component management integration test in backend/tests/integration/test_projects.py
- [ ] T093 [P] Component data provider integration test in backend/tests/integration/test_providers.py
- [ ] T094 [P] KiCad integration test in backend/tests/integration/test_kicad.py
- [ ] T095 [P] Bulk storage operations integration test in backend/tests/integration/test_bulk_storage.py
- [ ] T096 [P] Authentication and API access integration test in backend/tests/integration/test_auth.py

## Phase 3.9: Polish and Performance

### Unit Tests
- [ ] T097 [P] Component model unit tests in backend/tests/unit/test_component_model.py
- [ ] T098 [P] Storage location hierarchy unit tests in backend/tests/unit/test_storage_model.py
- [ ] T099 [P] Stock transaction validation unit tests in backend/tests/unit/test_stock_service.py
- [ ] T100 [P] Search and filtering unit tests in backend/tests/unit/test_search.py

### Frontend Testing
- [ ] T101 [P] Vue component unit tests with Vue Test Utils in frontend/tests/unit/
- [ ] T102 [P] Frontend integration tests with Playwright in frontend/tests/integration/

### Performance and Documentation
- [ ] T103 Database indexing optimization for component search performance in backend/src/database/indexes.py
- [ ] T104 [P] API documentation with FastAPI auto-generated OpenAPI specs
- [ ] T105 [P] Frontend build optimization and deployment configuration
- [ ] T106 User documentation and deployment guide in docs/

## Dependencies

### Critical Path Dependencies
- Setup (T001-T007) must complete before all other phases
- Contract tests (T008-T025) must fail before models and implementation
- Models (T026-T042) must complete before services (T043-T050)
- Services must complete before API endpoints (T051-T068)
- Backend APIs must be working before frontend integration

### Parallel Execution Opportunities
- All contract tests can run in parallel [P] (T008-T025)
- All data models can be created in parallel [P] (T026-T040)
- Frontend components can be developed in parallel [P] (T069-T081)
- Provider integrations can be developed in parallel [P] (T082-T087)
- All integration tests can run in parallel [P] (T090-T096)

## Parallel Execution Examples

### Setup Phase Parallel Tasks
```
Task: "Configure Python development environment with ruff, black, mypy, and pre-commit hooks"
Task: "Configure frontend linting with ESLint, prettier, and TypeScript for Vue.js components"
Task: "Initialize backend testing framework with pytest and FastAPI test client configuration"
```

### Contract Tests Parallel Execution (after setup complete)
```
Task: "Contract test GET /api/v1/components in backend/tests/contract/test_components_list.py"
Task: "Contract test POST /api/v1/components in backend/tests/contract/test_components_create.py"
Task: "Contract test GET /api/v1/storage-locations in backend/tests/contract/test_storage_list.py"
Task: "Contract test GET /api/v1/kicad/components in backend/tests/contract/test_kicad_search.py"
```

### Data Models Parallel Execution (after tests failing)
```
Task: "Component model with JSON specifications field in backend/src/models/component.py"
Task: "StorageLocation model with hierarchy support in backend/src/models/storage_location.py"
Task: "Category model with tree structure in backend/src/models/category.py"
Task: "Project model and ProjectComponent junction in backend/src/models/project.py"
```

### Frontend Components Parallel Execution
```
Task: "ComponentList component with search and filtering in frontend/src/components/ComponentList.vue"
Task: "StorageLocationTree component with hierarchy display in frontend/src/components/StorageLocationTree.vue"
Task: "Dashboard component with statistics cards in frontend/src/components/Dashboard.vue"
```

## Notes
- [P] tasks can run simultaneously as they work on different files
- Contract tests MUST fail before proceeding to implementation
- SQLite database allows single-file deployment and backup
- JSON fields in Component model support flexible specifications per component type
- Frontend uses Quasar Framework for professional UI components
- All external integrations (LCSC, KiCad) use plugin architecture for extensibility

## Validation Checklist

**Before marking complete, verify:**
- [ ] All contract tests exist and are failing
- [ ] All data models created with proper relationships
- [ ] All API endpoints implemented per OpenAPI specs
- [ ] Frontend can perform full component lifecycle (CRUD)
- [ ] Authentication system works with tiered access
- [ ] Component search performs well with 1000+ components
- [ ] Docker deployment creates self-contained application

This task list implements the complete PartsHub MVP with 106 specific, executable tasks following TDD principles and constitutional requirements.

---

## 📊 IMPLEMENTATION STATUS SUMMARY (Updated 2025-09-26)

### **Overall Progress: ~65% Complete**

#### ✅ **COMPLETED FEATURES**
- **Core Data Models**: Component, StorageLocation, Category, Tag, StockTransaction, Attachment, CustomField, Substitute
- **Contract Tests**: All 18 API contract tests implemented (T008-T025)
- **Frontend UI**: Complete Vue.js + Quasar components for component and storage management
- **Tag Management**: Full implementation with live search and dynamic tag creation ✨
- **Search Enhancement**: Main search includes tag filtering ✨
- **Database Setup**: SQLite with seeding and realistic electronic component data
- **Basic APIs**: Components, Storage, Tags CRUD operations working
- **Docker Setup**: Multi-container deployment ready

#### ⚠️ **CRITICAL MISSING FEATURES (High Priority)**

1. **🔐 Authentication System (T043-T045)** - **CRITICAL BLOCKER**
   - No JWT authentication implemented
   - No API token management
   - No admin user system
   - Required by spec: FR-029, FR-030, FR-031

2. **💰 Purchase Tracking (T031-T032)** - **HIGH PRIORITY**
   - No Supplier or Purchase models
   - No cost tracking or purchase history
   - Required by spec: FR-008, FR-018

3. **🔌 Provider Integration (T036-T037)** - **HIGH PRIORITY**
   - LCSC provider framework exists but not functional
   - No automatic component data fetching
   - Required by spec: FR-034, FR-035, FR-036

4. **📊 Project & Services (T048-T050)** - **MEDIUM PRIORITY**
   - No ProjectService for component allocation
   - No StockService for advanced inventory operations
   - No ReportService for dashboard statistics

5. **🛠️ Advanced Features (T038-T039)** - **LOWER PRIORITY**
   - No KiCad integration (symbol/footprint export)
   - No MetaPart/BOM management
   - No full-text search optimization

#### 🔗 **FILE ATTACHMENT SYSTEM (T064-T072)** - **HIGH PRIORITY**
   - **T064**: Create FileStorageService with hashed directory structure (FR-058)
   - **T065**: Write comprehensive tests for FileStorageService using TDD
   - **T066**: Implement thumbnail generation service for images (FR-061)
   - **T067**: Create nested API endpoints for component attachments (FR-060)
   - **T068**: Add file upload validation and security checks (FR-059)
   - **T069**: Implement provider auto-download functionality (FR-066)
   - **T070**: Create drag-and-drop frontend upload component (FR-022)
   - **T071**: Add primary image selection and gallery UI (FR-062, FR-064)
   - **T072**: Configure Docker volumes for persistent file storage (FR-065)

#### 🎯 **IMMEDIATE NEXT STEPS**
1. ✅ **Authentication System Complete (T043-T045, T057-T063)** - Production ready with enhanced UX
2. **🔗 File Attachment System (T064-T072)** - Core datasheet/image functionality
3. **Add Purchase Tracking (T031-T032)** - Core inventory functionality
4. **Complete Provider Integration (T036-T037)** - Automated component data
5. **Enhance Dashboard Services (T048-T050)** - Better user experience

#### 💪 **CURRENT STRENGTHS**
- Solid Vue.js + FastAPI architecture
- Comprehensive contract test coverage
- Modern tech stack with proper relationships
- Docker-ready deployment
- Excellent tag management system
- Working core component and storage functionality