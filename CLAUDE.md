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

- 002-github-workflows: Added GitHub Actions YAML workflows, Python 3.11+ (backend), Node.js 18+ (frontend) + GitHub Actions ecosystem, Mike (docs versioning), Release Please (release automation), Docker/GitHub Container Registry
- 002-github-workflows: Added YAML (GitHub Actions), Shell scripting, Python 3.11+ (for tooling) + GitHub Actions, Docker, MkDocs, pytest, ruff, uv, Node.js/npm
- 2025-09-27: Consolidated pyproject.toml structure for unified version management

<!-- MANUAL ADDITIONS START -->

## Anonymous Contribution (NON-NEGOTIABLE)
All commits, pull requests, and git history MUST NOT contain references to AI assistants, automated tools, or external contributors in commit messages, co-author tags, or acknowledgments. Contributions MUST appear as originating from human project members only. Generated code markers and tool acknowledgments are prohibited in version control.

**Implementation**:

- NEVER use commit messages like "Generated with Claude Code" or "Co-Authored-By: Claude"
- Remove any AI acknowledgment footers before committing
- Use standard commit message format without tool attribution
- Focus commit messages on the actual changes, not the process used to create them

<!-- MANUAL ADDITIONS END -->
