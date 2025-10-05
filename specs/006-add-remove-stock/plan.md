
# Implementation Plan: Stock Management Operations

**Branch**: `006-add-remove-stock` | **Date**: 2025-10-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-add-remove-stock/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Admin users need inline stock management operations (add, remove, move) accessible from component row expansion menus. Operations include multi-step add stock forms with pricing/lot tracking, simplified remove stock with auto-capping, and atomic move operations with weighted average price calculation. All operations log to persistent history with pagination (10 entries/page), support multi-format export (CSV/Excel/JSON), use pessimistic locking (30s timeout), and display real-time validation feedback (highlight errors, disable submit).

## Technical Context
**Language/Version**: Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic (backend); Quasar Framework, Pinia (frontend)
**Storage**: SQLite with SQLAlchemy ORM (existing stock_transactions table extended with lot_id, price_per_unit, total_price fields)
**Testing**: pytest with pytest-asyncio (backend), Vitest (frontend), in-memory SQLite for test isolation
**Target Platform**: Web application (Linux server backend, modern browsers frontend)
**Project Type**: web (frontend + backend)
**Performance Goals**: <200ms API response time for stock operations (<100 components), <50ms for history pagination
**Constraints**: 30-second pessimistic lock timeout, atomic transaction requirement for move operations, weighted average price calculation on merges
**Scale/Scope**: Admin-only feature (tiered access), 3 operations (add/remove/move), 10 entries per history page, 3 export formats (CSV/Excel/JSON)

**Recent Clarifications** (fore recent changes and additions to spec):
- Weighted average pricing on stock merges (FR-039)
- Paginated history (10 per page) with navigation controls (FR-045-048)
- 30-second lock timeout for pessimistic locking (FR-053)
- Multi-format export support: CSV, Excel (XLSX), JSON (FR-059)
- Validation UX: highlight invalid fields in red, disable submit until fixed (FR-014-015)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on PartsHub Constitution v1.2.0:

### Principle I: API-First Design
- [x] Backend API endpoints defined before frontend work
- [x] OpenAPI/Swagger documentation planned (contracts/ directory in Phase 1)
- [x] API responses follow consistent JSON schema (Pydantic models)
- [x] Breaking changes properly versioned (MAJOR bump) - new feature, no breaking changes

### Principle II: Test-Driven Development (TDD) - NON-NEGOTIABLE
- [x] Contract tests planned for all API endpoints (add/remove/move stock endpoints, history pagination, export)
- [x] Integration tests planned for all user stories (acceptance scenarios from spec.md)
- [x] Tests will be written BEFORE implementation (Phase 1 generates failing tests)
- [x] 80% minimum coverage target established

### Principle III: Tiered Access Control
- [x] Access levels defined (Anonymous/Authenticated/Admin) - Admin-only per FR-060-062
- [x] Authentication requirements specified (JWT token validation for all stock operations)
- [x] JWT token validation planned where needed (all 3 operations + history/export endpoints)
- [x] Security implemented by default, not retrofitted (admin-only from design)

### Principle IV: Quality Gates & Standards
- [x] Ruff linting and formatting will be applied (backend code)
- [x] CI checks identified (backend tests, frontend tests, security scans, Docker builds)
- [x] No direct main branch commits (branch: 006-add-remove-stock)
- [x] Pull request review process followed

### Principle V: Anonymous Contribution - NON-NEGOTIABLE
- [x] Commit messages will focus on changes, not tools
- [x] No AI assistant attribution in commits
- [x] Standard conventional commit format used (feat/fix/test/docs)

### Principle VI: Test Isolation - NON-NEGOTIABLE
- [x] Tests use isolated database (in-memory SQLite per test)
- [x] No test dependencies on execution order (parallelizable)
- [x] External services mocked or use test doubles (no external deps)
- [x] Database state reset between tests (fixtures create/destroy tables)
- [x] Tests runnable in parallel (pytest -n auto support)

### Principle VII: Documentation Review - NON-NEGOTIABLE
- [x] Documentation updates planned for all code changes (docs/user/, docs/api/)
- [x] OpenAPI specs will be updated for API changes (contracts/ generated in Phase 1)
- [x] README/setup guides will reflect configuration changes (N/A - no config changes)
- [x] Usage documentation will be included for new features (stock operations guide)
- [x] Migration paths documented for breaking changes (N/A - new feature, backward compatible)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   └── stock_transaction.py (extend with lot_id, price_per_unit, total_price)
│   ├── schemas/
│   │   └── stock_operations.py (add/remove/move request/response models)
│   ├── services/
│   │   ├── stock_operations_service.py (business logic, locking, weighted avg)
│   │   └── stock_history_service.py (pagination, export CSV/Excel/JSON)
│   └── api/
│       └── v1/
│           ├── stock.py (POST /components/{id}/stock/add|remove|move)
│           └── stock_history.py (GET /components/{id}/stock/history, /export)
├── migrations/
│   └── versions/
│       └── YYYYMMDD_HHMM_add_lot_pricing_to_stock_transactions.py
└── tests/
    ├── contract/
    │   ├── test_add_stock.py
    │   ├── test_remove_stock.py
    │   ├── test_move_stock.py
    │   └── test_stock_history.py
    ├── integration/
    │   ├── test_add_stock_scenarios.py
    │   ├── test_remove_stock_scenarios.py
    │   ├── test_move_stock_scenarios.py
    │   └── test_stock_history_scenarios.py
    └── unit/
        ├── test_stock_operations_service.py (weighted avg, locking, validation)
        └── test_stock_history_service.py (pagination, export formats)

frontend/
├── src/
│   ├── components/
│   │   ├── stock/
│   │   │   ├── AddStockForm.vue (multi-step inline form)
│   │   │   ├── RemoveStockForm.vue (simplified inline form)
│   │   │   ├── MoveStockForm.vue (source/dest selector inline form)
│   │   │   └── StockHistoryTable.vue (paginated, sortable, export buttons)
│   │   └── components/
│   │       └── ComponentRowExpansion.vue (updated with stock operation menu)
│   ├── services/
│   │   ├── stockOperations.ts (API client for add/remove/move)
│   │   └── stockHistory.ts (API client for history/export)
│   └── stores/
│       └── stockOperations.ts (Pinia store for operation state)
└── tests/
    └── components/
        ├── AddStockForm.spec.ts
        ├── RemoveStockForm.spec.ts
        ├── MoveStockForm.spec.ts
        └── StockHistoryTable.spec.ts

docs/
├── api/
│   └── stock-operations.md (API endpoint documentation)
└── user/
    └── stock-operations.md (user guide for stock management)
```

**Structure Decision**: Web application with separate backend (FastAPI) and frontend (Vue.js/Quasar). Backend uses existing repository structure with SQLAlchemy models, Pydantic schemas, service layer, and API routes. Frontend follows existing component/service/store pattern. Tests organized by tier (contract/integration/unit).

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Database Layer** (T001-T002):
   - T001: Create Alembic migration for StockTransaction extensions (lot_id, price_per_unit, total_price) [P]
   - T002: Create Pydantic schemas for stock operations (AddStockRequest, RemoveStockRequest, MoveStockRequest, StockHistoryResponse) [P]

2. **Contract Tests** (T003-T006) - TDD Red Phase:
   - T003: test_add_stock.py - POST /api/v1/components/{id}/stock/add [P]
   - T004: test_remove_stock.py - POST /api/v1/components/{id}/stock/remove [P]
   - T005: test_move_stock.py - POST /api/v1/components/{id}/stock/move [P]
   - T006: test_stock_history.py - GET /api/v1/components/{id}/stock/history with pagination [P]
   - T007: test_stock_history_export.py - GET /api/v1/components/{id}/stock/history/export (CSV/Excel/JSON) [P]

3. **Integration Tests** (T008-T011) - User Story Validation:
   - T008: test_add_stock_scenarios.py - Add stock acceptance scenarios from spec [P]
   - T009: test_remove_stock_scenarios.py - Remove stock acceptance scenarios with auto-capping [P]
   - T010: test_move_stock_scenarios.py - Move stock scenarios with weighted avg pricing [P]
   - T011: test_stock_history_scenarios.py - History pagination and export scenarios [P]

4. **Unit Tests** (T012-T013) - Business Logic:
   - T012: test_stock_operations_service.py - Locking, validation, weighted avg calculation [P]
   - T013: test_stock_history_service.py - Pagination logic, export format generation [P]

5. **Backend Implementation** (T014-T018) - TDD Green Phase:
   - T014: Implement StockOperationsService (add/remove/move with pessimistic locking, weighted avg)
   - T015: Implement StockHistoryService (pagination, export CSV/Excel/JSON)
   - T016: Implement POST /api/v1/components/{id}/stock/add endpoint
   - T017: Implement POST /api/v1/components/{id}/stock/remove endpoint
   - T018: Implement POST /api/v1/components/{id}/stock/move endpoint
   - T019: Implement GET /api/v1/components/{id}/stock/history endpoint (paginated)
   - T020: Implement GET /api/v1/components/{id}/stock/history/export endpoint (multi-format)

6. **Security Review** (T021):
   - T021: Review admin-only access control, JWT validation, pessimistic locking security

7. **Frontend Components** (T022-T027) - Vue.js/Quasar UI:
   - T022: Create AddStockForm.vue (multi-step inline form with validation highlighting) [P]
   - T023: Create RemoveStockForm.vue (simplified inline form with auto-cap feedback) [P]
   - T024: Create MoveStockForm.vue (source/dest selector with weighted avg display) [P]
   - T025: Create StockHistoryTable.vue (paginated, sortable, export buttons) [P]
   - T026: Update ComponentRowExpansion.vue (add stock operation menu items)
   - T027: Create stockOperations.ts service (API client) and Pinia store [P]

8. **Frontend Component Tests** (T028-T031):
   - T028: AddStockForm.spec.ts [P]
   - T029: RemoveStockForm.spec.ts [P]
   - T030: MoveStockForm.spec.ts [P]
   - T031: StockHistoryTable.spec.ts [P]

9. **Documentation** (T032-T034):
   - T032: Create docs/api/stock-operations.md (API endpoint documentation)
   - T033: Create docs/user/stock-operations.md (user guide for stock management)
   - T034: Update main docs/api.md with stock operations overview

10. **Validation & Integration** (T035-T036):
    - T035: End-to-end test: Complete stock workflow (add → move → remove → export)
    - T036: Performance validation: <200ms for operations, <50ms for history pagination

**Ordering Strategy**:
- TDD order: Contract tests (T003-T007) → Integration tests (T008-T011) → Unit tests (T012-T013) → Implementation (T014-T020)
- Dependency order: Database migration (T001) → Schemas (T002) → Tests (T003-T013) → Services (T014-T015) → API (T016-T020) → Frontend (T022-T027)
- Parallelizable tasks marked [P] (independent files, no shared state)

**Estimated Output**: ~36 numbered, ordered tasks in tasks.md

**Key Constitutional Compliance**:
- Principle II (TDD): All tests written BEFORE implementation (T003-T013 before T014-T020)
- Principle VI (Test Isolation): All tests use in-memory SQLite, no shared state
- Principle VII (Docs): Documentation tasks (T032-T034) included in same workflow

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - SKIPPED (no NEEDS CLARIFICATION in Technical Context)
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - approach documented, ~36 tasks planned)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (all 7 principles satisfied)
- [x] Post-Design Constitution Check: PASS (all constitutional requirements addressed in design)
- [x] All NEEDS CLARIFICATION resolved (no unknowns in Technical Context)
- [x] Complexity deviations documented (none - standard patterns used)

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] data-model.md (existing, validated)
- [x] contracts/add-stock.yaml (existing)
- [x] contracts/remove-stock.yaml (existing)
- [x] contracts/move-stock.yaml (existing)
- [x] contracts/stock-history.yaml (NEW - pagination support)
- [x] contracts/stock-history-export.yaml (NEW - CSV/Excel/JSON export)
- [x] CLAUDE.md updated (incremental O(1) update with new feature context)

---
*Based on Constitution v1.2.0 - See `.specify/memory/constitution.md`*
