
# Implementation Plan: MVP Electronic Parts Management Application

**Branch**: `001-mvp-electronic-parts` | **Date**: 2025-09-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mvp-electronic-parts/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
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
Build a comprehensive electronic parts inventory management system for hobbyists/makers that mimics PartsBox.io functionality. The system will track 10-10,000 electronic components with specifications, quantities, hierarchical storage locations, and project allocation. Key features include barcode scanning, component data provider integration (LCSC, Octopart, etc.), KiCad integration, and comprehensive reporting dashboard.

## Technical Context
**Language/Version**: Python 3.11+ with FastAPI web framework
**Primary Dependencies**: FastAPI, SQLAlchemy, SQLite, Vue.js 3, Quasar Framework, pyzbar (barcode scanning), uv (package management)
**Storage**: SQLite with JSON fields for flexible component specifications
**Testing**: pytest + FastAPI TestClient for backend, Vue Test Utils for frontend
**Target Platform**: Self-contained web application for desktop/hobbyist environments
**Project Type**: web - frontend + backend with API
**Performance Goals**: Support search/filter across 10,000 components <1 second, UI responsiveness <200ms
**Constraints**: Self-contained installation, offline-capable core features, minimal system requirements
**Scale/Scope**: Single-user initially, 10-10,000 components, extensible architecture for future multi-user

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Specification-Driven Development**: ✅ PASS
- Complete specification exists with user scenarios, functional requirements, and acceptance criteria
- Requirements are business-focused and technology-agnostic
- All clarifications have been resolved

**II. Test-Driven Development**: ✅ PASS
- Planning approach includes contract tests, integration tests, and unit tests
- TDD methodology will be followed: tests before implementation
- Test-first approach documented in Phase 1 contracts

**III. Incremental Design & Planning**: ✅ PASS
- Following systematic phases: Research → Design → Contracts → Task Generation
- Constitution compliance checks at each gate
- Phase-by-phase approach prevents over-engineering

**IV. Library-First Architecture**: ✅ PASS
- Modular design with clear separation of concerns
- Component data providers designed as pluggable interfaces
- Storage, authentication, and reporting designed as standalone libraries

**V. CLI-Centric Interface**: ✅ PASS
- Core functionality will be exposed through CLI interfaces
- JSON and human-readable output formats planned
- API-first design enables automation and testing

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
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 (Web application) - frontend for UI, backend for API and business logic

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
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design documents (data-model.md, contracts/, quickstart.md)
- Extract specific task categories:
  * **Setup Tasks**: Python/FastAPI project structure, Docker configuration, database setup
  * **Contract Tests**: API endpoint tests from OpenAPI specs (components-api.yaml, storage-api.yaml, kicad-api.yaml)
  * **Data Model Tasks**: SQLAlchemy models from data-model.md entities
  * **Core Implementation**: API endpoints, business logic, authentication
  * **Integration Tasks**: Component data providers (LCSC), KiCad integration, barcode scanning
  * **Frontend Tasks**: Vue.js/Quasar UI components and pages
  * **Validation Tests**: Integration scenarios from quickstart.md

**Specific Task Derivation**:

From **contracts/** directory:
- `components-api.yaml` → 8 endpoint contract tests [P]
- `storage-api.yaml` → 6 endpoint contract tests [P]
- `kicad-api.yaml` → 5 endpoint contract tests [P]

From **data-model.md** entities:
- Component model + validation → model creation task [P]
- StorageLocation model + hierarchy → model creation task [P]
- Project, StockTransaction, Purchase models → model creation tasks [P]
- Provider integration models → model creation tasks [P]

From **quickstart.md** scenarios:
- User authentication flow → integration test [P]
- Component CRUD operations → integration test [P]
- Storage bulk creation → integration test [P]
- Project allocation workflow → integration test [P]
- Provider data import → integration test [P]
- KiCad synchronization → integration test [P]

**Ordering Strategy**:
1. **Setup Phase**: Project structure, dependencies, database
2. **Tests-First Phase**: All contract tests must be written and failing
3. **Models Phase**: Core data models with relationships [P]
4. **Services Phase**: Business logic and data access layers
5. **API Phase**: FastAPI endpoint implementations
6. **Integration Phase**: External provider integrations
7. **Frontend Phase**: Vue.js components and pages [P where independent]
8. **Validation Phase**: End-to-end integration tests

**Parallel Execution Opportunities**:
- Contract tests (different API endpoints) [P]
- Data model creation (independent entities) [P]
- Frontend components (different pages/features) [P]
- Provider integrations (LCSC, Octopart interfaces) [P]

**Estimated Task Count**: 35-40 numbered, dependency-ordered tasks

**Technology-Specific Tasks**:
- FastAPI application setup with OpenAPI auto-generation
- SQLite database with SQLAlchemy ORM and Alembic migrations (chosen for self-contained deployment)
- JWT authentication with tiered access (anonymous, admin, API tokens)
- Vue.js 3 + Quasar Framework frontend with responsive design
- Docker Compose for self-contained deployment
- Component data provider plugin architecture
- Barcode scanning integration (pyzbar + browser APIs)
- KiCad library export functionality

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
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
