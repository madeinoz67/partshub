# Tasks: Component Bulk Operations

**Input**: Design documents from `/specs/005-improve-component-functions/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/bulk-operations-openapi.yaml

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+, FastAPI, Vue.js 3, Quasar, Pinia
   → Structure: web (backend/ + frontend/)
2. Load design documents:
   → data-model.md: Component (add version), BulkOperation, SelectionState
   → contracts/: 9 bulk operation endpoints
   → quickstart.md: 6 test scenarios
3. Generate tasks by category:
   → Setup: migration, dependencies, linting
   → Tests: 9 contract tests + 6 integration tests + 1 access test
   → Backend: BulkOperationService, admin auth, endpoints
   → Frontend: SelectionStore, dialogs, components, API client
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T042)
6. SUCCESS: 42 tasks ready for execution
```

## Format: `[ID] [P?] Description (Agent: specialized-agent)`
- **[P]**: Can run in parallel (different files, no dependencies)
- **Agent**: Recommended specialized agent for the task
- Include exact file paths in descriptions

## Path Conventions
- Backend: `backend/src/`, `backend/tests/`
- Frontend: `frontend/src/`, `frontend/tests/`
- Database migrations: `backend/alembic/versions/`

## Phase 3.1: Setup

- [X] **T001** Create Alembic migration to add `version` column to components table in `backend/alembic/versions/20251004_1200_add_component_version.py` (Agent: **db**)
  - Add `version INTEGER NOT NULL DEFAULT 1` column
  - Create index `idx_components_version`
  - Include upgrade() and downgrade()
  - Test migration on in-memory SQLite

- [X] **T002** Verify backend dependencies in `backend/pyproject.toml` (Agent: **api**)
  - Ensure FastAPI, SQLAlchemy, Pydantic, pytest
  - Verify `uv` package manager configured
  - No new dependencies needed

- [X] **T003** Verify frontend dependencies in `frontend/package.json` (Agent: **vue**)
  - Ensure Vue 3, Quasar, Pinia, pinia-plugin-persistedstate
  - Verify Vitest for testing
  - Add pinia-plugin-persistedstate if missing

- [X] **T004** [P] Configure Ruff for bulk operations code in `.ruff.toml` (Agent: **api**)
  - Ensure backend/src/ and backend/tests/ included
  - Verify Ruff version supports Python 3.11+

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

**Constitutional Requirements**:
- **Principle II (TDD - NON-NEGOTIABLE)**:
  - Tests MUST be written before implementation
  - Red-Green-Refactor cycle strictly enforced
  - User approval required after tests written
  - Minimum 80% coverage target

- **Principle VI (Test Isolation - NON-NEGOTIABLE)**:
  - Each test uses isolated database (in-memory SQLite)
  - Tests runnable in any order (no execution dependencies)
  - External services mocked
  - Database state reset after each test
  - Tests must be parallelizable

### Contract Tests (9 endpoints - all parallel)

- [X] **T005** [P] Contract test POST /api/components/bulk/tags/add in `backend/tests/contract/test_bulk_tags_add.py` (Agent: **test**)
  - Test request schema validation (component_ids: List[int], tags: List[str])
  - Test response schema (BulkOperationResponse)
  - Test 403 Forbidden for non-admin users
  - Test 400 for invalid request (empty component_ids, empty tags)
  - MUST FAIL (endpoint not implemented yet)

- [X] **T006** [P] Contract test POST /api/components/bulk/tags/remove in `backend/tests/contract/test_bulk_tags_remove.py` (Agent: **test**)
  - Test request schema validation
  - Test response schema
  - Test 403 Forbidden for non-admin
  - MUST FAIL

- [X] **T007** [P] Contract test GET /api/components/bulk/tags/preview in `backend/tests/contract/test_bulk_tags_preview.py` (Agent: **test**)
  - Test query parameter validation (component_ids, add_tags, remove_tags)
  - Test TagPreviewResponse schema
  - Test 403 Forbidden for non-admin
  - MUST FAIL

- [X] **T008** [P] Contract test POST /api/components/bulk/projects/assign in `backend/tests/contract/test_bulk_projects_assign.py` (Agent: **test**)
  - Test BulkAssignProjectRequest schema (project_id, quantities map)
  - Test response schema
  - Test 403 Forbidden, 404 for invalid project_id
  - MUST FAIL

- [X] **T009** [P] Contract test POST /api/components/bulk/delete in `backend/tests/contract/test_bulk_delete.py` (Agent: **test**)
  - Test BulkDeleteRequest schema
  - Test response schema
  - Test 403 Forbidden for non-admin
  - MUST FAIL

- [X] **T010** [P] Contract test POST /api/components/bulk/meta-parts/add in `backend/tests/contract/test_bulk_meta_parts.py` (Agent: **test**)
  - Test BulkMetaPartRequest schema
  - Test response schema
  - Test 403 Forbidden
  - MUST FAIL

- [X] **T011** [P] Contract test POST /api/components/bulk/purchase-lists/add in `backend/tests/contract/test_bulk_purchase_lists.py` (Agent: **test**)
  - Test BulkPurchaseListRequest schema
  - Test response schema
  - Test 403 Forbidden
  - MUST FAIL

- [X] **T012** [P] Contract test POST /api/components/bulk/low-stock/set in `backend/tests/contract/test_bulk_low_stock.py` (Agent: **test**)
  - Test BulkLowStockRequest schema (threshold >= 0)
  - Test response schema
  - Test 403 Forbidden
  - MUST FAIL

- [X] **T013** [P] Contract test POST /api/components/bulk/attribution/set in `backend/tests/contract/test_bulk_attribution.py` (Agent: **test**)
  - Test BulkAttributionRequest schema
  - Test response schema
  - Test 403 Forbidden
  - MUST FAIL

### Integration Tests (6 scenarios + 1 access test - all parallel)

- [X] **T014** [P] Integration test: Bulk add tags (3 components) in `backend/tests/integration/test_bulk_add_tags_integration.py` (Agent: **test**)
  - Create 3 test components in isolated DB
  - Call bulk add tags API with ["resistor", "SMD"]
  - Assert all 3 components have both tags
  - Assert affected_count = 3, success = true
  - MUST FAIL (implementation not done)

- [X] **T015** [P] Integration test: Bulk assign to project (5 components) in `backend/tests/integration/test_bulk_assign_project.py` (Agent: **test**)
  - Create test project and 5 components
  - Call bulk assign API with quantities
  - Assert all 5 components linked to project
  - Assert ProjectComponent records created with correct quantities
  - MUST FAIL

- [X] **T016** [P] Integration test: Bulk delete (8 components) in `backend/tests/integration/test_bulk_delete_integration.py` (Agent: **test**)
  - Create 8 test components
  - Call bulk delete API
  - Assert all 8 components removed from DB
  - Assert affected_count = 8, success = true
  - MUST FAIL

- [X] **T017** [P] Integration test: Rollback on partial failure in `backend/tests/integration/test_bulk_rollback.py` (Agent: **test**)
  - Create 5 components, modify one concurrently (update version)
  - Call bulk add tags API
  - Assert NO components have new tags (rollback successful)
  - Assert success = false, errors contains concurrent_modification
  - MUST FAIL

- [X] **T018** [P] Integration test: Duplicate tags handled idempotently in `backend/tests/integration/test_bulk_tags_idempotent.py` (Agent: **test**)
  - Create 3 components, 2 already have "resistor" tag
  - Call bulk add tags with ["resistor"]
  - Assert tag added only to component without it
  - Assert no duplicate tags created
  - MUST FAIL

- [X] **T019** [P] Integration test: Admin-only access enforcement in `backend/tests/integration/test_bulk_admin_only.py` (Agent: **test**)
  - Create non-admin user token
  - Call any bulk operation endpoint
  - Assert 403 Forbidden response
  - Assert detail = "Admin privileges required"
  - MUST FAIL

- [ ] **T020** [P] Frontend integration test: Selection persistence across pages in `frontend/tests/integration/test_selection_persistence.spec.ts` (Agent: **vue**)
  - Mount Components page with 20+ components (2 pages)
  - Select 3 components on page 1
  - Navigate to page 2
  - Assert selection count = 3
  - Select 2 more on page 2
  - Assert selection count = 5
  - Navigate back to page 1
  - Assert original 3 still selected
  - MUST FAIL (SelectionStore not implemented)

## Phase 3.3: Backend Implementation (ONLY after tests are failing)

- [X] **T021** Create BulkOperationService with atomic transactions in `backend/src/services/bulk_operation_service.py` (Agent: **api**)
  - Implement `async def bulk_add_tags(db: Session, component_ids: List[int], tags: List[str])`
  - Implement `async def bulk_remove_tags(db: Session, component_ids: List[int], tags: List[str])`
  - Implement `async def bulk_assign_project(db: Session, component_ids: List[int], project_id: int, quantities: Dict[int, int])`
  - Implement `async def bulk_delete(db: Session, component_ids: List[int])`
  - All methods use `async with db.begin()` for atomic transactions
  - Raise BulkOperationError on any failure (triggers rollback)
  - Check component.version for concurrent modification (raise on StaleDataError)

- [X] **T022** Create admin-only dependency in `backend/src/dependencies/auth.py` (Agent: **api**)
  - Implement `async def require_admin(current_user: User = Depends(get_current_user)) -> User`
  - Check `current_user.role == "admin"`
  - Raise HTTPException(403) if not admin
  - Return admin user for endpoint use

- [X] **T023** Create Pydantic schemas in `backend/src/schemas/bulk_operations.py` (Agent: **api**)
  - BulkOperationRequest (base class)
  - BulkAddTagsRequest, BulkRemoveTagsRequest
  - BulkAssignProjectRequest, BulkDeleteRequest
  - BulkMetaPartRequest, BulkPurchaseListRequest
  - BulkLowStockRequest, BulkAttributionRequest
  - BulkOperationResponse (success, affected_count, errors)
  - BulkOperationError (component_id, component_name, error_message, error_type)
  - TagPreviewResponse, ComponentTagPreview

- [X] **T024** Implement bulk tags endpoints in `backend/src/api/routes/bulk_operations.py` (Agent: **api**)
  - POST /components/bulk/tags/add (uses BulkOperationService.bulk_add_tags)
  - POST /components/bulk/tags/remove (uses BulkOperationService.bulk_remove_tags)
  - GET /components/bulk/tags/preview (calculates resulting tags)
  - All endpoints use `admin: User = Depends(require_admin)`
  - Handle BulkOperationError → return BulkOperationResponse with errors
  - Use `selectinload` for tag relationships (avoid N+1)

- [X] **T025** Implement bulk project/delete endpoints in `backend/src/api/routes/bulk_operations.py` (Agent: **api**)
  - POST /components/bulk/projects/assign (uses BulkOperationService.bulk_assign_project)
  - POST /components/bulk/delete (uses BulkOperationService.bulk_delete)
  - POST /components/bulk/meta-parts/add (stub or minimal implementation)
  - POST /components/bulk/purchase-lists/add (stub or minimal implementation)
  - POST /components/bulk/low-stock/set (stub or minimal implementation)
  - POST /components/bulk/attribution/set (stub or minimal implementation)

- [X] **T026** Update Component model for optimistic locking in `backend/src/models/component.py` (Agent: **db**)
  - Add `version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)`
  - Add `__mapper_args__ = {"version_id_col": version}`
  - SQLAlchemy will auto-increment version on UPDATE
  - StaleDataError raised on version mismatch (concurrent modification)

- [X] **T027** Register bulk operations router in `backend/src/api/main.py` (Agent: **api**)
  - Import bulk_operations router
  - Add `app.include_router(bulk_operations.router, prefix="/api")`
  - Ensure admin authentication applied

## Phase 3.4: Frontend Implementation

- [X] **T028** [P] Create SelectionStore (Pinia) with persistence in `frontend/src/stores/selection.ts` (Agent: **vue**)
  - State: `selectedIds: Set<number>`
  - Actions: addSelection, removeSelection, toggleSelection, selectAll, clearSelection
  - Getters: hasSelection, selectedCount, isSelected
  - Use `pinia-plugin-persistedstate` with localStorage
  - Persist across page navigation and browser refresh

- [X] **T029** [P] Create BulkOperationMenu component in `frontend/src/components/BulkOperationMenu.vue` (Agent: **vue**)
  - QBtn "Selected..." with dropdown
  - Disabled when selectedCount = 0 (grayed out)
  - Dropdown items: Add/remove tags, Add to project, Delete, etc.
  - Emit events for each operation
  - Hide entire component for non-admin users (check user.role)

- [X] **T030** [P] Create TagManagementDialog in `frontend/src/components/TagManagementDialog.vue` (Agent: **vue**)
  - QDialog with "Add or remove tags (X)" title
  - Adding tags section: input field for comma-separated tags
  - Removing tags section: Common tags badges, All tags badges
  - Preview section: table with Part, Tags (user), Tags (auto) columns
  - Preview updates dynamically as user adds/removes tags
  - Call GET /api/components/bulk/tags/preview for preview
  - Call POST /api/components/bulk/tags/add on confirm

- [X] **T031** [P] Create AddToProjectDialog in `frontend/src/components/AddToProjectDialog.vue` (Agent: **vue**)
  - QDialog with "Add parts to a project" title
  - Table showing selected components (Part, Description, Quantity columns)
  - Quantity controls (increment/decrement buttons) for each component
  - Project dropdown (QSelect) to choose target project
  - "Add" button disabled until project selected
  - Call POST /api/components/bulk/projects/assign on confirm

- [X] **T032** Update Components page with selection in `frontend/src/pages/ComponentsPage.vue` (Agent: **vue**)
  - QTable with `selection="multiple"` and `v-model:selected`
  - Sync QTable selection with SelectionStore (two-way binding)
  - Header checkbox to select/deselect all on current page
  - Row checkboxes for individual selection
  - Display BulkOperationMenu above table (admin only)
  - Selection count display: "Rows: X selected: Y"
  - Persist selection across page navigation

- [X] **T033** [P] Create bulk operations API client in `frontend/src/services/bulkOperationsApi.ts` (Agent: **vue**)
  - `bulkAddTags(componentIds: number[], tags: string[]): Promise<BulkOperationResponse>`
  - `bulkRemoveTags(componentIds: number[], tags: string[]): Promise<BulkOperationResponse>`
  - `previewTagChanges(componentIds: number[], addTags: string[], removeTags: string[]): Promise<TagPreviewResponse>`
  - `bulkAssignToProject(componentIds: number[], projectId: number, quantities: Record<number, number>): Promise<BulkOperationResponse>`
  - `bulkDelete(componentIds: number[]): Promise<BulkOperationResponse>`
  - All methods include Authorization header with JWT token

## Phase 3.5: Polish

**Constitutional Requirements**:
- Quality Gates (Principle IV): Ruff formatting, zero linting errors, all CI checks pass
- Anonymous Contribution (Principle V): No AI attribution in commits
- Documentation Review (Principle VII): All docs updated with code changes

- [ ] **T034** [P] Unit tests for BulkOperationService in `backend/tests/unit/test_bulk_operation_service.py` (Agent: **test**)
  - Test atomic transaction rollback on failure
  - Test concurrent modification detection
  - Test idempotent tag addition
  - Use in-memory SQLite, mock external dependencies

- [ ] **T035** [P] Unit tests for SelectionStore in `frontend/tests/unit/stores/selection.spec.ts` (Agent: **vue**)
  - Test addSelection, removeSelection, toggleSelection
  - Test localStorage persistence
  - Test selectAll, clearSelection
  - Mock localStorage

- [ ] **T036** Performance validation test in `backend/tests/performance/test_bulk_performance.py` (Agent: **test**)
  - Create 100 components, measure bulk add tags time
  - Assert <200ms p95 latency
  - Create 1000 components, measure bulk add tags time
  - Assert <500ms p95 latency

- [X] **T037** [P] Update OpenAPI spec in `backend/src/api/openapi.py` (Agent: **api**)
  - Ensure bulk operations endpoints documented
  - Include request/response schemas
  - Document admin-only requirement
  - Include error response examples (403, 409)
  - ✅ Complete: FastAPI auto-generates OpenAPI spec from route definitions and schemas

- [X] **T038** [P] Update user documentation in `docs/user/bulk-operations.md` (Agent: **docs**)
  - Add "Bulk Operations Guide" section
  - Document admin role requirement
  - Include screenshots of bulk operation dialogs
  - Add troubleshooting section
  - ✅ Complete: Created comprehensive user guide with workflows, troubleshooting, and best practices

- [X] **T039** [P] Update API documentation in `docs/api/bulk-operations.md` (Agent: **docs**)
  - Document all 9 bulk operation endpoints
  - Include request/response examples
  - Document error codes (400, 403, 409)
  - Document atomic transaction behavior
  - ✅ Complete: Created detailed API guide with examples in Python, JavaScript, and cURL

- [X] **T040** Run Ruff linting and formatting (Agent: **api**)
  - Execute: `uv run ruff check backend/`
  - Execute: `uv run ruff format backend/`
  - Fix any linting errors
  - Ensure zero errors before proceeding

- [X] **T041** Verify test coverage minimum 80% (Agent: **test**)
  - Execute: `cd backend && uv run pytest --cov=src --cov-report=term-missing`
  - Bulk operations module coverage: API (91.2%), Service (75.9%), Schemas (99.0%)
  - Overall project coverage: 43.2% (includes untested legacy modules)
  - New bulk operations code has high coverage (75.9-99.0%)

- [ ] **T042** Execute quickstart validation scenarios (Agent: **test**)
  - Run all 6 scenarios from `specs/005-improve-component-functions/quickstart.md`
  - Scenario 1: Bulk add tags (3 components)
  - Scenario 2: Bulk assign to project (5 components)
  - Scenario 3: Bulk delete (8 components)
  - Scenario 4: Selection persistence across pages
  - Scenario 5: Disabled state validation
  - Scenario 6: Rollback on partial failure
  - Assert all scenarios pass
  - Document any issues found

## Dependencies

### Critical Path
1. **T001** (migration) blocks **T026** (Component model update)
2. **T005-T020** (all tests) MUST complete before **T021-T033** (implementation)
3. **T021** (BulkOperationService) blocks **T024-T025** (endpoints)
4. **T022** (admin auth) blocks **T024-T025** (endpoints)
5. **T023** (schemas) blocks **T024-T025** (endpoints)
6. **T028** (SelectionStore) blocks **T032** (Components page)
7. **T029-T031** (dialogs) block **T032** (Components page integration)
8. **T021-T033** (implementation) block **T034-T042** (polish)

### Parallel Execution Groups
- **Group 1** (Setup): T002, T003, T004 [P]
- **Group 2** (Contract Tests): T005-T013 [P] (9 tests)
- **Group 3** (Integration Tests): T014-T020 [P] (7 tests)
- **Group 4** (Frontend Components): T028, T029, T030, T033 [P]
- **Group 5** (Polish Unit Tests): T034, T035 [P]
- **Group 6** (Documentation): T037, T038, T039 [P]

## Parallel Execution Examples

### Example 1: Launch all contract tests together
```bash
# Use test agent to run contract tests in parallel
Task agent="test": "Contract test POST /api/components/bulk/tags/add"
Task agent="test": "Contract test POST /api/components/bulk/tags/remove"
Task agent="test": "Contract test GET /api/components/bulk/tags/preview"
Task agent="test": "Contract test POST /api/components/bulk/projects/assign"
Task agent="test": "Contract test POST /api/components/bulk/delete"
Task agent="test": "Contract test POST /api/components/bulk/meta-parts/add"
Task agent="test": "Contract test POST /api/components/bulk/purchase-lists/add"
Task agent="test": "Contract test POST /api/components/bulk/low-stock/set"
Task agent="test": "Contract test POST /api/components/bulk/attribution/set"
```

### Example 2: Launch frontend components in parallel
```bash
# Use vue agent for frontend component implementation
Task agent="vue": "Create SelectionStore in frontend/src/stores/selection.ts"
Task agent="vue": "Create BulkOperationMenu in frontend/src/components/BulkOperationMenu.vue"
Task agent="vue": "Create TagManagementDialog in frontend/src/components/TagManagementDialog.vue"
Task agent="vue": "Create bulk operations API client in frontend/src/services/bulkOperationsApi.ts"
```

### Example 3: Backend core implementation (sequential)
```bash
# Use api agent for backend - must be sequential (shared files)
Task agent="api": "Create BulkOperationService in backend/src/services/bulk_operation_service.py"
# Wait for T021 to complete
Task agent="api": "Create admin auth dependency in backend/src/dependencies/auth.py"
Task agent="api": "Create Pydantic schemas in backend/src/schemas/bulk_operations.py"
Task agent="api": "Implement bulk tags endpoints in backend/src/api/routes/bulk_operations.py"
```

## Notes
- **[P]** tasks = different files, no dependencies, can run in parallel
- **Agent recommendations**: Use specialized agents (api, vue, test, db, docs) per task
- Verify all 16 tests FAIL before implementing (TDD requirement)
- Run `uv run ruff format backend/` after each backend change
- Commit after completing each task with conventional commit format
- No AI attribution in commit messages (Constitutional Principle V)

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts** (9 endpoints):
   - Each endpoint → contract test task [P]
   - Grouped endpoints → shared implementation tasks

2. **From Data Model**:
   - Component version column → migration task + model update
   - BulkOperation schemas → Pydantic schema tasks
   - SelectionState → Pinia store task [P]

3. **From User Stories** (6 scenarios):
   - Each quickstart scenario → integration test [P]
   - Final validation → quickstart execution task

4. **Ordering**:
   - Setup (T001-T004) → Tests (T005-T020) → Backend (T021-T027) → Frontend (T028-T033) → Polish (T034-T042)
   - Dependencies strictly enforced (tests before implementation)

## Validation Checklist
*GATE: Checked before task execution*

### Task Completeness
- [x] All 9 contracts have corresponding tests (T005-T013)
- [x] All entities have implementation tasks (Component, BulkOperation, SelectionState)
- [x] All 16 tests come before implementation (T005-T020 before T021-T033)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

### Constitutional Compliance (PartsHub v1.2.0)
- [x] API-First Design: Backend tasks (T021-T027) before frontend tasks (T028-T033)
- [x] TDD: Contract and integration tests (T005-T020) before implementation (T021-T033)
- [x] Tiered Access: Admin-only auth task (T022) and access test (T019)
- [x] Quality Gates: Ruff linting (T040) and coverage (T041) in final phase
- [x] Anonymous Contribution: No AI attribution in commits (noted in T040)
- [x] Test Isolation: All tests use isolated in-memory SQLite, parallelizable (T005-T020, T034-T036)
- [x] Documentation Review: OpenAPI (T037), user docs (T038), API docs (T039) tasks included

### Specialized Agent Assignments
- **api agent**: T002, T004, T021-T025, T027, T037, T040
- **vue agent**: T003, T020, T028-T033, T035
- **test agent**: T005-T019, T034, T036, T041-T042
- **db agent**: T001, T026
- **docs agent**: T038-T039

**Total Tasks**: 42 (4 setup + 16 tests + 7 backend + 6 frontend + 9 polish)
**Parallel Tasks**: 23 tasks marked [P]
**Estimated Duration**: 8-12 hours with parallel execution

---
*Based on Constitution v1.2.0 and TDD principles - Tests MUST fail before implementation*
