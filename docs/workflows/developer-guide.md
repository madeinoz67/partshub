# Developer Workflow Guide

This guide explains how to work with the automated GitHub workflows in the PartsHub project.

## Overview

The PartsHub project uses three main GitHub Actions workflows:

1. **CI (Continuous Integration)** - Runs on every push and PR
2. **CD (Continuous Deployment)** - Deploys to production on main branch
3. **Release** - Creates releases when tags are pushed

## Development Workflow

### 1. Feature Development

#### Starting a New Feature

```bash
# Create and switch to a new feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Commit your changes
git add .
git commit -m "feat: add new feature description"

# Push to remote
git push origin feature/your-feature-name
```

#### Creating a Pull Request

1. **Push your branch** to GitHub
2. **Create a PR** from your feature branch to `main`
3. **Wait for CI checks** to complete (should take ~5-10 minutes)
4. **Address any failures** by pushing additional commits
5. **Request review** from team members
6. **Merge** once approved and all checks pass

### 2. Understanding CI Workflow

The CI workflow automatically runs when you:
- Push commits to any branch
- Create or update a pull request to `main`

#### What CI Tests

**Backend Tests** (runs in parallel):
- Python linting with `ruff`
- Code formatting checks
- Type checking with `mypy`
- Unit and integration tests with `pytest`
- Code coverage validation (minimum 80%)

**Frontend Tests** (runs in parallel):
- JavaScript/TypeScript linting
- Unit tests with Vitest/Jest
- Build verification with Quasar

**Security Scan** (runs in parallel):
- Python dependency vulnerability scan with `safety`
- Security linting with `bandit`
- NPM audit for frontend dependencies

**Docker Build** (runs in parallel):
- Backend Docker image build verification
- Frontend Docker image build verification
- Container startup tests

#### CI Status Indicators

- ✅ **Green checkmark**: All tests passed
- ❌ **Red X**: Tests failed - click for details
- 🟡 **Yellow circle**: Tests are running
- ⚪ **Gray circle**: Tests pending or skipped

### 3. Deployment Process

#### Automatic Deployment

When you merge a PR to `main`:

1. **CI runs again** on the main branch
2. **CD workflow triggers** automatically after CI passes
3. **Backend deploys** to production
4. **Frontend deploys** after backend succeeds
5. **Documentation** is built and deployed
6. **Notifications** are sent via GitHub comments

#### Manual Emergency Deployment

For urgent fixes, you can trigger deployment manually:

1. Go to **Actions** tab in GitHub
2. Select **Continuous Deployment** workflow
3. Click **Run workflow**
4. Choose options:
   - Environment: `production`
   - Skip tests: Only for emergencies

### 4. Release Process

#### Creating a Release

1. **Update version** in `pyproject.toml`:
   ```toml
   [project]
   version = "1.2.3"
   ```

2. **Commit version update**:
   ```bash
   git add pyproject.toml
   git commit -m "bump: version to 1.2.3"
   git push origin main
   ```

3. **Create and push a git tag**:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

4. **Wait for Release workflow** to complete (~10-15 minutes)

#### What the Release Workflow Does

- ✅ **Validates** that tag matches `pyproject.toml` version
- ✅ **Builds** Docker images with version tags
- ✅ **Publishes** images to GitHub Container Registry
- ✅ **Creates** GitHub Release with auto-generated notes
- ✅ **Deploys** versioned documentation
- ✅ **Synchronizes** versions across all project files

## Best Practices

### Commit Messages

Use conventional commit format for automatic release notes:

```bash
# New features
git commit -m "feat: add user authentication"

# Bug fixes
git commit -m "fix: resolve login issue with special characters"

# Documentation
git commit -m "docs: update API documentation"

# Refactoring
git commit -m "refactor: simplify user service logic"

# Tests
git commit -m "test: add integration tests for payment flow"

# Breaking changes
git commit -m "feat!: change API response format"
```

### Branch Naming

Use descriptive branch names:

```bash
# Features
feature/user-authentication
feature/payment-integration

# Bug fixes
fix/login-error
fix/database-connection

# Documentation
docs/api-updates
docs/workflow-guide

# Refactoring
refactor/user-service
refactor/database-models
```

### Testing Locally

Before pushing, always test locally:

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test

# Linting
uv run ruff check .
cd frontend && npm run lint

# Docker build
docker build -t test-image .
```

### Code Review Guidelines

#### As an Author

1. **Test thoroughly** before creating PR
2. **Write descriptive** PR descriptions
3. **Keep PRs small** and focused
4. **Respond promptly** to review feedback
5. **Update documentation** if needed

#### As a Reviewer

1. **Check functionality** first
2. **Review for security** issues
3. **Ensure tests** are adequate
4. **Verify documentation** updates
5. **Test edge cases** mentioned

## Monitoring and Debugging

### Checking Workflow Status

```bash
# Install GitHub CLI
gh auth login

# List recent workflow runs
gh run list

# View details of a specific run
gh run view 1234567890

# Download logs for debugging
gh run download 1234567890
```

### Common Issues and Solutions

#### Tests Failing Locally But Passing in CI

- Check Python/Node versions match
- Ensure all dependencies are installed
- Verify environment variables are set correctly

#### Docker Build Failures

- Test Docker build locally first
- Check that all files are properly copied
- Verify base images are accessible

#### Slow CI Performance

- Check if caching is working properly
- Look for unnecessary operations
- Consider splitting large test suites

### Performance Expectations

| Workflow | Expected Duration | Failure Threshold |
|----------|------------------|-------------------|
| CI (Backend) | 3-5 minutes | > 8 minutes |
| CI (Frontend) | 2-4 minutes | > 6 minutes |
| CI (Security) | 1-3 minutes | > 5 minutes |
| CI (Docker) | 3-6 minutes | > 10 minutes |
| CD (Full deployment) | 5-10 minutes | > 15 minutes |
| Release | 10-15 minutes | > 20 minutes |

## Secrets and Environment Variables

### Repository Secrets

The following secrets are configured at the repository level:

- `GITHUB_TOKEN` - Automatically provided by GitHub
- Additional secrets may be added for external services

### Environment Variables

Common environment variables used in workflows:

```yaml
env:
  UV_CACHE_DIR: /tmp/.uv-cache
  DOCKER_REGISTRY: ghcr.io
  DOCKER_REPOSITORY: partshub
```

### Adding New Secrets

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add name and value
4. Update workflow files to use the secret

## Integration with External Services

### GitHub Container Registry

- Images are automatically pushed on release
- Tagged with both version and `latest`
- Accessible at `ghcr.io/owner/partshub`

### Documentation Deployment

- Built with MkDocs
- Deployed to GitHub Pages
- Versioned documentation available

## Troubleshooting

For detailed troubleshooting information, see:
- [Troubleshooting Guide](troubleshooting.md)
- [Branch Protection Configuration](branch-protection.md)

## Getting Help

1. **Check workflow logs** in GitHub Actions tab
2. **Review this guide** and troubleshooting docs
3. **Ask team members** for assistance
4. **Create GitHub issue** for persistent problems

Remember: The workflows are designed to help maintain code quality and automate deployments. When in doubt, test locally first and don't hesitate to ask for help!