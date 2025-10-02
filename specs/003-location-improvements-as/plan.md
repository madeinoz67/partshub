
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

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
[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context
**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on PartsHub Constitution v1.2.0:

### Principle I: API-First Design
- [x] Backend API endpoints defined before frontend work (POST /api/storage-locations/generate-preview, POST /api/storage-locations/bulk-create)
- [x] OpenAPI/Swagger documentation planned (FastAPI auto-generates OpenAPI specs)
- [x] API responses follow consistent JSON schema (Pydantic models for validation)
- [x] Breaking changes properly versioned (MAJOR bump) - new endpoints, no breaking changes

### Principle II: Test-Driven Development (TDD) - NON-NEGOTIABLE
- [x] Contract tests planned for all API endpoints (preview and bulk-create endpoints)
- [x] Integration tests planned for all user stories (8 acceptance scenarios + 5 edge cases)
- [x] Tests will be written BEFORE implementation (TDD workflow enforced)
- [x] 80% minimum coverage target established (pytest with coverage reporting)

### Principle III: Tiered Access Control
- [x] Access levels defined (Anonymous: read-only, Authenticated: create locations, Admin: N/A for this feature)
- [x] Authentication requirements specified (FR-024: authenticated users only, JWT validation)
- [x] JWT token validation planned where needed (all POST endpoints require authentication)
- [x] Security implemented by default, not retrofitted (authentication dependency from start)

### Principle IV: Quality Gates & Standards
- [x] Ruff linting and formatting will be applied (pre-commit requirement)
- [x] CI checks identified (backend tests, frontend tests, security scans, Docker builds)
- [x] No direct main branch commits (branch protection enforced)
- [x] Pull request review process followed (standard workflow)

### Principle V: Anonymous Contribution - NON-NEGOTIABLE
- [x] Commit messages will focus on changes, not tools (no AI attribution)
- [x] No AI assistant attribution in commits (constitutional requirement)
- [x] Standard conventional commit format used (conventional commits enforced)

### Principle VI: Test Isolation - NON-NEGOTIABLE
- [x] Tests use isolated database (in-memory SQLite for each test)
- [x] No test dependencies on execution order (independent test execution)
- [x] External services mocked or use test doubles (no external dependencies)
- [x] Database state reset between tests (pytest fixtures with cleanup)
- [x] Tests runnable in parallel (pytest -n auto support)

### Principle VII: Documentation Review - NON-NEGOTIABLE
- [x] Documentation updates planned for all code changes (OpenAPI specs, quickstart.md, README updates)
- [x] OpenAPI specs will be updated for API changes (contracts/location-layout-api.yaml)
- [x] README/setup guides will reflect configuration changes (no config changes in this feature)
- [x] Usage documentation will be included for new features (quickstart.md with 11 scenarios)
- [x] Migration paths documented for breaking changes (no breaking changes)

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
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

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

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
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

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
- [x] Phase 0: Research complete (/plan command) - research.md generated
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md generated
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command) - tasks.md to be created
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS - all 7 principles satisfied (including new Documentation Review)
- [x] Post-Design Constitution Check: PASS - no violations after Phase 1
- [x] All NEEDS CLARIFICATION resolved - no unknowns in Technical Context
- [x] Complexity deviations documented - none required, standard web app pattern

**Artifacts Generated**:
- [x] /specs/003-location-improvements-as/plan.md (this file)
- [x] /specs/003-location-improvements-as/research.md (10 technical decisions)
- [x] /specs/003-location-improvements-as/data-model.md (5 entities, 3 enums, migration)
- [x] /specs/003-location-improvements-as/contracts/location-layout-api.yaml (OpenAPI spec)
- [x] /specs/003-location-improvements-as/contracts/test_location_generation_contract.py (failing tests)
- [x] /specs/003-location-improvements-as/quickstart.md (11 test scenarios)
- [x] /CLAUDE.md updated (incremental context addition)

---
*Based on Constitution v1.2.0 - See `.specify/memory/constitution.md`*
