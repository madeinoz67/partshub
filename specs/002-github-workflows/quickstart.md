# Quickstart: GitHub Workflows for CI/CD

This guide validates that the GitHub workflows implementation correctly fulfills all functional requirements from the specification.

## Prerequisites

Before testing the workflows, ensure:

- [ ] Repository has `main` branch
- [ ] pyproject.toml exists with valid version field
- [ ] Backend and frontend directories are properly structured
- [ ] GitHub repository settings allow Actions to run

## Test Scenario 1: Continuous Integration (CI) Workflow

**Validates**: FR-001, FR-002, FR-003, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011

### 1.1 Test Push to Feature Branch

```bash
# Create a feature branch
git checkout -b test-ci-workflow
echo "# Test change" >> README.md
git add README.md
git commit -m "test: trigger CI workflow"
git push origin test-ci-workflow
```

**Expected Results**:
- ✅ CI workflow triggers automatically on push (FR-001)
- ✅ Both backend and frontend tests run in parallel (FR-009)
- ✅ Linting checks execute (FR-002)
- ✅ Security scanning completes (FR-011)
- ✅ Docker builds validate (FR-010)
- ✅ Dependencies are cached for faster execution (FR-007)
- ✅ Tests run in isolated environments (FR-008)

**Validation Points**:
- Check GitHub Actions tab shows workflow execution
- Verify all jobs complete successfully
- Confirm caching is working (subsequent runs faster)
- Validate test isolation (no cross-contamination)

### 1.2 Test Pull Request Creation

```bash
# Create pull request from feature branch
gh pr create --title "Test CI Workflow" --body "Testing automated CI"
```

**Expected Results**:
- ✅ CI workflow triggers on PR creation (FR-001)
- ✅ All required status checks appear (FR-003)
- ✅ PR cannot be merged until checks pass (FR-003)
- ✅ Clear feedback provided for any failures (FR-006)

**Validation Points**:
- PR shows required status checks
- Merge button disabled until checks pass
- Failure messages are actionable and clear

## Test Scenario 2: Continuous Deployment (CD) Workflow

**Validates**: FR-004, FR-013, FR-014, FR-015, FR-016

### 2.1 Test Automatic Deployment

```bash
# Merge PR to trigger deployment
gh pr merge --merge
```

**Expected Results**:
- ✅ CD workflow triggers on main branch push (FR-004)
- ✅ Backend deploys to production automatically (FR-004)
- ✅ Frontend deploys after backend success (FR-004)
- ✅ Documentation builds and deploys (FR-016)
- ✅ Stakeholders notified of deployment status (FR-013)

**Validation Points**:
- Deployment completes without manual intervention
- Production services are updated and accessible
- Documentation site reflects latest changes
- GitHub comments/issues show deployment notifications

### 2.2 Test Manual Emergency Deployment

```bash
# Trigger manual workflow in GitHub UI
# Go to Actions tab → Select CD workflow → Run workflow
```

**Expected Results**:
- ✅ Manual trigger option available (FR-014)
- ✅ Workflow execution history maintained (FR-015)

**Validation Points**:
- Manual trigger works from GitHub UI
- Deployment logs are preserved and accessible
- Emergency deployment bypasses normal triggers

## Test Scenario 3: Release Automation Workflow

**Validates**: FR-005, FR-012, FR-017, FR-018, FR-019, FR-020, FR-021

### 3.1 Test Version Management

```bash
# Update version in pyproject.toml
sed -i 's/version = ".*"/version = "1.2.3"/' pyproject.toml
git add pyproject.toml
git commit -m "bump: version to 1.2.3"
git push origin main
```

**Expected Results**:
- ✅ Version synchronizes across all components (FR-019)

### 3.2 Test Release Creation

```bash
# Create semantic version tag
git tag v1.2.3
git push origin v1.2.3
```

**Expected Results**:
- ✅ Release workflow triggers on tag creation (FR-005)
- ✅ Version from pyproject.toml matches git tag (FR-019)
- ✅ Build artifacts are generated and stored (FR-012)
- ✅ Docker images built and published to GitHub Container Registry (FR-021)
- ✅ Versioned documentation published (FR-017, FR-018)
- ✅ Release notes automatically generated (FR-020)

**Validation Points**:
- GitHub Release created with correct version
- Release artifacts downloadable
- Docker images available at ghcr.io with correct tags
- Documentation accessible at version-specific URL
- Release notes include commit and PR information

### 3.3 Test Documentation Versioning

```bash
# Verify documentation is accessible
curl -I https://owner.github.io/partshub/v1.2.3/
curl -I https://owner.github.io/partshub/latest/
```

**Expected Results**:
- ✅ Version-specific documentation URL works (FR-018)
- ✅ Latest documentation points to newest version

## Test Scenario 4: Error Handling and Recovery

**Validates**: FR-006, FR-008, FR-015

### 4.1 Test CI Failure Handling

```bash
# Introduce test failure
echo "assert False, 'Intentional test failure'" >> backend/tests/test_example.py
git add .
git commit -m "test: introduce failing test"
git push origin test-failure-branch
```

**Expected Results**:
- ✅ Workflow fails gracefully (FR-006)
- ✅ Clear failure reasons provided (FR-006)
- ✅ Logs maintained for debugging (FR-015)
- ✅ Failed tests don't affect other environments (FR-008)

### 4.2 Test Deployment Failure Recovery

```bash
# Introduce deployment configuration error
# (This would be tested in staging/test environment)
```

**Expected Results**:
- ✅ Deployment failures trigger automatic rollback
- ✅ Production remains stable during failure
- ✅ Stakeholders notified of deployment failure (FR-013)

## Performance Validation

### 5.1 Test Workflow Performance

**Validation Points**:
- CI workflow completes in < 10 minutes
- Docker builds complete in < 5 minutes
- Dependencies are cached effectively
- Parallel execution reduces total time

### 5.2 Test Dependency Caching

```bash
# Run workflow twice and compare execution times
# Second run should be significantly faster due to caching
```

**Expected Results**:
- ✅ Subsequent workflow runs are faster (FR-007)
- ✅ Node.js and Python dependencies cached properly
- ✅ Docker layer caching reduces build time

## Security Validation

### 6.1 Test Secret Management

**Validation Points**:
- Secrets never appear in workflow logs
- Environment-specific secrets properly scoped
- No credentials committed to repository

### 6.2 Test Security Scanning

**Expected Results**:
- ✅ Dependency vulnerabilities detected (FR-011)
- ✅ Code security issues identified
- ✅ Docker images scanned for vulnerabilities

## Cleanup

```bash
# Clean up test branches and tags
git branch -D test-ci-workflow test-failure-branch
git tag -d v1.2.3
git push origin --delete test-ci-workflow test-failure-branch
git push origin --delete v1.2.3
```

## Success Criteria

All scenarios must pass with the following outcomes:

- ✅ All 21 functional requirements validated
- ✅ Workflows execute automatically on correct triggers
- ✅ Quality gates prevent broken code from reaching production
- ✅ Deployments are automated and reliable
- ✅ Documentation stays current and versioned
- ✅ Release process is fully automated
- ✅ Error handling provides clear feedback
- ✅ Performance meets specified targets
- ✅ Security scanning catches vulnerabilities

## Troubleshooting

### Common Issues

1. **Workflow doesn't trigger**: Check repository permissions and trigger conditions
2. **Tests fail in CI but pass locally**: Verify test isolation and environment setup
3. **Deployment fails**: Check secrets configuration and target environment health
4. **Docker build fails**: Verify Dockerfile syntax and base image availability
5. **Documentation build fails**: Check MkDocs configuration and dependencies

### Debug Commands

```bash
# Check workflow status
gh run list --workflow="ci.yml"

# View workflow logs
gh run view <run-id> --log

# Check repository settings
gh repo view --web
```

This quickstart guide ensures that all functional requirements are properly tested and validated through realistic usage scenarios.