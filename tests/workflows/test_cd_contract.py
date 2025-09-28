"""
CD Workflow Contract Validation Test
Tests that the CD workflow implementation meets the contract requirements.
"""

from pathlib import Path

import pytest
import yaml


class TestCDWorkflowContract:
    """Test CD workflow contract compliance"""

    def setup_method(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent.parent
        self.workflow_file = self.repo_root / ".github" / "workflows" / "cd.yml"

    def test_workflow_file_exists(self):
        """Test that CD workflow file exists at expected location"""
        assert self.workflow_file.exists(), f"CD workflow file not found at {self.workflow_file}"

    def test_workflow_triggers_on_main_push(self):
        """Test that workflow triggers on main branch push (FR-004)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        triggers = workflow.get('on', {})
        assert 'push' in triggers, "CD workflow must trigger on push events"

        push_config = triggers['push']
        if isinstance(push_config, dict) and 'branches' in push_config:
            branches = push_config['branches']
            assert 'main' in branches, \
                "CD workflow must trigger on main branch push"

    def test_workflow_has_deployment_jobs(self):
        """Test that workflow includes deployment jobs (FR-004)"""
        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get('jobs', {})
        deploy_job_found = False

        for job_name, job_config in jobs.items():
            if 'deploy' in job_name.lower():
                deploy_job_found = True
                break

        assert deploy_job_found, "CD workflow must include deployment jobs"


# This test should FAIL initially since the CD workflow doesn't exist yet
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
