"""
Unit tests for ReorderService.
Tests service methods with mocked database session.
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.src.models import ComponentLocation, ReorderAlert
from backend.src.services.reorder_service import ReorderService


@pytest.mark.unit
class TestReorderService:
    """Unit tests for ReorderService"""

    def test_init_stores_session(self):
        """Test ReorderService stores database session"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)
        assert service.session is mock_session

    def test_get_active_alerts_no_filters(self):
        """Test get_active_alerts returns all active alerts"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        # Mock query chain
        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.component_location_id = "comp-loc-id"
        mock_alert.component_id = "comp-id"
        mock_alert.storage_location_id = "loc-id"
        mock_alert.status = "active"
        mock_alert.severity = "high"
        mock_alert.current_quantity = 10
        mock_alert.reorder_threshold = 50
        mock_alert.shortage_amount = 40
        mock_alert.shortage_percentage = 80.0
        mock_alert.created_at = "2025-01-01"
        mock_alert.updated_at = "2025-01-01"
        mock_alert.dismissed_at = None
        mock_alert.ordered_at = None
        mock_alert.resolved_at = None
        mock_alert.notes = None

        mock_component = Mock()
        mock_component.name = "Test Component"
        mock_component.part_number = "PN123"

        mock_location = Mock()
        mock_location.name = "Drawer 1"

        mock_alert.component_location = Mock()
        mock_alert.component_location.component = mock_component
        mock_alert.component_location.storage_location = mock_location

        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_alert]

        alerts = service.get_active_alerts()

        assert len(alerts) == 1
        mock_session.execute.assert_called_once()

    def test_get_active_alerts_with_component_filter(self):
        """Test get_active_alerts filters by component_id"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        alerts = service.get_active_alerts(component_id="test-component-id")

        assert isinstance(alerts, list)
        mock_session.execute.assert_called_once()

    def test_get_alert_by_id_success(self):
        """Test get_alert_by_id returns alert when found"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.component_location_id = "comp-loc-id"
        mock_alert.component_id = "comp-id"
        mock_alert.storage_location_id = "loc-id"
        mock_alert.status = "active"
        mock_alert.severity = "high"
        mock_alert.current_quantity = 10
        mock_alert.reorder_threshold = 50
        mock_alert.shortage_amount = 40
        mock_alert.shortage_percentage = 80.0
        mock_alert.created_at = "2025-01-01"
        mock_alert.updated_at = "2025-01-01"
        mock_alert.dismissed_at = None
        mock_alert.ordered_at = None
        mock_alert.resolved_at = None
        mock_alert.notes = None

        mock_component = Mock()
        mock_component.name = "Test"
        mock_component.part_number = "PN123"

        mock_location = Mock()
        mock_location.name = "Drawer"

        mock_alert.component_location = Mock()
        mock_alert.component_location.component = mock_component
        mock_alert.component_location.storage_location = mock_location

        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_alert

        result = service.get_alert_by_id(1)

        assert result is not None
        assert "id" in result
        mock_session.execute.assert_called_once()

    def test_get_alert_by_id_not_found(self):
        """Test get_alert_by_id raises 404 when alert not found"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_alert_by_id(999)

        assert exc_info.value.status_code == 404

    def test_dismiss_alert_success(self):
        """Test dismiss_alert updates alert status"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.component_location_id = "comp-loc-id"
        mock_alert.component_id = "comp-id"
        mock_alert.storage_location_id = "loc-id"
        mock_alert.status = "active"
        mock_alert.severity = "high"
        mock_alert.current_quantity = 10
        mock_alert.reorder_threshold = 50
        mock_alert.shortage_amount = 40
        mock_alert.shortage_percentage = 80.0
        mock_alert.created_at = "2025-01-01"
        mock_alert.updated_at = "2025-01-01"
        mock_alert.dismissed_at = None
        mock_alert.ordered_at = None
        mock_alert.resolved_at = None
        mock_alert.notes = None

        mock_component = Mock()
        mock_component.name = "Test"
        mock_component.part_number = "PN123"

        mock_location = Mock()
        mock_location.name = "Drawer"

        mock_alert.component_location = Mock()
        mock_alert.component_location.component = mock_component
        mock_alert.component_location.storage_location = mock_location

        mock_session.get.return_value = mock_alert

        with patch("backend.src.services.reorder_service.datetime") as mock_dt:
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_dt.now.return_value = mock_now

            result = service.dismiss_alert(1, notes="Test dismissal")

        assert mock_alert.status == "dismissed"
        assert mock_alert.notes == "Test dismissal"
        assert result is not None

    def test_dismiss_alert_not_found(self):
        """Test dismiss_alert raises 404 when alert not found"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.dismiss_alert(999)

        assert exc_info.value.status_code == 404

    def test_dismiss_alert_not_active(self):
        """Test dismiss_alert raises 400 when alert is not active"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.status = "dismissed"

        mock_session.get.return_value = mock_alert

        with pytest.raises(HTTPException) as exc_info:
            service.dismiss_alert(1)

        assert exc_info.value.status_code == 400

    def test_mark_alert_ordered_success(self):
        """Test mark_alert_ordered updates alert status"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.component_location_id = "comp-loc-id"
        mock_alert.component_id = "comp-id"
        mock_alert.storage_location_id = "loc-id"
        mock_alert.status = "active"
        mock_alert.severity = "high"
        mock_alert.current_quantity = 10
        mock_alert.reorder_threshold = 50
        mock_alert.shortage_amount = 40
        mock_alert.shortage_percentage = 80.0
        mock_alert.created_at = "2025-01-01"
        mock_alert.updated_at = "2025-01-01"
        mock_alert.dismissed_at = None
        mock_alert.ordered_at = None
        mock_alert.resolved_at = None
        mock_alert.notes = None

        mock_component = Mock()
        mock_component.name = "Test"
        mock_component.part_number = "PN123"

        mock_location = Mock()
        mock_location.name = "Drawer"

        mock_alert.component_location = Mock()
        mock_alert.component_location.component = mock_component
        mock_alert.component_location.storage_location = mock_location

        mock_session.get.return_value = mock_alert

        with patch("backend.src.services.reorder_service.datetime") as mock_dt:
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_dt.now.return_value = mock_now

            result = service.mark_alert_ordered(1, notes="PO-2025-001")

        assert mock_alert.status == "ordered"
        assert mock_alert.notes == "PO-2025-001"
        assert result is not None

    def test_mark_alert_ordered_not_active(self):
        """Test mark_alert_ordered raises 400 when alert is not active"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.status = "ordered"

        mock_session.get.return_value = mock_alert

        with pytest.raises(HTTPException) as exc_info:
            service.mark_alert_ordered(1)

        assert exc_info.value.status_code == 400

    def test_update_reorder_threshold_success(self):
        """Test update_reorder_threshold updates ComponentLocation"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_comp_loc = Mock(spec=ComponentLocation)
        mock_comp_loc.id = "comp-loc-id"
        mock_comp_loc.component_id = "comp-id"
        mock_comp_loc.storage_location_id = "loc-id"
        mock_comp_loc.quantity_on_hand = 100
        mock_comp_loc.needs_reorder = False

        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_comp_loc

        result = service.update_reorder_threshold(
            component_id="comp-id",
            location_id="loc-id",
            threshold=50,
            enabled=True,
        )

        assert mock_comp_loc.reorder_threshold == 50
        assert mock_comp_loc.reorder_enabled is True
        assert result["reorder_threshold"] == 50

    def test_update_reorder_threshold_negative_value(self):
        """Test update_reorder_threshold raises 400 for negative threshold"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update_reorder_threshold(
                component_id="comp-id",
                location_id="loc-id",
                threshold=-10,
                enabled=True,
            )

        assert exc_info.value.status_code == 400

    def test_update_reorder_threshold_not_found(self):
        """Test update_reorder_threshold raises 404 when ComponentLocation not found"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.update_reorder_threshold(
                component_id="nonexistent",
                location_id="nonexistent",
                threshold=50,
                enabled=True,
            )

        assert exc_info.value.status_code == 404

    def test_bulk_update_thresholds_all_success(self):
        """Test bulk_update_thresholds with all successful updates"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        # Mock successful threshold updates
        mock_comp_loc = Mock(spec=ComponentLocation)
        mock_comp_loc.id = "comp-loc-id"
        mock_comp_loc.component_id = "comp-id"
        mock_comp_loc.storage_location_id = "loc-id"
        mock_comp_loc.quantity_on_hand = 100
        mock_comp_loc.needs_reorder = False

        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_comp_loc

        updates = [
            {
                "component_id": "comp1",
                "location_id": "loc1",
                "threshold": 50,
                "enabled": True,
            },
            {
                "component_id": "comp2",
                "location_id": "loc2",
                "threshold": 30,
                "enabled": True,
            },
        ]

        result = service.bulk_update_thresholds(updates)

        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert len(result["errors"]) == 0

    def test_bulk_update_thresholds_partial_failure(self):
        """Test bulk_update_thresholds with some failures"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        # First update succeeds, second fails
        def mock_update(component_id, location_id, threshold, enabled):
            if component_id == "comp1":
                return {"success": True}
            else:
                raise HTTPException(status_code=404, detail="Not found")

        service.update_reorder_threshold = Mock(side_effect=mock_update)

        updates = [
            {
                "component_id": "comp1",
                "location_id": "loc1",
                "threshold": 50,
                "enabled": True,
            },
            {
                "component_id": "comp2",
                "location_id": "loc2",
                "threshold": 30,
                "enabled": True,
            },
        ]

        result = service.bulk_update_thresholds(updates)

        assert result["success_count"] == 1
        assert result["error_count"] == 1
        assert len(result["errors"]) == 1

    def test_check_low_stock_returns_below_threshold_items(self):
        """Test check_low_stock returns ComponentLocations below threshold"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_item = Mock(spec=ComponentLocation)
        mock_item.id = "comp-loc-id"
        mock_item.component_id = "comp-id"
        mock_item.component = Mock(name="Low Stock Component")
        mock_item.storage_location_id = "loc-id"
        mock_item.storage_location = Mock(name="Drawer 1")
        mock_item.quantity_on_hand = 5
        mock_item.reorder_threshold = 20
        mock_item.reorder_shortage = 15

        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_item]

        result = service.check_low_stock()

        assert len(result) == 1
        assert result[0]["shortage_amount"] == 15

    def test_get_alert_statistics_returns_counts(self):
        """Test get_alert_statistics returns status counts and metrics"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        # Mock status counts
        mock_session.query.return_value.group_by.return_value.all.return_value = [
            ("active", 5),
            ("dismissed", 3),
            ("ordered", 2),
        ]

        # Mock active alert stats
        mock_session.query.return_value.filter.return_value.first.return_value = (
            5,  # count
            25.5,  # avg shortage
            60,  # max shortage
        )

        result = service.get_alert_statistics()

        assert "by_status" in result
        assert result["by_status"]["active"] == 5
        assert "active_alerts" in result
        assert result["active_alerts"]["count"] == 5
        assert result["active_alerts"]["avg_shortage"] == 25.5

    def test_get_alert_history_with_limit(self):
        """Test get_alert_history respects limit parameter"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        # Create mock alert with all required attributes
        def create_mock_alert():
            mock_alert = Mock(spec=ReorderAlert)
            mock_alert.id = 1
            mock_alert.component_location_id = "comp-loc-id"
            mock_alert.component_id = "comp-id"
            mock_alert.storage_location_id = "loc-id"
            mock_alert.status = "active"
            mock_alert.severity = "high"
            mock_alert.current_quantity = 10
            mock_alert.reorder_threshold = 50
            mock_alert.shortage_amount = 40
            mock_alert.shortage_percentage = 80.0
            mock_alert.created_at = "2025-01-01"
            mock_alert.updated_at = "2025-01-01"
            mock_alert.dismissed_at = None
            mock_alert.ordered_at = None
            mock_alert.resolved_at = None
            mock_alert.notes = None

            mock_component = Mock()
            mock_component.name = "Test"
            mock_component.part_number = "PN123"

            mock_location = Mock()
            mock_location.name = "Drawer"

            mock_alert.component_location = Mock()
            mock_alert.component_location.component = mock_component
            mock_alert.component_location.storage_location = mock_location
            return mock_alert

        mock_alerts = [create_mock_alert() for _ in range(50)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_alerts

        result = service.get_alert_history(limit=50)

        assert len(result) <= 50

    def test_to_dict_converts_alert_to_dictionary(self):
        """Test _to_dict helper method converts ReorderAlert to dict"""
        mock_session = Mock(spec=Session)
        service = ReorderService(mock_session)

        mock_alert = Mock(spec=ReorderAlert)
        mock_alert.id = 1
        mock_alert.component_location_id = "comp-loc-id"
        mock_alert.component_id = "comp-id"
        mock_alert.storage_location_id = "loc-id"
        mock_alert.status = "active"
        mock_alert.severity = "high"
        mock_alert.current_quantity = 10
        mock_alert.reorder_threshold = 50
        mock_alert.shortage_amount = 40
        mock_alert.shortage_percentage = 80.0
        mock_alert.created_at = "2025-01-01T00:00:00"
        mock_alert.updated_at = "2025-01-01T00:00:00"
        mock_alert.dismissed_at = None
        mock_alert.ordered_at = None
        mock_alert.resolved_at = None
        mock_alert.notes = None

        mock_component = Mock()
        mock_component.name = "Test Component"
        mock_component.part_number = "PN123"

        mock_location = Mock()
        mock_location.name = "Drawer 1"

        mock_alert.component_location = Mock()
        mock_alert.component_location.component = mock_component
        mock_alert.component_location.storage_location = mock_location

        result = service._to_dict(mock_alert)

        assert result["id"] == 1
        assert result["component_name"] == "Test Component"
        assert result["location_name"] == "Drawer 1"
        assert result["shortage_percentage"] == 80.0
        assert result["status"] == "active"
