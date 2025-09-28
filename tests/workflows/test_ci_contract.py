"""
CI Workflow Contract Validation Test
Tests that the CI workflow implementation meets the contract requirements.
"""

from pathlib import Path

import pytest
import yaml


class TestCIWorkflowContract:
    """Test CI workflow contract compliance"""

    def setup_method(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent.parent
        self.workflow_file = self.repo_root / ".github" / "workflows" / "ci.yml"
        self.contract_file = self.repo_root / "specs" / "002-github-workflows" / "contracts" / "ci-workflow-contract.yml"

        # Load contract requirements
        with open(self.contract_file) as f:
            self.contract = yaml.safe_load(f)

    def test_workflow_file_exists(self):
        """Test that CI workflow file exists at expected location"""
        assert self.workflow_file.exists(), f"CI workflow file not found at {self.workflow_file}"

    def test_workflow_syntax_valid(self):
        """Test that workflow file has valid YAML syntax"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)
        assert workflow is not None, "Workflow YAML is invalid"
        assert isinstance(workflow, dict), "Workflow must be a dictionary"

    def test_workflow_name_matches_contract(self):
        """Test that workflow name matches contract specification"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        expected_name = self.contract['workflow_name']
        actual_name = workflow.get('name', '')
        assert actual_name == expected_name, f"Workflow name '{actual_name}' does not match contract '{expected_name}'"

    def test_workflow_triggers_push_events(self):
        """Test that workflow triggers on push events (FR-001)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        triggers = workflow.get('on', {})
        assert 'push' in triggers, "Workflow must trigger on push events"

        # Check branch configuration
        push_config = triggers['push']
        if isinstance(push_config, dict) and 'branches' in push_config:
            branches = push_config['branches']
            # Should allow all branches or specific branches
            assert branches is not None, "Push trigger must specify branch configuration"

    def test_workflow_triggers_pull_request_events(self):
        """Test that workflow triggers on pull request events (FR-001)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        triggers = workflow.get('on', {})
        assert 'pull_request' in triggers, "Workflow must trigger on pull request events"

        # Check target branches
        pr_config = triggers['pull_request']
        if isinstance(pr_config, dict) and 'branches' in pr_config:
            branches = pr_config['branches']
            expected_branches = self.contract['triggers'][1]['branches']
            for branch in expected_branches:
                assert branch in branches, f"Pull request must target branch '{branch}'"

    def test_workflow_has_backend_tests_job(self):
        """Test that workflow includes backend tests job (FR-002, FR-009)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        backend_job_found = False

        for job_name, job_config in jobs.items():
            if 'backend' in job_name.lower() or 'test' in job_name.lower():
                backend_job_found = True
                # Check if job includes required test steps
                steps = job_config.get('steps', [])
                has_test_step = any('test' in str(step).lower() or 'pytest' in str(step).lower()
                                   for step in steps)
                assert has_test_step, f"Backend job '{job_name}' must include test execution steps"
                break

        assert backend_job_found, "Workflow must include backend testing job"

    def test_workflow_has_frontend_tests_job(self):
        """Test that workflow includes frontend tests job (FR-002, FR-009)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        frontend_job_found = False

        for job_name, job_config in jobs.items():
            if 'frontend' in job_name.lower() or ('test' in job_name.lower() and 'npm' in str(job_config)):
                frontend_job_found = True
                # Check if job includes npm test steps
                steps = job_config.get('steps', [])
                has_npm_test = any('npm test' in str(step) or 'npm run test' in str(step)
                                  for step in steps)
                assert has_npm_test, f"Frontend job '{job_name}' must include npm test execution"
                break

        assert frontend_job_found, "Workflow must include frontend testing job"

    def test_workflow_has_security_scan_job(self):
        """Test that workflow includes security scanning (FR-011)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        security_job_found = False

        for job_name, job_config in jobs.items():
            if 'security' in job_name.lower() or 'scan' in job_name.lower():
                security_job_found = True
                break

            # Check if any job includes security scanning steps
            steps = job_config.get('steps', [])
            has_security_step = any('security' in str(step).lower() or 'vulnerability' in str(step).lower()
                                   for step in steps)
            if has_security_step:
                security_job_found = True
                break

        assert security_job_found, "Workflow must include security scanning"

    def test_workflow_has_docker_build_job(self):
        """Test that workflow includes Docker build validation (FR-010)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        docker_job_found = False

        for job_name, job_config in jobs.items():
            if 'docker' in job_name.lower() or 'build' in job_name.lower():
                docker_job_found = True
                # Check if job includes Docker build steps
                steps = job_config.get('steps', [])
                has_docker_step = any('docker' in str(step).lower() for step in steps)
                assert has_docker_step, f"Docker job '{job_name}' must include Docker build steps"
                break

        assert docker_job_found, "Workflow must include Docker build validation"

    def test_workflow_uses_dependency_caching(self):
        """Test that workflow implements dependency caching (FR-007)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        cache_found = False

        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if isinstance(step, dict) and 'uses' in step:
                    if 'cache' in step['uses']:
                        cache_found = True
                        break
                elif isinstance(step, dict) and 'name' in step:
                    if 'cache' in step['name'].lower():
                        cache_found = True
                        break
            if cache_found:
                break

        assert cache_found, "Workflow must implement dependency caching for performance"

    def test_workflow_produces_required_artifacts(self):
        """Test that workflow produces required artifacts for testing feedback"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        artifact_found = False

        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if isinstance(step, dict) and 'uses' in step:
                    if 'upload-artifact' in step['uses']:
                        artifact_found = True
                        break
            if artifact_found:
                break

        assert artifact_found, "Workflow must upload test results and artifacts"


# This test should FAIL initially since the CI workflow doesn't exist yet
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
