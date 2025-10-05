# Tasks: Simplified Component Creation Wizard

**Input**: Design documents from `/specs/007-simplify-component-creation/`
**Prerequisites**: plan.md, spec.md (requirements and entities defined)

## Execution Flow (main)
```
1. Load plan.md and spec.md from feature directory
   → ✅ Loaded successfully
   → Extracted: Python 3.11+ (backend), Vue.js 3 + TypeScript (frontend)
   → Structure: Web application (backend/ and frontend/)
2. Load optional design documents:
   → spec.md Key Entities: Provider, ProviderLink, Resource, Manufacturer, Footprint, Component
   → Functional Requirements: 23 requirements (FR-001 to FR-023)
3. Generate tasks by category:
   → Setup: Database migrations, dependencies
   → Tests: Contract tests, integration tests (TDD)
   → Backend: Models, services (provider adapters, fuzzy search), API endpoints
   → Frontend: Wizard components, Pinia store, API clients
   → Polish: Documentation, linting, coverage
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
   → Backend API before frontend
5. Number tasks sequentially (T001, T002...)
6. ✅ Specialized agents assigned where appropriate
7. Validate task completeness
8. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] [AGENT?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[AGENT]**: Specialized agent recommended (api, vue, db, test, review)
- Include exact file paths in descriptions

## Path Conventions
- Backend: `backend/src/` (models, services, api)
- Frontend: `frontend/src/` (components, pages, services, stores)
- Tests: `backend/tests/` (contract, integration, unit)

## Phase 3.1: Setup & Database

- [x] **T001** [db] Create database migration for Provider model
  - File: `backend/migrations/versions/20251005_1200_add_providers.py`
  - Add Provider table with fields: id, name, adapter_class, base_url, api_key_required, status, created_at
  - Add indexes on name (unique), status
  - **Agent: db** (database schema design specialist) ✅

- [x] **T002** [db] Create database migration for ProviderLink model
  - File: `backend/migrations/versions/20251005_1201_add_provider_links.py`
  - Add ProviderLink table with fields: id, component_id (FK), provider_id (FK), provider_part_number, provider_url, sync_status, last_synced_at, metadata (JSON), created_at
  - Add unique constraint (component_id, provider_id), indexes on provider_part_number
  - **Agent: db** (handles relationships and constraints) ✅

- [x] **T003** [db] Create database migration for Resource model
  - File: `backend/migrations/versions/20251005_1202_add_resources.py`
  - Add Resource table with fields: id, provider_link_id (FK), resource_type (enum), file_name, file_path, source_url, download_status (enum), file_size_bytes, downloaded_at, created_at
  - Add indexes on (provider_link_id, resource_type), download_status
  - **Agent: db** (enum types and file storage patterns) ✅

- [x] **T004** [db] Add indexes to Manufacturer and Footprint tables for fuzzy search
  - File: `backend/migrations/versions/20251005_1203_add_fuzzy_search_indexes.py`
  - Add case-insensitive index on manufacturers.name
  - Add case-insensitive index on footprints.name
  - **Agent: db** (index optimization for search performance) ✅

- [x] **T005** [P] Install rapidfuzz dependency for fuzzy matching
  - Add `rapidfuzz >= 3.5.0` to pyproject.toml
  - Run `uv sync` to install ✅

- [x] **T006** [P] Install httpx dependency for LCSC API calls
  - Add `httpx >= 0.25.0` to pyproject.toml (httpx already present from dev dependencies)
  - Run `uv sync` to install ✅

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

**Constitutional Requirements**:
- **Principle II (TDD - NON-NEGOTIABLE)**: Tests MUST be written before implementation
- **Principle VI (Test Isolation - NON-NEGOTIABLE)**: In-memory SQLite, no execution order dependencies

### Backend Contract Tests

- [x] **T007** [P] [test] Contract test GET /api/providers ✅
  - File: `backend/tests/contract/test_providers_contract.py`
  - Test: List all active providers (admin auth required)
  - Assert: 200 response with Provider schema array
  - *Agent: test** ✅ (TDD specialist, contract testing patterns)

- [ ] **T008** [P] [test] Contract test GET /api/providers/{provider_id}/search
  - File: `backend/tests/contract/test_provider_search_contract.py`
  - Test: Search LCSC provider with query param (admin auth)
  - Assert: 200 response with ProviderPart schema array, pagination
  - *Agent: test** ✅ (validates request/response schemas)

- [ ] **T009** [P] [test] Contract test GET /api/wizard/manufacturers/search
  - File: `backend/tests/contract/test_wizard_manufacturers_contract.py`
  - Test: Fuzzy search manufacturers with ranking (admin auth)
  - Assert: 200 response with ManufacturerSuggestion schema (id, name, score)
  - *Agent: test** ✅ (fuzzy search contract validation)

- [ ] **T010** [P] [test] Contract test GET /api/wizard/footprints/search
  - File: `backend/tests/contract/test_wizard_footprints_contract.py`
  - Test: Fuzzy search footprints with ranking (admin auth)
  - Assert: 200 response with FootprintSuggestion schema
  - *Agent: test** ✅ (parallel to T009)

- [ ] **T011** [P] [test] Contract test POST /api/wizard/components
  - File: `backend/tests/contract/test_wizard_components_contract.py`
  - Test: Create component with provider link and resource selections (admin auth)
  - Assert: 201 response with Component schema including provider_link and resources
  - *Agent: test** ✅ (complex request/response validation)

- [ ] **T012** [P] [test] Contract test GET /api/resources/{resource_id}/status
  - File: `backend/tests/contract/test_resources_status_contract.py`
  - Test: Get resource download status (admin auth)
  - Assert: 200 response with ResourceStatus schema (download_status, progress_percent)
  - *Agent: test** ✅ (async resource tracking)

- [ ] **T013** [P] [test] Contract test POST /api/provider-links/{link_id}/resources
  - File: `backend/tests/contract/test_resources_add_contract.py`
  - Test: Add resource to provider link (manual/deferred download, admin auth)
  - Assert: 201 response with Resource schema
  - *Agent: test** ✅ (deferred resource management)

### Backend Integration Tests

- [ ] **T014** [P] [test] Integration test: Complete wizard flow for linked part
  - File: `backend/tests/integration/test_wizard_linked_part_flow.py`
  - Scenario: Admin selects LCSC → searches "STM32F103" → selects part → downloads datasheet (sync) + images (async) → creates component
  - Validates: FR-001, FR-002, FR-003, FR-004, FR-005, FR-020
  - *Agent: test** ✅ (end-to-end workflow validation)

- [ ] **T015** [P] [test] Integration test: Local part creation with fuzzy manufacturer search
  - File: `backend/tests/integration/test_wizard_local_part_flow.py`
  - Scenario: Admin creates local part → types "TI" in manufacturer → sees "Texas Instruments" suggestion → creates new manufacturer "Custom Mfg" → creates component
  - Validates: FR-008, FR-010, FR-021, FR-022
  - *Agent: test** ✅ (fuzzy search and entity creation)

- [ ] **T016** [P] [test] Integration test: LCSC API failure fallback to local creation
  - File: `backend/tests/integration/test_lcsc_api_failure.py`
  - Scenario: LCSC API returns 500 → system shows error → allows switch to local part creation
  - Validates: FR-017
  - Mock LCSC API to simulate failure
  - *Agent: test** ✅ (error handling and fallback flows)

- [ ] **T017** [P] [test] Integration test: Provider auto-selection when only one exists
  - File: `backend/tests/integration/test_provider_auto_selection.py`
  - Scenario: Only LCSC provider configured → wizard auto-selects it
  - Validates: FR-023
  - *Agent: test** ✅ (conditional UX logic)

- [ ] **T018** [P] [test] Integration test: Admin-only access enforcement
  - File: `backend/tests/integration/test_wizard_auth.py`
  - Scenario: Non-admin user attempts wizard → 403 Forbidden
  - Validates: FR-018
  - *Agent: test** ✅ (authentication and authorization)

## Phase 3.3: Backend Models (ONLY after tests are failing)

- [ ] **T019** [P] [api] Create Provider model
  - File: `backend/src/models/provider.py`
  - SQLAlchemy model with fields from migration T001
  - Relationships: provider_links (one-to-many)
  - **Agent: api** (SQLAlchemy expertise, model patterns)

- [ ] **T020** [P] [api] Create ProviderLink model
  - File: `backend/src/models/provider_link.py`
  - SQLAlchemy model with fields from migration T002
  - Relationships: component (many-to-one), provider (many-to-one), resources (one-to-many)
  - Unique constraint (component_id, provider_id)
  - **Agent: api** (complex relationships)

- [ ] **T021** [P] [api] Create Resource model
  - File: `backend/src/models/resource.py`
  - SQLAlchemy model with fields from migration T003
  - Enums: ResourceType, DownloadStatus
  - Relationship: provider_link (many-to-one)
  - **Agent: api** (enum handling, file storage patterns)

- [ ] **T022** [api] Update Component model to add provider_links relationship
  - File: `backend/src/models/component.py`
  - Add relationship: provider_links = relationship("ProviderLink", back_populates="component")
  - **Agent: api** (updates existing model)

## Phase 3.4: Backend Services

- [ ] **T023** [api] Create ProviderAdapter abstract base class
  - File: `backend/src/services/provider_adapter.py`
  - Abstract methods: search(query, limit), get_part_details(part_number), get_resources(part_number)
  - Return types: ProviderPart, PartDetails, List[ResourceInfo]
  - **Agent: api** (abstract class design, adapter pattern)

- [ ] **T024** [api] Implement LCSCAdapter for LCSC API integration
  - File: `backend/src/services/lcsc_adapter.py`
  - Implements ProviderAdapter
  - Uses httpx for API calls to LCSC endpoints
  - Handles rate limiting (10 req/sec), pagination, error responses
  - Mocks for testing
  - **Agent: api** (external API integration, error handling)

- [ ] **T025** [api] Create ProviderService for provider management
  - File: `backend/src/services/provider_service.py`
  - Methods: list_providers(), get_provider(id), search_provider(provider_id, query, limit)
  - Dynamically instantiates adapter based on Provider.adapter_class
  - **Agent: api** (service layer, dynamic adapter loading)

- [ ] **T026** [api] Create FuzzySearchService for manufacturer/footprint matching
  - File: `backend/src/services/fuzzy_search_service.py`
  - Method: search_manufacturers(query, limit) → ranked suggestions with scores
  - Method: search_footprints(query, limit) → ranked suggestions
  - Uses rapidfuzz.fuzz.ratio for scoring, SQLAlchemy ilike for prefix match
  - Ranking: exact match (100) > prefix match (90) > fuzzy score (0-100)
  - **Agent: api** (fuzzy matching algorithms, ranking logic)

- [ ] **T027** [api] Create WizardService for component creation orchestration
  - File: `backend/src/services/wizard_service.py`
  - Method: create_component(data) → validates, creates component, provider_link, resources
  - Handles sync resource downloads (PDFs), queues async downloads (images, footprints)
  - Validates manufacturer/footprint names (FR-022: max 255 chars, alphanumeric + hyphens/spaces/periods/underscores, unique case-insensitive)
  - Creates new manufacturers/footprints if needed
  - **Agent: api** (complex business logic, transaction management)

- [ ] **T028** [api] Create ResourceService for resource download management
  - File: `backend/src/services/resource_service.py`
  - Method: download_resource_sync(resource_id) → downloads PDF synchronously
  - Method: download_resource_async(resource_id) → queues background download using FastAPI BackgroundTasks
  - Method: get_resource_status(resource_id) → returns download progress
  - Updates Resource.download_status, file_path, downloaded_at
  - **Agent: api** (async tasks, file I/O, progress tracking)

## Phase 3.5: Backend API Endpoints

- [ ] **T029** [api] Implement GET /api/providers endpoint
  - File: `backend/src/api/providers.py`
  - Uses ProviderService.list_providers()
  - Admin-only (JWT auth check)
  - Returns Provider schema array
  - **Agent: api** (FastAPI endpoint, auth middleware)

- [ ] **T030** [api] Implement GET /api/providers/{provider_id}/search endpoint
  - File: `backend/src/api/providers.py`
  - Uses ProviderService.search_provider(provider_id, query, limit)
  - Admin-only
  - Query validation: min 2 chars, limit max 100
  - Returns ProviderPart schema array with total count
  - **Agent: api** (search endpoint, pagination)

- [ ] **T031** [api] Implement GET /api/wizard/manufacturers/search endpoint
  - File: `backend/src/api/wizard.py`
  - Uses FuzzySearchService.search_manufacturers(query, limit)
  - Admin-only
  - Returns ManufacturerSuggestion schema array (ranked by score)
  - **Agent: api** (fuzzy search endpoint)

- [ ] **T032** [api] Implement GET /api/wizard/footprints/search endpoint
  - File: `backend/src/api/wizard.py`
  - Uses FuzzySearchService.search_footprints(query, limit)
  - Admin-only
  - Returns FootprintSuggestion schema array
  - **Agent: api** (parallel to T031)

- [ ] **T033** [api] Implement POST /api/wizard/components endpoint
  - File: `backend/src/api/wizard.py`
  - Uses WizardService.create_component(data)
  - Admin-only
  - Validates CreateComponentRequest schema
  - Downloads critical resources (datasheets) synchronously, others async
  - Returns 201 with Component schema including provider_link and resources
  - **Agent: api** (complex creation endpoint, hybrid sync/async)

- [ ] **T034** [api] Implement GET /api/resources/{resource_id}/status endpoint
  - File: `backend/src/api/resources.py`
  - Uses ResourceService.get_resource_status(resource_id)
  - Admin-only
  - Returns ResourceStatus schema
  - **Agent: api** (status polling endpoint)

- [ ] **T035** [api] Implement POST /api/provider-links/{link_id}/resources endpoint
  - File: `backend/src/api/resources.py`
  - Uses ResourceService to add resource to provider link
  - Admin-only
  - Starts download (async for non-critical types)
  - Returns 201 with Resource schema
  - **Agent: api** (deferred resource addition)

## Phase 3.6: Frontend Components & State

- [ ] **T036** [vue] Create Pinia wizard store
  - File: `frontend/src/stores/wizardStore.ts`
  - State: currentStep, partType, selectedProvider, searchResults, selectedPart, selectedResources, postAction
  - Actions: setStep, selectPartType, selectProvider, searchProvider, selectPart, toggleResource, createComponent, reset
  - Persist to localStorage for refresh recovery
  - **Agent: vue** (Pinia store patterns, Vue reactivity)

- [ ] **T037** [vue] Create wizard API client service
  - File: `frontend/src/services/wizardService.ts`
  - Methods: listProviders(), searchProvider(providerId, query), searchManufacturers(query), searchFootprints(query), createComponent(data)
  - Uses axios/fetch with JWT auth headers
  - **Agent: vue** (API client patterns, TypeScript)

- [ ] **T038** [vue] Create resource API client service
  - File: `frontend/src/services/resourceService.ts`
  - Methods: getResourceStatus(resourceId), addResource(linkId, resourceData)
  - Polling for async download status
  - **Agent: vue** (async status polling patterns)

- [ ] **T039** [vue] Create FuzzyAutocomplete reusable component
  - File: `frontend/src/components/FuzzyAutocomplete.vue`
  - Props: searchFunction, placeholder, modelValue
  - Emits: update:modelValue, createNew
  - Uses Quasar QSelect with filter and options-dense
  - Shows ranked results with scores, "Create new" option at bottom
  - **Agent: vue** (reusable component design, Quasar components)

- [ ] **T040** [vue] Create WizardContainer component
  - File: `frontend/src/components/wizard/WizardContainer.vue`
  - Manages wizard step flow (1-5)
  - Uses wizardStore for state
  - Shows step progress indicator (Quasar QStepper)
  - **Agent: vue** (container component, step navigation)

- [ ] **T041** [vue] Create PartTypeSelector component (Step 1)
  - File: `frontend/src/components/wizard/PartTypeSelector.vue`
  - Radio buttons: Linked part, Local part, Meta-part
  - Updates wizardStore.partType
  - **Agent: vue** (form component, validation)

- [ ] **T042** [vue] Create ProviderSelector component (Step 2)
  - File: `frontend/src/components/wizard/ProviderSelector.vue`
  - Fetches providers from wizardService.listProviders()
  - Auto-selects if only one provider (FR-023)
  - Shows provider dropdown if multiple
  - Updates wizardStore.selectedProvider
  - **Agent: vue** (conditional rendering, auto-selection logic)

- [ ] **T043** [vue] Create ProviderSearch component (Step 3 - Linked parts)
  - File: `frontend/src/components/wizard/ProviderSearch.vue`
  - Search input with debounce (300ms)
  - Calls wizardService.searchProvider(providerId, query)
  - Displays results in table: part number, name, manufacturer, datasheet link
  - Selects part → updates wizardStore.selectedPart
  - Shows "No results" with fallback to local creation (FR-017)
  - **Agent: vue** (search UI, debounce, error handling)

- [ ] **T044** [vue] Create LocalPartForm component (Step 3 - Local parts)
  - File: `frontend/src/components/wizard/LocalPartForm.vue`
  - Fields: name, description, manufacturer (FuzzyAutocomplete), footprint (FuzzyAutocomplete)
  - Manufacturer autocomplete uses wizardService.searchManufacturers()
  - Footprint autocomplete uses wizardService.searchFootprints()
  - Shows "Create new" option when no match (FR-010, FR-011)
  - Validates name length (255 chars), allowed chars (FR-022)
  - **Agent: vue** (form validation, fuzzy autocomplete integration)

- [ ] **T045** [vue] Create ResourceSelector component (Step 4)
  - File: `frontend/src/components/wizard/ResourceSelector.vue`
  - Displays available resources from selectedPart metadata
  - Checkboxes: Datasheet (checked, disabled - required), Images, Footprints, Symbols, 3D Models
  - Updates wizardStore.selectedResources
  - Shows note: "Datasheets download immediately, others in background"
  - **Agent: vue** (checkbox selection, resource categorization)

- [ ] **T046** [vue] Create PostCreationActions component (Step 5)
  - File: `frontend/src/components/wizard/PostCreationActions.vue`
  - Radio buttons: "Go to created part", "Add stock for created part", "Stay and continue creating new parts"
  - Updates wizardStore.postAction
  - On submit → calls wizardService.createComponent()
  - Navigates based on selection (FR-012, FR-013)
  - Resets wizard if "Stay and continue" (FR-014)
  - **Agent: vue** (post-action navigation, wizard reset)

- [ ] **T047** [vue] Create CreateComponentPage wrapper
  - File: `frontend/src/pages/CreateComponentPage.vue`
  - Wraps WizardContainer
  - Checks admin auth (redirects if not admin, FR-018)
  - Shows page title, breadcrumbs
  - **Agent: vue** (page component, auth guards)

- [ ] **T048** [vue] Add route for /components/create
  - File: `frontend/src/router/index.ts`
  - Route: /components/create → CreateComponentPage
  - Meta: requiresAuth: true, requiresAdmin: true
  - **Agent: vue** (Vue Router configuration)

## Phase 3.7: Frontend Tests

- [ ] **T049** [P] [vue] Test WizardContainer component
  - File: `frontend/tests/components/wizard/WizardContainer.spec.ts`
  - Test: Step navigation, state persistence
  - Uses Vitest + Vue Test Utils
  - **Agent: vue** (component testing patterns)

- [ ] **T050** [P] [vue] Test ProviderSearch component
  - File: `frontend/tests/components/wizard/ProviderSearch.spec.ts`
  - Test: Search debounce, result selection, no results fallback
  - Mock wizardService
  - **Agent: vue** (async component testing)

- [ ] **T051** [P] [vue] Test FuzzyAutocomplete component
  - File: `frontend/tests/components/FuzzyAutocomplete.spec.ts`
  - Test: Fuzzy search, ranking display, create new option
  - **Agent: vue** (reusable component testing)

## Phase 3.8: Polish & Documentation

**Constitutional Requirements**:
- Quality Gates (Principle IV): Ruff formatting, zero linting errors
- Anonymous Contribution (Principle V): No AI attribution in commits
- Documentation Review (Principle VII): All docs updated with code changes

- [ ] **T052** [P] Update OpenAPI documentation
  - File: `backend/src/api/openapi.yaml` (or auto-generated from FastAPI)
  - Add all new endpoints: /api/providers/*, /api/wizard/*, /api/resources/*
  - Include request/response schemas, auth requirements
  - **Agent: api** (OpenAPI/Swagger expertise)

- [ ] **T053** [P] Create wizard user guide
  - File: `docs/user-guide/component-wizard.md`
  - Screenshots/steps: Select part type → Choose provider → Search/Create → Download resources → Post-creation actions
  - Admin-only note, LCSC setup instructions
  - **Agent: docs** (user documentation specialist)

- [ ] **T054** [P] Update README with wizard feature
  - File: `README.md`
  - Add "Simplified Component Creation Wizard" section
  - Link to user guide, mention LCSC provider
  - **Agent: docs**

- [ ] **T055** [P] Create LCSC API setup guide
  - File: `docs/setup/lcsc-api-setup.md`
  - How to obtain LCSC API key
  - Environment variable configuration
  - Seed LCSC provider in database
  - **Agent: docs**

- [ ] **T056** [P] [test] Unit tests for fuzzy search ranking
  - File: `backend/tests/unit/test_fuzzy_search_ranking.py`
  - Test: Exact match > prefix match > fuzzy score
  - Test: "TI" suggests "Texas Instruments" at top
  - *Agent: test** ✅ (algorithm validation)

- [ ] **T057** [P] [test] Unit tests for resource download service
  - File: `backend/tests/unit/test_resource_service.py`
  - Test: Sync download (PDFs), async download (images), status tracking
  - Mock httpx for file downloads
  - *Agent: test** ✅ (async behavior testing)

- [ ] **T058** Run ruff linting and formatting on backend
  - Commands: `uv run ruff check backend/` and `uv run ruff format backend/`
  - Fix all linting errors
  - **Agent: api** (code quality enforcement)

- [ ] **T059** Verify 80% test coverage minimum
  - Command: `cd backend && uv run pytest --cov=src --cov-report=term-missing`
  - Add tests to reach coverage target if needed
  - *Agent: test** ✅ (coverage analysis)

- [ ] **T060** [review] Code review for adapter pattern and extensibility
  - Review: ProviderAdapter abstraction, LCSC implementation
  - Ensure new providers can be added without modifying existing code (FR-019)
  - **Agent: review** (architectural review, SOLID principles)

- [ ] **T061** [review] Security review for admin-only access
  - Review: JWT validation on all wizard endpoints
  - Test: Non-admin access blocked (FR-018)
  - **Agent: security** (authentication/authorization review)

- [ ] **T062** Manual validation of complete wizard workflow
  - Follow quickstart.md scenario
  - Test: LCSC search → part selection → resource download → component creation → post-action
  - Verify: Datasheet downloads immediately, images download in background
  - Test: Fuzzy search for manufacturers/footprints
  - Verify: Provider auto-selection when only LCSC configured

## Dependencies

**Setup Phase (T001-T006)**:
- Database migrations (T001-T004) can run in parallel after each is created
- Dependency installs (T005-T006) can run in parallel

**Test Phase (T007-T018)**:
- All tests can run in parallel [P] - different files, no dependencies
- Tests MUST be written and failing before Phase 3.3

**Backend Models (T019-T022)**:
- T019, T020, T021 can run in parallel [P]
- T022 depends on T019, T020 (needs ProviderLink model)

**Backend Services (T023-T028)**:
- T023 (abstract adapter) blocks T024 (LCSC adapter)
- T025 (ProviderService) depends on T023, T024
- T026 (FuzzySearchService) independent [P]
- T027 (WizardService) depends on T025, T026
- T028 (ResourceService) independent [P]

**Backend API (T029-T035)**:
- T029-T030 depend on T025 (ProviderService)
- T031-T032 depend on T026 (FuzzySearchService)
- T033 depends on T027 (WizardService)
- T034-T035 depend on T028 (ResourceService)

**Frontend State (T036-T038)**:
- T036 (Pinia store) independent [P]
- T037, T038 (API clients) can run in parallel [P]

**Frontend Components (T039-T048)**:
- T039 (FuzzyAutocomplete) blocks T044 (LocalPartForm)
- T040 (WizardContainer) blocks T041-T046
- T041, T042 can run in parallel after T040
- T043, T044 can run in parallel after T042
- T045 depends on T043, T044
- T046 depends on T045
- T047 depends on T046
- T048 (routing) independent, can run after T047

**Frontend Tests (T049-T051)**:
- All can run in parallel [P] after corresponding components

**Polish (T052-T062)**:
- T052-T055 (docs) can run in parallel [P]
- T056-T057 (unit tests) can run in parallel [P]
- T058-T059 (linting/coverage) sequential
- T060-T061 (reviews) can run in parallel [P]
- T062 (manual validation) runs last

## Parallel Execution Examples

### Specialized Agent Delegation (Recommended Approach)

```bash
# Phase 3.2: Launch all contract tests in parallel with test agent
Task: agent=test "Write contract test for GET /api/providers in backend/tests/contract/test_providers_contract.py"
Task: agent=test "Write contract test for GET /api/providers/{provider_id}/search in backend/tests/contract/test_provider_search_contract.py"
Task: agent=test "Write contract test for GET /api/wizard/manufacturers/search in backend/tests/contract/test_wizard_manufacturers_contract.py"
Task: agent=test "Write contract test for GET /api/wizard/footprints/search in backend/tests/contract/test_wizard_footprints_contract.py"
# ... all T007-T018 tests in parallel

# Phase 3.3: Launch backend models in parallel with api agent
Task: agent=api "Create Provider model in backend/src/models/provider.py"
Task: agent=api "Create ProviderLink model in backend/src/models/provider_link.py"
Task: agent=api "Create Resource model in backend/src/models/resource.py"

# Phase 3.6: Launch frontend components in parallel with vue agent
Task: agent=vue "Create PartTypeSelector component in frontend/src/components/wizard/PartTypeSelector.vue"
Task: agent=vue "Create ProviderSelector component in frontend/src/components/wizard/ProviderSelector.vue"
# ... after dependencies resolved
```

### Database Migration Sequence (db agent)

```bash
# Phase 3.1: Sequential database migrations
Task: agent=db "Create Provider table migration in backend/alembic/versions/20251005_1200_add_providers.py"
# Wait for T001 to complete, then:
Task: agent=db "Create ProviderLink table migration in backend/alembic/versions/20251005_1201_add_provider_links.py"
# Continue sequentially through T002-T004
```

### Review & Quality Gates

```bash
# Phase 3.8: Parallel reviews with specialized agents
Task: agent=review "Review adapter pattern implementation for extensibility (ProviderAdapter, LCSCAdapter)"
Task: agent=security "Review admin-only access controls on wizard endpoints"
Task: agent=api "Run ruff linting and formatting on backend/"
Task: agent=test "Verify 80% test coverage with pytest --cov"
```

## Notes

- **[P] tasks** = different files, no dependencies → can run in parallel
- **Specialized agents** assigned for domain expertise (api, vue, db, test, review, security)
- **Verify tests fail** before implementing (TDD)
- **Commit after each task** (or logical group) with conventional commit format
- **No AI attribution** in commits (Principle V)
- **Admin-only access** enforced on all wizard endpoints (FR-018)
- **Multi-provider architecture** via adapter pattern (FR-019)
- **Hybrid resource downloads**: Sync PDFs, async images/footprints (FR-020)
- **Fuzzy search** with ranking for manufacturers/footprints (FR-021)

## Validation Checklist

### Task Completeness
- [x] All entities have model tasks (Provider, ProviderLink, Resource)
- [x] All contract tests written before implementation (T007-T018 before T019+)
- [x] All functional requirements covered (FR-001 to FR-023)
- [x] Parallel tasks truly independent (different files, marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

### Constitutional Compliance (PartsHub v1.2.0)
- [x] API-First Design: Backend tasks (T007-T035) before frontend tasks (T036-T048)
- [x] TDD: Tests in Phase 3.2 (T007-T018), implementation in Phase 3.3+ (T019-T048)
- [x] Tiered Access: Admin-only enforcement (T018, T029-T035, T047)
- [x] Quality Gates: Ruff linting (T058), coverage check (T059)
- [x] Anonymous Contribution: Commit strategy follows standard format
- [x] Test Isolation: All tests use in-memory SQLite, mocked LCSC API, no execution order dependencies
- [x] Documentation Review: OpenAPI (T052), user guide (T053), README (T054), setup guide (T055)

### Specialized Agent Assignment
- [x] **db agent**: Database migrations and schema design (T001-T004)
- [x] **test agent**: All test tasks (T007-T018, T049-T051, T056-T057, T059)
- [x] **api agent**: Backend models, services, API endpoints (T019-T035, T052, T058)
- [x] **vue agent**: Frontend components, stores, routing (T036-T051)
- [x] **review agent**: Architectural review (T060)
- [x] **security agent**: Security review (T061)

---
*Total Tasks: 62 | Parallel Tasks: 35 | Estimated Completion: 5-7 days with agent delegation*
