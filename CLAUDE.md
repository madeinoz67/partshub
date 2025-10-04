# partshub Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-27

## Active Technologies
- Python 3.11+ with FastAPI backend
- Vue.js 3 with Quasar Framework frontend
- SQLite database with SQLAlchemy ORM
- UV for Python package management
- Consolidated pyproject.toml structure
- YAML (GitHub Actions), Shell scripting, Python 3.11+ (for tooling) + GitHub Actions, Docker, MkDocs, pytest, ruff, uv, Node.js/npm (002-github-workflows)
- GitHub Container Registry, GitHub Artifacts, GitHub Pages (002-github-workflows)
- GitHub Actions YAML workflows, Python 3.11+ (backend), Node.js 18+ (frontend) + GitHub Actions ecosystem, Mike (docs versioning), Release Please (release automation), Docker/GitHub Container Registry (002-github-workflows)
- YAML workflow files in `.github/workflows/`, GitHub Container Registry for Docker images (002-github-workflows)
- Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend) + FastAPI, SQLAlchemy, Pydantic (backend), Quasar Framework, Pinia (frontend) (003-location-improvements-as)
- SQLite database with SQLAlchemy ORM (existing storage_locations table) (003-location-improvements-as)
- Markdown, MkDocs (Python 3.11 for docs server) + MkDocs, Docker, existing PartsHub infrastructure (004-docker-and-user)
- N/A - Documentation files only (004-docker-and-user)
- Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend) + FastAPI, SQLAlchemy, Pydantic (backend); Quasar Framework, Pinia (frontend) (005-improve-component-functions)
- SQLite with SQLAlchemy ORM (existing components, projects, tags tables) (005-improve-component-functions)

## Project Structure
```
pyproject.toml     # Consolidated Python dependencies and configuration
backend/           # FastAPI backend with src/models/, src/api/, src/services/
frontend/          # Vue.js frontend with components/, pages/, services/
docs/              # MkDocs documentation
Makefile           # Development workflow commands
```

## Commands
```bash
make install       # Install all dependencies (Python + Node.js)
make dev          # Start backend + frontend + docs servers
make test         # Run backend tests with pytest
make lint         # Run ruff on backend code
make docs         # Start documentation server
```

## Code Style
- Use `uv run` commands from project root for Python tools
- Backend commands: `cd backend && uv run --project .. <command>`
- Follow ruff and black formatting standards
- Use consolidated dependency management

## Pre-Commit Guidelines

- **ALWAYS run ruff before committing**: `uv run ruff check backend/` and `uv run ruff format backend/`
- Ensure zero linting errors and proper formatting before pushing changes
- Use `uv run ruff check --fix backend/` to auto-fix common issues
- Run tests locally: `cd backend && uv run pytest`

## Recent Changes
- 005-improve-component-functions: Added Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend) + FastAPI, SQLAlchemy, Pydantic (backend); Quasar Framework, Pinia (frontend)
- 004-docker-and-user: Added Markdown, MkDocs (Python 3.11 for docs server) + MkDocs, Docker, existing PartsHub infrastructure
- 003-location-improvements-as: Added Python 3.11+ (backend), Vue.js 3 with TypeScript (frontend) + FastAPI, SQLAlchemy, Pydantic (backend), Quasar Framework, Pinia (frontend)


<!-- MANUAL ADDITIONS START -->

## Specialized Agents (NON-NEGOTIABLE)
ALWAYS use specialized agents for domain-specific tasks (testing, database, security, etc.). All agents MUST follow the project constitution, including isolated testing principles:

- Use in-memory SQLite (`sqlite:///:memory:`) for all tests (see `backend/tests/conftest.py`)
- Never modify production databases during testing
- Ensure tests are self-contained and repeatable
- Follow all testing guidelines in project constitution
- Database fixtures automatically create/destroy tables per test

## Anonymous Contribution (NON-NEGOTIABLE)
All commits, pull requests, and git history MUST NOT contain references to AI assistants, automated tools, or external contributors in commit messages, co-author tags, or acknowledgments. Contributions MUST appear as originating from human project members only. Generated code markers and tool acknowledgments are prohibited in version control.

**Implementation**:

- NEVER use commit messages like "Generated with Claude Code" or "Co-Authored-By: Claude"
- Remove any AI acknowledgment footers before committing
- Use standard commit message format without tool attribution
- Focus commit messages on the actual changes, not the process used to create them

## Git Workflow (NON-NEGOTIABLE)

**Commit Early, Commit Often**:
- Commit after completing each logical unit of work (not just at end of session)
- Push to remote regularly to prevent data loss and enable collaboration
- Use conventional commit format: `type(scope): description` (e.g., `feat(bulk-ops): add tag management service`)
- Atomic commits: Each commit should represent one cohesive change

**When to Commit**:
- After completing each task from tasks.md
- After fixing a bug or implementing a feature
- Before switching to a different task or feature
- After making significant progress (don't wait for "perfect")
- At natural breakpoints (end of function, end of test suite, etc.)

**Push Regularly**:
- Push after every 2-3 commits (or sooner for important changes)
- Always push before ending a work session
- Push immediately after completing a major milestone
- Use `git push` or `git push -u origin <branch-name>` for new branches

<!-- MANUAL ADDITIONS END -->
