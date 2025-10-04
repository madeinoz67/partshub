# PartsHub Constitution

<!--
SYNC IMPACT REPORT
==================
Version Change: 1.1.0 → 1.2.0
Action: Add Documentation Review principle
Amendment Date: 2025-10-02

Core Principles:
  1. API-First Design (unchanged)
  2. Test-Driven Development (TDD) - NON-NEGOTIABLE (unchanged)
  3. Tiered Access Control (unchanged)
  4. Quality Gates & Standards (unchanged)
  5. Anonymous Contribution - NON-NEGOTIABLE (unchanged)
  6. Test Isolation - NON-NEGOTIABLE (unchanged)
  7. Documentation Review - NON-NEGOTIABLE (NEW)

Added Sections:
  - Principle VII: Documentation Review

Modified Sections:
  - None (existing principles unchanged)

Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md (Constitution Check section - add Principle VII)
  ✅ .specify/templates/spec-template.md (Constitutional Alignment section updated)
  ✅ .specify/templates/tasks-template.md (Add documentation review task phase)

Version Bump Rationale:
  MINOR (1.1.0 → 1.2.0) - New principle added, backward compatible

Follow-up Actions:
  - Update plan-template.md Constitution Check section with Principle VII
  - Update tasks-template.md to include documentation review phase
  - Update spec-template.md Constitutional Alignment checklist

Last Updated: 2025-10-02
-->

## Core Principles

### I. API-First Design

Every feature MUST expose functionality via RESTful API before frontend implementation. All APIs MUST be documented using OpenAPI/Swagger specifications. Backend endpoints are the source of truth for functionality.

**Rationale**: Ensures consistent access patterns, enables API-first development, supports future integrations, and maintains clear separation between backend logic and frontend presentation.

**Rules**:
- Backend API implementation MUST be completed before frontend work begins
- All endpoints MUST include OpenAPI documentation
- API responses MUST follow consistent JSON schema patterns
- Breaking API changes require MAJOR version bump

### II. Test-Driven Development (TDD) - NON-NEGOTIABLE

Tests MUST be written before implementation. Follow strict Red-Green-Refactor cycle: write failing test → get user approval → implement to pass → refactor. Minimum 80% code coverage required.

**Rationale**: Prevents regression, ensures specifications are testable, documents expected behavior, and catches bugs before production.

**Rules**:
- Contract tests MUST be written for all API endpoints before implementation
- Integration tests MUST cover all user stories
- Unit tests MUST be added for complex business logic
- Tests MUST fail before implementation begins
- All tests MUST pass before merging to main branch
- Coverage below 80% blocks merge

### III. Tiered Access Control

Three access levels MUST be enforced: Anonymous (read-only), Authenticated (CRUD operations), and Admin (system administration). Security and authentication MUST be implemented by default, not added later.

**Rationale**: Balances accessibility with security, enables public browsing while protecting data integrity, provides clear permission boundaries.

**Rules**:
- Anonymous users: Read-only access to all inventory data
- Authenticated users: Full CRUD operations on components and storage
- Admin users: API token management and system administration
- All authenticated endpoints MUST verify JWT tokens
- Passwords MUST be hashed with bcrypt
- API tokens MUST be revocable

### IV. Quality Gates & Standards

All code MUST pass automated quality checks before merging. Ruff formatting and linting are mandatory. Direct pushes to main branch are prohibited.

**Rationale**: Maintains consistent code quality, prevents technical debt, ensures readability, and enforces best practices.

**Rules**:
- MUST run `uv run ruff check backend/` and `uv run ruff format backend/` before committing
- MUST achieve zero linting errors before pushing
- MUST pass all CI checks (backend tests, frontend tests, security scans, Docker builds)
- MUST use branch protection on main branch
- MUST require pull request reviews before merging
- MUST use conventional commit messages

### V. Anonymous Contribution - NON-NEGOTIABLE

All commits, pull requests, and git history MUST NOT contain references to AI assistants, automated tools, or external contributors. Contributions MUST appear as originating from human project members only.

**Rationale**: Maintains professional git history, focuses on code changes rather than development process, ensures commit messages are actionable and clear.

**Rules**:
- NEVER use commit messages like "Generated with Claude Code" or "Co-Authored-By: Claude"
- NEVER include AI acknowledgment footers in commits
- MUST use standard commit message format without tool attribution
- MUST focus commit messages on actual changes, not the process used to create them
- Generated code markers and tool acknowledgments are prohibited in version control

### VI. Test Isolation - NON-NEGOTIABLE

Tests MUST be completely isolated with no shared state, external dependencies, or side effects. Each test MUST be independently executable in any order. Database state MUST be reset between tests.

**Rationale**: Ensures test reliability, prevents flaky tests, enables parallel execution, makes tests reproducible, and simplifies debugging by eliminating test interdependencies.

**Rules**:
- Each test MUST use isolated database (in-memory SQLite or transaction rollback)
- Tests MUST NOT depend on execution order or other tests
- External services MUST be mocked or use test doubles
- Test fixtures MUST be created fresh for each test
- Database state MUST be cleaned/reset after each test
- Tests MUST be runnable in parallel without conflicts
- Shared test utilities allowed, but NO shared mutable state
- Integration tests MAY use test database with proper cleanup

### VII. Documentation Review - NON-NEGOTIABLE

All documentation MUST be reviewed and updated when code changes affect documented behavior, APIs, or workflows. Documentation updates MUST be included in the same pull request as code changes.

**Rationale**: Prevents documentation drift, ensures developers have accurate information, reduces onboarding friction, and maintains documentation as a reliable source of truth. Outdated documentation is worse than no documentation.

**Rules**:
- Code changes MUST include corresponding documentation updates in the same PR
- API endpoint changes MUST update OpenAPI specifications
- Configuration changes MUST update README or setup guides
- New features MUST include usage documentation before merging
- Breaking changes MUST document migration paths
- Pull request reviews MUST verify documentation completeness
- Documentation changes trigger docs deployment
- Feature specs (spec.md, plan.md) MUST be updated if implementation diverges

## Technology Stack Requirements

**Backend**:
- Python 3.11+ with FastAPI framework
- SQLAlchemy ORM with SQLite database (production may use PostgreSQL)
- Alembic for database migrations
- UV for Python package management
- Pydantic for data validation
- JWT authentication with bcrypt
- pytest with pytest-asyncio for async testing
- In-memory SQLite for test isolation

**Frontend**:
- Vue.js 3 with Composition API
- TypeScript for type safety
- Quasar Framework for UI components
- Pinia for state management
- Vue Router for navigation

**Development Tools**:
- Ruff for Python linting and formatting
- pytest for backend testing
- Vitest for frontend testing
- MkDocs for documentation
- Docker for containerization

**Project Structure**:
- Consolidated `pyproject.toml` at repository root
- Backend code in `backend/src/`
- Frontend code in `frontend/src/`
- Shared documentation in `docs/`
- Makefile for common development workflows

## Development Workflow Standards

**Commands** (via Makefile):
- `make install` - Install all dependencies (Python + Node.js)
- `make dev` - Start backend + frontend + docs servers
- `make test` - Run backend tests with pytest
- `make lint` - Run ruff on backend code
- `make docs` - Start documentation server

**Python Execution**:
- MUST use `uv run` commands from project root
- Backend commands: `cd backend && uv run --project .. <command>`
- Follow consolidated dependency management in `pyproject.toml`

**Pre-Commit Requirements**:
- Run `uv run ruff check backend/` and `uv run ruff format backend/`
- Ensure zero linting errors
- Run tests locally: `cd backend && uv run pytest`
- Use `uv run ruff check --fix backend/` to auto-fix issues

**Database Migrations**:
- MUST use Alembic for all schema changes
- Migration naming: `YYYYMMDD_HHMM_<description>.py`
- Test migrations on SQLite before PostgreSQL
- Include both upgrade and downgrade paths

**Test Execution**:
- Run tests with: `cd backend && uv run pytest -v`
- Run parallel tests: `cd backend && uv run pytest -n auto`
- Run with coverage: `cd backend && uv run pytest --cov=src --cov-report=term-missing`
- Each test file MUST be independently executable

## CI/CD & Deployment Policies

**Continuous Integration**:
- Triggers on every push and pull request
- Required checks: Backend tests, Frontend tests, Security scans, Docker builds
- All checks MUST pass before merging
- Minimum 80% test coverage enforced
- Tests run in parallel for speed
- Duration target: <10 minutes

**Continuous Deployment**:
- Automatic deployment on main branch merges
- Deployment order: Backend → Frontend → Documentation
- Health checks required after deployment
- Rollback automation on failure
- Manual override available for emergencies

**Release Process**:
- Semantic versioning (MAJOR.MINOR.PATCH)
- Automated release creation on git tags (v1.0.0)
- Docker images pushed to GitHub Container Registry
- Versioned documentation deployed to GitHub Pages
- Release notes auto-generated from commit history

**Branch Protection**:
- Main branch MUST require pull request reviews
- MUST pass all status checks before merge
- MUST be up-to-date with base branch
- Direct pushes to main are prohibited
- Force pushes to main are prohibited

## Governance

This constitution supersedes all other development practices and guidelines. Any deviation from these principles MUST be explicitly justified in pull request descriptions and approved by project maintainers.

**Amendment Process**:
- Amendments require documentation of rationale and impact
- Version bump according to change type (MAJOR/MINOR/PATCH)
- Update all dependent templates and documentation
- Migration plan required for breaking changes
- Approval required from project maintainers

**Compliance Review**:
- All pull requests MUST verify constitutional compliance
- Complexity additions MUST be justified with rationale
- Simpler alternatives MUST be documented when rejected
- Constitutional violations in legacy code MUST be tracked for remediation

**Runtime Guidance**:
- Use `CLAUDE.md` in repository root for agent-specific development guidance
- Constitution provides governance framework
- CLAUDE.md provides tactical implementation patterns
- Keep CLAUDE.md under 150 lines for token efficiency
- Update CLAUDE.md incrementally with each feature (O(1) operation)

**Version**: 1.2.0 | **Ratified**: 2025-10-02 | **Last Amended**: 2025-10-02
