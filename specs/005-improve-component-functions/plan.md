# Implementation Plan: Component Bulk Operations

**Branch**: `005-improve-component-functions` | **Date**: 2025-10-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-improve-component-functions/spec.md`

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

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Add bulk operations functionality to the component view, allowing admin users to select multiple components and perform actions (assign to projects, add/remove tags, set attributes, delete) in a single atomic transaction. All operations use all-or-nothing rollback strategy with persistent selection across page navigation.

## Technical Context
**Language/Version**: Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic (backend); Quasar Framework, Pinia (frontend)
**Storage**: SQLite with SQLAlchemy ORM (existing components, projects, tags tables)
**Testing**: pytest with in-memory SQLite (backend), Vitest (frontend)
**Target Platform**: Web application (FastAPI backend + Vue.js frontend)
**Project Type**: web (frontend + backend detected)
**Performance Goals**: <200ms p95 for bulk operations on <100 components, <500ms for 100-1000 components
**Constraints**: Atomic transactions required (all-or-nothing), admin-only access, selection state must persist across navigation
**Scale/Scope**: Handle bulk operations on 1-1000 components, support 9 operation types, 2 complex modal forms

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on PartsHub Constitution v1.2.0:

### Principle I: API-First Design
- [x] Backend API endpoints defined before frontend work
- [x] OpenAPI/Swagger documentation planned
- [x] API responses follow consistent JSON schema
- [x] Breaking changes properly versioned (MAJOR bump)

### Principle II: Test-Driven Development (TDD) - NON-NEGOTIABLE
- [x] Contract tests planned for all API endpoints
- [x] Integration tests planned for all user stories
- [x] Tests will be written BEFORE implementation
- [x] 80% minimum coverage target established

### Principle III: Tiered Access Control
- [x] Access levels defined (Admin only for bulk operations)
- [x] Authentication requirements specified (JWT validation)
- [x] JWT token validation planned where needed
- [x] Security implemented by default, not retrofitted

### Principle IV: Quality Gates & Standards
- [x] Ruff linting and formatting will be applied
- [x] CI checks identified (tests, security, builds)
- [x] No direct main branch commits
- [x] Pull request review process followed

### Principle V: Anonymous Contribution - NON-NEGOTIABLE
- [x] Commit messages will focus on changes, not tools
- [x] No AI assistant attribution in commits
- [x] Standard conventional commit format used

### Principle VI: Test Isolation - NON-NEGOTIABLE
- [x] Tests use isolated database (in-memory SQLite)
- [x] No test dependencies on execution order
- [x] External services mocked or use test doubles
- [x] Database state reset between tests
- [x] Tests runnable in parallel

### Principle VII: Documentation Review - NON-NEGOTIABLE
- [x] Documentation updates planned for all code changes
- [x] OpenAPI specs will be updated for API changes
- [x] README/setup guides will reflect configuration changes
- [x] Usage documentation will be included for new features
- [x] Migration paths documented for breaking changes

## Project Structure

### Documentation (this feature)
```
specs/005-improve-component-functions/
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
│   ├── models/          # Component, Project, Tag models (existing)
│   ├── services/        # NEW: BulkOperationService for transaction management
│   └── api/             # NEW: /components/bulk/* endpoints
└── tests/
    ├── contract/        # NEW: Bulk operation contract tests
    ├── integration/     # NEW: Bulk operation user story tests
    └── unit/            # NEW: BulkOperationService unit tests

frontend/
├── src/
│   ├── components/      # NEW: BulkOperationMenu, TagManagementDialog, AddToProjectDialog
│   ├── pages/           # MODIFY: Components page with selection state
│   ├── services/        # NEW: BulkOperationService API client
│   └── stores/          # NEW: SelectionStore (Pinia) for persistent state
└── tests/
    └── unit/            # NEW: Component and store tests
```

**Structure Decision**: Web application structure with backend and frontend directories. Backend implements atomic bulk operation transactions via new BulkOperationService. Frontend implements persistent selection state via Pinia store and new UI components for bulk operation dialogs.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - ✅ All technical context resolved via clarification session
   - No NEEDS CLARIFICATION markers remain in specification

2. **Research tasks**:
   - Research SQLAlchemy transaction patterns for atomic bulk operations with rollback
   - Research Pinia store persistence strategies for selection state across navigation
   - Research FastAPI dependency injection for admin-only endpoint protection
   - Research Vue.js/Quasar patterns for multi-select table with persistent state
   - Research optimistic concurrency control patterns for concurrent modification detection

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Component (existing): No schema changes needed
   - Project (existing): No schema changes needed
   - Tag (existing): No schema changes needed
   - BulkOperation (transient): Operation type, component IDs, parameters, status
   - SelectionState (frontend): Set of selected component IDs, persistence strategy

2. **Generate API contracts** from functional requirements:
   ```
   POST /api/components/bulk/tags/add
   POST /api/components/bulk/tags/remove
   POST /api/components/bulk/projects/assign
   POST /api/components/bulk/delete
   POST /api/components/bulk/meta-parts/add
   POST /api/components/bulk/purchase-lists/add
   POST /api/components/bulk/low-stock/set
   POST /api/components/bulk/attribution/set
   GET /api/components/bulk/tags/preview
   ```
   - All endpoints require Admin role (JWT validation)
   - All POST endpoints use atomic transactions
   - All endpoints return detailed error reports on failure
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint in `backend/tests/contract/`
   - Assert request/response schemas
   - Assert admin-only access (403 for non-admin)
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Scenario 1: Bulk assign to project (5 components)
   - Scenario 2: Bulk add tags (3 components)
   - Scenario 3: Bulk delete (8 components)
   - Scenario 4: Selection persistence across pages
   - Scenario 5: Disabled state with 0 components
   - Scenario 6: Rollback on partial failure

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add: Bulk operations patterns, Pinia selection store, atomic transactions
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Backend tasks:
  - Each bulk operation endpoint → contract test task [P]
  - BulkOperationService → unit test task + implementation
  - Admin role validation → integration test task
  - Transaction rollback → integration test task
- Frontend tasks:
  - SelectionStore (Pinia) → unit test + implementation [P]
  - BulkOperationMenu component → unit test + implementation [P]
  - TagManagementDialog component → unit test + implementation [P]
  - AddToProjectDialog component → unit test + implementation [P]
  - Components page modifications → integration test + implementation
- Integration tasks:
  - Each user story → E2E integration test
  - Selection persistence → integration test
  - Rollback on failure → integration test

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order:
  1. Backend models (no changes)
  2. Backend BulkOperationService + tests
  3. Backend API endpoints + contract tests [P]
  4. Frontend stores + tests [P]
  5. Frontend components + tests [P]
  6. Frontend page integration
  7. E2E integration tests
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations - all principles satisfied*

No complexity deviations from constitutional requirements.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

**Artifacts Generated**:
- [x] research.md - Technical decisions and patterns
- [x] data-model.md - Entity schemas and relationships
- [x] contracts/bulk-operations-openapi.yaml - API contract
- [x] quickstart.md - Test scenarios and validation steps
- [x] CLAUDE.md - Updated agent context
- [x] tasks.md - 42 ordered tasks with specialized agent recommendations

---
*Based on Constitution v1.2.0 - See `.specify/memory/constitution.md`*
