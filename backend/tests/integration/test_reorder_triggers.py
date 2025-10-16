"""
Integration tests for reorder alert database triggers.

Tests that SQLite triggers automatically create/update/resolve alerts when:
- Stock falls below threshold (trigger_check_low_stock_after_update)
- Stock is restocked above threshold (trigger_resolve_alert_on_restock)
- Threshold is enabled/disabled (trigger_threshold_change)
- ComponentLocation is updated
"""

import pytest
from sqlalchemy import text

from backend.src.models import ComponentLocation, ReorderAlert


@pytest.mark.integration
class TestReorderAlertTriggers:
    """Integration tests for SQLite reorder alert triggers"""

    def test_trigger_creates_alert_when_stock_falls_below_threshold(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test trigger_check_low_stock_after_update creates alert when stock decreases below threshold
        """
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock above threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Enable reorder threshold (stock is above, no alert yet)
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        # Verify no alert exists yet
        alerts_before = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .count()
        )
        assert alerts_before == 0

        # Remove stock to fall below threshold (should trigger alert)
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 60, "reason": "usage"},
            headers=auth_headers,
        )

        # Refresh session to see trigger results
        db_session.commit()

        # Verify alert was created by trigger
        alert = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert alert is not None
        assert alert.current_quantity == 40  # 100 - 60
        assert alert.reorder_threshold == 50
        assert alert.shortage_amount == 10  # 50 - 40
        assert alert.status == "active"

    def test_trigger_resolves_alert_when_restocked_above_threshold(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test trigger_resolve_alert_on_restock auto-resolves alert when stock rises above threshold
        """
        # Setup: Create low stock alert
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add low stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Set threshold to trigger alert
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify alert exists
        alert_before = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert alert_before is not None

        # Restock above threshold (should trigger auto-resolve)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 50},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify alert was resolved by trigger
        alert_after = (
            db_session.query(ReorderAlert)
            .filter(ReorderAlert.id == alert_before.id)
            .first()
        )
        assert alert_after.status == "resolved"
        assert alert_after.resolved_at is not None

    def test_trigger_creates_alert_when_threshold_enabled(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test trigger_threshold_change creates alert when reorder monitoring is enabled with low stock
        """
        # Create component with low stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add low stock (threshold not set yet, so no alert)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Enable threshold above current stock (should trigger alert creation)
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify alert was created
        alert = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert alert is not None
        assert alert.shortage_amount == 40  # 50 - 10

    def test_trigger_does_not_create_duplicate_alerts(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test triggers do not create duplicate active alerts for same component location
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add low stock and set threshold (creates first alert)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Remove more stock (should NOT create duplicate alert)
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 3, "reason": "usage"},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify only one active alert exists
        alert_count = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .count()
        )
        assert alert_count == 1

    def test_trigger_updates_existing_alert_when_stock_changes(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test trigger updates existing alert's current_quantity and shortage when stock changes
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Create alert
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Get initial alert
        alert_initial = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert alert_initial.current_quantity == 10
        assert alert_initial.shortage_amount == 40  # 50 - 10

        # Remove more stock (should update existing alert)
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 3, "reason": "usage"},
            headers=auth_headers,
        )

        db_session.commit()
        db_session.refresh(alert_initial)

        # Verify alert was updated (not replaced)
        assert alert_initial.current_quantity == 7  # 10 - 3
        assert alert_initial.shortage_amount == 43  # 50 - 7

    def test_trigger_ignores_disabled_monitoring(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test triggers do not create alerts when reorder monitoring is disabled
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add low stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )

        # Set threshold but disabled (should NOT create alert)
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": False},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify no alert was created
        alert_count = (
            db_session.query(ReorderAlert)
            .filter(ReorderAlert.component_id == component_id)
            .count()
        )
        assert alert_count == 0

    def test_trigger_severity_calculation(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """
        Test alert severity is correctly calculated based on shortage percentage
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Create critical shortage (shortage > 80%)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 5},  # Only 5 units
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 100, "enabled": True},  # Need 100 units
            headers=auth_headers,
        )

        db_session.commit()

        alert = (
            db_session.query(ReorderAlert)
            .filter(ReorderAlert.component_id == component_id)
            .first()
        )

        # Shortage: 95/100 = 95% (should be "critical")
        assert alert.shortage_percentage == 95.0
        assert alert.severity == "critical"

    def test_multiple_locations_independent_alerts(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
    ):
        """
        Test alerts are created independently for each component location
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create two locations
        loc1_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 1", "type": "drawer"},
            headers=auth_headers,
        )
        loc1_id = loc1_resp.json()["id"]

        loc2_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 2", "type": "drawer"},
            headers=auth_headers,
        )
        loc2_id = loc2_resp.json()["id"]

        # Add stock to both, set different thresholds
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": loc1_id, "quantity": 10},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{loc1_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": loc2_id, "quantity": 60},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{loc2_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Verify only Location 1 has alert (qty 10 < 50)
        alerts = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.status == "active",
            )
            .all()
        )

        # Location 1 should have alert, Location 2 should not
        loc1_alerts = [a for a in alerts if a.storage_location_id == loc1_id]
        loc2_alerts = [a for a in alerts if a.storage_location_id == loc2_id]

        assert len(loc1_alerts) == 1
        assert len(loc2_alerts) == 0

    def test_trigger_behavior_on_stock_move(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
    ):
        """
        Test triggers correctly handle stock moves between locations
        """
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create two locations
        source_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Source Location", "type": "drawer"},
            headers=auth_headers,
        )
        source_id = source_resp.json()["id"]

        dest_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Dest Location", "type": "drawer"},
            headers=auth_headers,
        )
        dest_id = dest_resp.json()["id"]

        # Add stock to source and set threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": source_id, "quantity": 60},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{source_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        # Set threshold for destination
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": dest_id, "quantity": 1},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{dest_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Move stock from source (60) to dest (1), causing source to go below threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json={
                "source_location_id": source_id,
                "destination_location_id": dest_id,
                "quantity": 20,
            },
            headers=auth_headers,
        )

        db_session.commit()

        # Check source alert (60 - 20 = 40, below threshold 50)
        source_alert = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.storage_location_id == source_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert source_alert is not None
        assert source_alert.current_quantity == 40

        # Check dest alert resolution (1 + 20 = 21, but still below 50)
        # Dest should still have active alert
        dest_alert = (
            db_session.query(ReorderAlert)
            .filter(
                ReorderAlert.component_id == component_id,
                ReorderAlert.storage_location_id == dest_id,
                ReorderAlert.status == "active",
            )
            .first()
        )
        assert dest_alert is not None
