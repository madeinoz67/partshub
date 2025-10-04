# Tasks: Stock Management Operations

**Input**: Design documents from `/specs/006-add-remove-stock/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/
**Feature Branch**: `006-add-remove-stock`

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✓ Tech stack: Python 3.11+, FastAPI, SQLAlchemy, Vue 3, Quasar, Pinia
   → ✓ Structure: Web application (backend/ + frontend/)
2. Load optional design documents:
   → ✓ data-model.md: StockTransaction + ComponentLocation entities
   → ✓ contracts/: 5 OpenAPI specs (add, remove, move stock + history pagination + export)
   → ✓ research.md: 6 technical decisions (locking, inline forms, etc.)
3. Generate tasks by category:
   → Setup: Database migration, Pydantic schemas
   → Tests: 5 contract tests (add/remove/move/history/export), 3 integration test suites, unit tests
   → Core: Backend services (stock ops + history), 5 API endpoints
   → Frontend: 4 components (3 forms + history table), API client, integration
   → Security: Admin-only access, SQL injection, locking vulnerabilities
   → Polish: Component tests (4 components), documentation, manual validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
   → Security review before frontend implementation
5. Number tasks sequentially (T001-T037 + T018A-T018F, T024A-T024C, T027A = 47 tasks total)
6. Specialized agents: test, api, vue, db, security, docs, review
7. Validate task completeness:
   → ✓ All contracts have tests (5 contracts: add/remove/move/history/export)
   → ✓ All entities have migrations
   → ✓ Security review included
   → ✓ Recent clarifications integrated (pagination, export, weighted avg)
8. Return: SUCCESS (47 tasks ready for execution, 10 new tasks for Session 2025-10-05 clarifications)
```

## Format: `[ID] [P?] [Agent] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Agent]**: Specialized agent to use (test, api, vue, db, security, docs, review)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Migrations**: `backend/alembic/versions/`
- **Docs**: `docs/`

---

## Phase 3.1: Setup & Database Migration

- [x] **T001** [db] Create Alembic migration for StockTransaction model extensions
  - **Agent**: `db` (database schema expert)
  - **File**: `backend/alembic/versions/YYYYMMDD_HHMM_add_stock_transaction_pricing.py`
  - **Task**: Create database migration adding `lot_id` (String 100), `price_per_unit` (Numeric 10,4), `total_price` (Numeric 10,4) to `stock_transactions` table
  - **Validation**: Migration runs cleanly up and down; no data loss
  - **Dependencies**: None (prerequisite for all other tasks)

- [x] **T002** [P] [api] Create Pydantic schemas for stock operations
  - **Agent**: `api` (FastAPI/Pydantic expert)
  - **File**: `backend/src/schemas/stock_operations.py`
  - **Task**: Define request/response schemas: `AddStockRequest`, `AddStockResponse`, `RemoveStockRequest`, `RemoveStockResponse`, `MoveStockRequest`, `MoveStockResponse`, `StockHistoryEntry`
  - **Reference**: OpenAPI specs in `contracts/` directory
  - **Validation**: Schemas match OpenAPI contracts exactly; include admin-only security annotations
  - **Dependencies**: None (independent schema definition)

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

**Constitutional Requirements**:
- **Principle II (TDD - NON-NEGOTIABLE)**:
  - Tests MUST be written before implementation
  - Red-Green-Refactor cycle strictly enforced
  - User approval required after tests written
  - Minimum 80% coverage target

- **Principle VI (Test Isolation - NON-NEGOTIABLE)**:
  - Each test uses isolated database (in-memory SQLite via conftest.py)
  - Tests runnable in any order (no execution dependencies)
  - External services mocked
  - Database state reset after each test
  - Tests must be parallelizable

### Contract Tests (API Endpoint Validation)

- [x] **T003** [P] [test] Contract test for POST /api/v1/components/{id}/stock/add
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/contract/test_add_stock.py`
  - **Task**: Write pytest contract tests from `contracts/add-stock.yaml` - test request/response schemas, status codes (200/400/403/404/409), admin JWT requirement, examples (manual entry, order receiving, no pricing)
  - **Reference**: `contracts/add-stock.yaml` OpenAPI spec
  - **Validation**: Test fails (endpoint not implemented yet); covers all response codes and examples
  - **Dependencies**: T001 (migration)

- [x] **T004** [P] [test] Contract test for POST /api/v1/components/{id}/stock/remove
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/contract/test_remove_stock.py`
  - **Task**: Write pytest contract tests from `contracts/remove-stock.yaml` - test auto-capping behavior, location deletion flag, admin-only access
  - **Reference**: `contracts/remove-stock.yaml` OpenAPI spec
  - **Validation**: Test fails (endpoint not implemented); validates auto-cap and location cleanup
  - **Dependencies**: T001 (migration)

- [x] **T005** [P] [test] Contract test for POST /api/v1/components/{id}/stock/move
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/contract/test_move_stock.py`
  - **Task**: Write pytest contract tests from `contracts/move-stock.yaml` - test atomicity, pricing inheritance, source/destination updates, same-location validation
  - **Reference**: `contracts/move-stock.yaml` OpenAPI spec
  - **Validation**: Test fails (endpoint not implemented); covers atomic operation requirements
  - **Dependencies**: T001 (migration)

### Integration Tests (User Story Validation)

- [x] **T006** [P] [test] Integration tests for Add Stock user stories
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/integration/test_add_stock_scenarios.py`
  - **Task**: Write pytest integration tests for 6 Add Stock acceptance scenarios from spec.md (inline form display, manual entry, pricing calculation, order receiving, quantity update, multi-row operations)
  - **Reference**: spec.md lines 58-63 (Add Stock acceptance scenarios)
  - **Validation**: Tests fail (no implementation); each scenario covered; use in-memory SQLite
  - **Dependencies**: T001 (migration)

- [x] **T007** [P] [test] Integration tests for Remove Stock user stories
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/integration/test_remove_stock_scenarios.py`
  - **Task**: Write pytest integration tests for 5 Remove Stock acceptance scenarios from spec.md (inline form, quantity validation, stock reduction, zero-quantity cleanup, multi-row operations)
  - **Reference**: spec.md lines 66-70 (Remove Stock acceptance scenarios)
  - **Validation**: Tests fail (no implementation); auto-capping tested; location deletion verified
  - **Dependencies**: T001 (migration)

- [x] **T008** [P] [test] Integration tests for Move Stock user stories
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/integration/test_move_stock_scenarios.py`
  - **Task**: Write pytest integration tests for 7 Move Stock acceptance scenarios from spec.md (inline form, destination options, quantity validation, new location creation, atomic transfer, source cleanup, multi-row operations)
  - **Reference**: spec.md lines 73-79 (Move Stock acceptance scenarios)
  - **Validation**: Tests fail (no implementation); atomicity verified; pricing inheritance tested
  - **Dependencies**: T001 (migration)

### Unit Tests (Business Logic)

- [x] **T009** [P] [test] Unit tests for pessimistic locking behavior
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/unit/test_locking.py`
  - **Task**: Write pytest unit tests for pessimistic locking: acquire lock with `with_for_update(nowait=False)`, concurrent access blocking, lock release on commit/rollback, deadlock prevention with consistent ordering
  - **Reference**: research.md "SQLAlchemy Pessimistic Locking" section
  - **Validation**: Tests fail (locking not implemented); concurrent access scenarios covered
  - **Dependencies**: T001 (migration)

- [x] **T010** [P] [test] Unit tests for stock operations service business logic
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/unit/test_stock_operations_service.py`
  - **Task**: Write pytest unit tests for service methods: add_stock, remove_stock, move_stock - test auto-capping, quantity validation, pricing calculations, transaction creation, total quantity updates
  - **Reference**: data-model.md "State Transitions" sections
  - **Validation**: Tests fail (service not implemented); all business rules tested
  - **Dependencies**: T001 (migration)

---

## Phase 3.3: Backend Core Implementation (ONLY after tests are failing)

### Database Models

- [x] **T011** [P] [db] Extend StockTransaction model with pricing fields
  - **Agent**: `db` (SQLAlchemy/database expert)
  - **File**: `backend/src/models/stock_transaction.py`
  - **Task**: Add fields: `lot_id` (String 100 nullable), `price_per_unit` (Numeric 10,4 nullable), `total_price` (Numeric 10,4 nullable); update `__repr__` and validation
  - **Reference**: data-model.md lines 22-30 (StockTransaction schema extensions)
  - **Validation**: Fields added correctly; alembic revision matches; tests in T003-T010 start passing
  - **Dependencies**: T001 (migration), T003-T010 (tests written and failing)

- [x] **T012** [P] [db] Add pessimistic locking helper to ComponentLocation model
  - **Agent**: `db` (SQLAlchemy/database expert)
  - **File**: `backend/src/models/component_location.py`
  - **Task**: Add class method `acquire_lock(session, location_ids)` using `with_for_update(nowait=False)` with consistent ordering (by id); document deadlock prevention
  - **Reference**: research.md "SQLAlchemy Pessimistic Locking" decision
  - **Validation**: Locking method implemented; T009 locking tests pass
  - **Dependencies**: T001 (migration), T009 (locking tests written and failing)

### Backend Services

- [x] **T013** [api] Implement stock operations service - add_stock method
  - **Agent**: `api` (FastAPI service layer expert)
  - **File**: `backend/src/services/stock_operations.py`
  - **Task**: Implement `add_stock(component_id, location_id, quantity, pricing, lot_id, comments, user)` with pessimistic locking, StockTransaction creation, ComponentLocation update/create, Component.total_quantity increment
  - **Reference**: data-model.md "Add Stock" state transition (lines 70-77)
  - **Validation**: T003 contract tests pass; T006 integration tests pass; T010 unit tests pass
  - **Dependencies**: T011, T012 (models ready), T003/T006/T010 (tests failing)

- [x] **T014** [api] Implement stock operations service - remove_stock method
  - **Agent**: `api` (FastAPI service layer expert)
  - **File**: `backend/src/services/stock_operations.py`
  - **Task**: Implement `remove_stock(component_id, location_id, quantity, comments, user)` with pessimistic locking, auto-capping to available stock, StockTransaction creation (negative qty), ComponentLocation update/delete if zero, Component.total_quantity decrement
  - **Reference**: data-model.md "Remove Stock" state transition (lines 79-86)
  - **Validation**: T004 contract tests pass; T007 integration tests pass; auto-capping tested
  - **Dependencies**: T011, T012 (models ready), T004/T007/T010 (tests failing)

- [x] **T015** [api] Implement stock operations service - move_stock method
  - **Agent**: `api` (FastAPI service layer expert)
  - **File**: `backend/src/services/stock_operations.py`
  - **Task**: Implement `move_stock(component_id, source_location_id, dest_location_id, quantity, comments, user)` with atomic transaction, locks on both locations (ordered), auto-capping, pricing inheritance, 2 StockTransactions, source update/delete, dest create/update, total quantity validation
  - **Reference**: data-model.md "Move Stock" state transition (lines 88-100)
  - **Validation**: T005 contract tests pass; T008 integration tests pass; atomicity verified
  - **Dependencies**: T011, T012 (models ready), T005/T008/T010 (tests failing)

### Backend API Endpoints

- [x] **T016** [P] [api] Implement POST /api/v1/components/{id}/stock/add endpoint
  - **Agent**: `api` (FastAPI routing expert)
  - **File**: `backend/src/api/stock_operations.py`
  - **Task**: Create FastAPI endpoint calling `add_stock` service method; admin-only dependency (403 for non-admin); error handling (400 validation, 404 not found, 409 conflict/lock); return StockHistoryEntry response
  - **Reference**: contracts/add-stock.yaml OpenAPI spec
  - **Validation**: T003 contract tests fully pass; admin access enforced; error codes correct
  - **Dependencies**: T013 (service implemented), T003 (tests failing)

- [x] **T017** [P] [api] Implement POST /api/v1/components/{id}/stock/remove endpoint
  - **Agent**: `api` (FastAPI routing expert)
  - **File**: `backend/src/api/stock_operations.py`
  - **Task**: Create FastAPI endpoint calling `remove_stock` service method; admin-only; error handling; return response with `capped` flag and `location_deleted` flag
  - **Reference**: contracts/remove-stock.yaml OpenAPI spec
  - **Validation**: T004 contract tests fully pass; auto-cap behavior working; location deletion flagged
  - **Dependencies**: T014 (service implemented), T004 (tests failing)

- [x] **T018** [P] [api] Implement POST /api/v1/components/{id}/stock/move endpoint
  - **Agent**: `api` (FastAPI routing expert)
  - **File**: `backend/src/api/stock_operations.py`
  - **Task**: Create FastAPI endpoint calling `move_stock` service method; admin-only; same-location validation (400); error handling; return source/dest state changes
  - **Reference**: contracts/move-stock.yaml OpenAPI spec
  - **Validation**: T005 contract tests fully pass; same-location rejected; atomicity maintained
  - **Dependencies**: T015 (service implemented), T005 (tests failing)

### Stock History & Export (Recent Clarifications - Session 2025-10-05)

- [x] **T018A** [P] [test] Contract test for GET /api/v1/components/{id}/stock/history
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/contract/test_stock_history.py`
  - **Task**: Write pytest contract tests from `contracts/stock-history.yaml` - test paginated response (10 entries/page per FR-045-048), sort functionality, pagination metadata (has_next, total_pages), admin/authenticated access
  - **Reference**: `contracts/stock-history.yaml` OpenAPI spec
  - **Validation**: Test fails (endpoint not implemented yet); covers pagination edge cases (empty, single page, multiple pages)
  - **Dependencies**: T001 (migration)

- [x] **T018B** [P] [test] Contract test for GET /api/v1/components/{id}/stock/history/export
  - **Agent**: `test` (TDD testing expert)
  - **File**: `backend/tests/contract/test_stock_history_export.py`
  - **Task**: Write pytest contract tests from `contracts/stock-history-export.yaml` - test CSV/Excel/JSON export formats (per FR-059), verify content-type headers, validate complete data export (no pagination), admin-only access
  - **Reference**: `contracts/stock-history-export.yaml` OpenAPI spec
  - **Validation**: Test fails (endpoint not implemented yet); covers all 3 formats with proper headers
  - **Dependencies**: T001 (migration)

- [x] **T018C** [api] Implement stock history service with pagination
  - **Agent**: `api` (FastAPI service layer expert)
  - **File**: `backend/src/services/stock_history_service.py` (NEW)
  - **Task**: Implement `get_paginated_history(component_id, page, page_size, sort_by, sort_order)` returning paginated StockTransaction entries (10/page default per FR-047), calculate pagination metadata, support sorting by created_at/quantity_change/transaction_type/user_name
  - **Reference**: data-model.md "Stock History Pagination" section, FR-045-048
  - **Validation**: T018A contract tests pass; pagination math correct; sorting works
  - **Dependencies**: T011 (StockTransaction model), T018A (tests failing)

- [x] **T018D** [api] Implement stock history export service (CSV/Excel/JSON)
  - **Agent**: `api` (FastAPI service layer expert)
  - **File**: `backend/src/services/stock_history_service.py`
  - **Task**: Implement `export_history(component_id, format)` supporting CSV (text/csv), Excel/XLSX (openpyxl library), JSON formats per FR-059; include all history entries (no pagination); proper column headers matching FR-043
  - **Reference**: contracts/stock-history-export.yaml, FR-059
  - **Validation**: T018B contract tests pass; all 3 formats generate valid output; Excel opens in spreadsheet app
  - **Dependencies**: T011 (StockTransaction model), T018B (tests failing)

- [x] **T018E** [P] [api] Implement GET /api/v1/components/{id}/stock/history endpoint
  - **Agent**: `api` (FastAPI routing expert)
  - **File**: `backend/src/api/v1/stock_history.py` (NEW)
  - **Task**: Create FastAPI endpoint calling `get_paginated_history` service; query params for page, page_size, sort_by, sort_order; return paginated response with metadata; authenticated access (not admin-only per FR-044)
  - **Reference**: contracts/stock-history.yaml OpenAPI spec
  - **Validation**: T018A contract tests fully pass; pagination works; default 10/page enforced
  - **Dependencies**: T018C (service implemented), T018A (tests failing)

- [x] **T018F** [P] [api] Implement GET /api/v1/components/{id}/stock/history/export endpoint
  - **Agent**: `api` (FastAPI routing expert)
  - **File**: `backend/src/api/v1/stock_history.py`
  - **Task**: Create FastAPI endpoint calling `export_history` service; query param for format (csv/xlsx/json); return streaming response with proper content-type and filename headers; admin-only access per FR-059
  - **Reference**: contracts/stock-history-export.yaml OpenAPI spec
  - **Validation**: T018B contract tests fully pass; CSV downloads correctly; Excel opens; JSON parses
  - **Dependencies**: T018D (service implemented), T018B (tests failing)

---

## Phase 3.4: Security Review

**CRITICAL: Security review MUST be completed before frontend implementation**

- [x] **T019** [security] Security review of stock operations backend
  - **Agent**: `security` (security analysis expert)
  - **File**: Review `backend/src/services/stock_operations.py`, `backend/src/api/stock_operations.py`
  - **Task**: Perform comprehensive security analysis:
    - **SQL Injection**: Verify all queries use parameterized statements (SQLAlchemy ORM)
    - **Admin Authorization**: Confirm admin-only enforcement on all 3 endpoints (FR-051, FR-052, FR-053)
    - **IDOR**: Check component/location ID validation prevents unauthorized access
    - **Race Conditions**: Verify pessimistic locking prevents TOCTOU attacks
    - **Input Validation**: Confirm quantity, pricing, location IDs validated (no negative, no overflow)
    - **Transaction Safety**: Verify atomicity prevents partial stock updates
    - **Error Leakage**: Check error messages don't expose internal state
    - **Logging**: Verify sensitive data (pricing) not logged inappropriately
  - **Deliverable**: Security report in `specs/006-add-remove-stock/security-review.md` with findings and remediation status
  - **Validation**: No high/critical vulnerabilities; all constitutional security requirements met
  - **Dependencies**: T013-T018 (backend implementation complete)

---

## Phase 3.5: Frontend Implementation

### Frontend API Client

- [x] **T020** [vue] Create stock operations API client service
  - **Agent**: `vue` (Vue/TypeScript frontend expert)
  - **File**: `frontend/src/services/stockOperations.ts`
  - **Task**: Create TypeScript API client with methods: `addStock`, `removeStock`, `moveStock` - call backend endpoints with JWT auth header; proper error handling; TypeScript interfaces matching Pydantic schemas
  - **Reference**: contracts/ OpenAPI specs, backend schemas
  - **Validation**: Type safety enforced; error responses handled; auth header included
  - **Dependencies**: T016-T018 (API endpoints implemented), T019 (security approved)

### Frontend Form Components

- [x] **T021** [P] [vue] Create AddStockForm.vue inline component
  - **Agent**: `vue` (Vue/Quasar component expert)
  - **File**: `frontend/src/components/stock/AddStockForm.vue`
  - **Task**: Create inline multi-step form component with tabs: "Enter manually", "Receive against order", "Add to order"; quantity input, pricing options (no price/per component/entire lot), total calculation, location selector; local ref state; Quasar components (QInput, QSelect, QStepper); emit events on success/cancel
  - **Reference**: research.md "Multi-Step Form State Management", spec.md FR-002 to FR-013
  - **Validation**: Renders inline (not modal); multi-step navigation works; pricing auto-calculated
  - **Dependencies**: T020 (API client), T019 (security approved)

- [x] **T022** [P] [vue] Create RemoveStockForm.vue inline component
  - **Agent**: `vue` (Vue/Quasar component expert)
  - **File**: `frontend/src/components/stock/RemoveStockForm.vue`
  - **Task**: Create inline simple form component: location display with current quantity, quantity input with auto-capping (watch input, cap at max, show Quasar notify), comments textarea; local ref state; emit events on success/cancel
  - **Reference**: research.md "Auto-Capping Validation", spec.md FR-014 to FR-023
  - **Validation**: Renders inline; auto-capping works with visual feedback; simple UX
  - **Dependencies**: T020 (API client), T019 (security approved)

- [x] **T023** [P] [vue] Create MoveStockForm.vue inline component
  - **Agent**: `vue` (Vue/Quasar component expert)
  - **File**: `frontend/src/components/stock/MoveStockForm.vue`
  - **Task**: Create inline form component: source location pre-selected (from row context), destination selector (existing locations + "Other locations" option), quantity input with auto-capping, comments; local ref state; prevent same source/dest; emit events on success/cancel
  - **Reference**: research.md "Inline Form Rendering", spec.md FR-024 to FR-039
  - **Validation**: Renders inline; destination options filtered correctly; same-location prevented
  - **Dependencies**: T020 (API client), T019 (security approved)

### Frontend Integration

- [x] **T024** [vue] Integrate stock operation forms into ComponentList.vue
  - **Agent**: `vue` (Vue integration expert)
  - **File**: `frontend/src/components/ComponentList.vue`
  - **Task**: Add three new tabs to expanded row: "Add Stock", "Remove Stock", "Move Stock"; import and render AddStockForm, RemoveStockForm, MoveStockForm components inline; wire up success handlers to refresh component data; hide/disable tabs for non-admin users (FR-052)
  - **Reference**: research.md "Inline Form Rendering in Vue 3 + Quasar", ComponentList.vue existing pattern (lines 370-945)
  - **Validation**: Forms display inline in expanded rows; multiple rows can have forms open simultaneously (FR-012, FR-023, FR-039); admin-only UI enforcement
  - **Dependencies**: T021, T022, T023 (form components ready)

### Frontend Stock History Display (Recent Clarifications - Session 2025-10-05)

- [x] **T024A** [vue] Create StockHistoryTable.vue paginated component
  - **Agent**: `vue` (Vue/Quasar component expert)
  - **File**: `frontend/src/components/stock/StockHistoryTable.vue`
  - **Task**: Create paginated table component displaying stock history with columns: Date, Quantity (+/- indicator per FR-043), Location, Lot ID, Price, Comments, User; support sorting by any column per FR-044; pagination controls (10 entries/page per FR-047); export buttons (CSV/Excel/JSON per FR-059); update table on stock operation success per FR-045
  - **Reference**: contracts/stock-history.yaml, FR-042-048, FR-059
  - **Validation**: Table displays inline in component row expansion; pagination works; sorting works; export buttons trigger downloads
  - **Dependencies**: T018E, T018F (API endpoints implemented), T020 (API client updated)

- [x] **T024B** [vue] Update stockOperations.ts API client with history methods
  - **Agent**: `vue` (Vue/TypeScript frontend expert)
  - **File**: `frontend/src/services/stockOperations.ts`
  - **Task**: Add methods: `getStockHistory(component_id, page, page_size, sort_by, sort_order)` and `exportStockHistory(component_id, format)` calling backend endpoints; proper TypeScript interfaces for pagination response; handle export file downloads with proper content-disposition
  - **Reference**: contracts/stock-history.yaml, contracts/stock-history-export.yaml
  - **Validation**: Type safety enforced; pagination metadata properly typed; export triggers browser download
  - **Dependencies**: T018E, T018F (API endpoints implemented)

- [x] **T024C** [vue] Integrate StockHistoryTable into ComponentList.vue expansion
  - **Agent**: `vue` (Vue integration expert)
  - **File**: `frontend/src/components/ComponentList.vue`
  - **Task**: Add "Stock History" tab to component row expansion; import and render StockHistoryTable component; pass component_id prop; wire up refresh on stock operation success (T021-T023 success handlers should trigger history reload per FR-045)
  - **Reference**: FR-042-044 (history display requirements)
  - **Validation**: History table displays in expanded row alongside operation forms; table updates immediately after add/remove/move operations; accessible to all authenticated users (not admin-only per FR-044)
  - **Dependencies**: T024A (StockHistoryTable component), T024B (API client updated)

---

## Phase 3.6: Frontend Tests

- [x] **T025** [P] [vue] Component tests for AddStockForm.vue
  - **Agent**: `vue` (Vue testing expert)
  - **File**: `frontend/tests/components/AddStockForm.spec.ts`
  - **Task**: Write Vitest component tests: rendering, tab navigation, pricing calculation (per-unit * quantity = total), location selection, form submission, validation errors, cancel handling
  - **Reference**: spec.md Add Stock acceptance scenarios
  - **Validation**: All user interactions tested; pricing logic verified; form state isolated
  - **Dependencies**: T021 (component implemented)

- [x] **T026** [P] [vue] Component tests for RemoveStockForm.vue
  - **Agent**: `vue` (Vue testing expert)
  - **File**: `frontend/tests/components/RemoveStockForm.spec.ts`
  - **Task**: Write Vitest component tests: rendering, auto-capping behavior (input > available → caps + shows notification), quantity validation, comments input, form submission, cancel
  - **Reference**: spec.md Remove Stock acceptance scenarios
  - **Validation**: Auto-capping tested; visual feedback verified; edge cases covered
  - **Dependencies**: T022 (component implemented)

- [x] **T027** [P] [vue] Component tests for MoveStockForm.vue
  - **Agent**: `vue` (Vue testing expert)
  - **File**: `frontend/tests/components/MoveStockForm.spec.ts`
  - **Task**: Write Vitest component tests: rendering, destination options (existing + other), same-location prevention, auto-capping, quantity validation, form submission, cancel
  - **Reference**: spec.md Move Stock acceptance scenarios
  - **Validation**: Destination filtering tested; same-location rejected; edge cases covered
  - **Dependencies**: T023 (component implemented)

- [x] **T027A** [P] [vue] Component tests for StockHistoryTable.vue
  - **Agent**: `vue` (Vue testing expert)
  - **File**: `frontend/tests/components/StockHistoryTable.spec.ts`
  - **Task**: Write Vitest component tests: table rendering, pagination controls (10/page), sorting by columns, export button functionality (CSV/Excel/JSON), real-time updates on stock operations, empty state, loading state
  - **Reference**: spec.md Stock History acceptance scenarios, FR-042-048
  - **Validation**: Pagination tested; sorting tested; export buttons mocked; update behavior verified
  - **Dependencies**: T024A (StockHistoryTable component implemented)

---

## Phase 3.7: Documentation

**Constitutional Requirements**:
- **Principle VII (Documentation Review - NON-NEGOTIABLE)**:
  - Documentation updates MUST be in same PR as code changes
  - API docs updated for endpoint changes
  - Usage documentation included for new features
  - Migration paths documented

- [x] **T028** [P] [docs] Update API documentation with stock operations endpoints
  - **Agent**: `docs` (technical documentation expert)
  - **File**: `docs/api/stock-operations.md` (new), `docs/api.md` (update index)
  - **Task**: Create comprehensive API documentation for 5 stock operation endpoints using OpenAPI specs (add/remove/move operations + history pagination + export); include request/response examples, error codes, admin authentication requirements, atomic transaction behavior, auto-capping explanation, pagination details (10/page), export format examples (CSV/Excel/JSON)
  - **Reference**: contracts/ OpenAPI specs (all 5), quickstart.md, FR-042-048, FR-059
  - **Validation**: All 5 endpoints documented; examples match contracts; pagination and export features explained; migration path from manual stock management explained
  - **Dependencies**: T016-T018, T018E-T018F (all API endpoints implemented)

- [x] **T029** [P] [docs] Create user guide for stock operations
  - **Agent**: `docs` (user-facing documentation expert)
  - **File**: `docs/user/stock-operations.md` (new), `docs/user/features.md` (update)
  - **Task**: Write user guide explaining: how to access stock operations (component row expansion), adding stock (manual vs order-based), removing stock (auto-cap behavior), moving stock (location selection), viewing stock history (paginated table, sorting, 10 entries/page), exporting history (CSV/Excel/JSON formats), troubleshooting common issues, validation UX (red highlights, disabled submit per FR-014-015)
  - **Reference**: spec.md user scenarios, quickstart.md test scenarios
  - **Validation**: Step-by-step instructions; screenshots/diagrams if applicable; admin-only access noted
  - **Dependencies**: T024 (frontend integration complete)

- [x] **T030** [P] [docs] Update CLAUDE.md with stock operations patterns
  - **Agent**: `docs` (agent context documentation expert)
  - **File**: `CLAUDE.md`
  - **Task**: Add to "Recent Changes" section: stock operations feature with pessimistic locking pattern, inline forms in expanded rows, admin-only CRUD operations; keep under 150 lines (remove oldest entry if needed)
  - **Reference**: plan.md summary, research.md decisions
  - **Validation**: CLAUDE.md updated; within 150-line limit; follows O(1) incremental update pattern
  - **Dependencies**: T001-T027 (implementation complete)

---

## Phase 3.8: Quality & Validation

**Constitutional Requirements**:
- Quality Gates (Principle IV): Ruff formatting, zero linting errors, all CI checks pass
- Test Coverage (Principle II): Minimum 80% coverage enforced
- Documentation Completeness (Principle VII): All docs updated with code changes

- [ ] **T031** [review] Code review of stock operations implementation
  - **Agent**: `review` (code quality review expert)
  - **Files**: Review all implementation files (T011-T024)
  - **Task**: Comprehensive code review checking:
    - **TDD Compliance**: Tests written before implementation (verify git history)
    - **Code Quality**: No duplication, proper error handling, consistent naming
    - **Performance**: Pessimistic locks held <1s, queries optimized
    - **Best Practices**: FastAPI/Vue.js patterns followed, Pydantic validation used
    - **Constitutional Alignment**: All 7 principles verified
  - **Deliverable**: Review report in `specs/006-add-remove-stock/code-review.md`
  - **Validation**: No major issues; recommendations documented
  - **Dependencies**: T011-T024 (all implementation complete)

- [ ] **T032** Run ruff linting and formatting on backend
  - **Agent**: None (automated quality gate)
  - **Command**: `uv run ruff check backend/ && uv run ruff format backend/`
  - **Task**: Run ruff linter and formatter on all backend code; fix any issues found; ensure zero linting errors before commit
  - **Reference**: Constitution Principle IV (Quality Gates)
  - **Validation**: Zero linting errors; consistent formatting applied
  - **Dependencies**: T011-T018 (backend code complete)

- [ ] **T033** Run frontend type checking and linting
  - **Agent**: None (automated quality gate)
  - **Command**: `cd frontend && npm run type-check && npm run lint`
  - **Task**: Run TypeScript type checker and ESLint on all frontend code; fix any type errors or linting issues
  - **Reference**: Constitution Principle IV (Quality Gates)
  - **Validation**: Zero type errors; zero linting errors
  - **Dependencies**: T020-T024 (frontend code complete)

- [ ] **T034** Verify 80% minimum test coverage
  - **Agent**: None (automated coverage check)
  - **Command**: `cd backend && uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80`
  - **Task**: Run pytest with coverage report; verify minimum 80% coverage on backend code; add tests if coverage below threshold
  - **Reference**: Constitution Principle II (TDD - 80% minimum)
  - **Validation**: Coverage ≥80%; coverage report shows no critical gaps
  - **Dependencies**: T003-T010 (all tests written), T011-T018 (implementation complete)

- [ ] **T035** Run all backend tests in parallel
  - **Agent**: None (test execution)
  - **Command**: `cd backend && uv run pytest -n auto -v`
  - **Task**: Execute all backend tests (contract, integration, unit) in parallel using pytest-xdist; verify all tests pass; confirm test isolation (no order dependencies)
  - **Reference**: Constitution Principle VI (Test Isolation - parallelizable)
  - **Validation**: All tests pass; parallel execution successful; no flaky tests
  - **Dependencies**: T003-T010 (tests written), T011-T018 (implementation complete)

- [ ] **T036** Run all frontend tests
  - **Agent**: None (test execution)
  - **Command**: `cd frontend && npm test`
  - **Task**: Execute all frontend component tests (AddStockForm, RemoveStockForm, MoveStockForm); verify all tests pass
  - **Reference**: Constitution Principle II (TDD)
  - **Validation**: All frontend tests pass; component behavior verified
  - **Dependencies**: T025-T027 (frontend tests written), T021-T024 (components implemented)

- [ ] **T037** Execute manual testing from quickstart.md
  - **Agent**: None (manual validation)
  - **File**: `specs/006-add-remove-stock/quickstart.md`
  - **Task**: Follow quickstart guide step-by-step: start servers, create admin user, create test data, execute all 4 test scenarios (add stock, remove with auto-cap, move atomically, concurrent operations), verify validation checks pass
  - **Reference**: quickstart.md complete workflow
  - **Validation**: All test scenarios pass; stock history recorded correctly; no negative quantities; locks prevent concurrent modifications
  - **Dependencies**: T001-T036 (all implementation and automated tests complete)

---

## Dependencies Graph

```
Setup Phase:
T001 (migration) → blocks all other tasks

Tests Phase (TDD):
T001 → T003-T010 (all test tasks in parallel)

Backend Implementation:
T003-T010 → T011, T012 (models - blocked by failing tests)
T011, T012 → T013-T015 (services - blocked by models)
T013-T015 → T016-T018 (API endpoints - blocked by services)

Security Review:
T016-T018 → T019 (security review - blocks frontend)

Frontend Implementation:
T019 → T020 (API client - blocked by security approval)
T020 → T021-T023 (form components in parallel)
T021-T023 → T024 (integration - blocked by components)

Frontend Tests:
T021 → T025 (AddStockForm tests)
T022 → T026 (RemoveStockForm tests)
T023 → T027 (MoveStockForm tests)

Documentation:
T016-T018 → T028 (API docs)
T024 → T029 (user guide)
T027 → T030 (CLAUDE.md update)

Quality & Validation:
T024 → T031 (code review)
T018 → T032 (backend linting)
T024 → T033 (frontend linting)
T018 → T034 (coverage check)
T018 → T035 (backend tests)
T024 → T036 (frontend tests)
T036 → T037 (manual testing - final validation)
```

---

## Parallel Execution Examples

### Phase 3.2: All Tests in Parallel (After T001 Complete)
```bash
# Launch T003-T010 together using specialized test agent:
Task agent="test" description="Contract tests for stock operations" prompt="
Write contract tests in parallel:
- backend/tests/contract/test_add_stock.py (from contracts/add-stock.yaml)
- backend/tests/contract/test_remove_stock.py (from contracts/remove-stock.yaml)
- backend/tests/contract/test_move_stock.py (from contracts/move-stock.yaml)
- backend/tests/integration/test_add_stock_scenarios.py (6 scenarios from spec.md)
- backend/tests/integration/test_remove_stock_scenarios.py (5 scenarios)
- backend/tests/integration/test_move_stock_scenarios.py (7 scenarios)
- backend/tests/unit/test_locking.py (pessimistic locking)
- backend/tests/unit/test_stock_operations_service.py (business logic)
All tests MUST fail (no implementation yet). Use in-memory SQLite fixtures.
"
```

### Phase 3.3: Backend Models in Parallel (After Tests Fail)
```bash
# Launch T011-T012 together using specialized db agent:
Task agent="db" description="Database models for stock operations" prompt="
Implement in parallel:
- Extend backend/src/models/stock_transaction.py (add lot_id, price_per_unit, total_price)
- Add locking to backend/src/models/component_location.py (acquire_lock method with with_for_update)
Follow data-model.md schema. Tests in T003-T010 should start passing.
"
```

### Phase 3.5: Frontend Components in Parallel (After API + Security Approved)
```bash
# Launch T021-T023 together using specialized vue agent:
Task agent="vue" description="Stock operation form components" prompt="
Create inline Vue components in parallel:
- frontend/src/components/stock/AddStockForm.vue (multi-step form, pricing calculation)
- frontend/src/components/stock/RemoveStockForm.vue (simple form, auto-capping)
- frontend/src/components/stock/MoveStockForm.vue (location selector, same-location prevention)
All render inline in expanded rows (not modal dialogs). Use Quasar components, local ref state.
"
```

### Phase 3.7: Documentation in Parallel (After Implementation Complete)
```bash
# Launch T028-T030 together using specialized docs agent:
Task agent="docs" description="Stock operations documentation" prompt="
Write documentation in parallel:
- docs/api/stock-operations.md (API reference from contracts/)
- docs/user/stock-operations.md (user guide from spec.md scenarios)
- Update CLAUDE.md (add stock operations to recent changes, keep <150 lines)
Follow Constitution Principle VII (documentation review).
"
```

---

## Specialized Agent Assignments Summary

| Agent | Tasks | Expertise |
|-------|-------|-----------|
| **db** | T001, T011, T012 | Database migrations, SQLAlchemy models, pessimistic locking |
| **api** | T002, T013-T018 | FastAPI services, Pydantic schemas, API endpoints, admin guards |
| **test** | T003-T010, T025-T027 | TDD workflow, pytest, Vitest, contract/integration/unit tests |
| **security** | T019 | Security analysis, SQL injection, auth, race conditions, OWASP |
| **vue** | T020-T024 | Vue 3, Quasar, TypeScript, Pinia, inline forms, component integration |
| **docs** | T028-T030 | Technical documentation, user guides, API docs, CLAUDE.md updates |
| **review** | T031 | Code quality, TDD compliance, performance, constitutional alignment |

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to parallelize
- **Specialized agents** = use Task tool with subagent_type matching agent column
- **Security review** (T019) is mandatory gate before frontend implementation
- **TDD workflow** strictly enforced: T003-T010 MUST fail before T011+ implementation
- **Test isolation** verified: all tests use in-memory SQLite, no execution order dependencies
- **Admin-only enforcement** required at API layer (FR-051) AND UI layer (FR-052)
- **Pessimistic locking** prevents concurrent modifications (FR-041, FR-042)
- **Auto-capping** implemented client-side (UX) + server-side (security)
- **Atomic operations** for stock moves (FR-033) - both locations updated or neither
- **Documentation** updates in same PR as code (Constitution Principle VII)
- Commit after completing each task group (e.g., after all tests pass, after backend complete)

---

## Task Generation Rules Applied

1. **From Contracts** (3 files):
   - Each contract → contract test task [P] (T003-T005)
   - Each endpoint → implementation task (T016-T018)

2. **From Data Model** (2 entities):
   - StockTransaction extensions → migration (T001) + model task (T011)
   - ComponentLocation locking → model task (T012)

3. **From User Stories** (spec.md):
   - Add Stock scenarios → integration test (T006)
   - Remove Stock scenarios → integration test (T007)
   - Move Stock scenarios → integration test (T008)
   - Quickstart scenarios → validation task (T037)

4. **Ordering Applied**:
   - Setup (T001-T002) → Tests (T003-T010) → Models (T011-T012) → Services (T013-T015) → API (T016-T018) → Security (T019) → Frontend (T020-T024) → Tests (T025-T027) → Docs (T028-T030) → Quality (T031-T037)

---

## Validation Checklist

### Task Completeness
- [x] All contracts have corresponding tests (T003-T005 from 3 contracts)
- [x] All entities have migration + model tasks (T001, T011-T012)
- [x] All tests come before implementation (T003-T010 before T011+)
- [x] Parallel tasks truly independent ([P] marks confirmed)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Security review included before frontend (T019)
- [x] Specialized agents assigned to appropriate tasks

### Constitutional Compliance (PartsHub v1.2.0)
- [x] **Principle I (API-First Design)**: Backend tasks (T013-T018) before frontend (T020-T024)
- [x] **Principle II (TDD)**: Contract/integration tests (T003-T010) in Phase 3.2, implementation in 3.3+
- [x] **Principle III (Tiered Access)**: Admin-only enforcement tasks (T016-T018 API, T024 UI)
- [x] **Principle IV (Quality Gates)**: Ruff linting (T032), type checking (T033), coverage (T034)
- [x] **Principle V (Anonymous Contribution)**: Commit strategy follows standard format (no AI attribution)
- [x] **Principle VI (Test Isolation)**: Tests use isolated DB (T003-T010), parallelizable (T035)
- [x] **Principle VII (Documentation Review)**: Docs tasks (T028-T030) in same feature branch

---

**Total Tasks**: 37
**Estimated Completion Time**: 8-12 hours with parallel execution
**Ready for Execution**: Yes - all tasks specific, dependency-ordered, agent-assigned
