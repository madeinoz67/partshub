# Implementation Plan: Stock Management Operations

**Branch**: `006-add-remove-stock` | **Date**: 2025-10-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-add-remove-stock/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✓ Loaded from /Users/seaton/Documents/src/partshub/specs/006-add-remove-stock/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✓ All clarifications resolved in Session 2025-10-04
   → ✓ Project Type: Web application (frontend + backend)
3. Fill the Constitution Check section based on the content of the constitution document.
   → ✓ Constitution v1.2.0 requirements mapped
4. Evaluate Constitution Check section below
   → ✓ No violations detected
   → ✓ Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✓ Research complete: 6 technical decisions documented
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✓ Design artifacts generated
7. Re-evaluate Constitution Check section
   → ✓ No new violations introduced
   → ✓ Progress Tracking: Post-Design Constitution Check PASS
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → ✓ Task generation strategy documented below
9. STOP - Ready for /tasks command
   → ✓ Execution complete
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Implement comprehensive stock management operations (add, remove, move) for PartsHub components with inline row-expansion forms, pessimistic locking for concurrent safety, and immutable audit history tracking. Admin-only operations support multi-step workflows for adding stock (with pricing/lot tracking), simplified removal with auto-capping validation, and atomic stock transfers between locations with pricing inheritance.

**Technical Approach**: Extend existing StockTransaction and ComponentLocation models with pessimistic row-level locking using SQLAlchemy's `with_for_update()`. Implement inline multi-step forms in Vue 3/Quasar within expanded component rows (not modal dialogs). Use database transactions with consistent lock ordering to ensure atomic operations and prevent deadlocks. Client-side auto-capping with server-side validation for quantity constraints.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript (frontend Vue 3)
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic (backend); Vue 3, Quasar Framework, Pinia (frontend)
**Storage**: SQLite database with SQLAlchemy ORM (existing StockTransaction and ComponentLocation tables)
**Testing**: pytest with in-memory SQLite (backend), Vitest (frontend)
**Target Platform**: Web application (Linux/macOS server, modern browsers)
**Project Type**: web (frontend + backend)
**Performance Goals**: <200ms API response time, pessimistic locks held <1s
**Constraints**: Admin-only operations, atomic stock transfers (ACID compliance), concurrent-safe with pessimistic locking
**Scale/Scope**: 3 new API endpoints, 3 inline form components, extend 2 existing models, ~25-30 implementation tasks

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on PartsHub Constitution v1.2.0:

### Principle I: API-First Design
- [x] Backend API endpoints defined before frontend work (contracts/ created in Phase 1)
- [x] OpenAPI/Swagger documentation planned (add-stock.yaml, remove-stock.yaml, move-stock.yaml)
- [x] API responses follow consistent JSON schema (using Pydantic models, standard error format)
- [x] Breaking changes properly versioned (new endpoints, no breaking changes to existing API)

### Principle II: Test-Driven Development (TDD) - NON-NEGOTIABLE
- [x] Contract tests planned for all API endpoints (3 contract test files from OpenAPI specs)
- [x] Integration tests planned for all user stories (6 add stock scenarios, 5 remove, 7 move scenarios)
- [x] Tests will be written BEFORE implementation (TDD workflow in task ordering)
- [x] 80% minimum coverage target established (contract + integration + unit tests)

### Principle III: Tiered Access Control
- [x] Access levels defined (Admin-only for all stock operations per FR-051, FR-052, FR-053)
- [x] Authentication requirements specified (JWT bearer token required, 403 Forbidden for non-admin)
- [x] JWT token validation planned where needed (all three endpoints require admin role)
- [x] Security implemented by default, not retrofitted (admin-only enforced at API layer)

### Principle IV: Quality Gates & Standards
- [x] Ruff linting and formatting will be applied (backend code follows project standards)
- [x] CI checks identified (backend tests, frontend tests, type checks, security scans)
- [x] No direct main branch commits (feature branch 006-add-remove-stock)
- [x] Pull request review process followed (standard PartsHub workflow)

### Principle V: Anonymous Contribution - NON-NEGOTIABLE
- [x] Commit messages will focus on changes, not tools (conventional commit format)
- [x] No AI assistant attribution in commits (clean git history)
- [x] Standard conventional commit format used (feat/fix/docs/test prefixes)

### Principle VI: Test Isolation - NON-NEGOTIABLE
- [x] Tests use isolated database (in-memory SQLite via conftest.py fixtures)
- [x] No test dependencies on execution order (each test creates own fixtures)
- [x] External services mocked or use test doubles (no external dependencies in this feature)
- [x] Database state reset between tests (automatic via in-memory DB and session fixtures)
- [x] Tests runnable in parallel (pytest-xdist compatible, no shared mutable state)

### Principle VII: Documentation Review - NON-NEGOTIABLE
- [x] Documentation updates planned for all code changes (quickstart.md, API docs, user guide)
- [x] OpenAPI specs will be updated for API changes (contracts/ created with full schemas)
- [x] README/setup guides will reflect configuration changes (if needed for locking configuration)
- [x] Usage documentation will be included for new features (quickstart.md for testing/validation)
- [x] Migration paths documented for breaking changes (database migration for StockTransaction extensions)

## Project Structure

### Documentation (this feature)
```
specs/006-add-remove-stock/
├── spec.md              # Feature specification (✓ complete)
├── plan.md              # This file (/plan command output - ✓ complete)
├── research.md          # Phase 0 output (/plan command - ✓ complete)
├── data-model.md        # Phase 1 output (/plan command - ✓ complete)
├── quickstart.md        # Phase 1 output (/plan command - ✓ complete)
├── contracts/           # Phase 1 output (/plan command - ✓ complete)
│   ├── add-stock.yaml
│   ├── remove-stock.yaml
│   └── move-stock.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── stock_transaction.py      # Extend with lot_id, price_per_unit
│   │   └── component_location.py     # Add pessimistic locking logic
│   ├── services/
│   │   └── stock_operations.py       # New: add/remove/move business logic
│   ├── api/
│   │   └── stock_operations.py       # New: three endpoints with admin guards
│   └── schemas/
│       └── stock_operations.py       # New: Pydantic request/response models
└── tests/
    ├── contract/
    │   ├── test_add_stock.py          # New: contract tests from add-stock.yaml
    │   ├── test_remove_stock.py       # New: contract tests from remove-stock.yaml
    │   └── test_move_stock.py         # New: contract tests from move-stock.yaml
    ├── integration/
    │   ├── test_add_stock_scenarios.py    # New: 6 user story scenarios
    │   ├── test_remove_stock_scenarios.py # New: 5 user story scenarios
    │   └── test_move_stock_scenarios.py   # New: 7 user story scenarios
    └── unit/
        ├── test_stock_operations_service.py  # New: business logic tests
        └── test_locking.py                    # New: pessimistic locking tests

frontend/
├── src/
│   ├── components/
│   │   ├── stock/
│   │   │   ├── AddStockForm.vue       # New: inline multi-step form
│   │   │   ├── RemoveStockForm.vue    # New: inline simple form
│   │   │   └── MoveStockForm.vue      # New: inline location selector form
│   │   └── ComponentList.vue          # Modify: add stock operation tabs
│   ├── services/
│   │   └── stockOperations.ts         # New: API client for stock operations
│   └── stores/
│       └── stockHistory.ts            # New: Pinia store for history tracking
└── tests/
    └── components/
        ├── AddStockForm.spec.ts       # New: component tests
        ├── RemoveStockForm.spec.ts    # New: component tests
        └── MoveStockForm.spec.ts      # New: component tests
```

**Structure Decision**: Web application structure with separate backend/ and frontend/ directories. Backend uses layered architecture (models → services → API). Frontend uses component-based architecture with Pinia for state management. Stock operation forms implemented as inline components within ComponentList.vue expanded rows, not as separate modal dialogs or pages.

## Phase 0: Outline & Research
✓ **Complete** - See [research.md](research.md)

**Research Areas Completed**:
1. **Inline Form Rendering in Vue 3 + Quasar**
   - Decision: Tab-based inline forms within expanded rows (existing ComponentList.vue pattern)
   - Rationale: Spec requires inline forms; existing infrastructure supports this

2. **SQLAlchemy Pessimistic Locking**
   - Decision: `with_for_update(nowait=False)` for blocking row-level locks
   - Rationale: Prevents concurrent modifications; spec explicitly requires pessimistic locking

3. **Stock History Tracking**
   - Decision: Extend existing StockTransaction model with lot_id and price fields
   - Rationale: Model already exists with immutable audit trail

4. **Multi-Step Form State Management**
   - Decision: Local ref-based state; Pinia only for server communication
   - Rationale: Simpler than global state for ephemeral UI data

5. **Atomic Stock Transfers**
   - Decision: Database transactions with pessimistic locks on both locations
   - Rationale: ACID compliance ensures both operations succeed or both fail

6. **Auto-Capping Validation**
   - Decision: Client-side auto-capping with visual feedback + server-side validation
   - Rationale: Spec requires automatic capping; defense in depth approach

**Key Findings**:
- ComponentList.vue already has inline expansion with tab navigation (lines 370-945)
- StockTransaction model exists with core fields; needs minor extensions
- Testing framework established (in-memory SQLite via conftest.py)
- Pessimistic locking will be new pattern (current code uses optimistic locking)

## Phase 1: Design & Contracts
✓ **Complete** - See design artifacts below

### 1. Data Model (data-model.md)
**Entities**:
- **StockTransaction** (extend existing): Add `lot_id`, `price_per_unit`, `total_price`
- **ComponentLocation** (existing): Document pessimistic locking strategy

**State Transitions**:
- Add Stock: Create StockTransaction → Update/Create ComponentLocation → Update Component.total_quantity
- Remove Stock: Create StockTransaction (negative qty) → Update ComponentLocation → Delete if zero → Update total
- Move Stock: Create 2 StockTransactions → Update/Delete source → Update/Create destination → Validate total unchanged

**Validation Rules**:
- Auto-cap removal/move quantities at available stock (FR-017, FR-029)
- Prevent same source/destination for moves (FR-031)
- Atomic operations with pessimistic locking (FR-033, FR-041-042)
- Zero-quantity cleanup (FR-021, FR-035)

### 2. API Contracts (contracts/)
**Three OpenAPI 3.0 Specifications**:
1. **POST /api/v1/components/{component_id}/stock/add** (add-stock.yaml)
   - Request: quantity, location_id, pricing (optional), lot_id (optional), comments
   - Response: updated stock, history entry, 200/400/403/404/409

2. **POST /api/v1/components/{component_id}/stock/remove** (remove-stock.yaml)
   - Request: location_id, quantity, comments, reason
   - Response: updated stock, capped flag, location_deleted flag, 200/400/403/404/409

3. **POST /api/v1/components/{component_id}/stock/move** (move-stock.yaml)
   - Request: source_location_id, destination_location_id, quantity, comments
   - Response: source/destination state, pricing inheritance, 200/400/403/404/409

**All contracts include**:
- Admin JWT bearer token security
- Comprehensive error responses
- Multiple examples (success, auto-capping, errors)
- Detailed operation descriptions

### 3. Quickstart Guide (quickstart.md)
**Test Scenarios**:
1. Add stock manually with pricing (UI + API testing)
2. Remove stock with auto-capping validation
3. Move stock atomically between locations
4. Test concurrent operations (pessimistic locking)

**Validation Checks**:
- Total quantity consistency across locations
- Stock history recorded correctly
- No negative quantities
- Locks prevent concurrent modifications

### 4. Agent Context (CLAUDE.md)
✓ Updated with new feature context (stock operations, pessimistic locking)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base template
2. Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
3. Task categories:
   - **Database Migration**: Alembic migration for StockTransaction extensions
   - **Contract Tests** (3 tasks): One per endpoint from OpenAPI specs
   - **Backend Models** (2 tasks): Extend StockTransaction, add locking to ComponentLocation
   - **Backend Services** (3 tasks): Add/remove/move business logic with locking
   - **Backend API** (3 tasks): Three endpoints with admin guards
   - **Integration Tests** (3 tasks): User story scenarios for each operation
   - **Frontend Services** (1 task): API client for stock operations
   - **Frontend Components** (3 tasks): AddStockForm, RemoveStockForm, MoveStockForm
   - **Frontend Integration** (1 task): Wire forms into ComponentList.vue tabs
   - **Component Tests** (3 tasks): Vitest tests for each form component
   - **Documentation** (2 tasks): API docs update, user guide additions
   - **Manual Testing** (1 task): Execute quickstart.md validation

**Ordering Strategy (TDD + Dependency)**:
1. Database migration (prerequisite for all)
2. Contract tests (define API contracts) [P]
3. Backend models (StockTransaction, ComponentLocation) [P]
4. Backend services (business logic with locking)
5. Backend API endpoints (wire services to routes) [P]
6. Integration tests (validate user stories)
7. Frontend API client (connect to backend)
8. Frontend form components [P]
9. Frontend integration (wire into ComponentList)
10. Component tests [P]
11. Documentation updates [P]
12. Manual testing (quickstart validation)

**Parallelization**: Tasks marked [P] are independent and can run in parallel

**Estimated Output**: 28-32 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations detected. All requirements align with PartsHub principles:
- API-first design with OpenAPI contracts
- TDD workflow (tests before implementation)
- Admin-only tiered access control
- Pessimistic locking for concurrent safety (new pattern but constitutionally sound)
- Isolated testing with in-memory SQLite
- Documentation updates included in same PR

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (Session 2025-10-04 with 6 clarifications)
- [x] Complexity deviations documented (none - no violations)

**Artifacts Generated**:
- [x] research.md (6 technical decisions)
- [x] data-model.md (StockTransaction + ComponentLocation)
- [x] contracts/add-stock.yaml (OpenAPI 3.0)
- [x] contracts/remove-stock.yaml (OpenAPI 3.0)
- [x] contracts/move-stock.yaml (OpenAPI 3.0)
- [x] quickstart.md (testing guide)
- [x] CLAUDE.md (updated with feature context)

---
*Based on Constitution v1.2.0 - See `.specify/memory/constitution.md`*

**Next Command**: Run `/tasks` to generate dependency-ordered tasks.md from this plan.
