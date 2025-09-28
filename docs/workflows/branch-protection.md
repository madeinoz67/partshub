# Branch Protection Configuration

This document outlines the required GitHub repository settings for branch protection to ensure all CI workflows pass before merging.

## Required Status Checks

The following status checks must be configured as required for the `main` branch:

### CI Workflow Status Checks
- `Backend Tests` - Ensures backend tests, linting, and coverage pass
- `Frontend Tests` - Ensures frontend tests, linting, and build succeed
- `Security Scan` - Ensures no critical vulnerabilities are found
- `Docker Build` - Ensures Docker images build successfully

## GitHub Repository Settings

### 1. Navigate to Branch Protection Rules

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Click on **Branches** in the left sidebar
4. Click **Add rule** or edit the existing rule for `main` branch

### 2. Configure Protection Rule

Configure the following settings:

#### Basic Settings
- **Branch name pattern**: `main`
- ✅ **Require a pull request before merging**
  - ✅ **Require approvals**: 1 (recommended)
  - ✅ **Dismiss stale PR approvals when new commits are pushed**
  - ✅ **Require review from code owners** (if CODEOWNERS file exists)

#### Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required status checks** (add these exact names):
```
Backend Tests
Frontend Tests
Security Scan
Docker Build
```

#### Additional Restrictions
- ✅ **Restrict pushes that create files** (optional, for security)
- ✅ **Allow force pushes** (unchecked - disabled)
- ✅ **Allow deletions** (unchecked - disabled)

### 3. GitHub Actions Permissions

Ensure GitHub Actions have the necessary permissions:

1. Go to **Settings** → **Actions** → **General**
2. Set **Actions permissions** to:
   - ✅ **Allow all actions and reusable workflows**
3. Set **Workflow permissions** to:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**

## Environment Protection Rules

For the `production` environment used in CD workflow:

### 1. Create Production Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `production`

### 2. Configure Environment Protection

#### Deployment Branches
- ✅ **Selected branches**
- Add branch: `main`

#### Environment Secrets
Add the following secrets (if applicable):
- `PRODUCTION_DATABASE_URL`
- `PRODUCTION_SECRET_KEY`
- `DOCKER_REGISTRY_TOKEN` (if using external registry)

#### Reviewers (Optional)
- Add required reviewers for production deployments
- Consider adding a deployment approval process

## Verification

After configuring branch protection:

1. Create a test branch and make a small change
2. Open a pull request to `main`
3. Verify that all status checks appear as required
4. Confirm that the merge button is disabled until checks pass
5. Verify that CI workflows run automatically

## Troubleshooting

### Status Checks Not Appearing
- Ensure the exact status check names match the job names in workflows
- Workflows must have run at least once to appear in the list
- Check that branch name patterns match exactly

### Merge Button Still Enabled
- Verify that all required status checks are added to the protection rule
- Check that "Require status checks to pass before merging" is enabled
- Ensure no administrator bypass is accidentally enabled

### CI Workflows Not Triggering
- Check GitHub Actions permissions
- Verify workflow trigger conditions match your branch setup
- Check repository Actions tab for any disabled workflows

## Additional Security Considerations

1. **CODEOWNERS File**: Create a `.github/CODEOWNERS` file to require specific team members to review certain paths
2. **Secret Scanning**: Enable GitHub's secret scanning in repository security settings
3. **Dependency Updates**: Configure Dependabot for automated dependency updates
4. **Security Advisories**: Enable GitHub security advisories for vulnerability alerts

This configuration ensures that all code changes go through proper CI validation before reaching the main branch.