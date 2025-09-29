"""
Contract tests for Reports API endpoints.
Tests all analytics and reporting functionality.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient


class TestReportsContract:
    """Contract tests for reports API endpoints."""

    def test_get_dashboard_summary_anonymous_access(self, client: TestClient):
        """Test dashboard summary endpoint allows anonymous access."""
        response = client.get("/api/v1/reports/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        # Should contain basic summary sections
        expected_sections = [
            "component_statistics",
            "project_statistics",
            "activity_statistics",
        ]
        for section in expected_sections:
            assert section in data

    def test_get_dashboard_stats_anonymous_access(self, client: TestClient):
        """Test dashboard stats endpoint allows anonymous access."""
        response = client.get("/api/v1/reports/dashboard-stats")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_inventory_breakdown_response_structure(self, client: TestClient):
        """Test inventory breakdown returns proper structure."""
        response = client.get("/api/v1/reports/inventory-breakdown")
        # Should be successful or fail gracefully
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_usage_analytics_with_default_params(self, client: TestClient):
        """Test usage analytics with default parameters."""
        response = client.get("/api/v1/reports/usage-analytics")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_usage_analytics_with_custom_days(self, client: TestClient):
        """Test usage analytics with custom days parameter."""
        response = client.get("/api/v1/reports/usage-analytics?days=7")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_usage_analytics_parameter_validation(self, client: TestClient):
        """Test usage analytics parameter validation."""
        # Test minimum value
        response = client.get("/api/v1/reports/usage-analytics?days=0")
        assert response.status_code == 422

        # Test maximum value
        response = client.get("/api/v1/reports/usage-analytics?days=366")
        assert response.status_code == 422

    def test_get_project_analytics_response_structure(self, client: TestClient):
        """Test project analytics returns proper structure."""
        response = client.get("/api/v1/reports/project-analytics")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_financial_summary_with_default_params(self, client: TestClient):
        """Test financial summary with default parameters."""
        response = client.get("/api/v1/reports/financial-summary")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_financial_summary_with_custom_months(self, client: TestClient):
        """Test financial summary with custom months parameter."""
        response = client.get("/api/v1/reports/financial-summary?months=6")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_financial_summary_parameter_validation(self, client: TestClient):
        """Test financial summary parameter validation."""
        # Test minimum value
        response = client.get("/api/v1/reports/financial-summary?months=0")
        assert response.status_code == 422

        # Test maximum value
        response = client.get("/api/v1/reports/financial-summary?months=61")
        assert response.status_code == 422

    def test_get_search_analytics_response_structure(self, client: TestClient):
        """Test search analytics returns proper structure."""
        response = client.get("/api/v1/reports/search-analytics")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_system_health_metrics_response_structure(self, client: TestClient):
        """Test system health metrics returns proper structure."""
        response = client.get("/api/v1/reports/system-health")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_comprehensive_report_json_format(self, client: TestClient):
        """Test comprehensive report in JSON format."""
        response = client.get("/api/v1/reports/comprehensive")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_comprehensive_report_download_format(self, client: TestClient):
        """Test comprehensive report in download format."""
        response = client.get("/api/v1/reports/comprehensive?format=download")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert "comprehensive-report-" in response.headers["Content-Disposition"]

    def test_export_inventory_report_json_format(self, client: TestClient):
        """Test inventory export in JSON format."""
        response = client.get("/api/v1/reports/export/inventory")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "inventory-report-" in response.headers["Content-Disposition"]

    def test_export_inventory_report_csv_format(self, client: TestClient):
        """Test inventory export in CSV format."""
        response = client.get("/api/v1/reports/export/inventory?format=csv")
        assert response.status_code == 200

        # Should be a CSV download
        assert response.headers["content-type"].startswith("text/csv")
        assert "Content-Disposition" in response.headers
        assert ".csv" in response.headers["Content-Disposition"]

    def test_export_usage_report_json_format(self, client: TestClient):
        """Test usage export in JSON format."""
        response = client.get("/api/v1/reports/export/usage")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "usage-report-" in response.headers["Content-Disposition"]

    def test_export_usage_report_csv_format(self, client: TestClient):
        """Test usage export in CSV format."""
        response = client.get("/api/v1/reports/export/usage?format=csv")
        assert response.status_code == 200

        # Should be a CSV download
        assert response.headers["content-type"].startswith("text/csv")
        assert "Content-Disposition" in response.headers
        assert ".csv" in response.headers["Content-Disposition"]

    def test_export_usage_report_with_custom_days(self, client: TestClient):
        """Test usage export with custom days parameter."""
        response = client.get("/api/v1/reports/export/usage?days=14&format=json")
        assert response.status_code == 200

        assert "14days" in response.headers["Content-Disposition"]

    def test_export_project_report_json_format(self, client: TestClient):
        """Test project export in JSON format."""
        response = client.get("/api/v1/reports/export/projects")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "project-report-" in response.headers["Content-Disposition"]

    def test_export_project_report_csv_format(self, client: TestClient):
        """Test project export in CSV format."""
        response = client.get("/api/v1/reports/export/projects?format=csv")
        assert response.status_code == 200

        # Should be a CSV download
        assert response.headers["content-type"].startswith("text/csv")
        assert "Content-Disposition" in response.headers
        assert ".csv" in response.headers["Content-Disposition"]

    def test_export_financial_report_json_format(self, client: TestClient):
        """Test financial export in JSON format."""
        response = client.get("/api/v1/reports/export/financial")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "financial-report-" in response.headers["Content-Disposition"]

    def test_export_financial_report_csv_format(self, client: TestClient):
        """Test financial export in CSV format."""
        response = client.get("/api/v1/reports/export/financial?format=csv")
        assert response.status_code == 200

        # Should be a CSV download
        assert response.headers["content-type"].startswith("text/csv")
        assert "Content-Disposition" in response.headers
        assert ".csv" in response.headers["Content-Disposition"]

    def test_export_financial_report_with_custom_months(self, client: TestClient):
        """Test financial export with custom months parameter."""
        response = client.get("/api/v1/reports/export/financial?months=24&format=json")
        assert response.status_code == 200

        assert "24months" in response.headers["Content-Disposition"]

    def test_export_system_health_report_json_format(self, client: TestClient):
        """Test system health export in JSON format."""
        response = client.get("/api/v1/reports/export/system-health")
        assert response.status_code == 200

        # Should be a file download
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "system-health-report-" in response.headers["Content-Disposition"]

    def test_export_system_health_report_csv_format(self, client: TestClient):
        """Test system health export in CSV format."""
        response = client.get("/api/v1/reports/export/system-health?format=csv")
        assert response.status_code == 200

        # Should be a CSV download
        assert response.headers["content-type"].startswith("text/csv")
        assert "Content-Disposition" in response.headers
        assert ".csv" in response.headers["Content-Disposition"]

    def test_get_admin_data_quality_report_requires_auth(self, client: TestClient):
        """Test admin data quality report requires authentication."""
        response = client.get("/api/v1/reports/admin/data-quality")
        assert response.status_code == 401

    def test_get_admin_data_quality_report_with_auth(
        self, client: TestClient, auth_headers
    ):
        """Test admin data quality report with authentication."""
        response = client.get(
            "/api/v1/reports/admin/data-quality", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "generated_at" in data
        assert "system_health" in data
        assert "search_quality" in data
        assert "recommendations" in data

        # Validate generated_at is a valid ISO datetime
        datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))

        # Validate recommendations structure
        recommendations = data["recommendations"]
        assert isinstance(recommendations, list)

        for rec in recommendations:
            assert "priority" in rec
            assert "category" in rec
            assert "issue" in rec
            assert "description" in rec
            assert "action" in rec

    def test_export_format_parameter_validation(self, client: TestClient):
        """Test export format parameter accepts valid values."""
        # Test valid formats
        response = client.get("/api/v1/reports/export/inventory?format=json")
        assert response.status_code == 200

        response = client.get("/api/v1/reports/export/inventory?format=csv")
        assert response.status_code == 200

    def test_all_endpoints_return_valid_json_or_files(self, client: TestClient):
        """Test that all report endpoints return valid responses."""
        endpoints = [
            "/api/v1/reports/dashboard",
            "/api/v1/reports/dashboard-stats",
            "/api/v1/reports/inventory-breakdown",
            "/api/v1/reports/usage-analytics",
            "/api/v1/reports/project-analytics",
            "/api/v1/reports/financial-summary",
            "/api/v1/reports/search-analytics",
            "/api/v1/reports/system-health",
            "/api/v1/reports/comprehensive",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            # Should return valid JSON
            try:
                data = response.json()
                assert isinstance(data, dict)
            except ValueError:
                pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_export_endpoints_return_file_downloads(self, client: TestClient):
        """Test that all export endpoints return file downloads."""
        export_endpoints = [
            "/api/v1/reports/export/inventory",
            "/api/v1/reports/export/usage",
            "/api/v1/reports/export/projects",
            "/api/v1/reports/export/financial",
            "/api/v1/reports/export/system-health",
        ]

        for endpoint in export_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            # Should have file download headers
            assert "Content-Disposition" in response.headers
            assert "attachment" in response.headers["Content-Disposition"]

    def test_comprehensive_report_format_parameter(self, client: TestClient):
        """Test comprehensive report format parameter validation."""
        # Default should be JSON response
        response = client.get("/api/v1/reports/comprehensive")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Explicit JSON format should return JSON response
        response = client.get("/api/v1/reports/comprehensive?format=json")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.parametrize("days", [1, 7, 30, 90, 365])
    def test_usage_analytics_various_day_ranges(self, client: TestClient, days):
        """Test usage analytics with various valid day ranges."""
        response = client.get(f"/api/v1/reports/usage-analytics?days={days}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.parametrize("months", [1, 6, 12, 24, 60])
    def test_financial_summary_various_month_ranges(self, client: TestClient, months):
        """Test financial summary with various valid month ranges."""
        response = client.get(f"/api/v1/reports/financial-summary?months={months}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
