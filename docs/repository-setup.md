# Repository Setup for GitHub Actions

This document outlines the required repository settings for GitHub Actions workflows.

## Required Repository Settings

### 1. GitHub Actions Permissions

**Settings → Actions → General**
- Actions permissions: Allow enterprise, and select non-enterprise, actions and reusable workflows
- Fork pull request workflows: Run workflows from fork pull requests (checked)
- Fork pull request workflows in private repositories: Require approval for first-time contributors

### 2. Branch Protection Rules

**Settings → Branches → Add rule**

**Branch name pattern**: `main`
- Require status checks to pass before merging: ✅
  - Require branches to be up to date before merging: ✅
  - Status checks to require:
    - `backend_tests`
    - `frontend_tests`
    - `security_scan`
    - `docker_build`
- Require pull request reviews before merging: ✅
  - Required number of reviews: 1
  - Dismiss stale reviews: ✅
- Require conversation resolution before merging: ✅
- Include administrators: ✅

### 3. GitHub Pages (for documentation)

**Settings → Pages**
- Source: Deploy from a branch
- Branch: `gh-pages` / `docs` (will be set up by workflow)

### 4. Required Secrets

**Settings → Secrets and variables → Actions**

#### Repository Secrets
- `DOCKER_USERNAME`: Docker Hub username (if using Docker Hub)
- `DOCKER_PASSWORD`: Docker Hub password (if using Docker Hub)
- `PRODUCTION_DATABASE_URL`: Production database connection string
- `PRODUCTION_SECRET_KEY`: Production application secret key

#### Variables
- `DOCKER_REGISTRY`: `ghcr.io` (GitHub Container Registry)
- `DOCKER_REPOSITORY`: `partshub`

### 5. Environments

**Settings → Environments**

#### Production Environment
- Environment name: `production`
- Protection rules:
  - Required reviewers: (optional for automatic deployment)
  - Wait timer: 0 minutes
  - Deployment branches: Selected branches → `main`

#### Secrets for Production Environment
- `DATABASE_URL`: Production database URL
- `SECRET_KEY`: Production secret key
- `REGISTRY_TOKEN`: GitHub Container Registry token

## GitHub Container Registry Setup

### 1. Enable Container Registry
- Go to your profile → Settings → Developer settings → Personal access tokens
- Create token with `write:packages` scope
- Add as `REGISTRY_TOKEN` secret

### 2. Configure Package Visibility
**Settings → Packages**
- Set packages to public or private as needed
- Configure access permissions for team members

## Verification Checklist

- [ ] Actions permissions configured
- [ ] Branch protection rules set for main branch
- [ ] Required status checks configured
- [ ] GitHub Pages enabled
- [ ] All secrets added
- [ ] Production environment configured
- [ ] Container registry access configured

## Notes

- These settings should be configured by a repository administrator
- Some settings may require organization-level permissions
- Test the setup with a simple workflow before deploying to production