# GitHub Workflows Troubleshooting Guide

This guide helps resolve common issues with GitHub Actions workflows in the PartsHub project.

## Common Issues

### 1. Workflow Not Triggering

#### Symptoms
- Push to branch or PR creation doesn't start workflows
- Workflows show as "skipped" or don't appear at all

#### Solutions
1. **Check workflow file syntax**:
   ```bash
   # Validate YAML syntax
   yamllint .github/workflows/ci.yml
   ```

2. **Verify trigger conditions**:
   - Ensure branch names match exactly (case-sensitive)
   - Check that paths or file patterns are correct
   - Verify workflow is not disabled in repository settings

3. **Check repository permissions**:
   - Go to Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected
   - Verify workflow permissions are set to "Read and write"

### 2. CI Tests Failing

#### Backend Test Failures

**Symptoms**: Backend Tests job fails with test errors

**Common Causes & Solutions**:

1. **Missing dependencies**:
   ```yaml
   # Ensure all dependencies are installed
   - name: Install dependencies
     run: uv sync --all-extras --dev
   ```

2. **Python version mismatch**:
   ```yaml
   # Check Python version matches project requirements
   - name: Set up Python
     uses: actions/setup-python@v4
     with:
       python-version: "3.11"  # Match pyproject.toml
   ```

3. **Database connection issues**:
   - Tests should use isolated test databases
   - Check that test configuration doesn't try to connect to production DBs

#### Frontend Test Failures

**Symptoms**: Frontend Tests job fails during npm test

**Common Causes & Solutions**:

1. **Node version mismatch**:
   ```yaml
   - name: Set up Node.js
     uses: actions/setup-node@v4
     with:
       node-version: "18"  # Match package.json engines
   ```

2. **Missing dependencies**:
   ```bash
   cd frontend
   npm ci  # Use npm ci instead of npm install for CI
   ```

3. **Build configuration**:
   - Ensure Quasar CLI is properly configured
   - Check that environment variables are set correctly

### 3. Docker Build Issues

#### Symptoms
- Docker Build job fails with image build errors
- "No space left on device" errors

#### Solutions

1. **Check Dockerfile syntax**:
   ```bash
   # Test Docker build locally
   docker build -t test-image .
   ```

2. **Cache issues**:
   ```yaml
   # Clear and rebuild cache
   - name: Cache Docker layers
     uses: actions/cache@v3
     with:
       path: /tmp/.buildx-cache
       key: ${{ runner.os }}-buildx-${{ github.sha }}
   ```

3. **Multi-stage build problems**:
   - Verify target stages exist in Dockerfile
   - Check that base images are accessible

### 4. Security Scan Failures

#### Symptoms
- Security Scan job reports critical vulnerabilities
- Safety or bandit tools fail

#### Solutions

1. **Python dependency vulnerabilities**:
   ```bash
   # Update vulnerable packages
   uv add package@latest
   uv lock
   ```

2. **NPM audit issues**:
   ```bash
   cd frontend
   npm audit fix
   npm audit fix --force  # For breaking changes
   ```

3. **False positives**:
   - Review security reports carefully
   - Consider adding exceptions for false positives
   - Update security tool configurations

### 5. Deployment Issues

#### CD Workflow Failures

**Symptoms**: Continuous Deployment workflow fails

**Common Causes & Solutions**:

1. **Missing secrets**:
   - Verify all required secrets are set in repository settings
   - Check environment-specific secrets for production

2. **CI dependency failures**:
   ```yaml
   # Ensure CI workflow completes successfully first
   needs: [check_ci_status]
   if: ${{ needs.check_ci_status.outputs.ci_passed == 'true' }}
   ```

3. **Docker registry authentication**:
   ```yaml
   - name: Log in to Container Registry
     uses: docker/login-action@v3
     with:
       registry: ghcr.io
       username: ${{ github.actor }}
       password: ${{ secrets.GITHUB_TOKEN }}
   ```

### 6. Performance Issues

#### Slow Workflow Execution

**Symptoms**: Workflows take longer than 10 minutes

**Solutions**:

1. **Optimize caching**:
   ```yaml
   # Ensure all dependencies are cached
   - name: Cache uv dependencies
     uses: actions/cache@v3
     with:
       path: /tmp/.uv-cache
       key: uv-${{ runner.os }}-${{ hashFiles('**/pyproject.toml', '**/uv.lock') }}
   ```

2. **Parallel execution**:
   - Verify jobs that can run in parallel are not dependencies
   - Use matrix builds for multiple versions if needed

3. **Runner resources**:
   - Consider using `ubuntu-latest` for best performance
   - Avoid unnecessary file operations

### 7. Branch Protection Issues

#### Can't Merge PRs

**Symptoms**: Merge button disabled even with passing checks

**Solutions**:

1. **Check required status checks**:
   - Go to Settings → Branches → Edit main branch rule
   - Verify all status check names match exactly

2. **Status check naming**:
   ```yaml
   # Job names must match status check requirements
   jobs:
     backend_tests:
       name: "Backend Tests"  # This becomes the status check name
   ```

## Debugging Commands

### Local Workflow Testing

```bash
# Test workflows locally with act
./scripts/test-workflows.sh

# Validate specific workflow
act -j backend_tests

# Test with specific event
act pull_request
```

### Checking Workflow Status

```bash
# List recent workflow runs
gh run list

# View specific run details
gh run view <run-id>

# Download run logs
gh run download <run-id>

# Cancel running workflow
gh run cancel <run-id>
```

### Repository Diagnostics

```bash
# Check repository settings
gh repo view --web

# List repository secrets
gh secret list

# Check branch protection
gh api repos/:owner/:repo/branches/main/protection
```

## Getting Help

### GitHub Actions Logs

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Click on the failed workflow run
4. Click on the failed job
5. Expand the failing step to see detailed logs

### Common Log Locations

- **Backend logs**: Look for pytest output and Python tracebacks
- **Frontend logs**: Check npm/Quasar build output
- **Docker logs**: Review build context and layer information
- **Security logs**: Check safety and bandit JSON reports

### Escalation Process

1. Check this troubleshooting guide first
2. Review GitHub Actions documentation
3. Search existing GitHub issues in the repository
4. Create a new issue with:
   - Workflow run URL
   - Error logs (sanitized of secrets)
   - Steps to reproduce
   - Expected vs actual behavior

## Prevention Tips

1. **Test locally first**: Always run tests and builds locally before pushing
2. **Use semantic commits**: Clear commit messages help with debugging
3. **Keep dependencies updated**: Regular updates prevent security issues
4. **Monitor workflow performance**: Set up alerts for long-running workflows
5. **Review changes carefully**: Large workflow changes should be tested in branches first

## Monitoring and Alerts

### Workflow Performance Metrics

- **CI execution time**: Should complete in < 10 minutes
- **Docker build time**: Should complete in < 5 minutes
- **Test success rate**: Should maintain > 95% pass rate
- **Security scan frequency**: Daily automated scans

### Setting Up Alerts

Consider setting up notifications for:
- Failed workflows on main branch
- Workflows taking longer than expected
- Security vulnerabilities found
- Deployment failures

This can be configured through GitHub's webhook system or third-party monitoring tools.